"""Hero card: the same rig rendered at 8x supersampling onto a painted backdrop."""
import math
from PIL import Image, ImageDraw, ImageFilter

import rig, orc

SIZE = 768
rig.SS = 8
orc.SS = 8
orc.W = orc.H = SIZE


def backdrop(size=SIZE):
    bg = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(bg)
    top, bot = (44, 48, 62), (86, 62, 46)
    for y in range(size):
        t = y / (size - 1)
        t = t ** 1.35
        d.line([(0, y), (size, y)],
               fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    # warm glow behind the subject
    glow = Image.new("L", (size, size), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([size * 0.16, size * 0.10, size * 0.86, size * 0.86], fill=170)
    glow = glow.filter(ImageFilter.GaussianBlur(size * 0.13))
    bg = Image.composite(Image.new("RGB", (size, size), (196, 150, 92)), bg, glow.point(lambda v: v // 2))
    # ground band
    gd2 = ImageDraw.Draw(bg)
    gd2.rectangle([0, int(size * 0.845), size, size], fill=(58, 44, 36))
    for i in range(26):
        y = int(size * 0.845) + i
        k = 1 - i / 26
        gd2.line([(0, y), (size, y)], fill=(int(58 + 46 * k), int(44 + 34 * k), int(36 + 26 * k)))
    # vignette
    vig = Image.new("L", (size, size), 0)
    ImageDraw.Draw(vig).ellipse([-size * 0.22, -size * 0.22, size * 1.22, size * 1.22], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(size * 0.10))
    return Image.composite(bg, Image.new("RGB", (size, size), (18, 16, 24)), vig).convert("RGBA")


def build(pose=None, out="karg-ironfang-portrait.png"):
    hero = orc.draw(pose or {})
    card = backdrop()
    # contact shadow on the ground
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([SIZE * 0.30, SIZE * 0.815, SIZE * 0.72, SIZE * 0.885],
                               fill=(12, 10, 16, 165))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)))
    card.alpha_composite(hero)
    return card.convert("RGB")


if __name__ == "__main__":
    build().save("karg-ironfang-portrait.png")
    print("portrait written")
