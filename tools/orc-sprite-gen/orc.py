"""Karg Ironfang — an original orc warrior in a Warcraft-flavoured key.

draw(pose) -> RGBA 192x192 frame, outlined, facing right.
Two-handed grip is solved by IK from the axe haft, so every pose keeps the grip.
"""
from __future__ import annotations

import math
from PIL import Image, ImageFilter

from rig import P, SS, W, H, Canvas, d_down, d_up, step

THIGH, SHIN, FOOT = 30, 27, 19
UPARM, FOREARM = 26, 23
SPINE, NECK, HEADOFF = 36, 10, 19
HAFT_UP, HAFT_DOWN = 40, 18

BASE_POSE = dict(
    hip_y=64.0, hip_x=0.0, lean=-5.0, head=5.0, squash=1.0, jaw=0.0,
    thigh_f=-16.0, shin_f=-16.0, foot_f=0.0,
    thigh_n=14.0, shin_n=10.0, foot_n=0.0,
    grip_x=22.0, grip_y=72.0, axe_ang=10.0, grip_gap=11.0,
    cape=0.0, axe_behind=0.0,
)


def rot(v, deg):
    r = math.radians(deg)
    return (v[0] * math.cos(r) - v[1] * math.sin(r),
            v[0] * math.sin(r) + v[1] * math.cos(r))


def ik(shoulder, target, l1, l2, sign):
    """Two-bone IK. sign=+1 bends the elbow one way, -1 the other."""
    dx, dy = target[0] - shoulder[0], target[1] - shoulder[1]
    d = math.hypot(dx, dy)
    d = min(max(d, abs(l1 - l2) + 0.01), l1 + l2 - 0.01)
    u = (dx / (math.hypot(dx, dy) or 1), dy / (math.hypot(dx, dy) or 1))
    ca = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    a = math.degrees(math.acos(max(-1.0, min(1.0, ca))))
    e = rot(u, a * sign)
    return (shoulder[0] + e[0] * l1, shoulder[1] + e[1] * l1)


def skeleton(po: dict) -> dict:
    hip = (po["hip_x"], po["hip_y"])
    sq = po["squash"]
    up = d_up(po["lean"])
    chest = step(hip, up, SPINE * sq)
    neck = step(chest, up, NECK)
    head_c = step(neck, d_up(po["lean"] + po["head"]), HEADOFF)
    j = {"hip": hip, "chest": chest, "neck": neck, "head": head_c}

    for tag, sx in (("f", -1.0), ("n", 1.0)):
        h = (hip[0] + sx * 3.0, hip[1] - 2)
        knee = step(h, d_down(po[f"thigh_{tag}"]), THIGH)
        ankle = step(knee, d_down(po[f"shin_{tag}"]), SHIN)
        toe = step(ankle, d_down(po[f"foot_{tag}"] + 90), FOOT)
        j[f"hip_{tag}"], j[f"knee_{tag}"], j[f"ankle_{tag}"], j[f"toe_{tag}"] = h, knee, ankle, toe
        rt = (up[1], -up[0])
        base = step(chest, up, 3.0)
        j[f"sh_{tag}"] = step(base, rt, 4.2 * sx)

    # axe haft and the two-handed grip
    u = rot((0.0, 1.0), -po["axe_ang"])            # haft direction, up-ish
    grip = (po["grip_x"], po["grip_y"])
    j["axe_u"] = u
    j["axe_butt"] = step(grip, u, -HAFT_DOWN)
    j["axe_head"] = step(grip, u, HAFT_UP)
    j["hand_n"] = grip
    j["hand_f"] = step(grip, u, -po["grip_gap"])

    j["elb_n"] = ik(j["sh_n"], j["hand_n"], UPARM, FOREARM, -1)
    j["elb_f"] = ik(j["sh_f"], j["hand_f"], UPARM, FOREARM, -1)
    return j


# ---------------------------------------------------------------- body parts
def _tone(dim):
    if dim:
        return (78, 112, 42), (54, 80, 28), (104, 144, 60)
    return P["skin"], P["skin_sh"], P["skin_hi"]


def _iron(dim):
    if dim:
        return (82, 92, 102), (52, 59, 68), (122, 133, 145)
    return P["iron"], P["iron_sh"], P["iron_hi"]


def _boot(c: Canvas, ankle, toe, dim):
    lt, ls, lh = ((92, 56, 30), (56, 33, 17), (124, 80, 47)) if dim else \
                 (P["leather"], P["leather_sh"], P["leather_hi"])
    fwd = 1.0 if toe[0] >= ankle[0] else -1.0
    sole = ankle[1] - 6.0
    heel = (ankle[0] - 3.5 * fwd, sole + 5.0)
    tip = (ankle[0] + 8.5 * fwd, sole + 4.0)
    c.limb_shaded(heel, tip, 11.5, 8.5, lt, ls, lh, stroke=2.2)
    c.limb_shaded((ankle[0] - 0.5 * fwd, ankle[1] + 3.0), heel, 11.5, 11.0, lt, ls, lh, stroke=2.2)
    c.limb(step(heel, (fwd, -0.4), 1.6), step(tip, (-fwd, -0.4), 1.6), 3.6, 3.0,
           (34, 28, 32) if dim else P["hair"])
    cuff = (46, 33, 26) if dim else (68, 48, 38)
    c.limb(step(ankle, (0, 1), 2), step(ankle, (0, 1), 9), 15.5, 13.5, P["outline"])
    c.limb(step(ankle, (0, 1), 2), step(ankle, (0, 1), 8.6), 13.5, 11.5, cuff)
    c.limb(step(ankle, (0, 1), 5.0), step(ankle, (0, 1), 8.6), 11.5, 9.0,
           (66, 50, 42) if dim else (96, 72, 58))
    c.disc(step(tip, (-fwd, 0), 2.0), 2.0, P["iron"])


def _leg(c: Canvas, j, tag, dim):
    sk, ss, sh = _tone(dim)
    c.limb_shaded(j["hip_" + tag], j["knee_" + tag], 22, 15, sk, ss, sh)
    c.limb_shaded(j["knee_" + tag], j["ankle_" + tag], 15, 11, sk, ss, sh)
    _boot(c, j["ankle_" + tag], j["toe_" + tag], dim)


def _arm(c: Canvas, j, tag, dim):
    sk, ss, sh = _tone(dim)
    ir, irs, irh = _iron(dim)
    S, E, Hd = j["sh_" + tag], j["elb_" + tag], j["hand_" + tag]
    c.limb_shaded(S, E, 20, 15, sk, ss, sh)
    c.limb_shaded(E, Hd, 15, 10, sk, ss, sh)
    v = (Hd[0] - E[0], Hd[1] - E[1])
    c.limb(step(E, v, 0.45), step(E, v, 0.92), 15, 12, irs)
    c.limb(step(E, v, 0.5), step(E, v, 0.88), 11, 9, ir)
    c.limb(step(E, v, 0.55), step(E, v, 0.8), 6, 5, irh)


def _hand(c: Canvas, j, tag, dim):
    """A fist closed around the haft, drawn across it."""
    sk, ss, sh = _tone(dim)
    Hd = j["hand_" + tag]
    u = j["axe_u"]
    n = (-u[1], u[0])
    a, b = step(Hd, n, -5.2), step(Hd, n, 5.2)
    c.limb(a, b, 12.4, 12.4, P["outline"])
    c.limb(a, b, 10.2, 10.2, ss)
    c.limb(step(a, u, 1.2), step(b, u, 1.2), 8.2, 8.2, sk)
    c.limb(step(a, u, 2.6), step(b, u, 2.2), 4.6, 4.2, sh)
    for k in (-2.4, 0.4, 3.0):
        q0 = step(step(Hd, n, k), u, 4.2)
        q1 = step(step(Hd, n, k), u, -1.0)
        c.limb(q0, q1, 1.5, 1.5, ss)


def _pauldron(c: Canvas, j, tag, dim):
    ir, irs, irh = _iron(dim)
    s = j["sh_" + tag]
    sx = 1 if tag == "n" else -1
    cen = (s[0] + 1.5 * sx, s[1] + 3.0)
    ang = -12 * sx
    c.oval(cen, 14.6, 11.0, P["outline"], angle=ang)
    c.oval(cen, 12.6, 9.2, irs, angle=ang)
    c.oval((cen[0], cen[1] + 0.9), 11.4, 8.0, ir, angle=ang)
    c.oval((cen[0] - 1.5 * sx, cen[1] + 3.0), 7.6, 3.6, irh, angle=ang)
    c.limb((cen[0] - 11, cen[1] - 4.5), (cen[0] + 11, cen[1] - 4.5), 4.0, 4.0, irs)
    for dx in (-5.5, 2.5):
        b = (cen[0] + dx, cen[1] + 6.0)
        tip = (cen[0] + dx * 1.2 - 1.0 * sx, cen[1] + 11.5)
        c.poly([(b[0] - 2.6, b[1]), (b[0] + 2.6, b[1]), tip], irh)
        c.poly([(b[0] + 0.3, b[1]), (b[0] + 2.6, b[1]), tip], ir)


def _torso(c: Canvas, j, po):
    hip, chest = j["hip"], j["chest"]
    up = d_up(po["lean"]); rt = (up[1], -up[0])

    def pt(t, side):
        p = (hip[0] + (chest[0] - hip[0]) * t, hip[1] + (chest[1] - hip[1]) * t)
        w = 10.5 + 7.0 * t ** 0.6
        return (p[0] + rt[0] * w * side, p[1] + rt[1] * w * side)

    c.poly([pt(t, 1) for t in (0, .25, .5, .75, 1)] +
           [pt(t, -1) for t in (1, .75, .5, .25, 0)], P["skin"])
    c.poly([pt(t, 1.02) for t in (.08, .4, .72, .98)] +
           [pt(t, 0.2) for t in (.98, .72, .4, .08)], P["skin_hi"])
    c.poly([pt(t, -1.02) for t in (.04, .4, .75, 1)] +
           [pt(t, -0.25) for t in (1, .75, .4, .04)], P["skin_sh"])
    # pecs and abs
    c.oval(step(chest, up, -7), 10.5, 5.2, P["skin_hi"], angle=-6)
    c.oval(step(chest, up, -6.2), 9.0, 3.8, (126, 172, 72), angle=-6)
    for k in (0, 1, 2):
        c.oval(step(chest, up, -15 - k * 6.5), 7.0 - k * 0.7, 2.3, P["skin_sh"], angle=-4)
    # shoulder strap
    a = step(chest, up, -2)
    c.limb(step(a, rt, 11), (hip[0] - rt[0] * 10, hip[1] - rt[1] * 10), 7, 7, P["leather_sh"])
    c.limb(step(a, rt, 11), (hip[0] - rt[0] * 10, hip[1] - rt[1] * 10), 3.5, 3.5, P["leather"])


def _kilt(c: Canvas, j, po, front: bool):
    hip = j["hip"]
    up = d_up(po["lean"]); rt = (up[1], -up[0])
    top = step(hip, up, 5)
    w, drop = 15, 24
    if front:
        c.poly([step(top, rt, w), step(top, rt, -w * .25),
                (hip[0] - rt[0] * 5, hip[1] - drop),
                (hip[0] + rt[0] * (w + 4), hip[1] - drop + 4)], P["cloth"])
        c.poly([step(top, rt, w * .85), step(top, rt, w * .1),
                (hip[0] + rt[0] * 4, hip[1] - drop + 2),
                (hip[0] + rt[0] * (w + 3), hip[1] - drop + 5)], P["cloth_hi"])
        for k in (0.15, 0.6):
            c.limb(step(top, rt, w * k), (hip[0] + rt[0] * (w + 2) * k, hip[1] - drop + 4),
                   2.2, 3.0, P["cloth_sh"])
    else:
        c.poly([step(top, rt, w * .3), step(top, rt, -w - 2),
                (hip[0] - rt[0] * (w + 3), hip[1] - drop + 3),
                (hip[0] + rt[0] * 4, hip[1] - drop)], P["cloth_sh"])
        c.limb(step(top, rt, -w * .55), (hip[0] - rt[0] * (w) , hip[1] - drop + 5),
               2.4, 3.0, (84, 22, 20))
    # belt over both flaps
    c.limb(step(top, rt, -w + 3), step(top, rt, w - 1), 13, 13, P["leather_sh"])
    c.limb(step(top, rt, -w + 4), step(top, rt, w - 2), 9, 9, P["leather"])
    c.oval(step(top, rt, 5), 7.0, 5.8, P["iron_sh"])
    c.oval(step(top, rt, 5), 5.2, 4.2, P["iron"])
    c.oval(step(top, rt, 4.2), 3.0, 2.2, P["iron_hi"])


def _head(c: Canvas, j, po):
    hc = j["head"]
    up = d_up(po["lean"] + po["head"]); rt = (up[1], -up[0])

    def q(f, u):
        return (hc[0] + rt[0] * f + up[0] * u, hc[1] + rt[1] * f + up[1] * u)

    c.limb(j["neck"], step(j["neck"], up, 9), 17, 15, P["skin_sh"])
    c.limb(j["neck"], step(j["neck"], up, 7), 11, 10, P["skin"])
    # skull, brow shelf, heavy jaw
    c.oval(hc, 17.6, 16.6, P["outline"], angle=-6)
    c.poly([q(-9, 3), q(14, 0), q(18.6, -9), q(14, -17.6), q(-2.5, -18.6), q(-11.6, -9)], P["outline"])
    c.oval(hc, 16.0, 15.0, P["skin"], angle=-6)
    c.poly([q(-8, 2), q(13, -1), q(17, -9), q(13, -16), q(-2, -17), q(-10, -9)], P["skin"])
    c.oval(q(-5, 5), 11.5, 6.8, P["skin_hi"], angle=-7)
    c.oval(q(-9.5, -5), 7.5, 9.0, P["skin_sh"])
    c.oval(q(8, -11), 9.0, 6.2, P["skin"], angle=-12)
    c.oval(q(8.5, -12.6), 7.0, 3.8, P["skin_hi"], angle=-12)
    c.poly([q(-5, 1.5), q(15, -2.0), q(15, -6.5), q(-4, -4.0)], P["skin_sh"])
    c.poly([q(-4, 0.8), q(14, -2.6), q(14, -4.8), q(-3, -2.6)], (58, 88, 30))
    # eye
    c.oval(q(8.0, -5.4), 3.6, 2.5, (26, 20, 13), angle=-12)
    c.oval(q(8.7, -5.1), 2.3, 1.6, P["eye"], angle=-12)
    c.oval(q(9.4, -4.9), 0.95, 1.05, (255, 248, 220))
    # nose
    c.poly([q(13, -7.5), q(17.5, -10.5), q(12.5, -12)], P["skin_sh"])
    c.oval(q(14.0, -10.6), 1.3, 0.95, (42, 60, 22))
    # mouth and tusks
    jw = po["jaw"]
    c.limb(q(1.5, -14.5 - jw), q(13.0, -15.0 - jw), 3.4, 2.4, (46, 30, 34))
    for fx, sc in ((10.8, 1.0), (2.0, 0.8)):
        b = q(fx, -15.0 - jw)
        tip = q(fx + 2.0, -5.5 - jw * 0.5) if sc == 1.0 else q(fx + 1.2, -7.5 - jw * 0.5)
        c.poly([(b[0] - 2.8 * sc, b[1]), (b[0] + 2.8 * sc, b[1]), tip], P["bone"])
        c.poly([(b[0] + 0.4, b[1]), (b[0] + 2.8 * sc, b[1]), tip], P["bone_sh"])
    # ear
    c.poly([q(-9, 1), q(-21, 6), q(-11, -7)], P["skin"])
    c.poly([q(-10.5, 0.5), q(-18, 4.5), q(-11.5, -4.5)], P["skin_sh"])
    # shaved sides, topknot, braid
    c.poly([q(-12, 5), q(1, 11), q(11, 5), q(9, 8.5), q(-3, 14), q(-13, 9)], P["hair"])
    c.oval(q(-4, 16.0), 7.0, 5.4, P["hair"], angle=16)
    c.oval(q(-5, 17.0), 4.4, 3.0, P["hair_hi"], angle=16)
    c.limb(q(-10, 9), q(-21, -3), 7.5, 5.5, P["hair"])
    c.limb(q(-21, -3), q(-25, -14), 5.5, 3.8, P["hair"])
    c.limb(q(-11, 9), q(-19, -1), 3.0, 2.2, P["hair_hi"])
    c.disc(q(-22, -7), 2.6, P["leather"])


def _axe(c: Canvas, j):
    u, butt, head = j["axe_u"], j["axe_butt"], j["axe_head"]
    n = (-u[1], u[0])
    c.limb(butt, head, 9.6, 8.6, P["outline"])
    c.limb(butt, head, 7.2, 6.2, P["haft"])
    c.limb(step(butt, u, 3), step(head, u, -3), 3.0, 2.4, P["haft_hi"])
    c.disc(butt, 4.8, P["iron_sh"])
    c.disc(step(butt, u, 1.5), 3.2, P["iron"])
    r = (u[1], -u[0])                       # forward side of the haft
    b = (-r[0], -r[1])
    p_lo = step(step(head, u, -11), r, 4.0)
    p_hi = step(step(head, u, 9), r, 4.5)
    e_hi = step(step(head, u, 6), r, 17)
    e_lo = step(step(head, u, -9), r, 20)
    c.poly([step(p_lo, (-r[0], -r[1]), 2.2), step(p_hi, (-r[0], -r[1]), 2.2),
            step(e_hi, r, 2.2), step(e_lo, r, 2.2)], P["outline"])
    c.poly([p_lo, p_hi, e_hi, e_lo], P["iron"])
    c.poly([p_lo, p_hi, step(step(head, u, 1), r, 10)], P["iron_sh"])
    c.poly([e_lo, e_hi, step(e_hi, r, -4.0), step(e_lo, r, -4.5)], P["iron_hi"])
    # back spike
    c.poly([step(step(head, u, -5), b, 3), step(step(head, u, 6), b, 3),
            step(step(head, u, 1), b, 12)], P["iron_sh"])
    c.poly([step(step(head, u, 0.5), b, 3), step(step(head, u, 6), b, 3),
            step(step(head, u, 1), b, 12)], P["iron"])
    c.limb(step(head, u, -11), step(head, u, 8), 8.5, 8.5, P["iron_sh"])
    c.limb(step(head, u, -9), step(head, u, 6), 5.0, 5.0, P["iron"])


def draw(pose: dict) -> Image.Image:
    po = dict(BASE_POSE); po.update(pose)
    j = skeleton(po)
    c = Canvas()
    _arm(c, j, "f", True)
    _hand(c, j, "f", True)
    _leg(c, j, "f", True)
    _kilt(c, j, po, front=False)
    _pauldron(c, j, "f", True)
    _torso(c, j, po)
    _leg(c, j, "n", False)
    _kilt(c, j, po, front=True)
    if po["axe_behind"]:
        _axe(c, j)
        _head(c, j, po)
    else:
        _head(c, j, po)
        _axe(c, j)
    _arm(c, j, "n", False)
    _pauldron(c, j, "n", False)
    _hand(c, j, "n", False)

    body = c.img
    a = body.split()[3]
    k = 3 * SS + 1 if (3 * SS) % 2 == 0 else 3 * SS
    grown = a.filter(ImageFilter.MaxFilter(k))
    out = Image.new("RGBA", body.size, P["outline"] + (0,))
    out.putalpha(grown.point(lambda v: 255 if v > 40 else 0))
    return Image.alpha_composite(out, body).resize((W, H), Image.LANCZOS)
