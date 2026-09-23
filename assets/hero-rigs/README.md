# Rigged heroes — full motion

Two characters drawn in code as rigs and driven through
[`aldegad/sprite-gen`](https://github.com/aldegad/sprite-gen). Built by
[`tools/hero-rigs`](../../tools/hero-rigs).

| Hero | States | Gear |
|---|---|---|
| **Sir Vaudin** (`knight`) | idle · walk · run · attack | arming sword, kite shield, plumed helm, cloak |
| **Ilwen Greenwatch** (`archer`) | idle · walk · run · shoot | longbow, back quiver, hood |

64 frames in total — 8 per state, 192x192 cells.

| Path | What it is |
|---|---|
| `<hero>/sprite-sheet-alpha.png` | 1536x768 runtime atlas, real alpha, 4 rows x 8 frames |
| `<hero>/manifest.json` | `frame_layout.rows` — absolute rectangles, per-state fps and loop flags |
| `<hero>/gifs/<state>.gif` | Transparent loop per state |
| `<hero>/gifs/aseprite.json` | Aseprite metadata for Phaser / Flame |
| `<hero>/qa/` | Contact sheets and QA loops |
| `showcase.png` | Every frame of every state, both heroes |
| `<hero>-reel.gif` | All four states back to back |

## Timing

| State | fps | Loops |
|---|---|---|
| idle | 8 | yes |
| walk | 12 | yes |
| run | 16 | yes |
| attack / shoot | 14 | no |

## The chroma key is the tool's call, not ours

`prepare` scores each candidate key against the subject's own colours and picked
**green `#00FF00` for the knight** and **magenta `#FF00FF` for the archer** — the archer
is dressed in green, so a green key would have eaten him. The first build rendered every
strip on magenta regardless and `extract` failed on the knight, correctly. The rig now
renders *after* prepare, on whichever key it chose.

## Why rigs

sprite-gen's generation stages need an image provider — the `codex` CLI, an
`OPENAI_API_KEY`, or a Grok login. None is available here, so the characters are authored
as forward-kinematic rigs and posed per frame. That also settles the problem sprite-gen
exists to solve: identity cannot drift between frames when every frame is the same rig.

Both heroes share `body.py` — skeleton, limbs, torso, head, cloak — and differ only in
their `Build` (proportions plus palette) and their own gear. Weapons drive the arms
rather than the other way round: a pose sets the grip point and the sword or bow angle,
then two-bone IK solves both elbows, so the grip cannot slip.
