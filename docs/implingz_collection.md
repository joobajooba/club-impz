# IMPLINGZ: Imp trait design reference

| Status | Last pass | Depends on |
|---|---|---|
| Draft | User request, 2026-10-30 | MODELS-BLOCKBENCH |

> Claude: read `docs/CLAUDE.md` before working from this file. Read this whole file before modelling any Imp trait in Blockbench.
>
> Labels: **Decided** (in `DECISIONS.md`) · **Proposed** (Claude's suggestion) · **Open question**. Everything under "Looks" in this doc is **observed** from the collection art, not a design choice. The art is the source of truth.

**Purpose of this doc:** a complete description of every trait in the IMPLINGZ NFT collection, detailed enough to write a prompt that builds each trait in Blockbench for the playable Imp (D-038: an NFT holder plays as their Imp).

**Sources studied**
- Images: `Club Impz All Files/Impz Collection Images/` (local, not in the repo). 1,720 PNGs. Token IDs **6–9, 55–99 and 547–999 have no image** (502 missing). Every trait still has at least 6 images.
- Metadata: `Club Impz All Files/Impz Metadata/implingz-metadata.json` (and `.csv`). 2,222 tokens, IDs 1–2222.
- Every image is **64×64 pixel art scaled ×10 to 640×640**. All measurements below are on the 64×64 grid.

**How it was studied:** every trait value was grouped across all of its images. For each group, a pixel that has the same colour in at least 85% of that group's images (95% for groups under 40) was taken as part of the trait, compared with the "None" version of the same trait type. That gives each trait as its own isolated layer with exact colours. Then the cleanest real examples (as few other traits covering it as possible) were looked at close up.

**Words used here.**
- **Grid:** the 64×64 pixel canvas. `x` runs left→right, `y` runs top→bottom, both 0–63.
- **Viewer's left / right:** as you look at the picture. The Imp's own left hand is on the **viewer's right**.
- **Outline:** almost every shape has a 1-pixel black (`#000000`) outline.
- **Shade ramp:** the 2–4 colours a part is painted with, from highlight to deepest shadow.

---

## 0. Reference files in the repo

All in [`docs/imp-traits/`](imp-traits/).

| Path | What it is |
|---|---|
| `bodies/body_<colour>_<id>.png` | One real Imp per body colour at native 64×64, picked with as few traits on top as possible. `body_silver_1870.png` has **no** head, back or clothing trait: the cleanest base Imp in the collection. |
| `layers/<type>_<value>.png` | Each trait isolated on a transparent 64×64 canvas, at its exact place on the grid. Parts the body always covers (for example the middle of a cape) are missing. |
| `layers-sheet-*.png` | The isolated layers of one trait type side by side, enlarged, on a checkerboard. |
| `examples/<type>_<n>.png` | Enlarged crops of the two cleanest real Imps for every trait value, labelled with the token ID. |

To see any token in full, open `<id>.png` in the local images folder.

---

## 1. The trait system

Seven trait types. Every token has exactly one value of each.

| Trait type | Values | Visual? | Notes |
|---|---|---|---|
| Background | 1 (Obsidian) | Backdrop only | Not part of the model. |
| Body | 10 | Yes | Skin colour of the whole Imp. Gold and Diamond also recolour the horns. |
| Head | 18 (incl. None) | Yes | Hair or headwear. |
| Back | 11 (incl. None) | Yes | Wings, cape or a weapon carried on the back. |
| Clothing | 20 (incl. None) | Yes | Covers torso, and for some, arms and legs. |
| Eyes | 19 | Yes | Always something. Some are the eyes themselves (pupil colours), some sit over the eyes. |
| Tier | 3 | **No** | Tier 1 (1,560), Tier 2 (558), Tier 3 (104). It does not change the picture, and it does not follow trait rarity (the average rarity score is the same in all three tiers). |

**Combinations:** traits are independent. No pair of traits is ever excluded beyond chance, so every Head can appear with every Back, Clothing, Eyes and Body. The 3D traits must fit **every** combination (see section 8).

**Draw order in the 2D art**, back to front: Background → **Back** → **Body** (with horns, ears, tail) → **Clothing** → **Head** → **Eyes**.
Exceptions seen in the art:
- The horns are drawn **in front of** the Afro. The Afro is painted around the horns.
- The Straw Hat brim is drawn **in front of** the horn roots.
- Blonde hair falls **over** the clothing and arms.
- Eyes always sit on top, including over hair (Robo over Blonde) and hats (Goggles over hat brims). Lazer and Neon Beam beams are drawn over everything.

---

## 2. The base Imp (every token shares this)

Reference: `bodies/body_silver_1870.png`, token #1870.

**Overall:** a chibi imp facing the viewer, standing with feet slightly apart. The head (with ears) is about as wide as the whole body is tall. Light comes from the **upper left**: the viewer's left half of every part is lit, the viewer's right half is in shade.

| Part | Where on the grid | Looks |
|---|---|---|
| Horns | Roots y≈17–19 at the sides of the skull (x≈14–20 and x≈44–50). Tips at y=1 (x≈13–15 and x≈48–50). | Two big crescent horns, about 6–7 px thick, curving out from the skull then up to a point. Off-white `#fefdfb` / `#ffffff`, shaded with cream-greys `#f0efec` `#e5e3e1` `#ddddda` `#d8d6d2`, black outline. The same white on 8 of the 10 bodies (see section 3 for Gold and Diamond). |
| Skull top | Crown at y≈7, x≈27–37. | Rounded dome. When the Head trait is None, the crown shows a darker cap of body colour with fine vertical streaks, ending at the front in a **V-shaped ridge** (a "widow's peak") pointing down to about y=20 at the middle. |
| Ears | y≈16–27. Tips at x≈9 and x≈54. | Large pointed ears sticking out sideways and slightly up, like a goblin's. The inside is one shade darker. |
| Face | y≈19–35, x≈12–50. | Wide, round, a little wider at the cheeks. No visible nose. |
| Eyes | y≈28–32. Left eye x≈23–28, right eye x≈36–41. | Angry: the black upper lid is thick and slopes **down toward the nose**, so the eyes glare. The default eye is white with a coloured pupil (see Eyes). |
| Mouth | y≈35–36, centred at x≈31–32. | A tiny dark mark. |
| Neck / chin | y≈35–38. | Short. The chin outline shades into the chest. |
| Torso | y≈38–55, x≈20–46. | Round belly. Black lines draw two pecs (an "X"-like cross between them) and a small **navel** at about y=48–50. |
| Arms | Shoulders y≈39. Fists y≈45–51 at x≈13–17 (viewer's left) and x≈45–50 (viewer's right). | Short, angled down and out. Mitten-like fists with one finger line. |
| Legs and feet | y≈55–63. | Short and stubby. The feet reach the bottom edge of the picture. |
| Tail | Leaves the body behind the viewer's-right hip (x≈44, y≈54), loops out right, then rises to the tip at x≈51–54, y≈34–38. | A thin 2-px tail in the body's dark shade, ending in a small **spade** (arrowhead) tip, white `#ffffff` shaded pale blue-grey `#9badb7`. The spade is the same on every body. |

**Background (Obsidian):** a smooth purple-grey gradient, lighter at the left (`#564767`) and darker at the right (`#2a2332`). Backdrop only.

---

## 3. Body (10 values)

The base Imp in one skin colour. All 8 standard colours use a **flat 3-tone ramp**: the main colour on lit areas, a mid shade on the shaded half and the inner ears and crown, and a deep shade for the darkest folds and the tail. Gold and Diamond are different: they are **shiny, textured materials** with many tones, and they recolour the horns too.

| Body | Count | Main (lit) | Mid shade | Deep shade | Horns | Look |
|---|---|---|---|---|---|---|
| Cyan | 306 (13.8%) | `#48ffe1` | `#07846f` | `#033029` | White | Bright aqua / mint. |
| Silver | 287 (12.9%) | `#cfc9c9` | `#919191` | `#4f4f4f` | White | Light warm grey, like stone. |
| Khaki | 277 (12.5%) | `#fffda9` | `#d9e03b`, `#a6ab33` | `#80700a`, `#8a6f30` | White | Pale lemon-cream, shading to olive-yellow. |
| Blue | 270 (12.2%) | `#686fff` | `#111795` | `#070a42` | White | Strong royal / periwinkle blue. |
| Pink | 269 (12.1%) | `#f4a8b8` | `#d94a67` | `#b1123a` | White | Soft pink, shading to raspberry. |
| Purple | 267 (12.0%) | `#9353ab` | `#4f1765` | `#280735` | White | Medium violet. |
| Green | 264 (11.9%) | `#4bd336` | `#285800`, `#1a5c07` | `#224604`, `#1b3902` | White | Bright grass green. |
| Red | 252 (11.3%) | `#ff3737` | `#7b0000` | `#420202` | White | The classic devil red. |
| Gold | 20 (0.9%) | `#fbc650`, `#fde06d` (highlights up to `#fef8d3`) | `#e5901f`, `#d07a10` | `#b05a07`, `#a35e08` | **Gold** | Polished metal: bright yellow-gold highlights, orange-amber shadows, glossy streaks. Horns are the same gold. |
| Diamond | 10 (0.5%) | `#b7e6ff`, `#d3eafd` (highlights to `#f3feff`) | `#83c5fe`, `#5a9ee6` | `#4692cd`, `#0e223b` | **Ice blue** | Pale icy blue crystal with faceted light and dark patches, like cut gem. Horns are ice blue. |

Rare bodies: Gold and Diamond together are 1.4% of the collection.

**Proposed (Blockbench):** the base Imp is one model with one texture per body colour, as in MODELS-BLOCKBENCH section 6. The 8 flat colours can be a palette swap of one painted texture (map main → mid → deep). Gold and Diamond need their own painted texture with metallic / crystal highlights and recoloured horns.

---

## 4. Head (18 values)

Hair or headwear. Bounding boxes are `x0,y0 → x1,y1` on the grid.

| Head | Count | Box | Colours (main → shade → highlight) |
|---|---|---|---|
| Blonde | 189 (8.5%) | 8,7 → 53,61 | `#f7d65b`, `#eabc0e`, `#dfaf0b`, `#c19205` |
| Hawk | 181 (8.1%) | 25,1 → 39,21 | `#45474f`, `#323642`, `#202430` |
| Afro | 177 (8.0%) | 8,1 → 54,32 | `#4a2e2a`, `#241413`, highlight `#84544b` |
| Bob | 175 (7.9%) | 14,8 → 49,35 | `#ed5a99`, `#ce3677`, deep `#590f2f`, highlight `#f6b6d1` |
| Cap | 171 (7.7%) | 19,8 → 44,23 | `#80c9ff`, `#4285b7`, `#316a94`, logo `#ffffff` |
| Slick | 165 (7.4%) | 16,7 → 47,28 | `#864a27`, `#7a401f`, `#3f1a09`, highlight `#af6c41` |
| Tiara | 159 (7.2%) | 18,11 → 46,23 | `#9fc5bf`, `#7b9390`, `#6b7b79`, highlight `#ddf3f0`, gem red |
| Soldier | 156 (7.0%) | 18,8 → 45,37 | `#6d9448`, `#446723`, highlight `#a4c980`, strap `#8f563b` / `#7d3b1b` |
| Spiky | 153 (6.9%) | 22,4 → 41,22 | `#ff6d00`, `#db5e00`, `#982e04`, highlight `#ffac6d` |
| Geezer | 148 (6.7%) | 21,7 → 42,21 | `#b4b4b4`, `#9e9c9c`, `#5c5757`, highlight `#cacaca` / `#e0dddd` |
| None | 136 (6.1%) | n/a | Bald (body colour) |
| Halo | 87 (3.9%) | 20,2 → 43,6 | `#ffd56d`, `#ffb600`, `#ce9300` |
| Clown | 87 (3.9%) | 13,3 → 50,31 | red `#f23630` / `#871023`, blue `#2390e8` / `#143f8a`, yellow `#fde230` / `#c59e05` |
| Straw Hat | 87 (3.9%) | 8,3 → 56,23 | `#e3b872`, `#bd9559`, band `#cb2924` |
| Fez | 76 (3.4%) | 22,1 → 41,18 | `#ce1d1d`, `#821c25`, `#48070d`, highlight `#f63535` |
| Crown | 28 (1.3%) | 21,1 → 43,14 | `#b38b26`, `#70571b`, highlight `#ffd467`, gems `#ac3232` / `#d95763` |
| Sea Captain | 26 (1.2%) | 22,6 → 41,21 | white `#dbd1d1` / `#ffffff`, grey `#9d9999`, visor `#4f4f4f` / `#6b6b6b`, gold `#fbb812` / `#d2990a` / `#ffd261` |
| MAYC Brim | 21 (0.9%) | 17,1 → 48,23 | cap `#ff331b` / `#bd2917`, flames `#ff7f28` / `#ffb028` / `#f6c36c`, patch `#b74d4d` / `#c06c6c` |

### Looks, value by value

- **None:** bald. The skull shows the darker streaked crown and the V-shaped ridge at the front (section 2). Halo and Crown also leave the bald head visible.
- **Afro:** a huge, round, dark-brown afro, shaped like a wide mushroom cap: flat-ish top from x≈8 to 54, puffing out over the ears and coming down beside the cheeks to about y=32. Dark lines suggest curls. The horns stick **out through it in front**, so the afro looks like it sits behind and around the horns.
- **Blonde:** long golden hair, shaped like a hood. It covers the crown, is parted in the middle, frames the face in a rounded arch, and falls in two long curtains past the shoulders, down the sides of the body to y≈61, ending in curls that turn inward. The ears poke out through the hair. A thin strand line runs across the crown. The hair hangs **in front of** the arms and clothes.
- **Bob:** a hot-pink bob cut. A straight-cut fringe across the forehead at about y=21, and side curtains down to the jaw (y≈35) that hide the cheeks' edges. A row of pale pink dashes runs across the crown as a shine line.
- **Cap:** a light-blue baseball cap with the brim to the front, sitting low between the horns. Two white chevron strokes (like an angled "^ ^") form the logo on the front panel. The brim is a darker blue band with a black edge just above the brows.
- **Clown:** a wild rainbow clown wig of chunky tufts in red, blue and yellow, in diagonal bands from upper left to lower right (blue streak through red, yellow on the viewer's right). It sits on the crown and spills out to the temples. Small red tufts poke out by the ears.
- **Crown:** a small gold king's crown with five points, the middle point tallest, and red gems set along the band and at the tips. It sits on top of the bald head, between the horns, high up (y≈1–14).
- **Fez:** a red felt fez: a short, flat-topped cylinder sitting on the crown between the horns. Lit on the viewer's left, dark red on the right, with a darker patch on the right side (the tassel hanging down).
- **Geezer:** short, thinning grey hair: a fan-shaped patch on the crown made of speckled light grey and dark grey pixels, like stubble or old-man hair. The rest of the head is bald.
- **Halo:** a thin golden ring floating flat above the head (y≈2–6), seen at an angle as a wide oval. Bright yellow front edge, orange-gold back edge. The head under it is bald.
- **Hawk:** a tall, narrow mohawk of dark slate-grey spikes up the middle of the head (x≈25–39), about 5 jagged spikes, the tallest reaching y=1. The sides of the head are bald.
- **MAYC Brim:** a red-orange cap with a faded rose-pink oval logo patch on the front and a darker red brim. The cap is **on fire**: flames rise from the top centre and flicker out from both sides at the brim, in orange and yellow. (MAYC = Mutant Ape Yacht Club; this is a nod to their flaming cap.)
- **Sea Captain:** a white peaked captain's cap. A white crown with grey shading, a gold anchor badge in the centre front, a thin gold cord above the visor, and a glossy black-grey visor pointing forward.
- **Slick:** brown hair combed straight back, drawn with many fine vertical comb lines (dark brown lines on mid brown, lighter strands catching the light). It covers the crown and runs down beside the face as short sideburns to the ears (y≈28).
- **Soldier:** an olive-green army helmet: a smooth dome with a lighter highlight on the viewer's left and a brim rim at the front. A thin **brown chin strap** runs down both sides of the face and under the chin (y≈37).
- **Spiky:** bright orange spiky hair, like flames: about five tall spikes leaning slightly, dark orange shading between them, pale orange tips.
- **Straw Hat:** a wide-brimmed straw hat (a nod to the pirate straw hat). A rounded crown, a red band around its base, and a wide, flat brim from x≈8 to 56 that covers the horn roots and shades the forehead.
- **Tiara:** a silver-mint metal tiara across the forehead (y≈11–23). A tall central pointed peak holding a **red gem**, with smaller points down each side. Pale mint highlights, grey-teal shadows.

---

## 5. Back (11 values)

Things behind the body: wings, cape or a weapon. The body always covers the middle, so only the parts outside the silhouette are drawn.

| Back | Count | Box | Colours |
|---|---|---|---|
| None | 1,112 (50.0%) | n/a | n/a |
| Mechanical Wings | 155 (7.0%) | 2,28 → 61,50 | plates `#9196a2` / `#868890` / `#4d4e55`, highlight `#b4bbc3`, frame `#995d43` / `#8e766e` |
| Bone Wings | 147 (6.6%) | 2,1 → 63,47 | bone `#f0f5fa` / `#f5f7f8`, membrane `#b1b2b3` / `#adadae` / `#c3c4c6`, shade `#6e6d72` |
| Angel Wings | 135 (6.1%) | 4,27 → 59,52 | `#e9f1f4`, `#dee7ef`, `#cccfd4`, `#bdc3d5`, `#b2b6c8`, `#8c92a6` |
| Sword | 134 (6.0%) | 7,25 → 20,41 | grip `#242e12`, metal `#4e4e4f` / `#666768`, shine `#97a99a` |
| Trident | 133 (6.0%) | 2,2 → 59,59 | head `#a71f1e` / `#d33630`, highlight `#db4540`, shaft `#222034` / `#353346` |
| Samurai | 125 (5.6%) | 9,27 → 54,39 | scabbard `#3b243d` / `#5c3861`, fittings `#80662b` / `#5c4410`, `#252b30` |
| Imp Wings | 124 (5.6%) | 4,29 → 59,43 | `#313130`, `#474847`, `#575957`, `#232423` |
| Scythe | 116 (5.2%) | 3,24 → 50,59 | blade `#2c3639` / `#41524f` / `#434847`, edge `#798488` |
| Cape | 23 (1.0%) | 6,39 → 57,62 | `#a81830`, `#ae1e2f`, lining / shade `#640720` / `#6d0721` |
| Golden Wings | 18 (0.8%) | 4,29 → 59,43 | `#e0b95c`, `#c99d32`, `#9d7d33`, `#7d611d`, highlight `#f6f398` |

### Looks, value by value

- **None:** nothing behind the Imp.
- **Imp Wings:** small dark-charcoal **bat wings**, one behind each shoulder, sticking out sideways (y≈28–43). Each wing has a top spar and a lower edge with three scalloped membrane points. Lighter grey picks out the spar and finger bones.
- **Golden Wings:** the **same shape** as Imp Wings, in shiny gold with pale-yellow highlights and bronze shadows.
- **Angel Wings:** small white **feathered wings** from the shoulders, about the same size as Imp Wings but rounder and drooping lower (to y≈52). Layered feathers point down and out, shaded with cool blue-grey.
- **Bone Wings:** **very large** skeletal bat wings, the biggest back trait. Bony spars (near white) arch up from the shoulders **above the horns**, ending in curled claw hooks at the top of the picture (y≈1). Grey membrane hangs between long finger bones down to y≈47, filling nearly the whole width (x≈2–63).
- **Mechanical Wings:** robotic wings: a fan of flat grey steel panels on a copper / rust-brown frame of struts, with rivets and a small red light at the joint. Medium size (out to x≈2 and 61, down to y≈50), angled down from the shoulders like folded panels.
- **Cape:** a deep crimson cape. A raised collar stands behind the shoulders, and the cape falls behind the body to the feet (y≈62), flaring out on both sides past the arms. A darker wine-red lining shows on the inner folds.
- **Sword:** one sword on the back. Only the **hilt** shows, over the viewer's-left shoulder: a round dark pommel, a dark olive wrapped grip with a lighter metal shine, and a short crossguard at about shoulder height (x≈7–20, y≈25–41). The blade is hidden behind the body.
- **Samurai:** two sheathed **katanas crossed in an X** behind the back. The ends of the dark plum scabbards / hilts show above and outside both shoulders (y≈27–39), with brass / gold fittings at the tips.
- **Scythe:** a reaper's scythe. A dark gunmetal **curved blade** at the upper left (x≈3–20, y≈24–45), its edge catching a grey light, curving down toward the body. The wooden shaft runs diagonally behind the body, and its far end shows near the lower right of the body (x≈45–50, y≈55–59).
- **Trident:** a **red trident** held diagonally. Its three barbed, arrow-like prongs are in the top-left corner (x≈2–15, y≈2–20), behind the viewer's-left horn. A dark navy shaft runs behind the body and ends in a dark butt cap at the lower right (x≈55–59, y≈55–59).

---

## 6. Clothing (20 values)

Outfits on the torso, and for some, the arms and legs. The arms and legs are body colour unless the outfit says otherwise.

| Clothing | Count | Box | Colours |
|---|---|---|---|
| None | 128 (5.8%) | n/a | n/a |
| Gi | 126 (5.7%) | 15,37 → 48,59 | orange `#f07219` / `#c1491b` / `#7f1b05`, navy `#1c3a6c` / `#12274c` |
| Puffer | 125 (5.6%) | 14,37 → 49,54 | `#455085`, `#313866`, `#21284e`, `#171b34` |
| Blue Skull Tee | 122 (5.5%) | 18,38 → 45,52 | `#639bff`, `#13449d`, skull `#ffffff` / `#9badb7` |
| Waterproof Coat | 120 (5.4%) | 14,34 → 49,58 | `#ffff00`, `#ffff79`, `#98980b`, `#626200` |
| Elegant | 115 (5.2%) | 15,38 → 48,59 | suit `#696a6a` / `#484541` / `#847e87`, shirt `#ffffff` / `#f6f6f6`, tie `#fbf9dd` / `#edecdc` / `#dbdabc` |
| Trench | 114 (5.1%) | 14,33 → 49,60 | `#303b3c`, `#2c3638`, `#1f2729`, `#19181d` |
| Worker Vest | 111 (5.0%) | 15,36 → 48,59 | leather `#5b483d` / `#4c413a` / `#2d2321`, belt grey, buckle bronze |
| Bikini | 110 (5.0%) | 22,39 → 41,57 | `#ff5bcb`, `#bc1b89`, flower `#639bff` / `#bbd0f6` |
| Robinhood Hoodie | 109 (4.9%) | 15,35 → 48,53 | `#90ff2a`, `#66b71b`, `#529416`, logo `#222034` |
| Vest | 109 (4.9%) | 22,38 → 41,52 | `#fcfdfd`, `#d1dbe1`, `#a5afb2` |
| Skelly Tee | 108 (4.9%) | 18,38 → 45,55 | `#2d3a3f`, `#1d2528`, bones `#ffffff` / `#dbd6d6` |
| Robinhood Tee | 108 (4.9%) | 16,37 → 47,53 | `#90ff2a`, `#8bfb25`, `#66b71b`, logo `#242424` |
| Armour | 108 (4.9%) | 21,38 → 42,58 | `#cbdbfc`, `#a7b3ce`, `#7d8baa`, `#3d4962`, `#282e3a` |
| Ragged Vest | 105 (4.7%) | 21,38 → 42,59 | `#8f563b`, `#663931`, `#3f1b15` |
| Polka Dress | 103 (4.6%) | 18,38 → 45,58 | `#9e1d18`, `#650f0d`, dots `#ffffff` |
| White Tee | 102 (4.6%) | 16,37 → 47,53 | `#fdfdfd`, `#bdc4c8`, `#b4bdc3` |
| Demon Hoodie | 101 (4.5%) | 15,35 → 48,53 | `#827986`, `#575159`, `#403a43`, logo `#ed3838` / `#b71a1a` / `#940e0e` |
| Pyjamas | 99 (4.5%) | 14,37 → 49,60 | `#7b98d7`, `#4c69a7`, moons `#b4dbff`, stars pale yellow |
| Battle Armour | 99 (4.5%) | 14,34 → 49,57 | plate `#567c94` / `#506f96` / `#273f50`, trim `#ddc062` / `#c89e1f`, pads `#d1d1cd` / `#fdfcf8` |

### Looks, value by value

- **None:** the bare body: pecs, navel and belly lines show.
- **Armour:** a silver-blue **muscle cuirass** (sculpted breastplate) with moulded pecs and a six-pack of ab plates, pale blue highlights and slate shadows. Below it, a **checkered skirt / shorts** in a small blue-and-white check (like chainmail) to y≈58. Arms and legs bare.
- **Battle Armour:** sci-fi warrior armour (Saiyan style). A segmented blue-grey chest plate with **gold trim**, and big white **flared shoulder pads** sticking out sideways like wings, edged in gold. White pointed **hip flaps** stick out at the waist on both sides. Blue-grey tasset plate hangs at the front to y≈57.
- **Bikini:** a hot-pink two-piece: a bandeau / triangle top and a bikini bottom, each with a small **pale-blue flower** in the centre. The belly and navel show between them.
- **Blue Skull Tee:** a mid-blue short-sleeved t-shirt, darker blue on the shaded side, with a small white **skull** in the centre of the chest.
- **Demon Hoodie:** a charcoal-grey hoodie with long sleeves to the wrists. The hood is down, bunched behind the neck. A **red demon face** logo (a little horned head) is on the chest, and a kangaroo pocket line crosses the belly.
- **Elegant:** a dark-grey **suit**: a jacket with lapels and buttons, a white shirt, a cream cravat / tie at the collar, long sleeves, and matching grey trousers down to the feet.
- **Gi:** an orange **martial-arts gi** (the Dragon Ball look). An orange crossover top with a black round emblem on the chest (viewer's right), a navy undershirt showing at the V neck, a navy belt sash, navy wristbands, and baggy orange trousers.
- **Polka Dress:** a dark-red sleeveless **A-line dress** with thin straps and a regular grid of white **polka dots**. It flares out to a hem at y≈58, just above the feet.
- **Puffer:** a navy **quilted puffer jacket** with horizontal padded bands, a high collar and long sleeves, ending at the hips (y≈54).
- **Pyjamas:** a periwinkle-blue short-sleeved pyjama top and shorts, printed with pale-blue **crescent moons** and small yellow **stars**.
- **Ragged Vest:** a brown sack-cloth **tunic**: sleeveless, a V-neck, and a torn **zigzag hem** at mid-thigh (y≈59). Darker brown patches for wear.
- **Robinhood Hoodie:** a lime-green hoodie with the hood down behind the neck, long sleeves, a pocket and the dark **Robinhood feather** logo on the chest (a dark, slanted leaf / feather shape).
- **Robinhood Tee:** a lime-green short-sleeved t-shirt with the same dark **feather** logo.
- **Skelly Tee:** a dark slate t-shirt printed with a white **skeleton ribcage**: a spine down the middle and ribs on both sides.
- **Trench:** a long black **trench coat**, worn open. Wide lapels flare out at the shoulders, long sleeves, and the coat falls almost to the feet (y≈60) on both sides. The bare torso shows down the middle, crossed by a **grey belt** with a buckle at the waist.
- **Vest:** a plain white **tank top / singlet** with thin straps, lit white on the viewer's left half and pale grey on the right, ending at the hips.
- **Waterproof Coat:** a bright yellow **raincoat**: a big collar ruff around the neck (like a folded-down hood), a seam down the front, long sleeves and a hem at y≈58. Olive-yellow seams draw a diamond-quilt pattern.
- **White Tee:** a plain white short-sleeved **t-shirt**, grey on the shaded side.
- **Worker Vest:** a dark-brown **leather work tunic / apron**, mottled like worn leather, with short shoulder caps. A grey **belt** with a square **bronze buckle** crosses the waist, and the bottom ends in a V point between the legs (y≈59).

---

## 7. Eyes (19 values)

Two kinds:
- **Eye colours** (Ghostly, Red / Gold / Purple Pupils): the eyes themselves.
- **Eyewear and effects:** on top of the eyes. Where one eye stays visible (Eye Patch, Monacle, Tracker), that eye has **red pupils**.

| Eyes | Count | Box | Colours |
|---|---|---|---|
| Monacle | 197 (8.9%) | 22,25 → 45,34 | rim `#947239` / `#70572d` / `#483619`, lens `#9794ac` |
| Red Pupils | 197 (8.9%) | 22,26 → 41,33 | pupil `#d02b06` / `#d83a39`, glow `#fbdfcd` / `#f3c5a5` |
| Eye Patch | 190 (8.6%) | 20,21 → 44,33 | `#201d39`, `#1d1a30`, `#191728` |
| Shades | 182 (8.2%) | 17,23 → 46,33 | lens `#4b3124` / `#33190c` / `#441e12`, frame `#423a3a` / black |
| 3D Glasses | 173 (7.8%) | 17,23 → 46,33 | frame `#c6c6c5` / `#b0acab` / `#868588`, red `#aa3a35`, blue `#2138a6` / `#2a49b6` |
| Ghostly | 172 (7.7%) | 22,26 → 41,33 | `#ffffff`, `#edf9ff`, `#cce2ed`, `#aec3cf` |
| Gold Pupils | 169 (7.6%) | 22,26 → 41,33 | pupil `#ffbe22` / `#a17713`, glow `#ffeec7` / `#ffe6a9` |
| Glasses | 165 (7.4%) | 18,26 → 45,33 | frame black, lens `#c0c0c0` / `#faefe6` |
| Bug-Eye | 160 (7.2%) | 18,26 → 45,33 | lens `#798f64` / `#798b56`, shade `#384e23` / `#616d27` |
| Purple Pupils | 147 (6.6%) | 22,26 → 41,33 | pupil `#76428a` / `#3f1251`, glow `#e4adfb` / `#ebcef6` |
| Tracker Blue | 79 (3.6%) | 15,22 → 41,33 | housing `#272727` / `#353232` / `#696868`, lens `#285f6a` / `#467396` |
| Hearts | 74 (3.3%) | 18,26 → 45,34 | `#d95763`, `#ed7580`, `#ac3232`, `#862424`, shine `#ffb7c5` |
| Stars | 71 (3.2%) | 17,24 → 46,34 | `#fbe10a`, `#b48f06`, highlight `#fef39f` |
| Tracker Purple | 61 (2.7%) | 15,22 → 41,33 | housing as Tracker Blue, lens `#7a2a99` / `#8b30ae` |
| Robo | 58 (2.6%) | 17,24 → 46,33 | visor `#515152` / `#79797c` / `#4c4c4c`, glow `#8effff` / `#3fd4d0` |
| Goggles | 57 (2.6%) | 17,18 → 46,33 | rim `#75858f` / `#5d6569`, lens `#ed7947` / `#d34627` / `#ac110e` / `#770423` |
| Lazer | 26 (1.2%) | 9,26 → 54,63 | `#ff0000`, `#ff8080`, `#f29d9d`, core `#ffffff` |
| Neon Beam | 26 (1.2%) | 9,26 → 54,63 | `#7be900`, `#86ff00`, `#a1fb3e`, core `#ffffff` |
| Mask | 18 (0.8%) | 17,22 → 46,35 | `#222f34`, `#304248`, eyes `#ffffff` |

### Looks, value by value

- **Ghostly:** angry eyes with **no pupils**: plain white, shaded with icy pale blue toward the bottom. Blank and spooky.
- **Red Pupils:** white eyes with a **red** iris / pupil at the inner side, a peach glow ring around it, and a white glint.
- **Gold Pupils:** the same with an **amber-gold** iris and a cream glow.
- **Purple Pupils:** the same with a **violet** iris and a lilac glow.
- **3D Glasses:** classic cardboard 3D glasses: a thick, light-grey frame across the whole eye band, a **red** lens over the viewer's-left eye and a **blue** lens over the right, with a nose notch between them. Eyes not visible.
- **Bug-Eye:** rounded, slightly cat-eye-shaped **sunglasses** with thin black frames and **olive-green** lenses. The eyes are not visible.
- **Eye Patch:** a dark navy pirate **eye patch** over the viewer's-right eye, held by a thin black strap running diagonally up across the forehead toward the viewer's-left. The other eye has a red pupil.
- **Glasses:** thin black rectangular **reading glasses**. The lenses are nearly clear with a faint warm sheen, so the eyes show through faintly.
- **Goggles:** big **ski / snow goggles** covering the eye band and forehead (y≈18–33): one wide lens in a mirrored red-to-orange gradient with diagonal shine streaks, set in a thick grey-blue rubber rim with the strap going round to the ears.
- **Hearts:** **heart-shaped sunglasses** with pink-red, see-through lenses (the face shows through faintly), a light-pink shine and a dark red rim.
- **Lazer:** both eyes glow red, and two **red laser beams** shoot from them diagonally down and outward to the bottom corners (reaching x≈9 and x≈54 at y=63). Each beam has a white-hot core and fading pink-red edges.
- **Neon Beam:** the same as Lazer in **lime green**.
- **Mask:** a black-teal **domino mask** (like a superhero or bandit) across the eyes, with pointed side flaps. The eyes inside are pure white, angry slits with no pupils.
- **Monacle:** a round **monocle** with a thick brass rim over the viewer's-right eye. A pale lilac-grey lens shows the eye faintly, and a little brass tab (where the chain clips on) hangs at the lower right. The other eye has a red pupil.
- **Robo:** a **cyber visor**: a solid dark-grey metal bar across both eyes with a glowing **cyan slit** across the middle (Cyclops style). Eyes not visible.
- **Shades:** wide black **sunglasses** with dark-brown tinted lenses. The eyes are only just visible through them.
- **Stars:** **star-shaped glasses**: two bright yellow five-pointed stars as lenses with a gold bridge, darker gold shading and a pale highlight.
- **Tracker Blue:** a **scouter** (the Dragon Ball one-eye display): a dark-grey device clipped to the viewer's-left ear, with a small indicator light, and a see-through **blue** lens over the viewer's-left eye. The other eye has a red pupil.
- **Tracker Purple:** the same scouter with a **purple** lens.

---

## 8. Building the traits in Blockbench (all **Proposed**)

These are suggestions for the later prompt, not decisions. They follow MODELS-BLOCKBENCH (D-044, D-047).

**Start from the base Imp.** `godot-game/assets/models/source/blockbench/creatures/implingz_voxel_character_model.bbmodel` is the HD Imp already built from the pixel-art portrait. Each trait should be a separate model (or a separate group) that **attaches to a named bone** on that Imp, so traits can be swapped in Godot.

| Trait type | Attach to | Notes |
|---|---|---|
| Body | The base Imp's texture | A texture swap, not new geometry. Gold and Diamond also swap the horn texture. |
| Head | Head bone | Must clear both horns. Hats sit **between** the horns (Cap, Fez, Crown, Sea Captain, Soldier, MAYC Brim). Afro and Straw Hat are wider than the horns: the horns pass **through** the Afro, and the Straw Hat brim sits over the horn roots. Blonde hair also needs pieces on the back and sides of the body, down to the hips, that follow the body. |
| Back | Body bone, behind the shoulders | Wings: one bone per wing, so they can flap. Weapons are props on the back, angled as in the art (Sword hilt over the Imp's right shoulder, Scythe and Trident diagonal). Cape: its own bone, hanging from the shoulders. |
| Clothing | Body, arms and legs | A shell slightly larger than the body. Sleeves move with the arm bones, trousers and skirts with the leg bones. Long coats (Trench, Waterproof Coat, Elegant trousers, Polka Dress) need to bend at the hips. |
| Eyes | Head bone, face plane | Pupil colours are a face texture swap. Eyewear is thin geometry on the face. Lazer and Neon Beam are glowing beams (an emissive material or a particle effect in Godot), not solid boxes. |

**Rules to keep the traits faithful**
- Take every colour from this doc's tables, the way MODELS-BLOCKBENCH says a model takes its colours from its icon.
- Keep the 2D lighting idea: the Imp's right side (the viewer's left) is lit, the other side is shaded.
- Keep the black outline feel with a dark rim on edges, as the existing Imp model does.
- Keep the angry face: angled lids, inward-pointing glare.
- Test every trait against the worst cases: Bone Wings with Cape-length clothes, Afro or Straw Hat with each eyewear, Blonde with each Back trait, Battle Armour pads with each wing.

**Open questions**
1. Do Lazer and Neon Beam fire all the time on the 3D Imp, or only in an action or emote?
2. Does Tier mean anything in the game? It changes nothing in the art.
3. Is one shared base Imp right for all 10 bodies, or do Gold and Diamond get extra shine (a metallic material) in Godot?
4. D-016 says "the Implings are already done, and no art work is done on them" and MODELS-BLOCKBENCH says Implings are left out. The HD Imp model and this trait work go beyond that. Should D-016 be updated?
