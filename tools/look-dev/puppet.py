"""Proof: animate the painted art itself by cutting it into a puppet.

Parts are lifted out of the painting, the holes they leave are inpainted with
the same push-pull diffusion used to repair the cutouts, and each part is then
rotated about its joint. The painting is never redrawn, so the look is the art's
own — that is the whole point of the approach.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, "/home/user/Screen-Translate-Overlay/tools/hero-repair")
from repair import _push_pull  # noqa: E402


def cut(art: Image.Image, box, pivot, feather=3):
    x0, y0, x1, y1 = box
    part = art.crop(box)
    a = np.array(part).astype(np.float32)
    al = a[..., 3]
    if feather:
        al = ndimage.gaussian_filter(al, feather * 0.4)
        a[..., 3] = al
    return {"img": Image.fromarray(a.astype(np.uint8), "RGBA"),
            "box": box, "pivot": (pivot[0] - x0, pivot[1] - y0), "world": pivot}


def hollow(art: Image.Image, boxes) -> Image.Image:
    """Remove the part regions and diffuse the surrounding paint into the gap."""
    a = np.array(art).astype(np.float32)
    hole = np.zeros(a.shape[:2], bool)
    for x0, y0, x1, y1 in boxes:
        hole[y0:y1, x0:x1] = True
    hole &= a[..., 3] > 24
    known = ((a[..., 3] > 200) & ~ndimage.binary_dilation(hole, np.ones((5, 5), bool)))
    filled = ndimage.gaussian_filter(_push_pull(a[..., :3], known.astype(np.float32)), (2, 2, 0))
    out = a.copy()
    out[..., :3] = np.where(hole[..., None], np.clip(filled, 0, 255), a[..., :3])
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def place(canvas: Image.Image, part, angle: float, offset=(0, 0)):
    img, piv = part["img"], part["pivot"]
    rotated = img.rotate(angle, resample=Image.BICUBIC, center=piv, expand=False)
    x0, y0, _, _ = part["box"]
    canvas.alpha_composite(rotated, (int(x0 + offset[0]), int(y0 + offset[1])))
