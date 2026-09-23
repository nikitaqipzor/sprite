"""Grade rig sprites toward the look of the painted hero art.

The gap between the two is measurable, not a matter of taste. Against the
supplied art the rig sprites come out far brighter and far more contrasty:

    set            sat mean  sat p90   val mean  val sd
    painted art      0.17      0.30      0.20     0.10
    rig sprites      0.30      0.55      0.34     0.22

So the sprites read as "cartoon" mostly because their mid-tones are bright and
saturated and their value range is twice as wide — not because they lack colours
(both sets quantise to a couple of hundred).

`grade` remaps saturation and value onto the reference statistics, tints the
black outline toward the material it borders, and lays down a little grain.
`strength` trades likeness against readability: the art is lit for a portrait on
a dark ground, and a sprite dropped all the way to its value mean gets muddy at
192px.
"""
from __future__ import annotations

import colorsys
from dataclasses import dataclass

import numpy as np
from PIL import Image
from scipy import ndimage

# Measured over the repaired art in assets/heroes/art.
PAINTED = dict(sat_mean=0.17, sat_sd=0.13, val_mean=0.20, val_sd=0.105)


def _hsv(rgb: np.ndarray):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx, mn = rgb.max(axis=-1), rgb.min(axis=-1)
    v = mx
    s = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    d = np.maximum(mx - mn, 1e-6)
    h = np.select(
        [mx == r, mx == g, mx == b],
        [((g - b) / d) % 6, (b - r) / d + 2, (r - g) / d + 4], default=0.0) / 6.0
    return h, s, v


def _rgb(h, s, v):
    i = np.floor(h * 6.0)
    f = h * 6.0 - i
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    i = (i % 6).astype(int)
    out = np.stack([
        np.choose(i, [v, q, p, p, t, v]),
        np.choose(i, [t, v, v, q, p, p]),
        np.choose(i, [p, p, t, v, v, q])], axis=-1)
    return np.clip(out, 0, 1)


def _remap(x: np.ndarray, mask: np.ndarray, mean: float, sd: float, strength: float):
    cur = x[mask]
    if cur.size < 16:
        return x
    cur_sd = cur.std() or 1e-6
    scaled = (x - cur.mean()) * (sd / cur_sd) + mean
    return np.clip(x + (scaled - x) * strength, 0.0, 1.0)


def grade(img: Image.Image, strength: float = 0.7, ref=PAINTED,
          grain: float = 1.0, tint_outline: bool = True) -> Image.Image:
    a = np.array(img.convert("RGBA")).astype(np.float32)
    rgb, al = a[..., :3] / 255.0, a[..., 3]
    solid = al > 200
    if not solid.any():
        return img

    h, s, v = _hsv(rgb)
    s = _remap(s, solid, ref["sat_mean"], ref["sat_sd"], strength)
    v = _remap(v, solid, ref["val_mean"], ref["val_sd"], strength)
    # painted shadows drift cool; keep lit areas where they are
    shade = np.clip(1.0 - v / max(ref["val_mean"] * 2, 1e-3), 0, 1) * 0.5 * strength
    h = (h * (1 - shade) + 0.58 * shade) % 1.0
    s = np.clip(s + shade * 0.05, 0, 1)
    out = _rgb(h, s, v)

    if tint_outline:
        # a flat black stroke is a cartoon cue; let it take the colour it borders
        dark = solid & (v < 0.09)
        if dark.any():
            lit = solid & ~dark
            if lit.any():
                idx = ndimage.distance_transform_edt(
                    ~lit, return_distances=False, return_indices=True)
                near = out[tuple(idx)]
                out[dark] = np.clip(near[dark] * 0.42 + out[dark] * 0.58, 0, 1)

    if grain:
        n = ndimage.gaussian_filter(
            np.random.default_rng(11).normal(0, 0.016 * grain, out.shape[:2]), 0.7)
        out = np.clip(out + n[..., None], 0, 1)

    a[..., :3] = out * 255.0
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def measure(img: Image.Image) -> dict:
    a = np.array(img.convert("RGBA")).astype(np.float32)
    rgb, al = a[..., :3] / 255.0, a[..., 3]
    m = al > 200
    _, s, v = _hsv(rgb)
    return {"sat_mean": float(s[m].mean()), "sat_p90": float(np.percentile(s[m], 90)),
            "val_mean": float(v[m].mean()), "val_sd": float(v[m].std())}
