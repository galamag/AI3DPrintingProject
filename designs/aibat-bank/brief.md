# Brief: $AIBAT$ name money box, version 1

Status: approved by the user on 2026-11-13 for the text `$AIBAT$`; size and proportions to be confirmed from the renders.

**Joint gap chosen on 2026-11-13 from the printed test piece.** The user tried the three backs: 0.15 mm closes well with no play and stays shut when turned over, 0.20 mm has play, 0.25 mm falls out. The box therefore uses a 0.15 mm sideways gap between lip and skirt: the back half's skirt is 1.65 mm thick, the wall behind each groove is 1.35 mm, and a ridge has 0.05 mm of free play in its groove. Wherever the text below still says 0.20 mm for the box's sideways gap, 1.60 mm for its skirt or 0.10 mm for the ridge play, read these values instead. The model was rebuilt and measured with them.

**Revisions of 2026-11-13.** The design changed six times on the same day. This brief includes the result of all six.

1. **Name on both sides** (replaced by change 5). The back half was to carry the name turned half a turn, so that it read left to right from behind.
2. **Straight letters, printed with supports.** No 45 degree bevel. Each side is a flat black face, and the green letters stand straight out of it by 4.0 mm, with upright walls. Each half prints letters down, so the flat black face is printed over supports. It will not have the plate texture and will show support marks; the user accepted this on 2026-11-13 in exchange for straight letters. The user's own point: the supports are printed during the green layers, so they come out green and cost no extra filament change or purge.
3. **Colour change two layers early.** The filament changes to black two layers before the flat black face starts, so the black face is not smeared with green from the supports. With a 4.0 mm relief and 0.2 mm layers the change is at 3.6 mm.
4. **The outline follows the letters, per side** (replaced by change 5 before it was built).
5. **Straight through, as in the references.** The user saw that in the references the inscription on the other side repeats straight through, letter behind letter, so only one side is readable.
   - The box is one outline, the front word grown by 8 mm, running straight from the front letter faces to the back letter faces.
   - The back carries the same letters straight behind the front ones, so from behind the name appears mirrored.
   - The back half's outside is the front half's outside mirrored through the seam plane (Y = 0).
6. **New text: `$AIBAT$` (sixth change).** The people the box is for do not like Cyrillic and want a dollar sign. The user chose the text `$AIBAT$` in Latin letters, with a dollar sign at each end. As a result:
   - **Width.** The box becomes 240 mm wide, to give seven characters room.
   - **Height.** It is no longer fixed at 100 mm. It follows from fitting the word (section 3.1) and is expected at roughly 85–97 mm (estimate).
   - **Top.** There is no hump any more.
   - **Slot.** It goes back to the middle of the top.
   - **The orchestrator's recommendation.** The new width, the height rule and the slot and ridge rules were shown to the user. They are to be confirmed from the renders.
   - **Name.** The folder `aibat-bank` and the object names stay.

Unchanged: the depth of 80 mm, the split at Y 0, the 4.0 mm straight relief, the colour change at the relief height minus two layers, the flat black face over supports, the 3.2 mm walls, the lip on the front half, the pry notch at the bottom seam, the colours and the test piece.

The user fixed these points: the text `$AIBAT$` in bold Latin capitals like the THOMAS reference, readable from the front and repeated straight through on the back, with the box's outline following the letters; green letters on a black body; a box for coins up to about 26 mm and folded banknotes; renders before printing; and a real print. Also agreed with the user: two halves split parallel to the front, a stepped lip with small click bumps and a pry notch, a test piece of the joint printed first, straight raised letters printed letters-down over supports, one filament change by layer height (green, then black) on each half, two layers before the black face, and a coin slot formed by a notch in each half. The size (240 mm wide, 80 mm deep, height from the fitting rule) is the orchestrator's recommendation, to be confirmed from the renders. The numbers below are mine; every estimate says so.

## 1. What it is

A personalised money box in the style of the name banks in the references. It is a thick black body whose outline follows the text `$AIBAT$`, running straight through from front to back like a cookie-cutter shape. The front face carries the text as raised green capitals, readable left to right: a dollar sign, the name AIBAT, and another dollar sign. Each side is a flat black face, and the seven characters stand straight out of it by 4 mm, with upright walls and flat faces, like the THOMAS reference.

Round the characters is an 8 mm black border that follows them. Seen from the front, this gives:
- a long block with a flat bottom;
- ends that round over with the curves of the two dollar signs;
- a top that is mostly flat, with small rises over the dollar signs, whose upright strokes reach above the letters;
- perhaps a dip or two between letters where the letters' own tops dip (the modeler reports which ones stay).

The back face carries the same green characters straight behind the front ones, as in the references. From behind, the text therefore reads mirrored, like the front seen through glass. A, I and T are symmetric, so they look the same from behind. Only the B and the two dollar signs look reversed. A coin slot runs along the middle of the top. The box splits down the middle into a front half and a back half, which click together and can be pried apart with a coin to take the money out.

**Surface finish, as accepted by the user.** Each half prints with its letter faces down on the textured plate. The green letter faces therefore get the fine plate texture. The flat black face is printed in mid-air, 4 mm above the plate, on supports that are snapped off afterwards. It comes out slightly rough and shows faint support marks, and it has no plate texture. The side walls and top show fine horizontal layer lines.

Assumptions I made where the references and the user's answers say nothing:

- **Font: Impact**, which is installed on this PC (`C:\Windows\Fonts\impact.ttf`). It is the closest installed match to the THOMAS letters: upright, heavy and narrow. The letters are the Latin A, I, B, T (not the Cyrillic look-alikes), and the dollar sign is Impact's own `$`.
- **Size: 240 mm wide, 80 mm deep** (the orchestrator's recommendation). The height follows from the fitting rule in 3.1: the word is stretched upwards by 1.25, unless that would make the box taller than 100 mm. Expected: roughly 85–97 mm tall (estimate; the modeler measures).
- **The dollar signs' strokes set the top and the bottom.** In Impact the upright stroke of `$` reaches a little above the capitals and below the baseline. The 8 mm border is measured from the lowest and highest points of all the green characters, so:
  - the bottom is 8 mm below the lowest point of the `$` strokes. Under the letters A, I, B and T the black border is wider than 8 mm by the stroke's depth below the baseline, about 3–6 mm (estimate);
  - the top over each `$` is 8 mm above its stroke, so the top rises a few millimetres over each dollar sign.
- **Relief height 4.0 mm.** That is 20 layers of 0.2 mm. On capitals of about 64–69 mm it reads clearly from the side and in the three-quarter view and casts a visible shadow. A higher relief would make the supports taller, use more filament and make them harder to pull out of the letter holes; a lower one would look flat.
- **The 80 mm depth is measured from the front letter faces to the back letter faces**, so it includes both 4 mm reliefs.
- **The text is centred by its width.** The green text, from the leftmost point of the first `$` to the rightmost point of the last `$`, is 224 mm wide and centred on the box.
- **Notches in the top and bottom.** A notch narrower than 6 mm halfway down its depth is filled flat; wider ones stay (section 3.1). This keeps the outline clean without hairline cracks.
- **A small edge break** (a 0.6 mm 45 degree chamfer) runs round the outer edge of each flat black face.
- **The coin slot is 38 mm long, in the middle of the top** if the flat top there allows it (section 3.2).
- **Letters do not touch.** They have a 3.0 mm gap, which shows as a thin black line of face.
- **The coin:** 200 tenge, about 26 mm across (the user's figure). I assume no coin is thicker than 2.5 mm.
- **The banknote** is folded lengthwise into thirds or quarters before it goes in, to a strip no wider than about 28 mm. This assumes a banknote about 70 mm tall, which is my estimate. The 38 mm slot also takes most notes folded only in half if they are no more than about 72 mm tall; that is an estimate too.
- **The box is opened from below.** You turn it over, put a coin into a small notch at the bottom seam and twist.

## 2. Dimensions

**Coordinate system** (for the modeler). The scene is in metres, as Blender's default; 1 mm = 0.001 m, and every number in this brief is in millimetres.

- X runs across the text, from the front viewer's left (−) to right (+). Y runs from the front (−, the front letter faces) to the back (+, the back letter faces). Z points up.
- The bottom face is at Z = 0. The box is centred in X and in Y, so it spans X −120 to +120, Y −40 to +40 and Z 0 to H, where H is the overall height from the fitting rule.
- The front faces −Y, straight into Blender's front-view camera. The back faces +Y.
- Every X and Z position holds through the whole depth: the back letters sit at exactly the same X and Z as the front ones.

| Measurement | Value | Source |
|---|---|---|
| Overall width (X) | **240 mm** | orchestrator's recommendation, to be confirmed from the renders |
| Overall depth (Y), front letter faces to back letter faces | **80 mm** | user |
| Overall height (Z), H | follows from the fitting rule; expected roughly 85–97 mm, never over 100 mm; stop if under 75 mm | rule in 3.1; the modeler measures |
| Green width of the text | 224 mm, X −112 to +112 | follows from the 8 mm border |
| Upward stretch of the font | 1.25, or less if 1.25 would make H more than 100 mm | rule in 3.1 |
| Lowest green point (bottom of the `$` strokes) | Z 8 | follows from the 8 mm border |
| Capital height (A, I, B, T) | about 64–69 mm | estimate; the modeler measures |
| `$` strokes beyond the capitals | about 3–6 mm above the capitals and below the baseline | estimate; the modeler measures |
| Baseline of A, I, B, T | Z 8 plus the depth of the `$` stroke below the baseline, about Z 11–14 | estimate; the modeler measures |
| Black border round the characters (the outline grown by) | 8 mm from the nearest green point; under A, I, B, T about 11–14 mm, because the bottom is set by the `$` strokes | my choice; estimate for the wider part |
| Body depth, flat black face to flat black face | 72 mm (Y −36 to +36) | follows |
| Relief: letters stand out of each flat black face by | **4.0 mm**, upright walls | my choice |
| Colour boundary on the letter walls | 3.6 mm behind the letter faces (Y −36.4 and +36.4): green towards the letter face, black for the last 0.4 mm | user's rule: relief height minus two 0.2 mm layers |
| Gap between neighbouring characters, at the narrowest point | 3.0 mm | my choice |
| Edge break round each flat black face | 0.6 mm, 45 degrees | my choice |
| Split plane, where the halves meet | Y 0, the exact middle | my choice |
| Front half, letter faces to the seam | 40 mm (4 mm relief + 36 mm body), plus a 4 mm lip | follows |
| Back half, letter faces to the seam | 40 mm (4 mm relief + 36 mm body) | follows |
| Outer walls | 3.2 mm | my choice |
| Face wall, behind each flat black face | 3.2 mm, so the hollow runs from Y −32.8 to +32.8 | my choice |
| Coin slot | 5 mm wide, 38 mm long, on the seam, centred at X 0 if the top allows it | the rule in 3.2 |
| Inside space | about 1.1–1.2 litres | estimate |
| Solid volume of both halves | about 340–400 cm³ | estimate |
| Weight of the printed box | about 310–400 g, of which about 30–45 g green; plus about 15–40 g of supports, removed after printing | rough estimate; the print engineer gives the real figure |

## 3. Parts (largest to smallest)

The box is **2 printed parts**: the front half and the back half. A separate **test piece of the joint** has 4 small printed parts and is printed first. The scene therefore holds 8 objects in three groups. A "collection" is Blender's folder of objects. Supports are not modelled; the slicer adds them.

| Collection | Objects | What for |
|---|---|---|
| `AibatBank` | `BankFront`, `BankBack` | the assembled box, for the renders and checks |
| `AibatBank_Print` | `BankFront_Print`, `BankBack_Print` | the same two halves turned the way they lie on the print plate, for export and the print-orientation renders |
| `AibatBank_Coupon` | `CouponFront`, `CouponBack_015`, `CouponBack_020`, `CouponBack_025` | the joint test piece, already in print orientation |

`BankFront` and `BankBack` have their origins at the world origin (the centre of the bottom face) and no rotation, so they sit together without moving. The `_Print` objects are independent full copies, not linked copies. They are made only once the halves are final, and made again after any change. Each lies with its letter faces on Z = 0, at X +300 mm or beyond, so it never overlaps the assembled box.

### 3.1 The text and the body outline (one outline, straight through)

**Fitting the text.** Do these steps in this order.

1. **Set** `$AIBAT$` in Impact: Latin capitals A, I, B, T and Impact's dollar sign, seven characters.
2. **Space** it so every pair of neighbours is exactly 3.0 mm apart at its closest point (six gaps).
3. **Scale evenly** until the green width is exactly 224.0 mm, from the leftmost point of the first `$` to the rightmost point of the last `$`.
4. **Measure** the unstretched green height h, from the lowest green point to the highest (both are expected on the `$` strokes).
5. **Stretch upwards only** by 1.25. The overall height is then H = 1.25 × h + 16 (the green height plus the 8 mm border above and below).
   - If H would be more than 100 mm, use the stretch that makes H exactly 100 mm instead: stretch = 84 / h. Report it.
   - If that stretch would be less than 1.00 (h more than 84 mm), do not squeeze: stop and report.
   - If H at 1.25 comes out under 75 mm, stop and report; the box would look too low for its width.
6. **Place** the text with its lowest green point at Z 8 and its green width centred on X 0 (X −112 to +112).
7. **Report:** the stretch used, H, the capital height, how far the `$` strokes reach above the capitals and below the baseline, and the baseline height of A, I, B, T.

**Checking the characters before building on them.** The modeler measures the real Impact glyphs at the fitted size and reports:
- how the `$` is built: the stub of its upright stroke above and below the S, and whether its counters (the spaces inside the S) are open bays or closed holes;
- the thinnest green feature on any character (strokes, the `$` stroke stubs, the ends of the S). If any green feature is thinner than 1.2 mm, stop and report; it would not print reliably;
- any enclosed black area inside a character narrower than 3 mm across. It would be hard to support and to clean out. Report it, and the orchestrator decides with the user whether to fill it green.

**The body outline.**

1. **Grow** the outline of all seven characters outwards by 8 mm, with round corners.
2. **Fill** every hole inside it: the insides of A and B, any closed counter of the `$`, and any closed gap between characters (for example under the arms of T).
3. **Cut** it flat at Z = 0, which is 8 mm below the lowest green point. Fill any dip in the bottom edge up to that flat line, so the bottom is one straight line.
4. **Notches:** any notch in the top or bottom edge whose width, measured halfway down its depth, is under 6 mm is filled flat to the straight line across its mouth. Wider notches stay as they are. This rule is applied before the rounds in step 5, so a narrow V between two letters never turns into a hairline crack.
5. **Round** sharp inside corners to 2 mm.
6. Nothing else is added or removed.

Growing an outline outwards makes no thin spikes or slivers, so there is nothing fragile to fill. Every outline edge is an upright wall when a half lies on the plate, so nothing in the outline is unprintable either.

**Expected outline in plain words** (estimates; the modeler reports the real shape):
- **Bottom:** flat over almost the full length, ending in the rounded lower curves of the two `$`.
- **Ends:** each rounds over with the S-curve of its `$`. They are upright in the middle but not straight walls.
- **Top:** 8 mm above the capitals over A, I, B, A, T. It rises a few millimetres over each `$`, where its upright stroke sticks up, with rounded shoulders.
- **Notches in the top:** perhaps a V between B and the second A, where B's rounded top corner meets A's slanted side, and shallow dips beside each A's flat top. Each one stays only if it is 6 mm or wider halfway down, so the modeler reports which survive and their sizes. No dip depths are promised here.
- **Black border:** 8 mm along the top of the letters and the sides of the `$`. Under the letters it is about 11–14 mm, because the bottom is set by the `$` strokes.

### 3.2 `BankFront` (front half, with the readable text and the lip)

**The front, from the letter faces back:**

- **Letter faces:** all seven characters are flat, at Y −40, and parallel to the black face. They read `$AIBAT$` left to right.
- **Letter walls:** each character outline (and its holes) runs straight back, square to the face, for exactly 4.0 mm, to the flat black face at Y −36. No bevel, no slope, no rounding on the letters; the letter face edges are crisp.
- **Colour boundary:** there must be a real edge in the mesh at Y −36.4, 3.6 mm behind the letter faces, all round every letter wall and every hole wall. The letter faces and the walls in front of this edge are green; the last 0.4 mm of the walls behind it, and everything further back, is black. This is where the filament changes in the print (section 10).
- **Flat black face:** one flat surface at Y −36, filling the outline round the characters: the border, the 3 mm gaps between characters, the insides of A and B, and any counters of the `$`. It meets the letter walls in sharp inside corners.
- **Edge break:** round the outer edge of the flat black face, where it meets the side walls, a 0.6 mm 45 degree chamfer.
- **Side wall:** the outline runs straight back from the black face to the seam at Y 0. It is 3.2 mm thick.
- **Inside:**
  - **Shape:** the hollow follows the outline, shrunk by 3.2 mm, with corners rounded to at least 2 mm. Any part of the hollow narrower than 6 mm is left solid; the modeler reports where that happens (for example under a notch that stays, or in the small rises over the `$`).
  - **Depth:** the hollow's front face is flat at Y −32.8, so the face wall behind the flat black face is 3.2 mm thick (7.2 mm behind the letters). The hollow is open towards the back (Y 0).
- **Seam line:** the outer edge of the rim (at Y 0) has a small 0.6 mm 45 degree bevel. With the matching one on the back half it makes a neat V line, so the seam looks intended.
- **Lip:** the inner 1.4 mm of the wall continues past the seam by 4.0 mm, to Y +4.0, all the way round, so it slides into the back half. Its inner face is flush with the inside wall. Its outer face is 1.8 mm in from the outside surface.
  - **Why the lip is on the front half:** the halves are otherwise mirror twins, so the joint works either way. Keeping it on the front half keeps the joint exactly as on the test piece (`CouponFront` has the lip), keeps the pry notch beside the lip as designed, and leaves the back half 4 mm lower on the plate.
- **Coin slot, front half:** a notch in the top wall from Y −2.5 to the seam at Y 0, through the full wall into the hollow. Each end is rounded (radius 2.5 mm), so the two halves together make a slot with round ends.
  1. **Stretch:** take the flat stretch of the top (after the notch rule) nearest to X 0.
  2. **Length:** 38 mm if that stretch is at least 46 mm long. Otherwise, the stretch minus 8 mm, but never less than 32 mm. If even 32 mm does not fit, try the next nearest flat stretch. If none fits 32 mm, stop and report.
  3. **Position:** centred at X 0 if the slot then has at least 4 mm of flat top beyond each end. Otherwise move it the shortest distance from X 0 that gives those 4 mm.
  4. **Report** the stretch used, the length and the centre.

  **Expected:** 38 mm centred at X 0, over B and its neighbours (estimate).
  - The capitals' flat tops over I and B join with no notch between them.
  - If the notch between B and the second A stays, the flat top may end a few millimetres right of X 0. The slot then moves left by up to about 20 mm (estimate), or shortens to 32–37 mm.
  - **What passes:** a 26 mm coin clears a 38 mm slot by 6 mm at each end. Banknotes folded lengthwise to 28 mm pass; notes up to about 72 mm tall folded in half pass tightly.
  - **Lip:** over the slot's length plus 2 mm at each end, the lip is left out.
- **Click bumps (4):** small ridges on the outer face of the lip. Each is 8 mm long along the wall, with its ends tapered over 1 mm.
  - **Profile across the ridge:** it stands 0.4 mm out from the lip. It is 1.4 mm wide at the base (Y +1.8 to +3.2) and has a flat top 0.6 mm wide (Y +2.2 to +2.8), with 45 degree sides.
  - **Placement rule** (the original one: two on the bottom wall, two on the top wall):
    - **Bottom wall:** two bumps, at about X −55 and X +55. Each is at least 10 mm from the pry notch and from where the bottom starts to curve up into the ends.
    - **Top wall:** one bump on each side of the slot. Each is centred on a flat top stretch, with its centre at least 14 mm from the ends of that stretch (10 mm clear plus half the bump) and at least 16 mm from the slot's end (10 mm clear, the 2 mm without lip, plus half the bump). Of the places that qualify, take the one nearest X −60 for the left bump and nearest X +60 for the right bump. If one side has no place that qualifies, stop and report.
  - **Expected** (estimate): bottom at X −55 and +55; top at about X −60 (over the first A or I) and about X +60 (over the second A or T).
- **Pry notch:** a notch for a coin, in the bottom wall at the seam, centred at X 0. It is 14 mm long (along X), 2.4 mm wide (Y −2.4 to 0) and 1.5 mm deep (Z 0 to 1.5). It is cut in the front half only. A coin pushed in bears against the back half's rim, and twisting it pries the halves apart.

### 3.3 `BankBack` (back half, with the text straight through)

- **Outside:** exactly the outside of `BankFront` from its letter faces to the seam, without its lip and pry notch, mirrored through the seam plane Y = 0. It is not turned round. So:
  - the letter faces are at Y +40, each character exactly behind its front character, at the same X and Z. Seen from behind, the text reads mirrored. A, I and T look the same; B and the two `$` look reversed;
  - the letter walls run straight forward 4.0 mm to the flat black face at Y +36, with the colour-boundary edge at Y +36.4;
  - the flat black face and its 0.6 mm edge break;
  - the same outline, with a 3.2 mm side wall, runs forward to the seam at Y 0.
- **Inside:** the same hollow as the front half, mirrored, with its back face flat at Y +32.8 (a 3.2 mm face wall). It is open towards the front.
- **Rebate for the lip:** the step in the wall that takes the front half's lip. Over the first 4.3 mm behind the seam (Y 0 to +4.3), only the outer 1.6 mm of the wall stays, as a thin skirt. The inner part is removed, which leaves a 0.2 mm gap round the lip's outer face. The lip stops 0.3 mm short of the floor of the step (Y +4.0 against +4.3), so the halves meet on the outer seam and not on the lip's end.
- **Click grooves (4):** in the skirt's inner face, opposite the 4 ridges. Each is 10 mm long and 0.3 mm deep.
  - **Profile:** it is 1.6 mm wide at the face (Y +1.7 to +3.3) and has a flat floor 1.0 mm wide (Y +2.0 to +3.0), with 45 degree sides.
  - **How it clicks:** when the halves close, each ridge has to push the skirt 0.2 mm outwards and then drops into its groove.
- **Coin slot, back half:** the matching notch, from the seam at Y 0 to Y +2.5. It has the same length, ends and place as in the front half. Over the slot's length plus 2 mm at each end, the rebate is filled solid (full wall thickness), because the lip is missing there.
- **Seam line:** the same 0.6 mm 45 degree bevel on the outer edge of the skirt's end.
- **No pry notch** on the back half.

### 3.4 Joint test piece (`CouponFront`, `CouponBack_015`, `CouponBack_020`, `CouponBack_025`)

The test piece is a small box with exactly the same joint as the money box, printed first to find the gap that clicks well. The joint did not change in these revisions, so the test piece is unchanged.

- **Outline:** a rectangle 60 x 30 mm with corners rounded to 6 mm.
- **Walls:** 3.2 mm. Floors: 2.4 mm.
- **`CouponFront`**
  - Floor on the plate, wall up to 10.0 mm, and then the lip, 1.4 mm thick and 4.0 mm tall, to 14.0 mm.
  - One click ridge centred on each long side.
  - A pry notch (14 x 2.4 x 1.5 mm) centred on one short side.
  - The 0.6 mm seam bevel.
- **`CouponBack_015`, `_020`, `_025`**
  - Floor on the plate, full wall up to 6.0 mm, then the skirt and step up to 10.3 mm.
  - One groove on each long side.
  - The 0.6 mm seam bevel.
- **The three backs differ only in the gap** between the lip and the skirt: 0.15, 0.20 and 0.25 mm. Their skirts are therefore 1.65, 1.60 and 1.55 mm thick. The grooves are 0.3 mm deep in each.
- **Labels:** each back carries its number, "15", "20" or "25", as raised digits on the inside of its floor. The digits are 8 mm tall, 0.6 mm high, with strokes at least 1.2 mm wide.
- **How it is used:** press `CouponFront` into each back in turn.
  - **The right one** closes by hand with a clear click, shows no gap at the seam, does not wobble, and opens with a coin in the pry notch.
  - **Applying the result:** the money box gets that gap. Its skirt is made thinner or thicker by the same difference before export.
  - **If two feel equally good**, take the tighter one. The long walls of the money box bend more easily than the walls of the small test piece.

## 4. Proportions the eye checks first

| What | Value |
|---|---|
| Body width : height : depth | 240 : about 85–97 : 80, a long, low, deep block (estimate; to be confirmed from the renders) |
| Capital height to body height | about 64–69 to 85–97, roughly 0.72. The letters fill most of the height, and the black border is a frame, not a base. |
| Black border to capital height | 8 : about 66 at the top and sides, about 1 : 8; a little wider under the letters |
| Dollar signs | their upright strokes stand a few millimetres above and below the letters, the only rises on the top |
| Relief to depth | 4 + 4 : 80. The letters stand clearly proud in the side view, as thin green slabs on a black block. |
| Green to black on the letter walls | 3.6 : 0.4. From the side the letter walls look green; the black sliver at their base merges with the black face. |
| Gap between characters | 3 mm, a thin black line |
| Seam position | in the middle, 40 mm behind each face |
| Slot | 5 mm wide, 38 mm long, in the middle of the top, about one sixth of the width |

## 5. Silhouette

- **Front:** like the reference photos.
  - `$AIBAT$` reads at a glance as five tall, heavy green capitals between two dollar signs, on a flat black face with a black border that follows the characters.
  - The bottom is a straight line. The top is mostly flat, with small rises over the two dollar signs and any notches the modeler reports between letters.
  - The ends round over with the S-curves of the dollar signs.
- **Back:** the same outline, with the same green characters straight behind the front ones, so the text reads mirrored. A, I and T look the same; B and the dollar signs look reversed.
- **Side (from an end):** a deep black block 72 mm deep with the characters standing 4 mm proud of each face, 80 mm overall, the same at front and back. A fine V-shaped seam line runs round the block in the middle.
- **Three-quarter front:** this is the hero view. The letters stand straight out of the flat black face, with green upright walls that catch the light and cast short shadows on the face. The slot shows in the middle of the top.
- **Three-quarter back:** the same block from behind, with the mirrored text.
- **Top:** a long, even block 72 mm deep (80 mm with the letters). The slot runs along the seam in the middle. Any notches that stay run straight through as grooves.

## 6. Topology (how the surface is built)

- **Type:** hard-surface solids made for printing. Each object is one closed solid: watertight, no holes in the surface, no loose or doubled faces, no parts passing through themselves, normals pointing outwards.
- **Real size:** everything is built at the sizes above, with the scale applied (reset to 1).
- **No smoothing step** (no subdivision). Curved letter outlines are made of enough short straight pieces that no facet shows in the renders: no more than 0.05 mm off the true curve.
- **Size of the mesh:** about 50,000–200,000 triangles per half is fine.
- **Thinnest parts:**
  - nothing thinner than 1.2 mm anywhere, green characters included. The thinnest parts of the box are the 1.3 mm wall behind each click groove and the 1.4 mm lip;
  - the click ridge (0.4 mm high) and the groove (0.3 mm deep) are shapes on a wall, not free-standing details.
- **Colour boundary:** on both halves, the edge 3.6 mm behind the letter faces is a real edge round every letter wall and hole wall, so the faces in front of it can carry the green.
- No animation, no rig.

## 7. Materials (for the renders)

The printed colours come from the spools, so the render colours are approximate. Both look like matte plastic.

| Part | Colour | Roughness | Metal | Note |
|---|---|---|---|---|
| Letter faces and the first 3.6 mm of the letter walls, on both halves | bright green, about #1FA24A | 0.5 | no | Bambu PLA Lite green, AMS slot A1. The real shade may differ. |
| Everything else on both halves, including the last 0.4 mm of the letter walls | black, rendered as #1C1C1E so the shape still reads | 0.55 | no | Bambu PLA Lite black, AMS slot A4 |
| Test piece | mid grey, about #8A8D90 | 0.55 | no | Bambu PLA Lite grey, AMS slot A2 |

In the print, the green letter faces get the fine pattern of the textured plate, and the flat black faces come out slightly rough with faint support marks. Version 1 renders both plain. No wear, no dirt, no gloss.

## 8. Lighting, background and camera for the presentation renders

- **Engine:** Cycles on the graphics card, 128 samples with denoising, 1600 x 1200 (landscape 4:3).
- **Background:** a light warm-grey seamless studio backdrop, #E6E3DE, with a soft shadow under the box. A black box on a dark background would vanish.
- **Lights:**
  - key: a large soft light to the front-left of the camera, 45 degrees to the side and 35 degrees up, so the letters cast short shadows on the black face;
  - fill: a weak light on the right, so the black face and the shadowed letter walls do not go flat;
  - rim: a light high behind the box, which draws a thin highlight along the black outline and the seam.
  - The whole light set turns with the camera, so every side is lit as the front is.
- **Camera:** an 85 mm lens, so there is almost no distortion. It aims at the centre of the box (X 0, Y 0, Z H/2). The box fills about 85 % of the frame width.
- **Angles:** "round" means turning round the box from straight in front, towards the front viewer's left (−X). So 90 degrees is the left end, 180 degrees is straight behind, and 270 degrees is the right end.
- **Print views:** a light grey square of 256 x 256 mm, #BDBDBD, stands for the print plate, so the size of each half on the bed reads. Supports are not shown; the space under the black face where they go stays visible.
- **Views** (10 images in `designs/aibat-bank/renders/`, named `v1-01-front.png` to `v1-10-coupon.png`):
  1. `front`: straight on from the front, at the height of the box's middle. The text reads `$AIBAT$` left to right; the view for checking the outline and the proportions.
  2. `back`: straight on from behind (180 degrees round), at the height of the box's middle. It shows the mirrored text, each character straight behind its front character.
  3. `hero`: three-quarter front from the viewer's left, 35 degrees round and 20 degrees down.
  4. `back-hero`: three-quarter back, 145 degrees round (behind the box, at the left end) and 20 degrees down. It should look like the mirror image of `hero`.
  5. `side`: from the right end, 270 degrees round, at the height of the box's middle. It shows the 4 mm relief on both faces and the seam in the middle.
  6. `top`: from above, 70 degrees down, from slightly in front. The slot in the middle of the top.
  7. `open`: `BankFront_Print` and `BankBack_Print` side by side, open sides up, seen 45 degrees down and close. It shows the lip with its ridges, the step with its grooves, both halves of the slot and the pry notch.
  8. `print-front`: `BankFront_Print` lying letters-down on the plate square, seen low (10 degrees down), so the green letters standing on the plate, the 4 mm space under the black face, and the tight fit along the 256 mm plate show.
  9. `print-back`: `BankBack_Print` lying letters-down on the plate square, seen the same way.
  10. `coupon`: the four test-piece parts on the plate square.

## 9. Animation

None.

## 10. Print

- **What it is for, and the load:**
  - A money box on a desk or shelf. It stands on its bottom face and holds coins and folded notes.
  - Full, it may hold about 2–3 kg of coins (estimate). The weight rests on the bottom walls of both halves.
  - The lip inside the step stops the halves from sliding against each other up and down or sideways. The 4 clicks only hold them together.
  - It is a box for keeping money, not a lock: a child can open it with a coin.
  - Pick it up full by holding both halves, not by one half alone.
- **Printed size:**
  - assembled: 240 x 80 x H mm (W x D x H), H about 85–97 mm (estimate);
  - front half on the plate: about 240 x H mm, 44 mm tall (40 mm plus the 4 mm lip);
  - back half on the plate: about 240 x H mm, 40 mm tall.
- **Fitting on the plate.** The P2S plate is 256 x 256 mm, so each half leaves only about 8 mm at each end along its length. The print engineer must check that the half, any brim or skirt the profile adds, and a possible purge tower all fit. The tower fits beside the half's short side, where there is about 160 mm to spare. If they do not fit:
  - the half can be placed diagonally on the plate (the diagonal is about 362 mm);
  - or the width can be reduced, which needs the user's consent and a new fit of the text.
- **Plates, in order:**
  1. **Test piece** (`CouponFront`, `CouponBack_015`, `_020`, `_025`).
     - Grey, slot A2, one colour, no supports.
     - Each part lies floor-down.
     - Small and quick, about 15 g (estimate).
     - Its result sets the gap before the box is exported (3.4).
  2. **Front half** (`BankFront_Print`), letter faces down, with supports and one colour change.
  3. **Back half** (`BankBack_Print`), exactly the same way.
- **For both halves:**
  - **Bed face:** only the green letter faces touch the plate (Y −40 for the front half, Y +40 for the back half). They are large and flat and get the textured-plate finish.
  - **The colour change rule:** green (A1) from the plate; the slicer changes to black (A4) **two layers below the flat black face**, that is at the relief height minus two layer heights. With 0.2 mm layers and the 4.0 mm relief this is **3.6 mm**: green for layers from 0 to 3.6 mm, black from the layer that starts at 3.6 mm to the top. The model's colour-boundary edge sits at the same 3.6 mm. If a different layer height is chosen, the change and the boundary edge move to 4.0 mm minus two of those layers, and the modeler moves the edge to match.
  - **Why two layers early (the user's reason):** the last support layers (their top interface) and the last layers of the letter walls are then already black, so the black face is not smeared with green from the supports. The 0.4 mm black at the base of each letter is not noticeable from the front.
  - **Layer height** must make both 3.6 mm and 4.0 mm layer boundaries, for example 0.2 mm layers with a 0.2 mm first layer.
  - **Supports are required** under the whole flat black face of each half, which lies 4.0 mm above the plate. That includes:
    - the border round the characters and the 3 mm gaps between them;
    - the insides of A and B;
    - any counters of the `$`.

    All supports stand on the plate; nothing inside the box needs support. The user's point, recorded: the supports are printed during the green layers, so they come out green (with black top layers) and cost no extra filament change or purge.
  - **For the print engineer to decide:**
    - the support type (normal or tree);
    - the interface layers and their pattern;
    - the top Z gap between the support and the black face, which decides how cleanly the face releases and how rough it is;
    - whether the narrow 3 mm gaps and the small closed letter holes can be bridged instead of supported.

    Pulling supports out of the closed holes of A and B, and out of any small counters of the `$`, is the awkward part of the clean-up; a support pattern that comes out in one piece helps.
  - Both halves change colour at the same height, but at about 240 x H mm each they do not fit one plate together. One plate each.
- **Surface finish, accepted by the user on 2026-11-13:** the flat black faces are printed over supports, so they do not get the plate texture and will show support marks. Only the letter faces get the plate texture. This was accepted in exchange for straight letters.
- **Filament estimate** (rough; the print engineer gives the real figures). All Bambu PLA Lite, loaded as A1 green, A2 grey, A3 white, A4 black:
  - the solid volume is expected at about 340–400 cm³, about 10 % more than the 340 cm³ measured on the earlier symmetric version. The box is 20 mm wider, and its outline is about 10 % larger in area;
  - black (A4): about 280–360 g for both halves, including the black top layers of the supports;
  - green (A1): about 45–85 g for both halves: about 30–45 g in the characters and about 15–40 g in the supports, which are thrown away;
  - grey (A2): about 15 g for the test piece;
  - white (A3): not used;
  - plus the waste of the two colour changes (purge), a few grams to about 15 g each (estimate).
- **Overhangs:** in print orientation, the only surfaces facing the plate are the letter faces (on the plate) and the flat black face with its edge break (on the supports). Everything else is upright or leans no more than 45 degrees:
  - the outline sides are upright walls, because the outline runs straight through;
  - the click ridges and the sides of the grooves are at 45 degrees;
  - the slot and the pry notch are open at the top of the rim;
  - there is no ceiling inside either half.
- **Walls:** outer walls 3.2 mm, face wall 3.2 mm behind each flat black face, lip 1.4 mm, skirt 1.6 mm, at least 1.3 mm behind a groove; no green feature under 1.2 mm.
- **Fits and gaps, starting values:**

  | Fit | Starting value | Tuned by |
  |---|---|---|
  | Lip to skirt, sideways | 0.20 mm | test piece: 0.15 / 0.20 / 0.25 |
  | Lip end to the floor of the step | 0.30 mm | |
  | Click ridge | 0.4 mm high, so 0.2 mm overlap when passing the skirt | |
  | Ridge sitting in its groove | 0.1 mm free | |
  | Slot | 5.0 mm wide, 38 mm long (32 mm at the least), for coins up to 26 mm across and 2.5 mm thick, and folded notes | |
  | Pry notch | 2.4 mm wide, for a coin edge | |

- **May not be changed without the user:**
  - the text `$AIBAT$`, the font, the outline following the characters straight through;
  - the width and the height rule, once the user has confirmed them from the renders;
  - the straight letter walls, the 4.0 mm relief, and the colour change two layers below the black face;
  - the split at Y 0, the slot size and position, the colours.
  - Turning either half to another face defeats the design. Report instead.
- **For the print engineer:**
  - The click joint needs solid walls near the rim. Four or more wall loops make the 3.2 mm walls nearly solid.
  - The letter faces of each half must touch the plate fully: flat, not tilted.
  - Whether `slice_model` can insert the filament change at 3.6 mm and set up the supports is not known. Either may have to be set in the Bambu Studio window, for two plates. This is a question for the orchestrator and the user, not a reason to change the model.

## 11. Acceptance criteria (checked by the inspector)

1. **Size and standing.**
   - The assembled box (`BankFront` + `BankBack`) measures 240 ± 1 mm in X and 80 ± 0.5 mm in Y (letter faces to letter faces), with its bottom at Z = 0.
   - Its height H matches the fitting rule within 0.3 mm: H = stretch × h + 16, stretch 1.25 unless that gives more than 100 mm. H is between 75 and 100 mm. The modeler reports H and the stretch.
   - The bottom face is flat at Z = 0 and contains a 190 x 70 mm rectangle centred on the origin. The centre of mass of the empty box lies above the middle third of that rectangle.
2. **One outline straight through.**
   - The green text is 224.0 ± 0.2 mm wide (X −112 to +112), with its lowest point at Z 8.0 ± 0.1 mm.
   - The outline matches the text grown by 8 mm, with only the fills and rounds of 3.1, within 0.2 mm. Its top is 8 ± 0.2 mm above the highest green point.
   - No notch narrower than 6 mm halfway down its depth remains in the top or bottom edge. The modeler reports every notch that remains, with its width and depth.
   - Every slice of the body from Y −36 to +36 has this same outline, within 0.1 mm. Excepted are the edge breaks, the seam bevel, the slot and the pry notch.
   - The outside of `BankBack` matches the outside of `BankFront` (without its lip and pry notch) mirrored through Y = 0, within 0.1 mm.
3. **Characters.**
   - Render 1 (`front`) reads `$AIBAT$` left to right in Impact, Latin letters, with all seven characters green and no missing-glyph boxes.
   - The narrowest gap between each pair of neighbouring characters is 3.0 ± 0.3 mm. No green feature is thinner than 1.2 mm.
   - Every back character sits exactly behind its front character: the back characters are the front ones mirrored through Y = 0, within 0.1 mm. Render 2 (`back`) shows the text mirrored, with B and the `$` reversed.
4. **Straight relief, on each side.**
   - All letter faces lie at Y −40.0 (front) and Y +40.0 (back), ± 0.05 mm.
   - The flat black face lies at Y −36.0 and Y +36.0, ± 0.05 mm, and is flat everywhere outside the characters, with no slope or bevel.
   - The letter walls stand at 90 ± 1 degrees to the face.
   - The colour-boundary edge is at Y −36.4 and Y +36.4, ± 0.05 mm, all round every letter wall and hole wall, with green towards the letter face and black behind.
   - The edge break round each black face is 0.6 ± 0.1 mm at 45 degrees.
5. **Walls, hollow and joint.**
   - The outer walls and the face walls are 3.2 ± 0.1 mm. No wall or detail is thinner than 1.2 mm.
   - The hollow is the outline shrunk by 3.2 mm. Every part narrower than 6 mm is left solid and reported.
   - With the halves assembled at their origins:
     - they touch only on the seam faces at Y 0;
     - the lip fits inside the step with 0.20 ± 0.03 mm sideways gap and 0.30 ± 0.05 mm at its end;
     - the only overlap is the 4 ridges, each sitting in its groove with 0.1 mm free;
     - the outer surfaces of the two halves are flush all round the seam within 0.05 mm.
   - The ridges follow the placement rule in 3.2: two on the bottom, one on the top on each side of the slot, each at least 10 mm from a corner, the slot and the pry notch. The modeler reports their positions.
   - The pry notch, in the front half at X 0, measures 14 x 2.4 x 1.5 mm.
6. **Overhangs.** On `BankFront_Print` and `BankBack_Print`, every face that points downwards more than 45 degrees from vertical is either a letter face on the plate (Z = 0) or part of the flat black face and its edge break at 4.0 mm above the plate. Nothing else needs support.
7. **Slot.**
   - Seen from above, the slot is 5.0 ± 0.1 mm wide and its length follows the rule in 3.2, ± 0.2 mm (38 mm expected, never under 32 mm). It is centred on Y 0 ± 0.1 mm, and on X 0 ± 0.5 mm unless the rule moved it; the modeler reports any move.
   - At least 4 mm of flat top lies beyond each end.
   - A test disc 26 mm across and 2.5 mm thick, held upright anywhere under the slot, can drop straight down to the bottom of the hollow without touching anything.
8. **Clean solids.**
   - Each of the 8 objects is watertight, has no non-manifold edges, no faces passing through each other and no stray pieces.
   - Scale is 1 on every object. The names are exactly those in section 3, with no ".001".
   - `export_for_print` reports no warnings for `BankFront_Print`, `BankBack_Print` and the four test-piece objects.
   - The `_Print` objects match `BankFront` and `BankBack` in shape: the same volume within 0.1 %.
9. **Mirror look.** Render 4 (`back-hero`) looks like the mirror image of render 3 (`hero`), apart from the pry notch.
10. **Renders.** All 10 images, 1600 x 1200, are in `designs/aibat-bank/renders/`.

**What the modeler must measure and report** before or while building:
- the stretch used and the overall height H;
- the capital height, the baseline height, and how far the `$` strokes reach above the capitals and below the baseline;
- how the `$` is built (stroke stubs, open or closed counters), the thinnest green feature, and any enclosed black area under 3 mm across;
- every notch left in the top and bottom edge (width halfway down, depth, position), and the flat stretches of the top;
- the slot's stretch, length and centre, and the four ridge positions;
- any part of the hollow left solid because it is narrower than 6 mm;
- the solid volume of each half.

## 12. Part diagrams (approximate, not to scale)

```
   Front view, outline only. The same outline runs straight through to the back.

   Z, mm
     H -      .---.                                                      .---.
             /     '----------------------------------------------------'     \    <- top: 8 mm above the capitals,
    H-3 -   |                                                                   |      rising a few mm over each $
            |                                                                   |
            |    $       A        I       B        A        T          $        |
            |                                                                   |
      8 -   |                                                                   |    <- lowest point of the $ strokes
      0 -    '-----------------------------------------------------------------'     <- flat bottom
         -120                                0                                 +120   X
                                       (=== slot 38 ===)

      the green text is 224 mm wide (X -112 to +112); the black border is 8 mm round the
      characters and wider under the letters; the ends round over with the S-curves of the $;
      notches that stay between letters are not drawn: the modeler reports them;
      H is about 85-97 mm (estimate)


   Top view (looking down; the front is at the bottom of the picture)

   Y, mm
    +40 -       back letter faces, 4 mm proud (green); the text reads mirrored from behind
    +36 -   .-------------------------------------------------------------------.
           (                                                                     )
      0 -  (  - - - - - - - - - - - - - (=== slot 38 ===) - - - - - - - - - - -  )  seam
           (                                                                     )
    -36 -   '-------------------------------------------------------------------'
    -40 -       front letter faces, 4 mm proud (green); the text reads $AIBAT$
          -120                               0                                +120  X


   Side view (from the right end; front on the left)

   Z, mm
     H -     .-------------------------------------------.
           [|                      ||                     |]     [ ] = characters, 4 mm out of each face
           [|                      ||                     |]         green for 3.6 mm, then 0.4 mm black
           [|     front half       ||      back half      |]
           [|      40 mm           ||       40 mm         |]
     8 -   [|                      ||                     |]
     0 -     '-------------------------------------------'
          -40 -36                  0                    +36 +40   Y
                                  seam (split), V-shaped line
           flat black faces at Y -36 and +36, with a 0.6 mm edge break round their outer edge


   One letter, cut through (front half; the back half is its mirror image)

        Y -40      Y -36.4  Y -36
          |  green   | black|
          |==========|==|   |      <- letter: face at Y -40, upright walls
          |==========|==|___|_____________   <- flat black face at Y -36
          |          |      |                   face wall 3.2 mm, then the hollow at Y -32.8
                  colour boundary edge, 3.6 mm behind the letter face


   The joint, cut across the bottom wall (front on the left); s = distance in from the outside

   s, mm
    0.0  ===========================V=========================================  outside surface
         front-half wall            |   back-half skirt (1.6)          back-half wall
    1.6  ...........................|.........____________________....        <- skirt inner face
         ...........................|  0.2 gap   /^\ ridge sits in groove      (groove 0.3 deep)
    1.8  ...........................+------------------------------+   +
         ...........................|  lip, 1.4 thick, 4.0 long    |0.3|      <- step floor at Y +4.3
    3.2  ===========================+==============================+   +=====  inside surface
                                  Y 0                            Y +4.0 Y +4.3
         V = the 0.6 mm seam bevel on both rims; the halves meet only on the seam faces at Y 0


   On the print plate (cut through the middle)

     Front half, letters down                       Back half, letters down
   Z, mm                                          Z, mm
    44 -   ||                         ||            40 -  |  |                        |  |  <- skirt
    40 -  |  |       open hollow      |  |         35.7 - |  '-.   open hollow      .-'  |  <- step for the lip
          |  |                        |  |                |    |                    |    |
   7.2 -  |  '------------------------'  |          7.2 - |    '--------------------'    |  <- inside floor
   4.0 -  '-.--------------------------.-'          4.0 - '-.--------------------------.-'  <- flat black face
   3.6 -  ss ## ss ##### ss ##### ss ## ss          3.6 -  ss ## ss ##### ss ##### ss ## ss  <- change to black
          ss ## ss ##### ss ##### ss ## ss                 ss ## ss ##### ss ##### ss ## ss
     0 -  ss ## ss ##### ss ##### ss ## ss            0 -  ss ## ss ##### ss ##### ss ## ss  <- letter faces on the plate
          ## = letters      ss = supports, added by the slicer (green up to 3.6 mm, black above)

     each half covers about 240 x H mm of the 256 x 256 mm plate: about 8 mm spare at each end
```

## 13. What a later version could add

- **A slot across the top (option):** a slot running front to back, 5 mm wide (in X) and up to 38 mm long (in Y), in the middle of the top.
  - Each half gets half of it as a notch open at the seam, so it prints without bridging.
  - The lip is interrupted for only about 9 mm.
  - It looks less like the references, which have the slot along the top.
- **A narrower box**, if the 240 mm halves are too tight on the 256 mm plate: refit the text to a smaller green width.
- **Rejected alternatives, kept for the record:**
  - the Cyrillic name «АЙБАТ», in all its versions (220 x 100 x 80 mm, with a hump over Й): the people the box is for do not like Cyrillic and want a dollar sign;
  - readable text on both sides with a different outline on each half: steps and ledges along the seam; the user preferred the references' straight-through look;
  - one symmetric shared outline with a flat top plateau: the outline no longer followed the letters.
- **A textured black face as well:**
  - letters as separate inserts: the black body prints with its flat face down on the plate, with pockets for the letters, and the green letters print separately face down and are pressed or glued in. Both colours get the plate texture and no supports are needed;
  - a flush two-colour face: green letters inlaid level with a flat black face, printed face down with the AMS swapping colours inside each layer;
  - the support-free 45 degree bevel of the first draft, if the support marks bother the user.
- The dollar signs in a third colour, for example white (A3 is loaded), as a separate print or an inlay.
- An engraved line on the bottom: a date, "from ...", or a small picture.
- A one-way flap under the slot so coins do not shake out, or a round plug in the bottom instead of the split.
- Small rubber feet or a printed non-slip pad.
- Magnets in the rim instead of the click bumps, if the clicks wear out.
- A rendered plate texture on the letter faces, so the renders show the real finish.
- Another font, if Impact turns out too heavy in the renders.
