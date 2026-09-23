# Hero rigs

Two rigged characters with full locomotion, rendered to sprite atlases via
[`aldegad/sprite-gen`](https://github.com/aldegad/sprite-gen). Output lives in
[`assets/hero-rigs/`](../../assets/hero-rigs).

| File | What it holds |
|---|---|
| `rig.py` | Primitives in character space: tapered capsules, shaded limbs, rotated ovals, two-bone IK, the supersampled canvas |
| `body.py` | The humanoid every hero shares — `Build` (proportions + palette), skeleton, legs, arms, torso, cloak, head |
| `knight.py` | Sir Vaudin: plate, pauldrons, tassets, kite shield, arming sword, plumed helm |
| `archer.py` | Ilwen Greenwatch: hood drawn behind the face, back quiver, longbow with a string that only bends when an arrow is nocked |
| `tracks.py` | Pose tracks — idle, walk, run, attack/shoot, 8 frames each |
| `build.py` | Renders both heroes and runs the sprite-gen half end to end |

## Rebuild

```bash
git clone https://github.com/aldegad/sprite-gen /tmp/sprite-gen
cd /tmp/sprite-gen && python3 -m venv .venv && ./.venv/bin/pip install -e .

cd tools/hero-rigs
python build.py --sprite-gen /tmp/sprite-gen/.venv/bin/sprite-gen
```

## Pipeline order matters

```
rig -> base.png
  └─ sprite-gen prepare        picks the chroma key from the base image
       └─ rig -> raw/<state>.png   strips rendered ON THAT KEY
            ├─ sprite-gen extract        key unmixed to real alpha
            ├─ sprite-gen compose-atlas  atlas + manifest.frame_layout
            ├─ sprite-gen compose-gif    transparent per-state loops
            ├─ sprite-gen preview        QA contact sheets
            └─ sprite-gen export-aseprite
```

Rendering the strips before `prepare` is a bug, not a shortcut: the key is chosen per
character, and it is green for the knight and magenta for the green-clad archer.

## Rig notes

- Character space puts the origin between the feet, `+x` forward, `+y` up. `Canvas.t` is
  the only conversion to pixels, so poses never deal in image coordinates.
- Gear drives the arms. A pose sets the grip point and the weapon angle; `ik()` solves
  both elbows. The sword and the bow cannot slip out of the hands in any frame.
- `head()` takes a `pre_fn` as well as a `face_fn`. The knight's helmet covers his face
  on purpose; the archer's hood has to sit *behind* the head or it paints over her face —
  which is exactly what the first version did.
- Every limb strokes itself with the outline colour before filling, so overlapping parts
  stay readable; the finished silhouette gets one more outline pass from a dilated alpha.
- `tools/orc-sprite-gen/rig.py` is an earlier, palette-bound copy of these primitives.
