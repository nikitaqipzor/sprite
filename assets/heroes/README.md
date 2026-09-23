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
