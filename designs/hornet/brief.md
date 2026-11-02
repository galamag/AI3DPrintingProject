# Brief: Hornet, game style, version 1

Status: revision 4b, 2026-11-02. Geometry passed the fourth inspection; lookdev may start. Revision 4 (straight right arm, cloak draped over it) was decided with the user; the modeler may rebuild ArmRight and reshape the right side of Cloak. Revision 3: The user decided the head shape from references 10 and 11, and decided that the legs end in plain points with no feet. In revision 2 the user had decided the direction of every change (spool under the cloak, thread back arc at shoulder height, cloak unchanged). The numbers are the art director's. The modeler may rebuild Mask, LegLeft and LegRight, and apply the revision 2a spool raise.

## Revision 2 (2026-11-02)

The user reviewed the first geometry renders (`designs/hornet/renders/v1-geometry-01` to `05`) and decided the following. Only these points changed.

- **Mask (3.2), rewritten.** The head and horns are now one continuous U-shaped shield, fullest at the eyes, with a slightly pointed chin. The side walls run straight up into the horns with no shoulder or step, and the horns taper and curve like a crescent. The overall height, the chin height and the width are kept: tips at 1.00 m, chin at 0.53 m, width 0.22 m. What changed:
  - the widest point is now at Z 0.62 m (was 0.66);
  - the bottom of the notch is now at Z 0.72 m (was 0.76), so the U is deeper;
  - the horn tips are now 0.17 m apart (was 0.15);
  - the head is now 0.16 m deep with a flatter face (was 0.20 m and round);
  - the horns are now as deep as the head where they start, instead of a flattened 7 × 5 cm section;
  - the eye centres are now at Z 0.62 m (was 0.61), so the eyes sit in the fullest part;
  - the eyes are now shallow black dishes, at most 1 cm deep, and the black stays on the front of the face;
  - the forward tilt of the head is now already included in the numbers.
- **Spool (3.9), moved.** It now hangs under the cloak from a thin belt round her waist at the back. It is a little smaller, to fit. The belt and a 4 cm cord are part of the `Spool` object, so the scene still has 10 objects.
- **Thread (3.7), new path.** The back of the loop is now at shoulder height (0.47 m). The thread starts at the spool under the cloak and comes out under the back hem. At the end it climbs her right side, on the outer side of the needle, to the eye. The eye crossing (back to front) and the loose end are unchanged. The length is about 3.8 m. The old figure of 2.6 m was an error, because the old points also gave about 3.8 m.
- **ArmRight (3.6).** The shoulder point moved from (−0.06, 0, 0.44) to (−0.03, 0, 0.44), so it now sits inside the torso.
- Sections updated to match: 1 (summary and assumptions), 3.1 and 3.4 (joins), 4, 5, 6 (spool budget note), 7 (cord and belt row, glow note), 10 (criteria 2, 4, 5, 6 and 7), 11 (diagrams).
- Unchanged: the cloak as built (the soft bell), the pose, the needle, the legs, the colours, the lighting, the camera and the list of renders.

## Revision 4 (2026-11-02)

The user reviewed the v3 renders and asked for a different right arm: "the arm seems to go under the cloak and then bends awkwardly up to the needle; make the arm straight, with the cloak pushed aside by the arm". Decided with the user; the numbers are the orchestrator's.

- **ArmRight (3.6), rewritten.** The arm is one straight tube from the shoulder inside the torso at (−0.03, 0, 0.44) to the hand on the needle's grip at about (−0.30, −0.09, 0.41): nearly horizontal, going out to her right, slightly forward and slightly down, about 0.29 m long. Diameters as before: 2.2 cm at the shoulder, 1.6 cm at the wrist. No elbow bend. The hand and its three fingers round the grip stay as built. The arm leaves the cloak through its right side at about X −0.13, so roughly the outer 16 cm of the arm plus the hand are visible.
- **Cloak (3.1), the right side.** The arm pushes the cloak: the fabric drapes over the arm like a ridge from the shoulder to where the arm comes out, and hangs from the arm below it, so the arm comes out from under the cloak's edge, not through a hole. On her right side the hem rises to about Z 0.34–0.36 directly under the arm and blends back to the old heights (0.28 at the right, 0.26 front, 0.24 back) within about 15 cm on either side. The cloak stays one single quad sheet with the same face count, never touches the arm (gap at least 1 cm, it rests on the ridge above the arm), and does not intersect itself. Everything else about the cloak is unchanged.
- **Criterion 7** now reads: the cloak does not touch the arm, the needle or the spool, and the arm is straight (no point of its centreline more than 1 cm off the shoulder-to-hand line).
- **Spool (3.9), revision 4a.** With the right side of the cloak lifted by the arm, the spool at X 0 showed through the opening under the arm in the hero view. So the spool moves to her left-back quadrant, under the low left side of the cloak: axis at about (X +0.055, Y +0.065), same heights as revision 3a (body Z 0.28–0.36, cone tip 0.2605, belt Z 0.37–0.385). The belt stays round the torso; the cord joins the belt at the spool. The thread still starts on the wound thread and comes out under the back hem on her right, so its first segment runs behind the legs under the cloak. Clearances as before: 1 cm torso, 1.5 cm cloak inside, 4 cm legs (the legs are inside the torso at these heights, so the torso gap covers it).
- **Criterion 2, revision 4a.** The cloak's width is measured at the hem on her left and at the front and back as before (0.46–0.50 m across the unlifted hem would no longer be reachable: her right hem is lifted by the arm). New check: the hem on her left (+X) reaches at least X +0.22, the front and back hem half-depths are 0.17–0.21 m, and the overall cloak width including the lifted right side is 0.40–0.50 m. Cloak-to-mask width ratio is dropped.
- Sections 3.1 (right hem at 0.28 m) and 3.6 (bent arm with an elbow at (−0.25, −0.03, 0.20)) are overridden by this revision where they conflict.
- **Torso (3.4), revision 4b.** The user asked for a waisted, slightly feminine torso instead of a blob. Built: shoulders 0.120 × 0.091 m at Z 0.44–0.46, waist 0.084 × 0.064 m at Z 0.37–0.375, hips 0.115 × 0.085 m at Z 0.30–0.31, a slight chest swell. The belt sits on the waist at Z 0.37–0.385. Overrides the "narrows towards the top" text in 3.4.
- **Spool (3.9), as built.** The axis is at (X +0.061, Y +0.082): at (0.055, 0.065) it was only 2.2 cm from the left leg. Clearances as built: torso 2.8 cm, cloak 1.5 cm, left leg 4.0 cm. The cord is about 6 cm. Zero spool pixels in the front, hero and side views.
- **Accepted deviations after the fourth inspection:** the thread's first segment comes 4.0 cm from the cloak just past its 10 cm exemption, under the cloak and invisible; directly under the arm the cloak forms a slit about 6 cm wide up to Z 0.46, through which the dark torso shows only from her right side, which is not one of the brief's views. Section 3.6's elbow edge-ring rule no longer applies.
- **Thread at the eye, revision 4c.** The approach to the eye was reworked after the lookdev close-up showed a "7"-shaped kink: the thread now arcs over the top of the ring about 2 cm above it and drops through the hole from back to front, with the loose end curving forward and down. Tightest bend radius 39 mm (was 18 mm). The length is now about 4.05 m, accepted over the 3.6–4.0 m guide.
- Unchanged: the needle, the grip position, the thread's loop, the mask, the legs.

## Revision 3 (2026-11-02)

The user supplied two new references for the head, `reference/10-mask-model-front-colour-zones.png` (front, turned slightly to a three-quarter view) and `reference/11-mask-model-side-teardrop.png` (side), and said: "This is what the head must be, front and side view." The user also asked for plain pointed legs without the bend at the ends. Only these points changed.

- **Mask (3.2), rewritten from references 10 and 11.** The numbers are measured on those two images (section 3.2 says how). Kept: the horn tips at Z 1.00 m, the chin at Z 0.53 m, the width of 0.22 m, the bottom of the notch at Z 0.72 m (it measures 0.72 on ref. 10 too), the front of the face at Y −0.085 m, the eye size, tilt and depth rules. What changed:
  - **front:** the head is now a tall egg with a broad round chin (was a pointed V chin). It is widest between Z 0.68 and 0.70 m, just above the eyes (was 0.62). Above that the sides curve inwards without any break and become the outer edges of the horns;
  - **horns:** each horn is thick, about 0.072 m wide at its base (Z 0.78 m), about a third of the head width. Its outer edge is a convex arc and its inner edge is nearly straight, so the tip points up and slightly inwards;
  - **notch:** it is now a narrow slot, 0.06 m wide, with nearly parallel walls and a round bottom (was a U that opened to 0.18 m). So the horn tips are now 0.06 m apart (was 0.17);
  - **side:** the whole head is now one teardrop that leans back. The face is the fat round bottom. The front edge sweeps back from just above the eyes at about 40° from vertical. The back edge is nearly straight from the neck to the tip, at about 20°. The horn tips are now at Y +0.20 m (was +0.118), 0.285 m behind the front of the face. The separate rounded back of the skull is gone;
  - **depth:** 0.167 m at Z 0.61 m (was 0.16 m at 0.64). The frontmost point of the face is now at Z 0.59 m (was 0.64). The lowest point of the chin is at Y −0.04 m (was −0.03);
  - **eyes:** the centres are now at Z 0.61 m (was 0.62). The round chin gives more room, so the eye-to-outline margin is now at least 1.5 cm (revision 2a: 1.4 cm). The designed value is about 1.7 cm;
  - **the back lip of the notch** must be rounded, with no fold. The version 2 build had a sharp fold there.
- **Legs (3.5).** The 6 cm forward toes are removed. Each leg is a straight tapering tube with the same slight knee bend, ending in a sharp point that touches the floor at (±0.065, 0, 0). The thicknesses are kept.
- **Spool (3.9).** The revision 2a raise is now written into the main text. Revision 3a: raised a further 1.5 cm after the build, because the cone tip still showed in the hero view: body Z 0.28–0.36 m, cone tip Z 0.2605 m, belt Z 0.37–0.385 m. Half a pixel of the cone tip remains in the hero view, accepted.
- Sections updated to match: 1 (assumptions), 3.2, 3.5, 3.9 (text only), 4, 5, 6 (the legs no longer have an ankle joint), 10 (criteria 1, 2, 4, 5 and 8), 11 (the front view and the side view of the mask).
- Unchanged: the cloak, the pose, the needle, the thread (including the revision 2a point 10), the colours, the lighting, the camera and the list of renders.

## 1. What it is

Hornet from Hollow Knight: Silksong in a calm standing pose. She stands upright with her feet slightly apart. Her right hand rests on her needle, which is planted point-down in the floor beside her. The style is "as in the game": simple clean shapes and flat, even colours, with no dirt, scratches or textures, as if the 2D game art were brought into 3D. The mood is quiet, composed and a little watchful. The background is dark, and only the thread glows. This is our own take on the character, not a copy of any one statue in the references.

The glowing thread starts at a small spool hidden under her cloak and comes out under the back edge of the cloak. It wraps once around Hornet in a loose tilted loop, at shoulder height at the back and low at the front. Then it climbs beside the needle on her right and passes through the needle's eye from back to front. A short loose end hangs out past the eye.

Assumptions I made where the references show nothing or disagree:

- Scale: 1.00 m tall. The game gives no size. Section 2 explains the choice.
- No base and no diorama in version 1: no lamp post, mushrooms, gravestone or stones. Only the character and a plain dark floor. A base is left for a second pass.
- Her left arm is fully hidden under the cloak and is not built in version 1.
- The spool hangs under the cloak, on a thin belt at the back of her waist. This was the user's decision after the first pass. I leave out the beads and the extra legs from reference 03, because they are most likely the artist's own additions.
- The mask's shape is measured from references 10 and 11, which the user chose as the target. Its overall height and width are kept from earlier revisions, so the mask is 2.1 times taller than wide, a little fuller than ref. 10, which measures about 2.3.
- Reference 11 is taken as the head already worn the way she holds it, looking very slightly down. So no extra forward tilt is added on top of it. If the whole head were tipped forward another 6°, the horn tips would come about 5 cm forward and the backward sweep would look weaker.
- Reference 10 is seen from a slightly turned angle, so its widths were corrected for the turn. Its near horn looks longer because of perspective. I made both horns the same.
- The needle is our own design, based on references 05, 06 and 09: a ring-shaped eye, a long thin shaft, a thread-wrapped grip and a leaf-shaped blade.
- The head looks straight ahead and tilts slightly forward, with no sideways tilt.

## 2. Dimensions

**Coordinate system** (for the modeler). The floor is at Z = 0. The origin is on the floor between her feet, and Z points up. Hornet faces −Y, straight into Blender's front-view camera. Her right side, where the needle is, is −X (the viewer's left). Her left side is +X, and her back is +Y.

| Measurement | Value | Source |
|---|---|---|
| Height from floor to horn tips | **1.00 m** | our choice |
| Width of the character, without needle and thread (at the cloak hem) | 0.48 m | ratio from ref. 07: cloak width ≈ 0.49 × height |
| Depth of the character (at the cloak hem) | 0.38 m | estimate from ref. 09 |
| Width of the whole composition, with needle and thread loop | ≈ 0.90 m | follows from section 3 |
| Depth of the whole composition, with thread loop | ≈ 0.85 m | follows from section 3 |
| Needle length | 0.85 m | our choice, from the proportions in ref. 05 and 07 |

**Why 1 m and not 111 mm.** The 111 mm in reference 06 is the height of a printed figure including its base and the pink "thread" shape, not the character's height, so that number cannot be used directly. I chose 1 m for three reasons. Blender's cloth and lighting are tuned for objects of roughly human size: at 11 cm the cloak would behave like sheet metal and need a lot of tuning. Round numbers make it easy for the modeler and the inspector to check proportions. For a printed figure, the model can simply be scaled down later: at 1 m tall, a 1:9 scale gives about 11 cm.

**How the proportions were found.** I measured the share of each part in pixels on ref. 07 (the cleanest front view) and checked it against ref. 09 (side view). In ref. 09 the camera looks down from above, so the head looks larger there. I used the average. The mask is measured on refs. 10 and 11 (see section 3.2).

## 3. Parts (largest to smallest)

**10 parts** in total. All of them sit in one group (a "collection", which is a folder of objects in Blender) named `Hornet`.

### 3.1 `Cloak`

- **Shape:** a short flared bell-shaped cloak, like an upside-down bellflower. It is closed all the way round, with no opening at the front. It is a thin sheet of fabric. A thickness of about 8 mm appears only in the render, while the model itself is a single sheet, like real cloth. This lets the cloak be animated as cloth later.
- **Profile by height** (half-width to the side / half-depth front to back):
  - top, Z 0.50 m: a narrow neck opening Ø 0.10 m, hidden inside the collar;
  - shoulders, Z 0.45 m: 0.12 / 0.10 m, softly rounded;
  - middle, Z 0.35 m: 0.19 / 0.15 m;
  - hem, Z 0.21–0.28 m: 0.24 / 0.19 m.
- **Folds:** 7 large soft waves, like a bellflower. They start about 8 cm below the collar and get deeper towards the hem. The hem is wavy, and the waves stand out ±2.5 cm from the average edge.
- **Hem height around the cloak** (the hem is uneven, as in ref. 07): 0.26 m at the front, 0.24 m at the back, sagging to 0.21 m on her left (+X), and lifted to 0.28 m on her right (−X), where her right arm comes out from under it.
- **Joins:** the top goes under the `Collar`. The `Torso` is inside the cloak, and the cloak does not touch it: the gap is at least 1.5 cm. The `Spool` and its belt hang inside the cloak at the back, at least 1.5 cm from it. `ArmRight` comes out from under the right edge of the hem.

### 3.2 `Mask` (one solid piece, horns included)

- **The idea:** the mask is one smooth, solid shape, like a tall egg with a slot cut down into it from the top.
  - **From the front** it is a tall egg. The chin is a broad round curve, with no point. The sides swell out to the widest part just above the eyes, then keep going upwards and curve gently inwards, without any break, until they meet at two sharp tips.
  - **The slot** splits the top of the egg into two thick horns. It is narrow, with nearly parallel walls and a round bottom at Z 0.72 m, about two fifths of the way up from the chin.
  - **From the side** the whole mask is one teardrop that leans back. The face is the fat round bottom. Above the eyes the front edge sweeps back steeply into the horns. The back edge runs nearly straight from the neck to the tip. There is no separate back of the skull.
  - **No shoulder, no seam, no crease.** It is one smooth surface everywhere, including the bottom and both lips of the slot. The mask covers the whole head, so it is white from behind too.
- **How the numbers were found.** The heights come from ref. 10 and ref. 11, scaled so that the chin is at Z 0.53 m and the tips are at Z 1.00 m. Ref. 10 is turned about 30° from the front, so its widths were corrected for the turn and then scaled to the 0.22 m width. The side numbers come from ref. 11 (at this scale, 1 pixel is about 1 mm), placed so that the front of the face is at Y −0.085 m. My reading accuracy is about ±1 cm.
- **How to read the numbers.** All numbers are for the finished pose. The slight downward look of the head is already in them (see "Tilt" below), so nothing extra is rotated. The mask is symmetric about her centre line (X = 0). Y runs from the front (−) to the back (+), and Z is the height above the floor. The tolerance is ±5 mm unless stated.
- **Front view, outline by height:**

  | Height Z (m) | Full outer width (m) | Width of the slot between the horns (m) | Width of each horn (m) | What it is |
  |---|---|---|---|---|
  | 0.53 | a point | — | — | lowest point of the round chin |
  | 0.535 | 0.064 | — | — | |
  | 0.54 | 0.090 | — | — | |
  | 0.55 | 0.124 | — | — | |
  | 0.56 | 0.148 | — | — | |
  | 0.57 | 0.166 | — | — | bottom of the eyes |
  | 0.58 | 0.180 | — | — | |
  | 0.59 | 0.190 | — | — | |
  | 0.60 | 0.198 | — | — | |
  | 0.61 | 0.203 | — | — | centre of the eyes |
  | 0.62 | 0.208 | — | — | |
  | 0.64 | 0.214 | — | — | |
  | 0.66 | 0.218 | — | — | top of the eyes (0.651) |
  | 0.68 | **0.22** | — | — | widest part |
  | 0.70 | **0.22** | — | — | widest part |
  | 0.72 | 0.218 | 0 | — | round bottom of the slot |
  | 0.74 | 0.214 | 0.036 | 0.089 | |
  | 0.76 | 0.208 | 0.050 | 0.079 | |
  | 0.78 | 0.200 | 0.056 | **0.072** | base of the horns |
  | 0.82 | 0.184 | 0.060 | 0.062 | |
  | 0.86 | 0.166 | 0.060 | 0.053 | |
  | 0.90 | 0.144 | 0.060 | 0.042 | |
  | 0.94 | 0.116 | 0.060 | 0.028 | |
  | 0.97 | 0.090 | 0.060 | 0.015 | |
  | 1.00 | tips at X ±0.030 | — | 0 | two sharp tips, 0.06 m apart |

  - **The chin** is the round bottom of the egg. In the front view it curves with a radius of about 10 cm, so it reads as round, not pointed.
  - **The outer outline** is one smooth, convex curve from the chin to each tip, like the outline of an egg. There is no waist, no shoulder and no step anywhere on it, and no dent where the head becomes a horn. The outline narrows slowly just above the widest part and faster towards the tips.
  - **The horns.** Each horn's outer edge is a convex arc, like the outer edge of a crescent moon. Its inner edge, the wall of the slot, is nearly straight and vertical. The two edges meet at a sharp tip on the inner side, so the tips point up and very slightly towards each other.
  - **The slot** goes right through the head from front to back. In the front view its bottom is a round U with a radius of about 2.5 cm, and above Z 0.78 m its walls stay about 6 cm apart. Seen from above, its floor is a smooth rounded trough that stays level within 2 cm from front to back. Both lips of the slot, front and back, are rounded with a radius of at least 1.5 cm. Where the floor meets the back of the head there is no fold, crease or sharp edge.
- **Side view, profile by height** (her face is at −Y; the two horns overlap in this view):

  | Height Z (m) | Front edge, Y (m) | Back edge, Y (m) | Depth (m) | What it is |
  |---|---|---|---|---|
  | 0.53 | −0.040 | −0.040 | 0 | lowest point of the round chin |
  | 0.54 | −0.068 | +0.030 | 0.098 | |
  | 0.55 | −0.076 | +0.048 | 0.124 | |
  | 0.57 | −0.083 | +0.068 | 0.151 | |
  | 0.59 | **−0.085** | +0.078 | 0.163 | frontmost point of the face |
  | 0.61 | −0.084 | +0.083 | **0.167** | deepest |
  | 0.63 | −0.081 | +0.085 | 0.166 | |
  | 0.65 | −0.075 | +0.088 | 0.163 | |
  | 0.67 | −0.066 | +0.091 | 0.157 | |
  | 0.69 | −0.055 | +0.094 | 0.149 | |
  | 0.72 | −0.032 | +0.101 | 0.133 | height of the slot bottom |
  | 0.76 | +0.002 | +0.115 | 0.113 | |
  | 0.80 | +0.036 | +0.130 | 0.094 | |
  | 0.84 | +0.070 | +0.144 | 0.074 | |
  | 0.88 | +0.105 | +0.157 | 0.052 | |
  | 0.92 | +0.139 | +0.170 | 0.031 | |
  | 0.96 | +0.172 | +0.184 | 0.012 | |
  | 1.00 | +0.200 | +0.200 | 0 | horn tip |

  - **The face** is the fat round bottom of the teardrop. Between Z 0.55 and 0.66 m its front moves by only about 1 cm, so the face reads as gently convex and upright.
  - **The chin** is round from the side too. The bottom curves from the face, through the lowest point at Y −0.04 m, up into the back, with no point or edge.
  - **The back lean.** Above the eyes the front edge sweeps back in one smooth curve and leans about 40° from vertical above Z 0.72 m. The back edge is nearly straight from Z 0.61 m to the tip: about 10° from vertical up to Z 0.72 m, then about 20°. Between them, the centre line of the horns leans back about 30°. The tips end 0.285 m behind the front of the face.
  - **The horns grow out of the full depth of the head** and taper evenly to the tip, like a wedge. Each horn is about 0.33 m long along its centre line, measured from the slot bottom. Its cross-section, measured across the horn, is a rounded oval, about 7 cm wide and 8 cm deep near the base, and it becomes round towards the tip.
- **Top view of the head across the eyes.** The front of the face is a gently curved shield. The Y of the face's front across the face is:

  | At height Z 0.58 m: X (m) | 0 | ±0.04 | ±0.06 | ±0.075 | ±0.090 (the side) |
  |---|---|---|---|---|---|
  | Y of the face's front (m) | −0.084 | −0.079 | −0.070 | −0.056 | about 0.00 |

  | At height Z 0.61 m: X (m) | 0 | ±0.04 | ±0.07 | ±0.09 | ±0.1015 (the side) |
  |---|---|---|---|---|---|
  | Y of the face's front (m) | −0.084 | −0.080 | −0.068 | −0.050 | about 0.00 |

  Behind the widest point, the back of the head is a smooth curve reaching +0.083 m at the centre line at Z 0.61 m.
- **Eyes:**
  - **Size and place:** two large black ovals, each 6 cm wide and 8.5 cm tall, low on the face. Their centres are at Z 0.61 m, 4.5 cm either side of the middle, so each eye runs from about Z 0.57 to 0.65 m. The ovals are tilted 15° with their top ends towards the middle of the face ("/ \"), which gives a calm, attentive look. They are part of the mask in a black colour, not a separate object.
  - **Depth:** each eye is a shallow, smooth dish, no more than 1 cm deep at its centre. The dish slopes gently inwards from its rim, with no wall steeper than 45° to the face around it. The whole dish is black, from rim to centre, and the rim is a clean edge between white and black. So from the side or the three-quarter view you see a black oval, never a hole with inner walls.
  - **The black stays on the front of the face:**
    - **Maximum Y extent:** no point of either eye outline lies further back than **Y −0.055 m**. With the numbers above, the furthest-back point, at the lower outer edge of each eye, is at about Y −0.060 m.
    - **Distance from the outline:** in the front view, every point of the eye outline is at least **1.5 cm** inside the mask's outline. The designed value is about 1.7 cm, and the tightest spot is the lower outer edge of each eye. (Revision 2a: 1.4 cm. The round chin gives more room.)
    - The black never wraps round the side of the head.
- **Tilt:** the head looks very slightly down, about 6° (chin slightly down), as it does in ref. 11. This is already in the numbers above, so nothing extra is rotated. There is no sideways tilt.
- **Joins:** the round bottom of the chin rests on the `Collar` and sinks 1 cm into it.

### 3.3 `Needle` (the weapon)

- **Construction, top to bottom** (0.85 m in total):
  - **eye:** a smooth ring, outer Ø 6.5 cm, hole Ø 4 cm, 1.2 cm thick. The ring faces the front-view camera, so the background shows through the hole;
  - **shaft:** thin and round, 0.36 m long, Ø 1.4 cm, slightly thicker towards the grip;
  - **grip:** 4 cm of white thread wrapping, in 5 separate turns;
  - **blade:** 0.38 m long, leaf-shaped. Over the first 6 cm below the grip it widens to 4.5 cm, then tapers in a straight line to the point. Its cross-section is a diamond with a crisp ridge down the middle, 1.4 cm thick at the ridge. The flat faces of the blade face front and back.
- **Position:** the point is planted in the floor at X −0.244, Y −0.09 m (to her right and slightly in front). The needle leans outwards, top towards −X, 8° from vertical. The grip is at about (X −0.30, Y −0.09, Z 0.40) and the centre of the eye at about (−0.357, −0.09, 0.81) m.
- **Joins:** the grip is in the right hand of `ArmRight`. The needle stays at least 5 cm from the cloak horizontally.

### 3.4 `Torso` (almost always hidden)

- **Shape:** a dark elongated body that narrows towards the top: 0.12 m wide, 0.09 m deep, from Z 0.27 to Z 0.51 m. At the top, a thin neck goes up into the collar.
- **Why it is needed:** the cloak rests on it, the legs and the arm attach to it, and the spool's belt wraps round it.

### 3.5 `LegLeft`, `LegRight`

- **Shape:** very thin black legs. Each one is a straight tube that gets thinner towards the bottom and ends in a plain, sharp point. There is no foot and no toe.
  - **Thickness:** 3.2 cm at the thigh, 2.2 cm at the knee and 1.6 cm at Z 0.06 m. Over the last 6 cm the leg narrows to a sharp point.
  - **Knee:** about half-way down, at Z ≈ 0.15 m, the leg bends 5° forward, so the knee comes about 7 mm in front of the straight line.
- **Position:** the legs start inside the torso at (±0.04, 0, 0.30), and the points touch the floor at (±0.065, 0, 0), so the stance is a slight upside-down "V". About 0.22 m of leg shows below the hem, with background visible between the legs.
- **Joins:** the tops are hidden inside `Torso`, and the points stand on the floor (Z = 0).

### 3.6 `ArmRight` (right arm with hand)

- **Shape:** a thin black arm (Ø 2.2 cm at the shoulder, 1.6 cm at the wrist). The hand is simple: three thin pointed fingers wrapped around the needle's grip.
- **Position:** the shoulder is inside the torso at about (−0.03, 0, 0.44), with at least 1 cm of torso around it. The upper arm runs down and outwards under the cloak, and the elbow appears from under the right edge of the hem at about (−0.25, −0.03, 0.20). The forearm rises to the needle's grip at about (−0.30, −0.09, 0.40). Only the elbow, forearm and hand are visible. The pose is like a person resting a hand on a tall staff with the elbow down.
- **Joins:** the shoulder is hidden inside `Torso`. The lifted right edge of the hem (Z 0.28 m) does not touch the arm. The hand wraps around the grip of `Needle`.

### 3.7 `Thread` (the glowing thread)

- **Shape:** one continuous smooth thread, Ø 8 mm, with no kinks and a slight natural sag. It is a controllable curve with 12 control points, not a frozen mesh, so it can be animated later. A control point is a point the curve passes through. Its length is about **3.8 m** (anywhere from 3.6 to 4.0 m is fine).
- **Path** (approximate control points in metres, in order):
  1. (−0.025, 0.085, 0.285): the start, on the wound thread of the spool, on the side towards her right, under the cloak;
  2. (−0.08, 0.14, 0.16): low under the back of the cloak. From here the thread passes out under the back hem, at least 5 cm below the hem's edge;
  3. (−0.33, 0.16, 0.18): behind her on the right, low, outside the cloak;
  4. (−0.40, −0.30, 0.27): front right, outside and in front of the needle;
  5. (0, −0.42, 0.33): centre front, at the height of the lower cloak;
  6. (0.42, −0.02, 0.41): her left side;
  7. (0, 0.38, 0.47): behind her, at shoulder height, below the collar;
  8. (−0.39, −0.06, 0.47): her right side, at shoulder height, outside the needle. On the way here the thread passes about 12 cm behind the needle's shaft;
  9. (−0.42, −0.13, 0.66): climbing on the outer side of the needle, a little in front of it, beside the face;
  10. (−0.40, −0.078, 0.80): just behind the needle's eye, on its outer side. (Revision 2a: was Y −0.065, which in the side view hides about 10 cm of the climb behind the face; at Y −0.075 or further forward the climb stays in front of the face. Still 1.2 cm behind the ring's centre plane at Y −0.09.)
  11. through the needle's eye at (−0.357, −0.09, 0.81), from back to front, without touching the ring (unchanged from version 1);
  12. a loose end of about 10 cm hangs in front of the eye and ends near (−0.38, −0.16, 0.72) (unchanged from version 1).
- **The result:** a tilted "orbit" around her, low at the front (about 0.27–0.33 m) and at shoulder height at the back (about 0.47 m). After the orbit the thread climbs her right side, outside the needle, to the eye. Her right side is passed twice: low at the start and high on the way to the needle. Near the eye, the climbing strand and the loose end both hang on the outer side of the needle, like the two strands of a threaded sewing needle.
- **Rules:**
  - **Clearance.** The thread stays at least 5 cm away from the cloak, mask, horns, body, legs, arm, needle and spool everywhere, with two exceptions: within 8 cm of the centre of the needle's eye, and along its first 10 cm from the spool. There it may come closer, but it touches nothing except the wound thread it starts from.
  - **Front view.** It never crosses the mask, the horns or the eyes. At the front it runs below the collar, across the cloak. On the climb it stays more than 20 cm to the viewer's left of the head.
  - **Side view from her left.** The climbing part shows in front of the face line, next to the needle. It never disappears behind the head or the horns.
  - **Three-quarter views.** It stays clear of the outline of the head and horns.
  - **If the face sticks out further.** Points 9 and 10 are placed so that the thread stays in front of the face in the side view. If the built mask's face comes further forward than section 3.2 says, move both points forward by the same amount.

### 3.8 `Collar`

- **Shape:** a thick, soft red ring, like a rolled-up scarf. Outer Ø 0.12 m, 3.5 cm tall, from Z 0.505 to Z 0.54 m, with rounded top and bottom edges.
- **Joins:** it covers the cloak's neck opening and the neck, and the mask's chin rests on it. Same colour as the cloak.

### 3.9 `Spool` (thread spool under the cloak, with its belt)

- **Shape** (as in ref. 03, but simpler, and a little smaller than in version 1 so that it fits under the cloak): a spool with a vertical axis, 8 cm tall.
  - **End discs:** two discs, Ø 6 cm and 6 mm thick.
  - **Wound thread:** between the discs, Ø 5 cm.
  - **Cone tip:** below the bottom disc, a small pointed cone 2 cm tall.
  - **Axle stub:** on top, Ø 1 cm and 5 mm tall.
- **Belt:** a thin dark strap round the torso at waist height, 1.5 cm tall and 4 mm thick, from Z 0.355 to Z 0.37 m. It hugs the torso all round: it may touch the torso, but sinks into it by no more than 2 mm. At the back it has a small ring.
- **Cord:** a short dark cord, about **4 cm** long and Ø 5 mm. It runs from the ring at the back of the belt to the axle stub, so the spool hangs just behind and below the belt.
- **Position:** the spool's axis is at X 0, Y 0.085 m. The spool runs from Z 0.265 to Z 0.345 m (centre at 0.305 m), and the cone tip reaches down to Z 0.2455 m. That puts it in the space between the back of the torso (Y ≈ 0.045 m) and the inside of the back of the cloak (Y ≈ 0.14 m at this height, allowing for the folds). (Revision 2a: the spool and belt were raised by 2 cm from Z 0.245–0.325 and 0.335–0.35 m, because the cone showed under the front hem between the legs in the front and hero views. The user wants the spool hidden.)
- **Clearances:**
  - at least 1 cm from the torso;
  - at least 1.5 cm from the inside of the cloak, ideally 2 cm;
  - at least 4 cm from the legs.

  At the raised height the gap to the cloak as built is at least 1.5 cm. Do not reshape the cloak, and do not lower the spool again: lower down, its cone shows under the front hem.
- **Visibility:** the spool is a hidden detail, not a visible feature in any of the five renders. At most its lower tip, or the glow of its wound thread, can be glimpsed under the back hem (about 0.215–0.265 m high at the back) or in the three-quarter back view.
- **Joins:** the belt sits on the torso, and the cord joins the belt and the spool. The `Thread` starts from the wound thread. The belt and the cord are part of the `Spool` object, so the scene still has 10 objects.

## 4. Proportions the eye checks first

| What | Value |
|---|---|
| Mask with horns to total height | 0.47 (from 0.53 to 1.00 m); ref. 07 gives ≈ 0.43, ref. 09 ≈ 0.5 |
| Mask height to mask width | 0.47 : 0.22 ≈ 2.1 : 1, a tall egg; ref. 10 ≈ 2.3 : 1 (we keep the width a little fuller, see section 1) |
| Horns above the slot to the head part of the mask (chin to slot bottom) | 0.28 : 0.19 ≈ 1.5 : 1; ref. 10 ≈ 1.45 : 1 |
| Horn base to head width | each horn 0.072 : 0.22 ≈ 1 : 3; at the horn base the horn, the slot and the other horn share the width about 1.3 : 1 : 1.3 |
| Head depth to head width | 0.167 : 0.22 ≈ 0.76 |
| Backward lean of the horns | centre line about 30° from vertical; the tips are 0.285 m behind the front of the face, more than the depth of the head itself (ref. 11) |
| Where the eyes sit | low on the face: eye centres 8 cm above the chin and 11 cm below the bottom of the slot; the widest part of the head is just above them |
| Cloak width to mask width | 0.48 : 0.22 ≈ 2.2 : 1; ref. 07 gives ≈ 2.1 |
| Cloak (collar to hem) to total height | ≈ 0.27 |
| Visible leg (hem to floor) to total height | ≈ 0.22 |
| Needle to total height | 0.85 : 1; the eye is at horn height |
| Needle shaft to blade | 0.36 : 0.38, nearly equal, as in ref. 05 |
| Eye to mask width | 6 cm : 22 cm, each eye is large, almost a third of the width |

The main impression: a big white horned head on a small red bell, on very thin legs.

## 5. Silhouette

- **Front:**
  - **The mask** reads as one tall egg. It has a broad round chin, and its sides swell to the widest part just above the eyes. Above that they curve inwards in one smooth line into two thick horns, whose tips are close together. A narrow slot with a round bottom runs down the middle to about two fifths of the mask's height, with background showing through it. There is no shoulder, step or waist anywhere on the outline.
  - **The rest of the figure:** two black eyes low on the face, the red bell of the cloak, and two separate thin legs, ending in points, with background between them.
  - **The needle** stands at the viewer's left as a separate vertical line, with its eye at horn height and no closer than 20 cm to the horns.
  - **The thread loop** shows as a tilted oval around the figure, below the mask at the front. Its last part climbs on the outer side of the needle to the eye.
- **Side (from her left, +X):**
  - **The head:** one teardrop leaning back. The face is the fat, gently convex bottom. The front edge sweeps back steeply from just above the eyes, and the back edge runs nearly straight from the collar to the tip. The tip ends far behind the face, about 0.285 m. The eyes show at most as a thin black edge at the front of the face.
  - **The body:** the cloak is bell-shaped, and the legs end in plain points, with no feet. The spool is not seen.
  - **The needle** is visible behind the body. The thread rises next to it, in front of the face line, and passes through the eye. The thread never disappears behind the head.
- **Three-quarter front (from her right):** the hero view. It clearly shows the hand on the grip, the whole needle, the eye with the thread through it, and the thread going round the figure and climbing beside the needle, well clear of the head. The horns sweep back away from the needle.
- **Three-quarter back:** the thread coming out from under the back hem, its arc across her back at shoulder height below the head, and the back waves of the cloak. The back of the slot between the horns is a smooth rounded lip, with no fold. The spool is at most glimpsed under the hem.

## 6. Topology (how the surface is built)

The mesh is the model's surface, built from many small faces.

- **Type:** organic (smooth, flowing shapes) for the mask, cloak, collar, torso, legs and arm. Hard-surface (crisp edges) for the needle and the spool.
- **Smoothing:** the organic parts are expected to use subdivision. Subdivision means Blender splits each face into 4 and rounds the shape. Level 1 in the viewport, level 2 in the render. The edges of the needle's blade stay sharp.
- **Faces:** everything that will bend (cloak, legs, arm, torso) is made only of four-sided faces, because cloth and joints only bend cleanly with them. The knees and the elbow have at least 3 rings of faces across them, so the joints can bend later without creasing. The legs no longer have an ankle joint.
- **Cloak:** a single sheet with an even, nearly uniform grid of about 2,500–3,500 faces. This is needed for future cloth animation.
- **Budget:** no more than 20,000 faces for the whole model before smoothing. Rough guide per part: Mask about 3,000, Cloak about 3,000, Collar about 400, Torso about 600, each leg about 500, ArmRight about 800, Needle about 800, Spool about 600 (including its belt and cord). Thread is a curve.
- **Future animation:** every part has its scale "applied" (reset to 1), so cloth and bones calculate correctly. The mask, needle and spool are rigid and will move as whole pieces. The legs and arm will bend. The cloak will be cloth. The thread keeps movable control points.

## 7. Materials

Style: flat, clean colours, with no textures, dirt, wear or patterns.

| Part | Colour | Roughness | Metal | Note |
|---|---|---|---|---|
| Mask (the bone shell) | warm white, #F2EFE8 | 0.35, soft sheen | no | smooth, like glazed ceramic |
| Mask (eyes) | deep black, #050505 | 0.3 | no | a small highlight brings the eyes to life; they do not glow |
| Cloak, Collar | saturated red, #B3141E | 0.75, matte fabric | no | must stay red in the render, not pink or brown |
| Torso, LegLeft, LegRight, ArmRight | near-black with a cool tint, #14121A | 0.5 | no | |
| Needle (eye, shaft, blade) | light cool silver, #C9CCD2 | 0.3 | yes | even metal, no scratches |
| Needle (grip wrapping) | creamy white thread, #EDE8DE | 0.6 | no | does not glow |
| Spool (discs, core, cone) | matte silver, #A8ABB2 | 0.4 | yes | |
| Spool (cord and belt) | near-black, #14121A | 0.6 | no | |
| Thread | warm white, #FFF4E0 | — | no | **glows**, the main glowing element |
| Spool (wound thread) | warm white, #FFF4E0 | — | no | **glows**, 3–4 times dimmer than the thread |

**What glows in version 1: only the thread and the thread wound on the spool.** The lamp and mushrooms in the references belong to the base and come in the second pass. Brightness guide for lookdev: the thread is the brightest thing in the frame and casts a warm glow onto the cloak, but the white mask next to it is not blown out. The wound thread now sits under the cloak. A faint warm glow on the inside of the back hem is welcome.

## 8. Lighting, background and camera for the presentation

> **As built (2026-11-02, lookdev revisions 1–5).** The key is warm white #FFF6EC, 50 W, 1.5 m area light, 45° to the viewer's left of the hero camera and 40° up; the fill neutral 20 W front-right low; two pale-blue #E0E8FF 0.35 m rims of 190 W and 180 W behind her left and right, light-linked to the Hornet objects except Cloak and Collar, so they outline the mask, horns, legs, arm and needle and tint neither the floor nor the cloak; a 60 W 0.1 m `Light_Catch` linked to the Mask only gives each eye one catch-light (eye roughness 0.1). The thread material emits 6.0 for camera rays and 1.25 for all other rays, so it blooms but lights the cloak softly (a Light Path / Map Range node pair). Glare Bloom threshold 2.5. View transform Khronos PBR Neutral, because Filmic and AgX turned the red pink. The five lights and `Cam_02_Hero` (3.15 m from (0, 0, 0.5)) are parented to an Empty `Rig_Pivot` at the origin: the front, left-side and back-left views are rendered through the hero camera with the pivot rotated +35°, +125° and +170°, so every view, and every turntable frame, is lit like the hero view. `Cam_05_EyeCloseup` is separate. Final renders are made in a background Blender from the saved file, not through the socket.


- **Render engine:** Cycles on the graphics card (OptiX), 128–256 samples with denoising.
- **Floor:** a plain dark matte disc, Ø 1.6 m, blue-grey (#1E232B), with no pattern, its edges fading smoothly into the background. It is not a base, only a surface for the needle to stand in and for shadows to fall on. Lookdev makes it, not the modeler.
- **Background:** deep dark blue with a teal tint (#0C121C), slightly darker towards the edges of the frame.
- **Lights:**
  - key: a large soft light front-left of the camera, 45° to the side and 40° up, neutral cool white;
  - rim: behind her on the right, high, pale blue, strong. It draws a light outline around the horns, the mask and the edge of the cloak, so the silhouette separates from the dark background;
  - fill: weak, front-right, low, so the black legs do not disappear into shadow;
  - the thread itself lights the figure with warm light.
- **Glow halo:** a soft glow around the thread (an effect added after rendering), kept moderate so it does not wash over the mask and eyes.
- **Camera:** an 85 mm telephoto lens, which gives almost no distortion. The camera is 0.50 m above the floor and looks at a point 0.50 m above the centre. The distance is set so that the character, the needle and the thread loop fill about 85% of the frame height.
- **Frame:** 1080 × 1350 (portrait, 4:5).
- **Views** (5 images in `designs/hornet/renders/`):
  1. front;
  2. three-quarter front from her right (the needle side), 35° from the front view, the hero shot;
  3. side from her left (+X), 90°;
  4. three-quarter back from her left, 135°;
  5. close-up of the needle's eye from the front, to check that the thread passes through the hole.

## 9. Animation (later, not part of version 1)

> **Revision 5 (2026-11-02), decided with the user after the first turntable.** The user's words, translated: "I want a static camera, not a full turn, or a slow half-turn; and the cloak with a much stronger animation, as if streaming sideways in the wind; the thread can wind about in the same way." The user chose the static camera. So version 1's animation is now:
> - **Camera:** static, `Cam_02_Hero`, `Rig_Pivot` fixed at 0°. No turntable. The lighting rig stays as built.
> - **Length:** 8 s, frames 1–192 at 24 fps. No loop is required: it is a clip, not a cycle. The cloth gets a pre-roll of about 2 s before frame 1 so it is already streaming at the first frame.
> - **Cloak:** a cloth simulation with collisions, not the Displace sway. Wind blows from her right (the needle side, −X) towards her left (+X), slightly towards the back (+Y), so the cloak streams away from the needle and the arm and to the viewer's right in the hero view. Strength: the lee-side hem lifts and streams about 10–20 cm, with gusts and flutter (as accepted on 2026-11-02: 5–13 cm sideways and 5–10 cm up; stronger wind pushed the cloth through the body, and the user said this is enough) (a Wind force field plus Turbulence, with the wind strength varying over time). Pinned: the neck ring and the top of the cloak down to about Z 0.44, and the fabric resting on the arm's ridge, so the drape over the arm is kept. Collisions with Torso, Collar, ArmRight, both legs, Spool and Needle; self-collision on. The cloak never passes through any part and keeps its single-sheet quad mesh; Solidify and Subdivision stay after the cloth modifier.
> - **Thread:** static. A waving version was built and previewed; the user's words, translated: "the thread does not need to move at all, the twitching looks bad" (2026-11-02). The thread stays in its approved rest shape; the cloth must keep at least 5 cm from it except under the back hem, where a hidden collision proxy along the first segment keeps the cloak off the thread.
> - **Acceptance:** rendered frames show the cloak streaming sideways with visible flutter; no intersection of the cloak with the body, arm, needle or spool on any sampled frame; the cloak never touches the thread; the thread, mask, needle, hand and legs do not move.

The original section 9 text below described the turntable version, which was built and rendered (`v1-turntable.mp4`) and then replaced by this revision.


This records only what the model must allow:

- **Turntable:** the camera circles the character 360° in 5 s (120 frames at 24 frames per second), looping with no visible seam.
- **Cloak:** sways gently, as if in a light breeze. The hem moves ±2–3 cm, about one sway every 2.5 s, looping every 5 s.
- **Thread:** drifts slowly, with control points moving ±2 cm, looping every 5 s. The ends at the spool and the eye stay fixed.

## 10. Acceptance criteria (checked by the inspector)

1. **Height and floor:** from the floor to the horn tips is 1.00 m ± 2 cm. The points of both legs and the needle's point are at Z = 0 ± 5 mm.
2. **Proportions:** checked from scene data.
   - **Mask height and width:** the bottom of the mask is at Z 0.53 ± 0.02 m. The mask is 0.22 ± 0.01 m wide at its widest, which lies between Z 0.64 and 0.72 m.
   - **Mask depth:** the mask is 0.167 ± 0.015 m deep from front to back at its deepest, which lies between Z 0.57 and 0.65 m.
   - **Slot and horn tips:** the bottom of the slot between the horns is at Z 0.72 ± 0.02 m. The horn tips are 0.06 ± 0.015 m apart and lie at Y +0.20 ± 0.02 m.
   - **Cloak:** the cloak is 0.46–0.50 m wide. Cloak width to mask width is between 2.0 and 2.4.
   - **Needle:** the needle is 0.85 ± 0.02 m long.
3. **Scene contents:** the `Hornet` collection holds exactly 10 objects with the names from section 3, with no ".001" suffixes. Every object has a scale of 1.
4. **Front view (render 1):**
   - **What reads:** two horns with background between them, two black eyes, the red cloak, and two legs with background between them, plus the needle at the viewer's left as a separate line. The eye of the needle is no closer than 20 cm to the horns.
   - **The mask reads as one tall egg split at the top.** From scene data:
     - at Z 0.55, 0.61, 0.70, 0.78, 0.86 and 0.94 m, the outer width matches the table in section 3.2 within ±1 cm;
     - the outer outline has no inward dent: from the chin to each tip, every outline point lies on or outside the straight line between the outline points 4 cm above and 4 cm below it, within 2 mm;
     - each horn is 0.065–0.080 m wide at Z 0.78 m and gets steadily narrower up to its tip;
     - the slot walls stay 0.05–0.07 m apart from Z 0.78 to 0.97 m;
     - every point of each eye outline is at least 1.5 cm inside the mask's outline.

     In the render the chin is round, not pointed, there is no shoulder or step where the head becomes a horn, and the slot has a round bottom.
   - **The thread** does not cross the mask.
5. **Side view (render 3):**
   - **Face:** it reads as a gently convex, upright face. From scene data, the frontmost point of the face is at Y −0.085 ± 0.01 m, and the front along the centre line moves by no more than 1.5 cm between Z 0.55 and 0.66 m.
   - **Horns:** the head reads as one teardrop leaning back. From scene data, the front edge above Z 0.72 m leans 35–45° from vertical. Between Z 0.64 and 1.00 m the back edge stays within 1 cm of a straight line, with no bump of a separate skull.
   - **Back lip of the slot:** in render 4 the back of the slot is a smooth rounded lip, with no fold, crease or sharp edge.
   - **Eyes:** each is a dish no deeper than 1 cm, and no point of either eye outline lies further back than Y −0.055 m. Renders 2 and 3 show no inner walls in the eyes and no black on the side of the head.
   - **Legs:** each leg ends in a plain point with no foot or toe. From scene data, the point is at X ±0.065 ± 0.01 m and Y 0 ± 0.01 m, and the lowest 5 cm of each leg stay within 1.5 cm of that point horizontally.
   - **Spool:** it is not a visible feature. At most its lower tip shows under the back hem.
   - **Thread:** it does not disappear behind the head or the horns.
6. **Thread:**
   - **Shape and length:** one continuous glowing line, 3.6–4.0 m long. It starts at the spool under the cloak, comes out under the back hem, goes once round her, and climbs to the eye of the needle.
   - **Through the eye:** the close-up (render 5) shows it passing through the hole from back to front without touching the ring.
   - **Clearance:** it stays at least 5 cm from every part, except within 8 cm of the eye's centre and along its first 10 cm from the spool (checked from scene data).
   - **Head:** in renders 1–4 it never overlaps the mask or the horns.
7. **No intersections:**
   - **Intended joins only:** parts do not pass through each other, except at the intended joins: the grip in the hand, the chin on the collar, the legs and arm inside the torso, and the belt hugging the torso.
   - **Cloak:** it does not touch the arm, the needle, the spool or the belt.
   - **Spool:** it is at least 1 cm from the torso and at least 1.5 cm from the inside of the cloak.
8. **Mesh:** the cloak, legs, arm and torso are made only of four-sided faces. The knees and the elbow each have at least 3 rings of faces. The total is no more than 20,000 faces before smoothing. The cloak is a single sheet.
9. **Colours:** flat, with no textures. The cloak reads as saturated red in the render. Only `Thread` and the wound thread on `Spool` glow.
10. **Renders:** all 5 images, 1080 × 1350, are in `designs/hornet/renders/`.

## 11. Part diagrams (approximate)

```
   Front view

        Z, m
        1.00 -                    /\ /\             <- two horn tips (part of Mask), only 0.06 m apart
                                 / | | \
        0.90 -                  /  | |  \           <- each horn: outer edge a convex arc,
                               /   | |   \             inner edge nearly straight
  needle eye ->  O            |    | |    |         <- the slot between the horns: narrow, 0.06 m wide
        0.78 -   |           |     | |     |        <- horn base: each horn about 0.07 m wide
                 |           |     \_/     |        <- 0.72: round bottom of the slot
        0.68 -   |          |               |       <- widest part of the mask, 0.22 m
                 |          |  /\       /\  |
        0.61 -   |          | (  )     (  ) |       <- black eyes, low on the face
                 |           \ \/       \/ /
                 |             \         /
        0.53 -   |              '._____.'           <- round chin, no point
                 |              (=======)     0.50-0.54 <- Collar
                 |            /           \
                 |          /     Cloak     \       <- red bell-shaped cloak
                 |  hand  /      (red)        \
                 |=<    _/                     \_
                 |   \ ~~~~~~~~~~~~~~~~~~~~~~~~~~~  0.21-0.28 - wavy hem
   shaft,        |    \_/ <-elbow  |   |
   blade below   |                 |   |            <- LegRight / LegLeft: thin straight tubes
   (Needle)      |                /     \
                 V               v       v          <- plain pointed ends on the floor, no feet
        0.00 - ========================================  floor
               viewer's left = her right side


   Side view of the Mask, from her left (+X); her face is on the left

        Z, m
        1.00 -                             .        <- horn tip, Y +0.20: 0.285 m behind the face
        0.96 -                          //          <- front edge leans back about 40 deg,
        0.92 -                      /  /               back edge about 20 deg, nearly straight
        0.88 -                   /    /
        0.84 -               /       /              <- the horn tapers from the full depth of the head
        0.80 -            /        /
        0.76 -         /          /
        0.72 -     /             /                  <- height of the slot bottom (the slot is hidden here)
        0.68 -  /               |                   <- above the eyes the face curves back into the horn,
        0.64 - |                |                      with no step
        0.60 -|                 |                   <- face: frontmost at Z 0.59; deepest, 0.167 m, at Z 0.61
        0.56 - \             /
        0.53 -   '---------'                        <- round chin, lowest point at Y -0.04
             face (-Y)        back (+Y)


   Top view of the thread path (Thread), looking down; numbers are the points in section 3.7

                                     7                <- back (+Y): the thread runs at
                        .  '  '  '       '  '  '  .      shoulder height (0.47 m)
                   .  '                             '  .
               3 - - - - - - - - 2 - 1 [Spool]           .
             .            .-----------------------.        .
            .            /                         \        .
        8, 10           |          Hornet           |        6
        9     O========|  needle, eye 11              |       .
          12             \                         /        .
            4             '-----------------------'       .
              ' .                                      . '
                   '  .  .  .  .  .  5  .  .  .  .  '
                                                      <- front (-Y): she faces this way
       her right (-X)                                her left (+X)

   - - -  the start: from the spool under the cloak, out under the back hem, low (0.16-0.29 m)
   . . .  the loop: low at the front (0.27-0.33 m), at shoulder height at the back (0.47 m)
   3 is low and 8 is high: the thread passes her right side twice, then 9 and 10
   climb outside the needle to the eye (11); 12 is the loose end.
```

## 12. What a second pass could add

- A base or diorama: a stone or gravestone with a carved swirl, a lamp post with a glowing orb, glowing mushrooms, white flowers (inspired by ref. 01, 02, 05).
- A left arm holding the edge of the cloak.
- A sideways head tilt for more life.
- A cloak lining slightly darker than the outside.
- Beads on the spool cord, if the user wants them (ref. 03).
- Animation: cloak cloth, thread movement, turntable (section 9).
- The two other styles, vinyl figurine and realistic, as separate works with their own briefs.
