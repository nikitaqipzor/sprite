"""Normalise the repaired heroes to one baseline and a believable height order."""
from __future__ import annotations

from PIL import Image

CELL = 512
FLOOR = 496            # baseline inside the cell
TALLEST = 470

# Relative stature, so a hobbit does not end up as tall as a wizard.
STATURE = {"mithrandir": 1.00, "faelas": 0.97, "arator": 0.95,
           "baldin": 0.70, "peregrin": 0.62}
ORDER = ["mithrandir", "faelas", "arator", "baldin", "peregrin"]


def normalise(path: str, name: str, cell: int = CELL) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    box = im.split()[3].point(lambda v: 255 if v > 8 else 0).getbbox()
    im = im.crop(box)
    target_h = int(round(TALLEST * STATURE[name]))
    scale = target_h / im.height
    im = im.resize((max(1, round(im.width * scale)), target_h), Image.LANCZOS)
    out = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
    out.alpha_composite(im, ((cell - im.width) // 2, FLOOR - target_h))
    return out
