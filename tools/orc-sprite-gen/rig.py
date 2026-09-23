"""Ork warrior rig: forward-kinematic 2D character, rendered with Pillow.

Character space: origin at ground between the feet, +x forward (facing right),
+y up. render() converts to image space at SS x supersampling and returns RGBA.
"""
from __future__ import annotations

import math
from PIL import Image, ImageDraw, ImageFilter

SS = 3                      # supersample factor
W = H = 192                 # final cell size
BASELINE = 178              # ground line in final px
CX = 88                     # character origin x in final px

P = {
    "outline":  (23, 16, 33),
    "skin":     (109, 154, 62),
    "skin_sh":  (70, 105, 36),
    "skin_hi":  (147, 190, 92),
    "iron":     (112, 124, 136),
    "iron_sh":  (66, 74, 85),
    "iron_hi":  (168, 180, 192),
    "leather":  (122, 74, 40),
    "leather_sh": (74, 44, 22),
    "leather_hi": (164, 106, 62),
    "cloth":    (168, 50, 44),
    "cloth_sh": (106, 29, 26),
    "cloth_hi": (206, 90, 78),
    "hair":     (32, 27, 36),
    "hair_hi":  (62, 54, 70),
    "bone":     (232, 222, 190),
    "bone_sh":  (176, 163, 130),
    "eye":      (255, 208, 96),
    "haft":     (92, 60, 34),
    "haft_hi":  (128, 88, 52),
}


def d_down(a: float) -> tuple[float, float]:
    """Unit vector: straight down rotated `a` degrees toward +x (forward)."""
    r = math.radians(a)
    return (math.sin(r), -math.cos(r))


def d_up(a: float) -> tuple[float, float]:
    r = math.radians(a)
    return (math.sin(r), math.cos(r))


def step(p, v, n):
    return (p[0] + v[0] * n, p[1] + v[1] * n)


class Canvas:
    """Draws in character space, writes to a supersampled image."""

    def __init__(self):
        self.img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def t(self, p):
        return ((CX + p[0]) * SS, (BASELINE - p[1]) * SS)

    def poly(self, pts, fill):
        self.d.polygon([self.t(p) for p in pts], fill=fill)

    def disc(self, c, r, fill):
        x, y = self.t(c)
        rr = r * SS
        self.d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=fill)

    def oval(self, c, rx, ry, fill, angle=0.0):
        """Rotated ellipse as a polygon."""
        ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        pts = []
        for i in range(40):
            th = 2 * math.pi * i / 40
            ux, uy = rx * math.cos(th), ry * math.sin(th)
            pts.append((c[0] + ux * ca - uy * sa, c[1] + ux * sa + uy * ca))
        self.poly(pts, fill)

    def limb(self, a, b, wa, wb, fill):
        """Tapered capsule from a to b."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        self.poly([
            (a[0] + nx * wa / 2, a[1] + ny * wa / 2),
            (b[0] + nx * wb / 2, b[1] + ny * wb / 2),
            (b[0] - nx * wb / 2, b[1] - ny * wb / 2),
            (a[0] - nx * wa / 2, a[1] - ny * wa / 2),
        ], fill)
        self.disc(a, wa / 2, fill)
        self.disc(b, wb / 2, fill)

    def limb_shaded(self, a, b, wa, wb, base, sh, hi, stroke=2.4):
        if stroke:
            self.limb(a, b, wa + stroke, wb + stroke, P["outline"])
        self.limb(a, b, wa, wb, base)
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln          # left normal in char space
        off = 0.26
        self.limb(step(a, (nx, ny), -wa * off), step(b, (nx, ny), -wb * off),
                  wa * 0.42, wb * 0.42, sh)
        self.limb(step(a, (nx, ny), wa * off * 1.05), step(b, (nx, ny), wb * off * 1.05),
                  wa * 0.3, wb * 0.3, hi)
