#!/usr/bin/env python3
"""Render both rigged heroes and drive them through sprite-gen.

    python build.py --sprite-gen /path/to/.venv/bin/sprite-gen --out ../../assets/hero-rigs

Stage 1 (here)      rig -> base still + one magenta strip per state.
Stage 2 (sprite-gen) prepare -> extract -> compose-atlas -> compose-gif -> preview.

The magenta strips stand in for what an image provider would return, so the
sprite-gen half runs exactly as it does on generated art. Posing a rig is also
what keeps the character identical across frames, which is the failure mode
sprite-gen exists to correct.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

import archer
import knight
import tracks

CELL = 192
MODULES = {"knight": knight, "archer": archer}
FPS = {"idle": 8, "walk": 12, "run": 16, "attack": 14, "shoot": 14}
LOOP = {"idle": True, "walk": True, "run": True, "attack": False, "shoot": False}
DESC = {
    "knight": "plate knight with arming sword and kite shield, red plume and cloak",
    "archer": "hooded elf ranger with a longbow and a back quiver",
}


def render_base(hero: str, work: Path) -> Path:
    hero_dir = work / hero
    hero_dir.mkdir(parents=True, exist_ok=True)
    MODULES[hero].draw({}).save(hero_dir / "base.png")
    return hero_dir


def render_strips(hero: str, run: Path, chroma: tuple[int, int, int]) -> None:
    """One strip per state, on the key `prepare` picked for this character.

    The key is not ours to choose: prepare scores each candidate against the
    subject's own colours, and it lands on green for the knight and magenta for
    the green-clad archer. Rendering on a fixed key would key away the hero.
    """
    module = MODULES[hero]
    for name, fn in tracks.HEROES[hero].items():
        poses = fn()
        strip = Image.new("RGBA", (CELL * len(poses), CELL), chroma + (255,))
        for i, pose in enumerate(poses):
            strip.alpha_composite(module.draw(pose), (i * CELL, 0))
        strip.convert("RGB").save(run / "raw" / f"{name}.png")


def request_for(hero: str, path: Path) -> Path:
    states = {
        name: {"frames": tracks.N, "fps": FPS[name], "loop": LOOP[name],
               "action": f"{name} cycle" if LOOP[name] else f"{name} sequence"}
        for name in tracks.HEROES[hero]
    }
    path.write_text(json.dumps({
        "states": states,
        "style": "hand-painted cartoon sprite, bold dark outline, warm rim light",
    }, indent=2))
    return path


def run_pipeline(cli: Path, hero_dir: Path, hero: str) -> Path:
    run = hero_dir / "run"

    def sg(*a: str) -> None:
        subprocess.run([str(cli), *a], check=True, stdout=subprocess.DEVNULL)

    sg("prepare", "--out-dir", str(run), "--character-id", hero,
       "--base-image", str(hero_dir / "base.png"),
       "--request", str(request_for(hero, hero_dir / "request.json")),
       "--description", DESC[hero], "--cell-size", str(CELL), "--force")
    request = json.loads((run / "sprite-request.json").read_text())
    chroma = tuple(request["chroma_key"]["rgb"])
    print(f'{hero}: chroma key {request["chroma_key"]["name"]} {request["chroma_key"]["hex"]}')
    render_strips(hero, run, chroma)

    sg("extract", "--run-dir", str(run))
    sg("compose-atlas", "--run-dir", str(run))
    sg("compose-gif", "--run-dir", str(run), "--out-dir", str(run / "exports"))
    sg("preview", "--run-dir", str(run))
    sg("export-aseprite", "--run-dir", str(run))
    return run


def publish(hero: str, run: Path, out: Path) -> None:
    dst = out / hero
    (dst / "gifs").mkdir(parents=True, exist_ok=True)
    (dst / "qa").mkdir(parents=True, exist_ok=True)
    for name in ("sprite-sheet-alpha.png", "manifest.json", "sprite-request.json"):
        shutil.copy2(run / name, dst / name)
    for src in (run / "exports").iterdir():
        if src.suffix in (".gif", ".json"):
            shutil.copy2(src, dst / "gifs" / src.name)
    for src in (run / "qa").iterdir():
        shutil.copy2(src, dst / "qa" / src.name)


def main() -> int:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--sprite-gen", required=True)
    ap.add_argument("--work", default=str(here / "_work"))
    ap.add_argument("--out", default=str(here.parents[1] / "assets" / "hero-rigs"))
    args = ap.parse_args()

    cli, work, out = Path(args.sprite_gen).resolve(), Path(args.work), Path(args.out).resolve()
    work.mkdir(parents=True, exist_ok=True)
    for hero in MODULES:
        run = run_pipeline(cli, render_base(hero, work), hero)
        publish(hero, run, out)
        manifest = json.loads((run / "manifest.json").read_text())
        rows = manifest["frame_layout"]["rows"]
        print(f'{hero}: ' + ', '.join(f'{k} x{len(v)}' for k, v in rows.items()))
    print(f"assets written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
