# Heroes — repaired assets

Source art supplied by the user; repaired by [`tools/hero-repair`](../../tools/hero-repair).
Cast: Arator (ranger), Baldin (dwarf), Faelas (elf archer), Mithrandir (wizard),
Peregrin (halfling).

| Path | What it is |
|---|---|
| `art/<name>.png` | Repaired full-body art, transparent, ~512 tall — checkerboard removed, holes repainted |
| `lineup/<n>_<name>.png` | Same art normalised: 512x512 cell, baseline at y=496, scaled by stature |
| `heroes-lineup.png` | 2560x512 line-up strip, wizard to halfling |
| `sprite-sheet-alpha.png` | Runtime atlas of the line-up, 2560x512 |
| `manifest.json` | `frame_layout` — absolute frame rectangles per row |
| `sprites/<name>.png` | The 256px cuts, de-hazed and de-speckled |
| `shadows/<name>/` | Projected ground shadow from the foot anchor, plus its asset json |
| `before-after.png` | Side-by-side of every fix |

## Repairs applied

| Hero | Background removed | Hole repainted |
|---|---|---|
| Arator | 6 406 px | — |
| Baldin | 8 643 px | 1 608 px (axe blade) |
| Faelas | 4 227 px | 3 426 px (cape, quiver) |
| Mithrandir | — (1px edge frame only) | — |
| Peregrin | 971 px | — |

Repainted areas are reconstructed from surrounding material, not recovered — the
original pixels are absent from the source files. See the tool README.

## Idle animation (`idle/`)

Built with sprite-gen's **Breathe** layer — a post-process that warps a single still
into a living loop. No image provider is involved, which is why it works on painted art
that has no rig.

| Path | What it is |
|---|---|
| `idle/idle-atlas.png` | 2560x9216 atlas — 5 heroes x 18 frames |
| `idle/manifest.json` | `frame_layout.rows`, 18 rectangles per hero |
| `idle/gifs/<name>.gif` | Transparent idle loop, 18 frames @ 4fps (4.5s) |
| `idle/curation.json` | The breathe sidecar that drives the bake |
| `idle/gif-manifest.json` | Per-state `breathe.phases` and the resolved anatomy |
| `idle/filmstrip.png` | Six phases of each hero, side by side |

Loop length is not arbitrary: `recommended_breathe_frames` asks for 6 frames per breath,
so 3 breaths is 18 cells. Shorter loops make the 1px phase toggle almost every frame and
read as vibration rather than breathing.

The rigid boundary is pinned per hero rather than autodetected. Autodetect looks for a
neck bottleneck; on hooded, helmeted and hatted figures it found Baldin's waist (row 212
of 329) and mid-body on Faelas. Pinned values live in `tools/hero-repair/animate.py`.

**What this is and is not.** It is an idle: the body squashes and rises, the head rides
along. Faelas, Baldin and Peregrin keep a strictly bit-identical head band; Mithrandir's
hat and Arator's hood sit inside the taper, so theirs deform very slightly — the warp is
designed around a clear neck, which a pointed hat does not provide.

Walk, attack and other locomotion are **not** included and cannot be derived from these
files. A single painted still carries no limb separation, so moving a leg needs either a
rig (as in `tools/orc-sprite-gen`, where the character is drawn in code) or an image
provider to generate new poses. Neither applies to supplied flat artwork.
