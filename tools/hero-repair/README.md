# Hero cutout repair

Repairs the five hero assets in [`assets/heroes/`](../../assets/heroes), then normalises
them into one line-up and a runtime atlas via
[`aldegad/sprite-gen`](https://github.com/aldegad/sprite-gen).

## What was wrong with the source

Every file in the supplied `new/` set had a **transparency checkerboard flattened into
the image** — someone exported a preview rather than the asset. An 8px grid for Baldin,
about 5px for Faelas, because the images were scaled independently.

Two different problems hide behind that grid, and they need opposite treatment:

| | What it is | Fix |
|---|---|---|
| **Background** | The cutter keyed the dark checker squares but kept the light ones, leaving opaque blobs above the heads — 5.9k px on Arator, 8.6k px on Baldin | Erase |
| **Holes** | The cutter ate light, low-contrast parts of the *character*: Baldin's axe blade, Faelas' cape and quiver. The preview grid shows through the gap | Repaint |

Mithrandir had neither — just a 1px dark translucent frame around the image edge.

The `sprites/` set had a different fault: a threshold-style cut that left soft background
haze floating off the silhouette, loose debris, and a chewed matte.

## How background and holes are told apart

Not by the grid pitch, which differs per file, and not by colour, which would eat steel
and white hair. **A checker patch that can reach the image border through empty space is
background; one sealed inside the subject's own silhouette is a hole.** One flood fill
decides it, and it classified all nine regions correctly across the five files.

Holes are filled by push-pull diffusion from their own rim, so the fill inherits the
material around it. The mask is grown by 7px first — the anti-aliased rim of the grid is
too dim to pass the bright test, and left in place it reads as a dotted outline tracing
the repair.

## Honest limits

The filled areas are **reconstructed, not recovered**. The original pixels are not in
the supplied files. Baldin's blade comes back as smooth steel without its engraving, and
Faelas' cape as plain cloth. At line-up and sprite size they read correctly; at full
resolution they read as flat. If the un-flattened originals exist, re-cutting from those
beats any repair here.

Stature in the line-up is authored, not measured — the source images are all 512 tall
regardless of who is in them, so scaling to equal height would have made the hobbit as
tall as the wizard. Relative heights live in `lineup.py:STATURE`.

## Files

| File | What it does |
|---|---|
| `repair.py` | `classify` (background vs hole), `inpaint`, `strip_border_frame`, `despeckle`, `clean_edges`, `strip_haze`, `repair_sprite` |
| `lineup.py` | Trim to alpha bbox, scale by stature, bottom-align on a common baseline |

## Rebuild

```bash
git clone https://github.com/aldegad/sprite-gen /tmp/sprite-gen
cd /tmp/sprite-gen && python3 -m venv .venv && ./.venv/bin/pip install -e . && ./.venv/bin/pip install scipy

# with the source archive unpacked to ./new and ./sprites
python -c "import repair; ..."          # see the module docstrings
/tmp/sprite-gen/.venv/bin/sprite-gen unpack-atlas --pngs-dir pngs --out-dir run --force
/tmp/sprite-gen/.venv/bin/sprite-gen compose-atlas --run-dir run
/tmp/sprite-gen/.venv/bin/sprite-gen shadow --source pngs/heroes/0_mithrandir.png --out-dir shadows/mithrandir
```
