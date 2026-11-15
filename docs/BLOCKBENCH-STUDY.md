# IMPLINGZ: Blockbench study (how the pros do it)

| Status | Last pass | Depends on |
|---|---|---|
| Draft | User addition, 2026-10-21 | MODELS-BLOCKBENCH, ART-DIRECTION, GODOT |

> Claude: read `docs/CLAUDE.md` and [MODELS-BLOCKBENCH.md](MODELS-BLOCKBENCH.md) before working from this file. This doc is the research behind the Blockbench rules. The rules themselves live in MODELS-BLOCKBENCH. If this doc and that one disagree, raise it with the user; don't silently change either.
>
> Labels: **Decided** (in `DECISIONS.md`) · **Proposed** (Claude's suggestion) · **Open question** · **Seen** (what Claude saw in a reference, as a fact about that listing)

**Purpose of this doc:** study the 26 Blockbench listings the user picked as the quality bar (section 9). It covers how they look, how they are built, and how we can make and optimise models at that level for a Godot browser game.

**How it was made.** On 2026-10-21 Claude opened all 26 listings on mcmodels.net, read each description and looked at the preview images (the first image of each, more for packs with several). Nothing was bought or downloaded. The listing text is thin: most don't give cube counts, and none gives a texture sheet size. Anything about *how* a model is built is Claude's reading of the previews, so it is labelled **Proposed** or **Seen**, never Decided.

**Words used here** (as well as the ones in MODELS-BLOCKBENCH):
- **Resolution "16" or "32":** what the listings call texel density. 16 means 16 texture pixels per Minecraft block, which is **1 pixel per Blockbench unit**. 32 means 2 pixels per unit.
- **3D sprite (extruded sprite):** a flat pixel-art drawing turned into a thin 3D slab, one box per pixel or per row of pixels. This is how Minecraft draws held items.
- **Emissive:** pixels that glow by themselves and stay bright in the dark.
- **Texture animation:** the picture on the model changes over time (a flickering flame, a pulsing glow). The model doesn't move.
- **Rig:** the bones of a creature and how they are linked, so it can be animated.
- **ModelEngine / MythicMobs:** Minecraft server plugins that play Blockbench animations. Every creature reference is sold for them. We don't use them. We take the models' look and animation ideas, not their setup.

---

## 1. What all 26 have in common (Seen)

1. **Almost everything is at resolution 16** (1 pixel per unit). All 11 tool and weapon packs are 16, and so are 12 of the 15 creature packs. Only three giant bosses use 32: Cerberus, Matatabi and the Celestial Dragon.
2. **One pixel size inside each model.** Even the 32 bosses keep one density across the whole model. Nothing mixes sizes.
3. **Few colours per material, strong value steps.** Each material has a short ramp of 3 to 5 shades with clear jumps between them, not soft gradients.
4. **One glowing accent per model.** Ice-blue on Boreas Whisper, cyan on Celestine Radiance, pink-purple on Netherforge and Frayed, red on Bloody and Sanguinesti, magma on the Hedgehog, eyes on the demons. Everything else is calmer, so the glow is what you see first.
5. **Silhouettes are exaggerated.** Tool heads are huge next to their handles. Demons have oversized horns and claws. The Cogbound Foreman is a drill on legs.
6. **One base, many skins.** Embered tool sets reuse the same six item types in every theme. Cubees Dragons is one dragon shape in eight elements. The mimics come in three or more chest skins, and the Dodo in three colours. This is exactly the tier plan in MODELS-BLOCKBENCH section 6.
7. **Effects sell the quality.** Floating pixels around tools, sparks, magma drips, glowing eyes, breath and beam effects. Most packs list VFX as a feature.
8. **The previews are lit and post-processed.** Almost every in-world preview uses Minecraft shader packs (soft shadows, bloom, warm sky) or a posed render with bloom. The models look as good as they do partly because of that lighting. In Godot we get the same lift only if we light the scene for it (section 7.6).

---

## 2. Tools and weapons: the Embered and Ashen packs (Seen)

All 11 are by **SirValeron** (sold by Cubosynth), $9.99 each, resolution 16.

| Pack | What's in it | Look |
|---|---|---|
| Ashen Weapons Vol. 1 | 10 weapons: swords, axes, daggers. Not animated. | Calm steel, gold and teal-grey. The cleanest pixel work in the set. |
| Embered Weapons Vol. 1, 2, 3 | 5 animated weapons each: swords, scythes, curved blades | One theme per weapon (fire, ice, void, blood). Glowing edges, floating pixels. |
| Embered Tool Sets: Boreas Whisper, Netherforge, Celestine Radiance, Moon, Frayed, Bloody, Sanguinesti | 6 animated items per set: **fishing rod, bow, pickaxe, hoe, axe, shovel** (the sword is sold only in the weapon packs) | One theme per set. Same six item types every time. |

### 2.1 How they are built (Proposed, from the previews)

- **The head is a 3D sprite. The handle is a box.** The pickaxe, axe and hoe heads read as flat pixel drawings pushed out to a slab about 1 pixel thick. The handle is a long box about 2 × 2 pixels with wrapping bands (Celestine's gold-and-brown wrap, Netherforge's dark iron rings).
- **The head breaks the handle's line.** Every head hooks, flares or spikes sideways: Bloody's curved pick, Celestine's winged axe, Boreas's icicle spikes. A plain T-shape pickaxe reads as "default".
- **Rim glow.** The accent colour runs along the outer edge of the head as a 1-pixel bright line, with the darker body colour inside. This is what makes them pop on any background.
- **Detached pixels.** Single pixels float off the head (embers, snowflakes, sparkles, blood drops). In Minecraft these are part of the texture or separate tiny boxes. They make a static item look magical.
- **"Animated" means texture animation.** A held Minecraft item can't move its geometry, so the animation is frames of the texture: the glow pulses and the floating pixels drift. **Proposed for us:** Godot can do the same with a shader that scrolls or flips the emission texture. That is cheaper than animating bones on a held tool.

### 2.2 Colour recipe (Seen)

Every themed set uses the same three-part recipe:

| Part | Role | Example (Celestine Radiance) |
|---|---|---|
| Base material | Mid-dark, low saturation, carries the shape | Antique gold and bronze |
| Accent | Bright, saturated, glows, sits on edges and tips | Cyan / turquoise |
| Handle | Warm wood or dark metal, banded | Brown wood with gold bands |

Moon and Ashen show the calm version: steel ramps with a single cool highlight and almost no glow. **Proposed:** low tiers follow Ashen (calm, little glow) and high tiers follow Embered (strong glow, floating pixels). Then the tier reads from across the room, not just from its colour.

### 2.3 What we take for IMPLINGZ (Proposed)

- **Pickaxes, sickles and bows fit this model of work exactly.** An Embered set is a "tier": one theme over fixed item shapes. Our pickaxe tiers (D-006, D-020), sickle tiers (D-024) and bow tiers (D-030) can follow the same plan: one model and UV layout per item, one texture per tier (MODELS-BLOCKBENCH section 6).
- **The hoe is our sickle reference.** The Embered hoes are the closest thing in the references to a sickle.
- **Glow grows with the tier.** Tin to Iron: no glow, Ashen-calm. Gold to Dreadstone: rim highlight, no particles. Void Stone and Stellarite: rim glow, floating pixels, pulse animation. The colours still come from each tier's icon (ART-DIRECTION section 2).
- **Keep the head shape fixed per item if possible.** Embered sets change head shapes per theme, which costs a new model each time. MODELS-BLOCKBENCH section 6 says one model per tool. The pros' extra shapes are a reason to allow a **second head shape for the top tiers only**, not one per tier.

---

## 3. Creatures (Seen)

| Listing | By | Res | What it shows | Most useful for us |
|---|---|---|---|---|
| Demons Vol.2 | Necron | 16 | 3 demons and a Warlock Imp boss, 36 animations in the pack, VFX | Horns and spikes from rotated boxes. Glowing eyes on dark faces. |
| Archdemon raid boss | Necron | 16 | Boss and 2 imp mobs, 2 phases, 23 animations for the boss | How to layer armour plates and spikes on a big body without losing the silhouette. |
| Cubees Dragons | CUBEES | 16 | 8 small dragons (Air to Nature) on one shape | **One rig, many elements.** Each element adds its own pieces (ice crystals, leaves, flame wisps) and changes the colours. |
| Living Treasures mimics | Troyi's Crafts | 16 | One mimic, 3 chest skins, hidden and monster states | A disguise state and a reveal. Long thin limbs from a chunky body. |
| RPG Dungeon Chest Mimics | MC Garage | 16 | 4 mimic types, 2 chests, coin and key projectiles | Clean, readable wood and metal. A big green eye as the one accent. |
| Monstrum Ice Mobs | QueueModels | 16 | 6 ice monsters and a mount, VFX | Shaggy white fur with blue icy horns. Fringe pixels hanging over edges. |
| Antlerbit pet | DepartmentQDE | 16 | A hopping antlered bunny that becomes a mount, plus a 2D icon | **Closest to our Hare and Goldhorn Stag.** Fur shading in clear clusters, striped limbs, a big readable face. |
| Rune's Dodo mount | RuneFist Studios | 16 | Idle, walk, run, walk-back; 3 colours; body lean while turning | Animation polish on a simple shape: lean, gallop tiers, step height. |
| Nog's Seagull | Nog's Menagerie | 16 | 9 bones, 3 animations, plus a hat, plushie and icon | **How little you need.** A big beak, a few boxes, clean flat shading, and it's charming. |
| SoloCraft Cerberus | opERR0R | 32 | Three-headed fire dog boss with fire-breath VFX | Dense detail for a colossal boss. Emissive cracks of lava in dark rock-like skin. |
| Matatabi two-tailed beast | Anime Store | 32 | Giant blue spirit-fire cat, 12 animations, enraged state | Painted swirl markings across the body. |
| Celestial Dragon | EliteCreatures | 32 | Huge flying dragon, 5 abilities | Scale rows from stepped boxes. Strong warm emissive belly. |
| Cogbound Machine Uprising | ModelBlox | 16 | 4 machine enemies in abandoned mines, plus an arena | **Mining-themed enemies.** Drills, saws, brass and teal oxidised metal. |
| Cogbound Icarosphinx | ModelBlox | 16 | Mechanical winged sphinx boss with an arena | Patterned brass wings as big flat shapes. |
| Magma Hedgehog | Bojarsky Legacy | 16 | Lava boss with glowing quills | Emissive tips on dark quills, dripping lava pixels. |

### 3.1 Techniques seen across the creatures

- **Fringe pixels.** Fur, ice and moss hang over box edges as a row of uneven pixels, painted on a slightly larger outer box or on thin planes. It breaks the box outline without adding much geometry (Antlerbit, Monstrum, Cubees' Nature dragon).
- **Horns, spikes and quills are stacks of small rotated boxes**, each a few pixels thick and turned a little more than the last, so they curve. Demons, Archdemon and Magma Hedgehog do this everywhere.
- **Faces are mostly painted, not modelled.** Eyes, brows and mouths are pixels on a flat face. A jaw or beak is the one extra box. The seagull's whole character is one beak box and two dark eye pixels.
- **Eyes are the accent.** Bright eyes on dark faces (demons, Cerberus) or big dark eyes on pale faces (Antlerbit, seagull). Hostile creatures glow; friendly ones don't.
- **Markings follow the form.** Stripes wrap round limbs (Antlerbit), swirls flow along the body (Matatabi), scales step down the neck (Celestial Dragon). Markings drawn across the form, ignoring it, look pasted on.
- **Big creatures stay chunky.** Even the 32-resolution bosses are built from large boxes. The extra resolution goes into the painting, not into more, smaller boxes.
- **Bonus items from the same model.** The seagull ships with a hat, a plushie and a GUI head. The Antlerbit ships with a 2D icon. Every creature can give a trophy or icon cheaply (our trophies, D-031 and D-033).

### 3.2 Animation scale (Seen)

What the pros ship, as a benchmark:

| Creature | Animations |
|---|---|
| Nog's Seagull (ambient animal) | 3, on 9 bones |
| Rune's Dodo (mount) | 4: idle, walk, run, walk-back |
| Matatabi (raid boss) | 12 |
| Archdemon (raid boss, 2 phases) | 23 |
| Demons Vol.2 (4 mobs) | 36 in total, about 9 each |

**Proposed for us:** the 4-animation minimum in MODELS-BLOCKBENCH section 4.5 (`idle`, `walk`, `attack`, `hit`) is in line with the pros for an ordinary creature. A boss would need 10 or more. Bosses are not decided in our design.

---

## 4. How the pros build a model, step by step (Proposed)

This is the order that produces work like the references. It adds detail to MODELS-BLOCKBENCH sections 3 and 4. It does not replace them.

1. **Brief and references.** Write down in one line what it is, its tier, and its one accent colour. Open the item's 48×48 icon if it has one. Collect 3 to 5 reference images: real animals for creatures, the reference listings for finish.
2. **Silhouette sketch.** A quick 2D pixel sketch, side and front, at the real model size (for example 16 pixels tall for a hare). This sets proportions before any box exists.
3. **Blockout in grey.** Big boxes only, untextured, against the scale dummy (the Imp's height). Check the silhouette from the game camera's angle and distance, not up close.
4. **Bones and pivots.** Group parts into bones and set pivots at the joints *before* detailing. Moving a pivot later breaks animations.
5. **Detail boxes.** Add the boxes that change the silhouette: horns, ears, fringe, the jaw. Delete any box nobody will see.
6. **UV layout.** Box UV for simple creatures, per-face UV for tools and detailed parts (MODELS-BLOCKBENCH 4.4). Pack tightly and keep every face at the same density.
7. **Texture in passes:**
   1. Flat base colours per material.
   2. Light: top faces lighter, bottom faces darker, one light direction.
   3. Form shading: darker where parts meet, under overhangs, inside the mouth.
   4. Edge highlights on top edges and corners.
   5. Details: markings, fringe, cracks, rivets.
   6. Accent and emissive pixels last, on a separate emission texture (section 5.4).
8. **Check in the engine early.** Put the textured model in the Godot scene, under the real light, next to the Imp. Fix it there, not only in Blockbench's viewport.
9. **Animate.** Idle first: it's what players see most. Then walk, attack, hit.
10. **Variants last.** Once one skin is right, make the tier and element skins on the same UV layout.

---

## 5. Texturing like the references (Proposed)

### 5.1 Palettes
- **3 to 5 shades per material**, chosen as a ramp before painting. Save them as a palette file. Aseprite and Blockbench both take `.gpl` palettes.
- **Hue-shift the ramp.** Shadows move toward blue or purple, highlights toward yellow (MODELS-BLOCKBENCH 4.3). Every Embered set does this. Netherforge's darks are blue-violet, not black.
- **Big value steps.** Neighbouring shades should be clearly different at game distance. If two shades blur together from the camera, drop one.
- **One saturated accent.** Everything else stays 20 to 40% less saturated (ART-DIRECTION section 5).

### 5.2 Metal (tool heads)
- A ramp of 4 shades plus a near-white highlight pixel at the brightest corner.
- Light bands running **along** the blade or head, not across it.
- Dark outline pixels only where the head meets the handle or overlaps itself. No dark outline all round (Ashen's blades have none on the outer edge).

### 5.3 Fur, scales and skin
- Fur: clusters of 2 to 4 pixels pointing the way the fur lies, plus fringe pixels on the edges (section 3.1).
- Scales: rows of stepped shapes, lighter at the top of each scale.
- Skin: very few pixels of noise. Let the form shading do the work.

### 5.4 Glow (emissive)
- Paint glowing pixels into **their own emission texture** with the same UV layout, black everywhere else. In Godot, put that texture in the material's Emission slot. Only those pixels glow, and the glow can be animated or tuned per tier without repainting.
- Glowing pixels should be surrounded by a dark ring of 1 pixel, so the glow has contrast (Cerberus's lava cracks, Magma Hedgehog's quills).
- **Open question:** does Blockbench's glTF or FBX export carry an emission texture into Godot? Claude found no documentation saying so. Assume it doesn't: set the emission texture by hand in Godot, or in a material that all models share.

### 5.5 Don'ts the references avoid
- No noise filters or random speckle.
- No soft airbrush gradients.
- No black outlines around the whole model.
- No pure black or pure white, except the single brightest highlight pixel.

---

## 6. Animation like the references (Proposed)

- **Idle is never still.** Breathing (body scale 1 to 2%), a head tilt, an ear flick, a tail sway. The seagull and the dodo do this with very few bones.
- **Lean into movement.** The dodo leans into turns. Body lean and head lag sell weight cheaply.
- **Anticipation, action, recovery.** Every attack has a wind-up (pull back), a fast strike, and a slower settle. The demons and the Archdemon attacks follow this.
- **Hit reactions are short.** A quick recoil and a flash. In Godot the flash can be the emission turned up for 0.1 seconds, with no Blockbench animation needed.
- **Tools:** a pulsing glow and drifting pixels (section 2.1), done as texture or emission animation in Godot. The swing comes from the Imp's arm animation, not the tool.
- **Loops:** the first and last keyframes match (MODELS-BLOCKBENCH 4.5). Test them looping for 30 seconds. A pop you missed in 2 seconds is obvious in 30.

---

## 7. Optimising for a Godot browser game (Proposed)

The references are made for Minecraft servers. We run in a browser (D-046), so every model must be cheap.

### 7.1 Geometry
- **Boxes are cheap; hidden faces are waste.** In Blockbench, a face can be turned off by removing its texture. Do that for faces that touch another box or are never seen (the underside of a body against a leg, the inside of a jaw when closed).
- **3D sprites get expensive fast.** A 16×16 tool head made one box per pixel is hundreds of faces. Build it from **one box per row or block of pixels**, or a single slab with a cut-out texture (transparent pixels). Test both in Godot. **Open question:** which one Godot draws faster for our tools.
- **Merge what doesn't move.** Boxes that never move apart go in one bone. Fewer bones means fewer transforms each frame.
- **Budgets:** keep to MODELS-BLOCKBENCH section 7. The references don't list counts, so the budgets stay ours.

### 7.2 Textures
- **One texture per model** (or per model and tier), power-of-two size, with an optional emission texture at the same size.
- **All tier textures for one tool in one atlas** is possible later, if draw calls become a problem. Not needed at first.
- **Nearest filter, no mipmaps, lossless** (GODOT.md section 7). At our resolution 32 (D-053) a whole creature texture is still small (128×128 or 256×256), so memory is not the concern. Draw calls are.

### 7.3 Materials and draw calls
- **One material per model**, shared across every instance. 30 hares on screen should be 30 copies of one mesh and one material, not 30 materials.
- **Tier skins:** swap the texture on a shared material per tier, or use a small per-instance setting. Don't duplicate materials per instance.
- **Many of the same creature** (a herd, a flock): Godot's MultiMesh can draw them in one call when they share a mesh. Animated creatures can't use it directly. Keep it for static items such as dropped ore.

### 7.4 Animation cost
- Bone count matters more than box count for animated creatures. The seagull's 9 bones is a good target for small animals, and 15 to 30 is fine for big ones.
- Creatures out of view or far away don't need to animate every frame. Godot can pause or slow animation by distance.

### 7.5 Export (D-044 says FBX)
- **Seen in Blockbench's own docs:** Blockbench's FBX export is **ASCII**. Blockbench recommends **glTF for Godot**, with "great support for hierarchy and animations" and pixel-perfect filtering.
- Godot 4.3 and later imports FBX through its own importer. **Open question:** does it import Blockbench's ASCII FBX with animations correctly? This is the test already planned in MODELS-BLOCKBENCH section 5. Run it on the first creature, and export glTF alongside it. Changing D-044 is the user's call.
- One Godot forum thread reports a Blockbench glTF animation that played wrongly in Godot, with no fix posted. That is one more reason to test the first animated model before making the rest.

### 7.6 Lighting the scene so models look like the previews
- The previews' soft shadows and bloom come from shader packs. In Godot the same lift comes from the WorldEnvironment: **glow (bloom) on**, tone mapping on, soft directional shadows, and a warm sun with a cool fill (ART-DIRECTION section 8).
- Glow should catch the emissive pixels and little else. Set the glow threshold so only the emissive pixels bloom.
- **Open question:** the browser renderer (Compatibility, per GODOT.md) supports less glow and shadow quality than the desktop renderer. Check the first model in a web export, not just in the editor.

---

## 8. How the references map onto IMPLINGZ (Proposed)

Style references only (D-018). We take ideas, never shapes or textures.

| Our model | Closest references | Take |
|---|---|---|
| Pickaxes, 10 tiers (D-006, D-020) | Embered tool sets, Ashen | Six-items-per-theme logic, rim glow growing with the tier |
| Sickles, 10 tiers (D-024) | Embered hoes | Curved blade with a strong hook silhouette |
| Bows, 16 tiers (D-030) | Embered bows | Limb tips as the accent, string as a thin plane |
| Hare, Fox | Antlerbit, Nog's Seagull | Clean fur clusters, big face, few bones |
| Boar, Wolf, Goldhorn Stag | Antlerbit, Rune's Dodo | Antlers from stacked boxes, body lean in movement |
| Shadowcat | Matatabi | Markings that follow the form, glowing eyes |
| Frostmane Yeti | Monstrum Ice Mobs | Shaggy fringe, icy horns as the accent |
| Cinder Salamander | Magma Hedgehog, Cerberus | Emissive lava cracks and tips on a dark body |
| Voidstalker | Demons Vol.2, Netherforge colours | Dark body, violet glow |
| Starwyrm, Tidecrest Serpent, Eclipse Dragon | Cubees Dragons, Celestial Dragon | Long bodies from stepped boxes, one rig with element skins |
| Stormhorn Ram, Mossmane Behemoth, Crystalback Basilisk | Archdemon, Monstrum, Cubees Nature dragon | Big chunky bodies, accent on the horns, moss or crystal growths |
| Sunfeather Griffin | Cogbound Icarosphinx | Wings as big patterned flat shapes |
| Mining enemies (not designed) | Cogbound Machine Uprising | Machine creatures that live in mines |

The 16 hunting creatures are Decided (D-032, D-033). The pairings above are not.

---

## 9. Reference library (Decided list, D-052)

The user chose these 26 listings on 2026-10-21 as the look and quality to aim for. They are style references only (D-018): we make our own models. The notes are in sections 2 and 3.

**Watch for:** Matatabi is based on a character from an existing anime. Take its finish, never the character. Several creature packs are dark "Dark Souls" themes; our world is a bright stylised cartoon (D-047), so take their technique, not their mood.

### Tools and weapons
| # | Listing | By |
|---|---|---|
| 1 | [Embered Weapons Vol. 1 ANIMATED](https://mcmodels.net/products/12999/embered-weapons-vol-1-animated) | SirValeron (Cubosynth) |
| 2 | [Embered Weapons Vol. 2 ANIMATED](https://mcmodels.net/products/13059/embered-weapons-vol-2-animated) | SirValeron (Cubosynth) |
| 3 | [Embered Weapons Vol. 3 ANIMATED](https://mcmodels.net/products/17696/embered-weapons-vol-3-animated) | SirValeron (Cubosynth) |
| 4 | [Ashen Weapons Vol. 1](https://mcmodels.net/products/12977/ashen-weapons-vol-1) | SirValeron (Cubosynth) |
| 5 | [Embered Tool Sets: Boreas Whisper](https://mcmodels.net/products/13098/embered-tool-sets-boreas-whisper-animated) | SirValeron (Cubosynth) |
| 6 | [Embered Tool Sets: Netherforge](https://mcmodels.net/products/13154/embered-tool-sets-netherforge-animated) | SirValeron (Cubosynth) |
| 7 | [Embered Tool Sets: Celestine Radiance](https://mcmodels.net/products/13220/embered-tool-sets-celestine-radiance-animated) | SirValeron (Cubosynth) |
| 8 | [Embered Tool Sets: Moon](https://mcmodels.net/products/14972/embered-tool-sets-moon-animated) | SirValeron (Cubosynth) |
| 9 | [Embered Tool Sets: Frayed](https://mcmodels.net/products/14883/embered-tool-sets-frayed-animated) | SirValeron (Cubosynth) |
| 10 | [Embered Tool Sets: Bloody](https://mcmodels.net/products/14907/embered-tool-sets-bloody-animated) | SirValeron (Cubosynth) |
| 11 | [Embered Tool Sets: Sanguinesti](https://mcmodels.net/products/17768/embered-tool-sets-sanguinesti-animated) | SirValeron (Cubosynth) |

### Creatures
| # | Listing | By |
|---|---|---|
| 12 | [Demons Vol.2: Mobs and Boss](https://mcmodels.net/products/17817/demons-vol2-mobs-and-boss) | Necron |
| 13 | [Cubees Dragons: Pets & Companions](https://mcmodels.net/products/17844/rework-cubees-dragons-pets-companions) | CUBEES |
| 14 | [Living Treasures: Mimic Pack](https://mcmodels.net/products/17845/living-treasures-mimic-pack) | Troyi's Crafts |
| 15 | [RPG Dungeon Chest Mimics Pack 1](https://mcmodels.net/products/17670/rpg-dungeon-chest-mimics-pack-1) | MC Garage |
| 16 | [Archdemon: Raid Boss & Mobs](https://mcmodels.net/products/17657/archdemon-raid-boss-mobs) | Necron |
| 17 | [Monstrum: Ice Mobs](https://mcmodels.net/products/17549/monstrum-ice-mobs) | QueueModels |
| 18 | [Antlerbit Pet](https://mcmodels.net/products/16651/antlerbit-pet) | DepartmentQDE |
| 19 | [Rune's RPG Companions: Dodo Mount](https://mcmodels.net/products/16514/runes-rpg-companions-dodo-mount) | RuneFist Studios |
| 20 | [Nog's Seagull](https://mcmodels.net/products/16522/nogs-seagull) | Nog's Menagerie |
| 21 | [SoloCraft: Cerberus](https://mcmodels.net/products/15469/solocraft-cerberus) | opERR0R |
| 22 | [Matatabi: Two-Tailed Beast Boss](https://mcmodels.net/products/17805/matatabi-two-tailed-beast-boss) | Anime Store |
| 23 | [Celestial Dragon: Colossal of the Sky](https://mcmodels.net/products/16255/celestial-dragon-colossal-of-the-sky) | EliteCreatures |
| 24 | [Cogbound Machine Uprising Dungeon Pack](https://mcmodels.net/products/16060/cogbound-machine-uprising-dungeon-pack) | ModelBlox |
| 25 | [Magma Hedgehog: RPG Boss](https://mcmodels.net/products/16088/magma-hedgehog-rpg-boss) | Bojarsky Legacy |
| 26 | [Cogbound Icarosphinx Boss with Arena](https://mcmodels.net/products/15828/cogbound-icarosphinx-boss-with-arena) | ModelBlox |

---

## 10. Open questions

1. **Glow by tier.** Do higher tiers get more glow and floating pixels (section 2.3)?
2. **A second head shape for top tiers?** One model per tool (MODELS-BLOCKBENCH section 6), or a second shape for the last two or three tiers, like the Embered sets?
3. **Do emission textures and animations survive export into Godot?** Answer with the first test model (sections 5.4 and 7.5).
4. **3D-sprite tool heads:** one box per pixel row, or one slab with a cut-out texture (section 7.1)? Answer by testing both in Godot.

Answered on 2026-10-21: texel density is **2 pixels per unit** (D-053), finer than the references' usual 16. We take their look, not their density. A 3D-sprite tool head at this density has twice as many pixel rows, so question 4 matters more.

## Pass history
| Pass | Change |
|---|---|
| User addition, 2026-10-21 | Doc created from the user's 26 mcmodels.net reference listings (D-052). Research on how the references are built, textured, animated and optimised, and how they map onto IMPLINGZ. All rules Proposed. Status Draft. |
| User addition, 2026-10-21 (later) | Texel density decided: 2 pixels per unit (D-053). Open question 1 removed, section 7.2 updated. |
