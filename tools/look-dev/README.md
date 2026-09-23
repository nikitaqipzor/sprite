# Look-dev: making sprites resemble the painted art

Two experiments answering "how do we get the sprites closer to the arts and the sets".
One of them failed, and the failure is the useful part.

## Experiment 1 — colour grading (`grade.py`): matches the numbers, misses the look

Measured over the subject pixels of both sets:

| set | sat mean | sat p90 | val mean | val sd |
|---|---|---|---|---|
| painted art | 0.17 | 0.30 | 0.20 | 0.105 |
| rig sprites | 0.30 | 0.55 | 0.34 | 0.22 |

The sprites are brighter and about twice as contrasty. `grade.py` remaps saturation and
value onto those reference statistics, drifts shadows cool, tints the flat black outline
toward the material it borders, and adds grain. At `strength=1.0` the output lands on the
target within a hundredth:

    knight graded 1.0 -> sat 0.169 / val 0.204 / sd 0.099
    archer graded 1.0 -> sat 0.186 / val 0.198 / sd 0.105

**And it still does not look like the art.** See `assets/look-dev/grade_compare.png`: at
0.75 and above the sprites just get dark and muddy, and the knight's plate loses its
read. The gap was never the palette — it is detail density (folds, straps, buckles,
scratches), edge quality, and proportion. Matching a histogram without matching those
only darkens a cartoon.

Keep `grade` for what it is actually good for: a light set-unifier at **0.35–0.5**, which
calms the palette and makes several characters agree without muddying them.

## Experiment 2 — puppet the painting (`puppet.py`): this is the one that works

Cut parts out of the painted art, inpaint the holes they leave with the same push-pull
diffusion used to repair the cutouts, then rotate each part about its joint. The painting
is never redrawn, so the look is the art's own.

`assets/look-dev/puppet_strip.png` and `puppet_idle.gif` are an 8-frame idle for Faelas
built from five parts (head, both upper arms, both forearms) plus a hollowed base.

**What it can and cannot animate.** The supplied poses are frontal portraits with the
legs together under a long coat. That supports idle, breathing, head turns, aiming,
casting, cloak sway — anything driven from the shoulders up. It does **not** support a
side-view walk cycle: the legs are neither separated nor visible, and no amount of
cutting invents them. Locomotion from painted art needs art drawn for it — side view,
legs apart, limbs not overlapping.

## Files

| File | What it does |
|---|---|
| `grade.py` | `grade(img, strength)` and `measure(img)` — the statistics above are its reference |
| `puppet.py` | `cut` (lift a part with a feathered edge), `hollow` (remove parts and inpaint), `place` (rotate about the joint) |
