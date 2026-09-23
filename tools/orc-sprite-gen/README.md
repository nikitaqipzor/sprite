# Karg Ironfang — orc warrior, rig + sprites

An original Warcraft-flavoured orc, drawn in code and run through
[`aldegad/sprite-gen`](https://github.com/aldegad/sprite-gen) to produce a game-ready atlas.

Output lives in [`assets/karg-ironfang/`](../../assets/karg-ironfang).

## Why the character is drawn in code

sprite-gen's generation stages (`gen`, `gen-set`, `video`) need an image provider —
the `codex` CLI, an `OPENAI_API_KEY`, or a Grok login for the video pipeline. None was
available here, so the artwork is authored directly: a forward-kinematic 2D rig whose
poses are rendered with Pillow. That also solves the hard part of sprite work for free —
every frame is the same character, because every frame is the same rig.

Everything downstream of generation is the real sprite-gen pipeline, unchanged.

## Files

| File | What it is |
|---|---|
| `rig.py` | Drawing primitives in character space: tapered limbs, shaded capsules, rotated ovals, supersampled canvas |
| `orc.py` | The character — skeleton, two-bone IK for the two-handed grip, body parts, palette, silhouette outline |
| `anim.py` | Pose tracks: `idle`, `walk`, `attack`, `roar`, 8 frames each |
| `card.py` | Hero card: the same rig at 8x supersampling on a painted backdrop |
| `request.json` | sprite-gen run request — states, frame counts, fps, loop flags |
| `build.py` | Rebuilds every asset end to end |

## Rebuild

```bash
git clone https://github.com/aldegad/sprite-gen /tmp/sprite-gen
cd /tmp/sprite-gen && python3 -m venv .venv && ./.venv/bin/pip install -e .

cd tools/orc-sprite-gen
python build.py --sprite-gen /tmp/sprite-gen/.venv/bin/sprite-gen
```

## Pipeline

```
rig (orc.py + anim.py)
  └─ base.png                     one still, 192x192, transparent
  └─ raw/<state>.png              8-frame strips on #FF00FF, one per state
       │
       ├─ sprite-gen prepare      sprite-request.json, per-state prompts, chroma choice
       ├─ sprite-gen extract      chroma unmixed to real alpha -> frames/<state>/frame-N.png
       ├─ sprite-gen compose-atlas sprite-sheet-alpha.png + manifest.json.frame_layout
       ├─ sprite-gen compose-gif  exports/<state>.gif, transparent
       ├─ sprite-gen preview      qa/<state>-contact.png, qa/<state>.gif
       └─ sprite-gen export-aseprite exports/aseprite.json
```

`prepare` picked the chroma key itself: magenta scored 203.83 on subject distance against
green 160.01, cyan 194.32 and blue 169.24 — the green skin is what rules green out.

## Rig notes

- Character space puts the origin between the feet, `+x` forward, `+y` up. `Canvas.t()` is
  the only place that converts to image coordinates.
- The grip drives the arms, not the other way round: a pose sets the haft angle and grip
  point, then `ik()` solves both elbows. The axe cannot slip out of the hands.
- `axe_behind` flips the axe and head draw order, so an overhead wind-up puts the blade
  behind the skull instead of across the face.
- Every limb strokes itself with the outline colour before filling, so overlapping parts
  stay readable; the whole silhouette gets one more outline pass from a dilated alpha.
