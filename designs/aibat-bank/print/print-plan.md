# Print plan: $AIBAT$ money box, version 1

Prepared on 2026-11-13 from the brief (sixth revision) and the Blender file `aibat-bank.blend`.
Nothing here has been sent to the printer. Every plate needs the user's own yes before it starts.

## Printer and spools

- Bambu Lab P2S, 0.4 mm nozzle, textured PEI plate, AMS 2 Pro.
- Spools as last known on **2026-11-12, not checked again today**: A1 green, A2 grey, A3 white, A4 black, all Bambu PLA Lite. Check on the `Устройство` (Device) tab before each plate. Also check that the spools hold enough: about 45 g of grey, 80 g of green and 310 g of black, plus a margin.
- All three plates use the same settings for nozzle (220 °C) and bed (55 °C), from the shipped Bambu PLA Lite profile.

## The three plates, in printing order

| # | File | What | Colour | Time | Filament | Height |
|---|---|---|---|---|---|---|
| 1 | `coupon-v1.gcode.3mf` | joint test piece: one front and three backs (gaps 0.15 / 0.20 / 0.25 mm) | grey, A2 | 52 min | 38 g | 14 mm |
| 2 | `bank-front-v1.gcode.3mf` | front half, letters down | green A1, then black A4 | 3 h 37 min | 188 g | 44 mm |
| 3 | `bank-back-v1.gcode.3mf` | back half, letters down | green A1, then black A4 | 3 h 29 min | 178 g | 40 mm |
| | **Total** | | | **7 h 58 min** | **404 g** | |

Times and weights come from the slicer. They do not include the two colour changes: each change adds a few minutes and some grams of purged plastic, and more if Bambu Studio adds a purge tower.

Plate 1 comes first because its result can change the box. Press the front piece into each of the three backs. Pick the one that closes with a clear click, shows no gap and opens with a coin. If the best one is not "20", the model has to be changed and the halves exported and sliced again as version 2 **before** plates 2 and 3 are printed.

## Plate 1: joint test piece

- **Orientation:** each of the four pieces lies on its floor, open side up, in a 2 x 2 group about 130 x 70 mm in the middle of the plate. The plate picture shows four separate pieces.
- **Supports:** none. Nothing on these pieces hangs out over empty space. The small ridges and grooves are at 45 degrees and print without help.
- **Brim and skirt:** none. Each floor is 60 x 30 mm, which is plenty of grip.
- **Walls:** 4 instead of the profile's 2. This is the same as the box, so the test piece tests the same joint the box will have.
- **Infill:** 15 % (profile default).
- **Note:** the four pieces are one file, so Bambu Studio shows them as one object. That is fine for printing.

## Plates 2 and 3: the two halves

### How each half lies on the plate

Each half lies with its green letter faces on the plate and its open side up. The 7 characters touch the plate with about 109 cm² in total, so they hold well and get the fine pattern of the textured plate. The half is 240 x 96 mm and sits in the middle of the plate, about 8 mm from the left and right edges.

The flat black face around the letters hangs **4 mm above the plate**. It has nothing under it, so the slicer builds small temporary pillars under it ("supports"). You snap them off after the print. You accepted on 2026-11-13 that this face will be a little rough and show faint marks.

### Settings that differ from the profile, and why

| Setting | Value | Profile default | Why |
|---|---|---|---|
| Walls (`wall_loops`) | 4 | 2 | The brief asks for 4 or more so the 3.2 mm walls near the click joint are nearly solid. |
| Supports on (`enable_support`) | on | off | The black face is 4 mm above the plate and needs something under it. |
| Support type (`support_type`) | normal (auto) | tree (auto) | Tree supports need height to branch and only touch a large flat face at scattered points. Normal supports at 4 mm give an even, flat bed for the whole face. |
| Support style (`support_style`) | snug | default (grid) | Snug supports follow the shape of the face instead of filling square blocks, so less material and less to pull out between letters. |
| Supports only from the plate (`support_on_build_plate_only`) | on | off | A safety lock: no support can ever stand on the part itself, for example inside the open hollow. |
| Gap between supports and the letter walls (`support_object_xy_distance`) | 2.5 mm | 0.35 mm | This is how the narrow places get bridged instead of supported (see below). It also keeps the supports away from the green letter walls, so those walls stay clean. |

Unchanged from the profile and checked in the slice: 0.2 mm layers with a 0.2 mm first layer, 15 % grid infill, 3 bottom and 5 top layers, 2 support top layers ("interface") with the profile's own pattern, a gap of 0.2 mm (one layer) between the support top and the black face, no skirt, and "auto" brim, which added no brim.

**Why 0.2 mm layers:** they land exactly on 3.6 mm (the colour change) and 4.0 mm (the black face).

**Why a 0.2 mm gap on top of the supports:** one layer is the usual gap for PLA on PLA. The face comes off the supports cleanly but still lies flat. A larger gap makes the face rougher, a smaller one makes it stick.

### Which places are bridged instead of supported

The 2.5 mm gap means that any opening narrower than about 5 mm gets no support at all. The black face simply spans across it, like a bridge, from letter to letter. That covers the places that would be hardest to clean:

- the insides of both A (4.8 mm wide at most, ending in a point);
- the two closed holes of the B (4.6 mm wide);
- the two slits in each `$` (4 to 5 mm wide);
- the narrow parts of the 3 mm gaps between letters.

Spans of 3 to 5 mm bridge well in PLA. In the slice, there is no support at all inside the A and B holes.

Still supported are the wide places: the black border all round the letters (8 to 14 mm wide), the wider wedges next to the slanted sides of each A, and the spaces under the arms of the T. Along every letter, a strip 2.5 mm wide right next to the letter is bridged from the letter's top to the support.

All supports stop at 3.8 mm. Nothing is generated above 4 mm, so there is nothing inside the hollow.

### The colour change: this must be added by hand in Bambu Studio

The slice is in **one filament** only. The tool that made it cannot add a colour change, so the change must be added in the Bambu Studio window before each half is printed. **This step has not been tried yet.** The exact Russian menu names will be read from the window when it is done.

- **Rule from the brief:** green from the plate up to 3.6 mm, black from 3.6 mm to the top. That is two layers before the black face at 4.0 mm, so the top of the supports is already black and does not smear green onto the black face.
- **In plain 0.2 mm layers:** layers 1 to 18 (up to 3.60 mm) are green. Black starts with **layer 19**, which runs from 3.60 to 3.80 mm.
- **What the window will probably show:** the supports print a few extra thin layers of their own, so the slice has 232 layers (front) and 212 layers (back), not 220 and 200. The black layer that ends at 3.80 mm is **number 31** in that count, on both halves, and the layer before it ends at 3.60 mm (number 30). Choose the layer by its **height, 3.80 mm**, not by its number. The colour must change *before* that layer is printed.
- **Then, in the window:**
  - Filament 1 (green) goes to slot A1.
  - Filament 2 (black) goes to slot A4.
  - Slice again in the window.
  - Check that a purge tower, if Bambu Studio adds one, sits in the free area in front of or behind the half. There is about 80 mm free on each side. The tower must not touch the half.
- **When it happens:** about 1 hour after the start (the slicer's own estimate). The printer does it alone through the AMS; nobody needs to be there.
- **Not settable from here:** the profile pushes some of the purge plastic into the supports at the change layer (`flush_into_support`). The tool that made these slices could not switch this off. If it stays on, the top support layer may come out dark green or mixed instead of clean black. It touches the black face only through the 0.2 mm gap. It can be switched off in the window for the object, but this has not been tried.

### Colour split per half (from the slice)

- Green: about 37 g, of which about 28 g is the letters and about 9 g the supports, which are thrown away.
- Black: about 153 g on the front half and about 143 g on the back half, including about 1 g of black support top.
- Both halves together: about 74 g green and 296 g black.

## Compared with the brief's estimate

| | Brief | Slice |
|---|---|---|
| Solid volume of both halves | 340–400 cm³ | 351 cm³ |
| Box with supports | about 325–440 g | 366 g |
| Green, both halves | 45–85 g | about 74 g |
| Black, both halves | 280–360 g | about 296 g |
| Supports | 15–40 g | about 21 g |
| Test piece | about 15 g | 38 g (the brief's estimate was too low; the four pieces are 31 cm³ of plastic) |

## Risks

- **The colour change is untried.** If it is put on the wrong layer, the black starts one layer too early or too late. That is a small visual difference, not a failed print.
- **The window slices again.** Bambu Studio re-slices the file when it opens it, and that slice is what the printer gets. Its time, weight and supports must be compared with this plan before sending. It is not verified that the window keeps all the settings above. Check the support settings there.
- **Nozzle variant.** The printer has a high-flow nozzle, but these slices use the Standard nozzle values (flow 1.01 instead of 0.98, lower speeds). They may over-extrude very slightly and print slower than the nozzle could. No such slice has been printed yet.
- **Long, flat part.** At 240 mm long, the black body could pull up at the ends as it cools ("warping"). This is unlikely with PLA on a textured plate, and the letters are well stuck down. If a corner lifts in the first hour, the print can be stopped early with little waste.
- **Tight fit on the plate.** The supports' first layer comes within 6.8 mm of the left and right plate edges, and the part within 8.2 mm. This is fine. A brim around the outside would have to stay under about 6 mm, and none is used.
- **Bridged areas** (inside A and B, the `$` slits, the 3 mm gaps) may sag a fraction of a millimetre on the black face. This is hidden between the letters.
- **Small details on the test piece:** the raised numbers "15" and "25" on the inside floors have spots measured at 0.8 mm across, under the brief's 1.2 mm. They may print a little thin. This is cosmetic only.
- **Watching the print** works only while the Claude session and the Bambu Studio window stay open. It does not replace the printer's own protection. Plates 2 and 3 run for about 3.5 hours each.

## After each print

- **Test piece:** let the plate cool for a few minutes, then flex the plate to pop the pieces off. Press the front piece into each back and listen for the click.
- **Halves:**
  - Let the plate cool, then flex it to release the half.
  - Turn the half over. The green supports are between and around the letters, under the black face.
  - Snap them off with your fingers, or with small pliers for the wedges next to the A's. Pull them outwards, towards the edge of the box, not upwards into the letters.
  - The inside of the A and B and the `$` slits have no supports, so there is nothing to dig out there.
- **Fragile places:**
  - The lip on the open side of the front half (1.4 mm thick, 4 mm tall) and the thin skirt on the open side of the back half (1.6 mm). Do not lever against them when removing the part.
  - The small ridges and grooves of the click joint. Keep the support-removal pliers away from the open side.
- The black face will be a little rough with faint support lines, as agreed. Sanding is not needed.
