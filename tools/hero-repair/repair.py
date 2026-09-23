"""Repair the hero cutouts.

Every file in `new/` carries a flattened transparency checkerboard. Two very
different things hide behind it, and they need opposite treatment:

* **background** the upstream cutter never keyed — erase it;
* **holes punched through the subject**, where the cutter ate light, low
  contrast parts of the character (Baldin's axe blade, Faelas' cape and
  quiver) and the preview grid shows through — paint them back in.

Telling them apart does not need the grid pitch, which differs per file
because the images were scaled independently. A checker patch that can reach
the image border through empty space is background; one sealed inside the
subject's own silhouette is a hole.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from scipy import ndimage

BRIGHT_ALPHA, BRIGHT_LUM, BRIGHT_SAT = 200, 160, 60
MIN_REGION = 300


def _channels(a: np.ndarray):
    rgb = a[..., :3].astype(float)
    al = a[..., 3].astype(float)
    lum = rgb.mean(axis=2)
    sat = rgb.max(axis=2) - rgb.min(axis=2)
    return rgb, al, lum, sat


def classify(a: np.ndarray):
    """Split the baked checkerboard into background to drop and holes to fill."""
    _, al, lum, sat = _channels(a)
    bright = (al > BRIGHT_ALPHA) & (lum > BRIGHT_LUM) & (sat < BRIGHT_SAT)
    empty = al < 32

    lab_p, _ = ndimage.label(empty | bright)
    edge = set(np.unique(np.concatenate(
        [lab_p[0], lab_p[-1], lab_p[:, 0], lab_p[:, -1]]))) - {0}

    lab, n = ndimage.label(bright)
    background = np.zeros_like(bright)
    holes = np.zeros_like(bright)
    for i in range(1, n + 1):
        m = lab == i
        reaches = bool(set(np.unique(lab_p[m])) & edge)
        if reaches:
            background |= m
        elif m.sum() >= MIN_REGION:
            holes |= m

    # webp smeared the grid edges; take the halo around dropped background too
    halo = ndimage.binary_dilation(background, np.ones((5, 5), bool))
    background |= halo & (al > 120) & (lum > 140) & (sat < 75) & ~holes
    holes = ndimage.binary_closing(holes, np.ones((5, 5), bool)) & (al > 120)
    return holes, background & ~holes


# ------------------------------------------------------------------ inpainting
def _push_pull(values: np.ndarray, weight: np.ndarray, levels: int = 9):
    vs, ws = [values * weight[..., None]], [weight]
    for _ in range(levels):
        v, w = vs[-1], ws[-1]
        if min(v.shape[:2]) < 2:
            break
        h, wd = v.shape[0] // 2 * 2, v.shape[1] // 2 * 2
        vs.append(v[:h, :wd].reshape(h // 2, 2, wd // 2, 2, -1).sum(axis=(1, 3)))
        ws.append(w[:h, :wd].reshape(h // 2, 2, wd // 2, 2).sum(axis=(1, 3)))
    out = vs[-1] / np.maximum(ws[-1][..., None], 1e-6)
    for k in range(len(vs) - 2, -1, -1):
        up = np.repeat(np.repeat(out, 2, axis=0), 2, axis=1)
        up = up[:vs[k].shape[0], :vs[k].shape[1]]
        pad = [(0, vs[k].shape[0] - up.shape[0]), (0, vs[k].shape[1] - up.shape[1]), (0, 0)]
        if pad[0][1] or pad[1][1]:
            up = np.pad(up, pad, mode="edge")
        w = ws[k][..., None]
        out = np.where(w > 0, vs[k] / np.maximum(w, 1e-6), up)
    return out


def inpaint(a: np.ndarray, holes: np.ndarray, grain: float = 1.0) -> np.ndarray:
    """Fill holes by diffusing the surrounding material inward.

    The mask is grown before filling: the anti-aliased rim of the grid is too
    dim to pass the bright test, and left in place it reads as a dotted outline
    tracing the repair. Every remaining bright-flat pixel is also withheld from
    the source, so no grid colour leaks into the fill.
    """
    if not holes.any():
        return a
    _, al, lum, sat = _channels(a)
    grown = ndimage.binary_dilation(holes, np.ones((7, 7), bool))
    leftover = (lum > 150) & (sat < 75) & (al > 120)
    known = ((al > 200) & ~grown & ~(leftover & ndimage.binary_dilation(
        holes, np.ones((25, 25), bool)))).astype(np.float32)

    rgb = a[..., :3].astype(np.float32)
    filled = ndimage.gaussian_filter(_push_pull(rgb, known), (2.6, 2.6, 0))

    if grain:
        rim = ndimage.binary_dilation(grown, np.ones((13, 13), bool)) & (known > 0)
        sigma = float(rgb[rim].std()) if rim.any() else 6.0
        noise = ndimage.gaussian_filter(
            np.random.default_rng(7).normal(0, min(sigma, 12.0) * 0.28 * grain, holes.shape), 0.9)
        filled = filled + noise[..., None]

    out = a.copy()
    paint = grown & (al > 60)
    out[..., :3] = np.where(paint[..., None], np.clip(filled, 0, 255), rgb).astype(np.uint8)
    out[..., 3] = np.where(paint, np.maximum(out[..., 3], 255), out[..., 3]).astype(np.uint8)
    return out


# --------------------------------------------------------------------- tidy-up
def strip_border_frame(a: np.ndarray, depth: int = 2) -> np.ndarray:
    """Clear a dark translucent frame baked around the image edge."""
    rgb, al, _, _ = _channels(a)
    h, w = al.shape
    out = a.copy()
    alpha = out[..., 3]
    for sy, sx in ((slice(0, depth), slice(None)), (slice(h - depth, h), slice(None)),
                   (slice(None), slice(0, depth)), (slice(None), slice(w - depth, w))):
        band_a, band_rgb = al[sy, sx], rgb[sy, sx]
        vis = band_a > 8
        if vis.mean() < 0.5:
            continue
        dark = vis & (band_rgb.mean(axis=2) < 45) & (band_a < 200)
        if dark.sum() / max(vis.sum(), 1) > 0.75:
            band = alpha[sy, sx]
            band[dark] = 0
            alpha[sy, sx] = band
    return out


def despeckle(a: np.ndarray, min_area: int = 140) -> np.ndarray:
    al = a[..., 3]
    lab, n = ndimage.label(al > 24)
    if n <= 1:
        return a
    areas = ndimage.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1))
    keep = np.isin(lab, np.nonzero(areas >= min_area)[0] + 1)
    out = a.copy()
    out[..., 3] = np.where(keep, al, 0)
    return out


def clean_edges(a: np.ndarray) -> np.ndarray:
    """Soften the chewed matte and pull background colour out of edge pixels."""
    out = a.copy()
    al = out[..., 3].astype(np.float32)
    al = ndimage.median_filter(al, 3)
    al = ndimage.gaussian_filter(al, 0.5)
    out[..., 3] = np.clip(al, 0, 255).astype(np.uint8)

    solid = out[..., 3] > 235
    if solid.any():
        idx = ndimage.distance_transform_edt(~solid, return_distances=False, return_indices=True)
        near = out[..., :3][tuple(idx)]
        edge = (out[..., 3] > 8) & ~solid
        w = (1.0 - out[..., 3][edge, None] / 235.0)
        out[..., :3][edge] = (out[..., :3][edge] * (1 - w) + near[edge] * w).astype(np.uint8)
    return out


def repair(a: np.ndarray):
    holes, background = classify(a)
    out = a.copy()
    out[..., 3] = np.where(background, 0, out[..., 3])
    out = inpaint(out, holes)
    out = strip_border_frame(out)
    out = despeckle(out)
    out = clean_edges(out)
    return out, {"hole_px": int(holes.sum()), "background_px": int(background.sum())}


def load(p):
    return np.array(Image.open(p).convert("RGBA"))


def save(a, p):
    Image.fromarray(a, "RGBA").save(p)


def strip_haze(a: np.ndarray, floor: int = 70, reach: int = 4) -> np.ndarray:
    """Drop faint background left behind by a threshold-style cut.

    Genuine soft edges hug the silhouette; leftover haze floats away from it.
    Anything faint and further than `reach` from a solid pixel goes.
    """
    al = a[..., 3]
    solid = al > 180
    if not solid.any():
        return a
    dist = ndimage.distance_transform_edt(~solid)
    haze = (al > 0) & (al < floor) & (dist > reach)
    out = a.copy()
    out[..., 3] = np.where(haze, 0, al)
    return out


def repair_sprite(a: np.ndarray):
    """Cleanup for the 256px cuts: haze, debris and a chewed matte."""
    before = int(((a[..., 3] > 0) & (a[..., 3] < 180)).sum())
    out = strip_haze(a)
    out = despeckle(out, min_area=90)
    out = clean_edges(out)
    after = int(((out[..., 3] > 0) & (out[..., 3] < 180)).sum())
    return out, {"soft_px_before": before, "soft_px_after": after}
