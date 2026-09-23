"""Pose tracks for Karg Ironfang. Each state returns N pose dicts."""
from __future__ import annotations

import math

TAU = math.tau


def _bob(p, amp, phase=0.0):
    return amp * math.sin(p + phase)


def idle(n=8):
    out = []
    for i in range(n):
        p = TAU * i / n
        b = math.sin(p)
        out.append(dict(
            squash=1.0 + 0.016 * b,
            hip_y=64.0 + 1.1 * b,
            lean=-5.0 + 1.4 * b,
            head=5.0 + 1.8 * math.sin(p + 0.7),
            jaw=0.0,
            grip_y=72.0 + 1.3 * b,
            grip_x=22.0 + 0.6 * math.sin(p + 0.3),
            axe_ang=10.0 + 1.8 * math.sin(p + 0.4),
            thigh_f=-16.0, shin_f=-16.0, thigh_n=14.0, shin_n=10.0,
        ))
    return out


def walk(n=8):
    out = []
    for i in range(n):
        p = TAU * i / n
        sn, sf = math.sin(p), math.sin(p + math.pi)
        out.append(dict(
            hip_y=61.0 + 2.4 * abs(math.sin(p)),
            hip_x=0.6 * math.sin(2 * p),
            lean=5.0 + 1.2 * math.sin(2 * p),
            head=3.0 - 1.2 * math.sin(2 * p),
            thigh_n=31.0 * sn,
            shin_n=-30.0 * max(0.0, math.sin(p + 1.35)),
            foot_n=16.0 * sn,
            thigh_f=31.0 * sf,
            shin_f=-30.0 * max(0.0, math.sin(p + math.pi + 1.35)),
            foot_f=16.0 * sf,
            grip_x=21.0 + 1.6 * math.sin(p + math.pi),
            grip_y=71.0 + 1.8 * abs(math.sin(p)),
            axe_ang=12.0 + 4.0 * math.sin(p + math.pi),
        ))
    return out


def attack(n=8):
    """Overhead chop: 0-2 wind up, 3-5 strike, 6-7 recover."""
    keys = [
        # (grip_x, grip_y, axe_ang, lean, head, thigh_n, thigh_f, jaw, hip_y, behind)
        (18.0,  84.0,  -20.0,   -8.0,  7.0,  12.0, -15.0, 0.0, 65.0, 0),
        ( 8.0, 102.0,  -32.0,  -14.0, 11.0,   9.0, -13.0, 1.2, 66.0, 1),
        ( 2.0, 112.0,  -42.0,  -19.0, 14.0,   6.0, -12.0, 3.2, 66.0, 1),
        (12.0, 110.0,    5.0,   -6.0,  6.0,  14.0, -16.0, 3.0, 65.0, 1),
        (26.0,  94.0,   58.0,    8.0, -4.0,  24.0, -22.0, 2.0, 62.0, 0),
        (31.0,  72.0,  112.0,   19.0,-10.0,  30.0, -27.0, 0.5, 58.0, 0),
        (29.0,  62.0,  138.0,   23.0,-11.0,  27.0, -25.0, 0.0, 56.0, 0),
        (23.0,  74.0,   45.0,    6.0,  0.0,  18.0, -18.0, 0.0, 61.0, 0),
    ]
    out = []
    for gx, gy, aa, ln, hd, tn, tf, jw, hy, bh in keys[:n]:
        out.append(dict(
            grip_x=gx, grip_y=gy, axe_ang=aa, lean=ln, head=hd, jaw=jw,
            hip_y=hy, thigh_n=tn, shin_n=-tn * 0.55,
            thigh_f=tf, shin_f=tf * 0.9, grip_gap=11.0, axe_behind=bh,
        ))
    return out


def roar(n=8):
    out = []
    for i in range(n):
        p = TAU * i / n
        e = 0.5 - 0.5 * math.cos(min(1.0, i / 2.5) * math.pi)   # ramp in, hold
        b = math.sin(p * 2)
        out.append(dict(
            lean=-5.0 - 13.0 * e + 1.2 * b,
            head=5.0 + 15.0 * e,
            jaw=5.5 * e + 0.6 * b,
            hip_y=64.0 - 1.5 * e,
            squash=1.0 + 0.02 * b,
            grip_x=22.0 + 6.0 * e,
            grip_y=72.0 + 14.0 * e + 1.0 * b,
            axe_ang=10.0 - 46.0 * e + 2.0 * b,
            thigh_f=-19.0, shin_f=-16.0, thigh_n=16.0, shin_n=11.0,
        ))
    return out


STATES = {"idle": idle, "walk": walk, "attack": attack, "roar": roar}
