#!/usr/bin/env python3
"""Rebuild every Karg Ironfang asset from the rig.

    python build.py --sprite-gen /path/to/sprite-gen --out ../../assets/karg-ironfang

Stage 1 (this file)  rig -> base still, magenta state strips, hero card.
Stage 2 (sprite-gen) extract -> compose-atlas -> compose-gif -> preview -> export-aseprite.

The magenta strips stand in for what an image provider would return, so the
sprite-gen half of the pipeline runs exactly as it does on generated art.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

import anim
import card
import orc
import rig

CELL = 192
CHROMA = (255, 0, 255, 255)


def render_art(work: Path) -> None:
    rig.SS = orc.SS = 3
    orc.W = orc.H = CELL
    orc.draw({}).save(work / "base.png")

    raw = work / "run" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    for state, track in anim.STATES.items():
        poses = track(8)
        strip = Image.new("RGBA", (CELL * len(poses), CELL), CHROMA)
        for i, pose in enumerate(poses):
            strip.alpha_composite(orc.draw(pose), (i * CELL, 0))
        strip.convert("RGB").save(raw / f"{state}.png")

    rig.SS = orc.SS = 8
    orc.W = orc.H = 768
    orc.draw({}).save(work / "karg-ironfang-720-alpha.png")
    card.SIZE = 768
    card.build().save(work / "karg-ironfang-portrait.png")


def run_pipeline(cli: Path, run_dir: Path, base: Path, request: Path) -> None:
    def sg(*args: str) -> None:
        subprocess.run([str(cli), *args], check=True, stdout=subprocess.DEVNULL)

    raw_backup = run_dir.parent / "_raw"
    if raw_backup.exists():
        shutil.rmtree(raw_backup)
    shutil.copytree(run_dir / "raw", raw_backup)
    sg("prepare", "--out-dir", str(run_dir), "--character-id", "karg-ironfang",
       "--base-image", str(base), "--request", str(request), "--cell-size", str(CELL),
       "--description",
       "orc warrior with a two-handed axe, green skin, tusks, iron pauldron, red kilt",
       "--force")
    for png in raw_backup.glob("*.png"):
        shutil.copy2(png, run_dir / "raw" / png.name)
    shutil.rmtree(raw_backup)

    sg("extract", "--run-dir", str(run_dir))
    sg("compose-atlas", "--run-dir", str(run_dir))
    sg("compose-gif", "--run-dir", str(run_dir), "--out-dir", str(run_dir / "exports"))
    sg("preview", "--run-dir", str(run_dir))
    sg("export-aseprite", "--run-dir", str(run_dir))


def publish(work: Path, out: Path) -> None:
    (out / "exports").mkdir(parents=True, exist_ok=True)
    (out / "qa").mkdir(parents=True, exist_ok=True)
    run = work / "run"
    for name in ("karg-ironfang-portrait.png", "karg-ironfang-720-alpha.png", "base.png"):
        shutil.copy2(work / name, out / name)
    for name in ("sprite-sheet-alpha.png", "manifest.json", "sprite-request.json"):
        shutil.copy2(run / name, out / name)
    for src in list((run / "exports").iterdir()):
        if src.suffix in (".gif", ".json"):
            shutil.copy2(src, out / "exports" / src.name)
    for src in (run / "qa").iterdir():
        shutil.copy2(src, out / "qa" / src.name)


def main() -> int:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--sprite-gen", required=True,
                    help="sprite-gen executable (the venv one, e.g. <clone>/.venv/bin/sprite-gen)")
    ap.add_argument("--work", default=str(here / "_work"))
    ap.add_argument("--out", default=str(here.parents[1] / "assets" / "karg-ironfang"))
    args = ap.parse_args()

    work = Path(args.work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    render_art(work)
    run_pipeline(Path(args.sprite_gen).resolve(), work / "run",
                 work / "base.png", here / "request.json")
    publish(work, Path(args.out).resolve())
    print(f"assets written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
