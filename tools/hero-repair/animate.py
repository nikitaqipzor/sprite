#!/usr/bin/env python3
"""Turn the repaired hero stills into idle breathing loops with sprite-gen.

    python animate.py --sprite-gen /path/to/.venv/bin/sprite-gen --lineup ../../assets/heroes/lineup

Breathe is sprite-gen's own post-process layer: it warps a single still into a
living loop, squashing the body while the head rides along as a unit. No
generation provider is involved, which is why it works here at all.

Two things are not left to autodetect:

* **Sequence length.** `recommended_breathe_frames` wants SMOOTH_CYCLE_FRAMES(6)
  frames per breath — 3 breaths means 18 cells. Shorter loops make the 1px
  phase toggle almost every frame and read as vibration, not breathing.
* **The rigid boundary.** Autodetect looks for a neck bottleneck. These are
  painted figures in hoods, helmets and a pointed hat, so it found the waist on
  Baldin (row 212 of 329) and mid-body on Faelas. Pinned per hero below.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Rows below the crown of each silhouette where the body may start deforming.
RIGID_ROW = {"mithrandir": 103, "faelas": 68, "arator": 71, "baldin": 86, "peregrin": 70}
DEPTH = {"mithrandir": 0.055, "faelas": 0.05, "arator": 0.05, "baldin": 0.045, "peregrin": 0.06}
BREATHS, LAG, FPS = 3, 0.10, 4


def stage_frames(lineup: Path, work: Path) -> int:
    from sprite_gen.effects.breathe import recommended_breathe_frames

    n_frames = recommended_breathe_frames({"depth": 0.06, "breaths": BREATHS, "lag": LAG})
    src_dir = work / "frames_in"
    if src_dir.exists():
        shutil.rmtree(src_dir)
    for name in RIGID_ROW:
        matches = sorted(lineup.glob(f"*_{name}.png")) or sorted(lineup.glob(f"{name}.png"))
        if not matches:
            raise SystemExit(f"no lineup PNG for {name} in {lineup}")
        out = src_dir / name
        out.mkdir(parents=True)
        for i in range(n_frames):
            shutil.copy(matches[0], out / f"frame-{i:02d}.png")
    return n_frames


def write_sidecar(run: Path) -> None:
    from sprite_gen.curate.curation import write_curation_atomic

    request = json.loads((run / "sprite-request.json").read_text())
    for name in RIGID_ROW:
        request["states"][name].update({"fps": FPS, "loop": True, "action": "idle breathing"})
    (run / "sprite-request.json").write_text(json.dumps(request, indent=2))

    write_curation_atomic(run, {
        "version": 1,
        "kind": "sprite-gen-curation",
        "states": {name: {"breathe": {"depth": DEPTH[name], "breaths": BREATHS,
                                      "lag": LAG, "rigid_row": row}}
                   for name, row in RIGID_ROW.items()},
    })


def main() -> int:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--sprite-gen", required=True)
    ap.add_argument("--lineup", default=str(here.parents[1] / "assets" / "heroes" / "lineup"))
    ap.add_argument("--work", default=str(here / "_anim"))
    args = ap.parse_args()

    cli, work = Path(args.sprite_gen).resolve(), Path(args.work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    frames = stage_frames(Path(args.lineup).resolve(), work)

    run = work / "run"
    def sg(*a: str) -> None:
        subprocess.run([str(cli), *a], check=True, stdout=subprocess.DEVNULL)

    if run.exists():
        shutil.rmtree(run)
    sg("unpack-atlas", "--pngs-dir", str(work / "frames_in"), "--out-dir", str(run), "--force")
    write_sidecar(run)
    sg("compose-atlas", "--run-dir", str(run))
    sg("compose-gif", "--run-dir", str(run), "--out-dir", str(run / "exports"))

    report = json.loads((run / "exports" / "gif-manifest.json").read_text())
    for entry in report["exports"]:
        anat = entry["breathe"]["resolved"]["anatomy"]
        print(f'{entry["state"]:11s} {entry["frames"]:2d} frames @ {entry["fps"]}fps  '
              f'rigid_row={anat["rigid_row"]} ({anat["rigid_source"]})')
    print(f"{frames} frames per state; run at {run}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
