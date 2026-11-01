# IMPLINGZ: art direction (3D world and 2D icons)

| Status | Last pass | Depends on |
|---|---|---|
| Draft | User addition, 2026-10-14 | 00, 02 |

> Claude: read `docs/CLAUDE.md` before working from this file. Read this whole file before making, buying, editing or reviewing **any** 3D asset, material, light or scene layout.
>
> Labels: **Decided** (in `DECISIONS.md`) · **Proposed** (Claude's suggestion) · **Open question**

> **Changed on 2026-10-20.** The game is now built in **Godot** (D-037), so the Three.js settings in sections 7 and 10 apply only to the old test build. Godot settings are in [GODOT.md](GODOT.md). **Tools, weapons, creatures and items** are now Blockbench voxel models (D-044) and follow [MODELS-BLOCKBENCH.md](MODELS-BLOCKBENCH.md) where it differs from this doc (its section 10 lists the clashes). The world itself stays stylised cartoon and keeps this doc (D-047).

**Purpose of this doc:** keep everything in the 3D world looking like one game. It turns the user's 32 reference listings into rules a modeller, a texture artist or a developer can check an asset against.

**How the rules were made.** On 2026-10-14 Claude opened all 32 Fab listings in section 11, read each description, and looked at the first three preview images of each. The colour values in section 5 were sampled from those previews. The rules in sections 3–10 are Claude's reading of what the references share, so they are **Proposed** until the user agrees. The two headline rules in section 1 are **Decided**.

---

## 1. The two rules everything else follows

1. **Decided (D-014):** the 3D game world uses a **cartoon, stylised 3D** art style. The look stays close to the 32 reference listings in section 11.
2. **Decided (D-015):** IMPLINGZ uses **both** 2D and 3D art, each for one job:
   - **2D pixel art** is for menus and inventory items: icons, the inventory grid, the HUD, pickup messages.
   - **3D** is for anything in the world or anything physical: the ground, rocks, ore veins, buildings, plants, creatures, the player, and any item you can see in the scene (a held pickaxe, a dropped ore).

**The look in one sentence (Proposed):** *chunky, toy-like shapes with big bevelled facets, painted in warm, saturated colours with soft gradients, lit by a warm sun with cool, coloured shadows, so that every object reads clearly from the game camera.*

---

## 2. 2D and 3D: who does what

### What goes where (Decided, D-015)

| It is… | Art form | Examples in the game today |
|---|---|---|
| An icon in a menu, the inventory or the HUD | 2D pixel art, 48×48 PNG | `sprites/items/` (ores, ingots, gems, prestige), `sprites/pickaxes/` |
| Something standing in the world | 3D model | Ore veins (`models/tin_orevein.fbx`, `models/copper_vein.glb`), the furnace, the anvil, the cave floor and walls |
| Something the player holds or wears in the world | 3D model | The pickaxe (`models/pickaxe.glb`) |
| The player and any creature | 3D model | The character (`models/character.glb`) |

### Rules where the two meet (Proposed)

- **One item, one colour story.** When an item exists as both a 2D icon and a 3D model (an ore, an ingot, a gem, a pickaxe), the 3D model takes its main colours from the icon. `docs/CLAUDE.md` already says the picture is the source of truth for how an item looks. So: open the PNG, take its two or three main colours, and build the 3D materials from them. The pickaxe skins already do this (`models/pickaxe-skins.json` colours each part from its sprite).
- **Same silhouette idea.** The 3D model and the icon should be recognisable as the same thing at a glance. Example: Void Stone's icon is a dark purple spiral, so its 3D vein should carry a spiral motif, not just be a purple rock.
- **No pixel art in the 3D world.** Do not put pixel-art textures on 3D models, and never use `THREE.NearestFilter` on a world texture. Pixels belong to the 2D layer only.
- **No 3D renders as icons.** Inventory icons stay hand-made pixel art at 48×48. Do not swap in rendered screenshots of the 3D models.
- **Floating text is UI.** Name tags over veins, prompts like "F Mine Tin" and "+1 Iron ore" are interface, not physical objects. They follow the 2D/UI look, not the 3D rules below.

---

## 3. The five things that make the look (Proposed)

Every 3D asset must pass all five. Section 12 turns them into a checklist.

| # | Pillar | What it means | Seen most clearly in |
|---|---|---|---|
| 1 | **Chunky shapes** | Everything is thicker, rounder and heavier than in real life. Big simple forms first, small details last. | Crystals and Ores, Stylized Tavern, RPG Monster Wave |
| 2 | **Big bevelled facets** | Hard things (rock, stone, wood, metal) are built from a few large flat planes, with every edge bevelled so it catches a highlight. No razor-sharp edges, no noisy surfaces. | Crystals and Ores, Stylized Ore, Stylized Rocks, Stylized barrels |
| 3 | **Painted gradients** | Surfaces carry a soft painted gradient (lighter on top, darker at the bottom and in cracks) and painted edge highlights. Detail is painted, not photographed. | Stylized House – 1 Material, Stylized Chests, Stylized Trees |
| 4 | **Warm light, coloured shadows** | A warm sun, a cool blue sky fill, and shadows that are dark blue or purple, never black or grey. | Stylized Forest, Stylized MEGA PACK, Crystals and Ores |
| 5 | **Saturated accents on calm bases** | Big areas (rock, ground, walls) are calm and slightly tinted. Small things that matter (ore, crystals, crops, eyes, windows) are bright and saturated, and often glow. | Crystals and Ores, Stylized Ore, Stylized "Underworld" |

### What this style is not (Proposed)

The references rule these out. If an asset looks like one of these, it is off-style.

- **Not realistic.** No photo-scanned textures, no real-world thin proportions, no fine surface noise.
- **Not anime cel shading.** None of the references use black outlines or hard two-tone toon bands. Shading is smooth and painted.
- **Not flat-shaded low poly.** Faceted, yes, but the facets are bevelled and smooth-shaded with painted gradients. Not the hard-edged, one-colour-per-triangle "low poly" look.
- **Not pixel art in 3D.** See section 2.
- **Not neon everywhere.** Strong saturation is kept for accents. A scene where every surface is saturated has nothing for the eye to land on.

---

## 4. Shape language (Proposed)

### Silhouette and proportion
- **Design the silhouette first.** Fill the model black against a light background. If you can't tell what it is, the shape isn't done.
- **Exaggerate thickness.** Make planks, beams, tree trunks, handles and limbs about 1.5× to 2× as thick as real life. The barrels, chests and tavern beams in the references are all oversized.
- **Exaggerate key features.** Chimneys, crystal clusters, roof overhangs, creature heads and eyes are bigger than real. Unimportant parts shrink.
- **Taper and wobble.** Organic and hand-built things are never perfectly straight: walls lean slightly, roof lines sag, tiles are uneven, trunks twist and flare at the base (Stylized House, Stylized Tavern, Stylized Trees). Keep manufactured metal (ingots, pickaxe heads, chest bands) straighter, but still bevelled.
- **Wider at the bottom.** Rocks, veins, buildings and trees sit on a broad base and get narrower towards the top. This makes them feel planted.

### Facets and edges
- **Few, big facets.** A rock is 8–20 big planes, not hundreds of small ones. Compare Stylized Ore and Stylized Rocks: each face is large enough to hold its own gradient.
- **Bevel every hard edge.** One or two bevel segments are enough. The bevel is what catches the painted highlight.
- **No detail smaller than the camera can read.** At the scene's camera distance, a detail thinner than about **2 cm** (the character is **1.15 m** tall in the build) turns into flicker. Paint it instead of modelling it.

### Scale reference
- The player character is scaled to **1.15 m** tall in `main.js`. That is a build value, not a design decision. Use it as the reference until the character is final.
- Real-world sizes are a starting point only. Props near the player (barrels, chests, veins) can be scaled up 10–25% so they read well from the camera.

---

## 5. Colour (Proposed)

### Rules
- **Tint every neutral.** Stone is blue-grey or purple-grey. Ground is warm brown, often pushed towards purple in shade. Pure grey (equal red, green and blue) appears nowhere in the references.
- **Shadows are coloured.** The shadow side of a rock is a deep blue or purple, not a darker grey. The same goes for every material.
- **Lighter at the top.** Every object is lighter where the sky hits it and darker near the ground. Paint this into the texture or vertex colours as well as relying on lights.
- **Accents carry the saturation.** Ore, crystals, gems, crops, flowers, eyes and windows are the brightest colours on screen. Keep big surfaces 20–40% less saturated than the accents on them.
- **Crystals are two-tone.** Every crystal in the references shifts colour from base to tip (pink to orange, cyan to blue), and is brightest at the tip.
- **Warm materials are warm.** Wood is orange-brown, never grey-brown. Roof tiles, bricks and clay lean pink or red.

### Starting swatches
Sampled from the reference previews on 2026-10-14. They are a starting point, not a fixed palette. Check them under the game's lighting.

| Use | Colour | Sampled from |
|---|---|---|
| Rock, lit top | `#536B9F` | Crystals and Ores |
| Rock, side | `#2C3B64` | Crystals and Ores |
| Rock, shadow side | `#1A2745` | Crystals and Ores |
| Rock, purple-grey version | `#847385` | Stylized Ore |
| Ground, dirt | `#6A5667` | Stylized Ore |
| Crystal, pink | `#FF94DC` | Crystals and Ores |
| Crystal, orange tip | `#FE996C` | Crystals and Ores |
| Crystal, blue | `#6E9FFF` | Crystals and Ores |
| Gold | `#DFBD56` | Crystals and Ores |
| Ruby red ore | `#DD5A5C` | Stylized Ore |
| Timber wall | `#C7955C` | Stylized House – 1 Material |
| Roof tile | `#B99C8D` | Stylized House – 1 Material |
| Chimney brick | `#C9917C` | Stylized House – 1 Material |
| Grass, bright meadow | `#8DCA05` | Stylized Forest |
| Grass, dry or golden | `#A88D2A` | Stylized House – 1 Material |
| Grass, autumn | `#AB7B49` | Stylized Autumn Forest |
| Tree canopy | `#648236` | Stylized Forest |
| Tree trunk | `#534334` | Stylized Forest |
| Sky, blue | `#7090B7` | Stylized Environment Pack |
| Sky, near the horizon | `#D7E6F3` | Stylized MEGA PACK |
| Water | `#24A6A1` | Stylized waterfall |
| Desert sand | `#FFD4B2` | Stylized Desert |
| Desert rock | `#563C4C` | Stylized Desert |
| Cave wall, dark | `#432F2F` | Stylized "Underworld" |
| Lava, glowing | `#FFE11A` | Stylized "Underworld" |
| Creature, warm red | `#F8605E` | RPG Monster Wave Bundle |
| Creature, orange fur | `#BD753B` | Animated Stylized Cat |

### Ore tiers
The ten ore tiers are **Decided** (D-005). Their 3D colours must come from each tier's icons in `sprites/items/` (the `nugget_` and `gemstone_` files), following section 2. Do not pick tier colours from this table or from the tier's name. See `02-resources.md` for what each icon shows.

---

## 6. Surfaces and textures (Proposed)

### The painted look
1. **Base colour** per material, from the palette.
2. **Top-to-bottom gradient:** lighter on top, darker at the base.
3. **Cavity darkening:** cracks, gaps between planks and the undersides of overhangs are darker and slightly more saturated.
4. **Edge highlights:** a thin, lighter stroke along bevelled edges. This is what makes the Crystals and Ores rocks and the Stylized barrels pop.
5. **A few large brush marks or wood-grain strokes.** Big and soft. Nothing finer than the camera can read.

### Do and don't
- **Do** let large detail carry the material: big wood planks with deep grooves, big stone blocks, big roof tiles.
- **Do** keep normal maps soft and large-scale (bevels, plank grooves, block edges), if a normal map is used at all.
- **Don't** use photo textures, tiling photo noise or fine micro-detail normal maps.
- **Don't** bake hard, dark ambient occlusion. Contact shading should be soft and coloured, like the rest of the shadows.

### Three ways to texture, cheapest first
The references use all three. Pick the cheapest one that holds up at the camera distance.

| Method | Best for | Reference |
|---|---|---|
| **Gradient atlas or vertex colours.** One small shared texture of colour ramps. Each part of the model points at a ramp. | Crops, plants, small props, distant scenery | Stylized Farm Crops (NewLua, "Gradient", "Atlas" tags) |
| **One shared painted texture (a trim sheet).** One painted sheet of wood, stone, tiles and metal that a whole building reuses. | Buildings, walls, fences, modular kits | Stylized House – 1 Material |
| **A painted texture per asset.** | Hero props, creatures, ore veins | Stylized Chests, Stylized barrels, RPG Monster Wave (one 512×512 atlas for all 30 monsters) |

---

## 7. Materials in Three.js (Proposed)

The game renders with Three.js. These rules turn the look into settings.

- **Use `MeshStandardMaterial`.** It is already used across `main.js`. Keep `roughness` high (0.7–1.0) for stone, wood, ground, cloth and skin. The references are soft and matte.
- **Metalness only on metal.** `metalness` stays at 0 except on ingots, pickaxe heads, chest bands and other real metal. Metal in the references is stylised: bright, clean highlights, lower roughness (0.3–0.5) and a painted gradient, never a mirror.
- **Glow with `emissive`.** Crystals, gems in veins, lava, lit windows, lanterns and creature eyes use `emissive` with a matching colour. Keep the glow on the accent, not on the rock around it.
- **No toon materials, no outlines.** Do not use `MeshToonMaterial` or outline passes. The references don't use them (section 3).
- **No flat shading.** Leave `flatShading` off. Hard facets come from the model's bevels and painted gradients.
- **One material per asset where possible.** Fewer materials means fewer draw calls, which matters in a browser. The Stylized House (one material) and RPG Monster Wave (one atlas for 30 monsters) show it can be done without losing the look.
- **Textures in sRGB.** Colour textures use `THREE.SRGBColorSpace`, as the renderer already does for output. Normal and roughness maps stay linear.

---

## 8. Light, sky and atmosphere (Proposed)

### What the build already does
`main.js` already points the right way. It uses ACES filmic tone mapping (exposure 1.05), soft shadows, a hemisphere light (cool sky `#c5d4ff`, warm ground `#3a2c24`), a warm sun (`#fff6ea`, strength 2.3) and a cool blue fill light (`#9eb6ff`). That is the warm-key, cool-fill setup the references use.

### Rules
- **Warm sun, cool sky.** The key light is warm white to golden. The fill and the sky are blue. Never light a scene with a pure white sun and a grey ambient light.
- **Shadows read as colour.** With the hemisphere and fill lights, shadow sides should come out blue or purple (compare the rock swatches in section 5). If shadows look grey or black, the fill is too weak or the materials aren't tinted.
- **Depth through haze.** Outdoor scenes in the references fade distant things into a light, slightly blue haze (Stylized Forest, Stylized Swamp Forest, Stylized MEGA PACK). In Three.js that is `scene.fog`, with a colour close to the horizon sky.
- **Caves and dark areas are lit by their accents.** In Stylized "Underworld" the light comes from lava, glowing plants and crystals. The rock stays dark and warm, and the emissive accents do the work. Apply this to the cave scene and the ore veins.
- **Mood by time of day.** The references range from bright midday (Stylized Forest) to golden afternoon (Stylized Town, Stylized Autumn Forest). Which times of day the game has is an **open question**.

---

## 9. Category guides (Proposed)

Each guide lists the references for that category in section 11, what to take from them, and what to watch for. Where a category belongs to a game system that isn't designed yet, the guide says how things **look** if that system is added. It does not decide that the system exists.

### 9.1 Ores, crystals and veins
*References: Crystals and Ores, Stylized Ore.*

**Stylized Ore is the target (Decided, D-019).** The user owns a licence for it, and the game's veins should look like it: faceted grey rock spires, mounds and small piles, with chunky ore pieces set into the rock faces. Its files are Unreal Engine only, so the game's veins are our own models built to match it.

- **A vein is a calm rock body with bright ore in it.** The rock is a tinted blue-grey or purple-grey (section 5) and stays the same family across tiers. The ore or crystals set into it carry the tier's colour and are the brightest thing on the vein.
- **Ore sits in the rock, crystals grow out of it.** Nuggets and chunks sit partly sunk into the rock faces (Stylized Ore). Crystals burst out in clusters of three to seven points of different sizes (Crystals and Ores).
- **Size shows value.** Stylized Ore sells each ore in small, medium and large. Bigger and taller veins read as richer.
- **Every tier is recognisable from across the room.** Shape and colour together, not colour alone, so colour-blind players can tell tiers apart.
- **Tier colours come from the icons.** See section 2 and section 5.
- **Today's veins.** Tin and Copper are drawn models. Tiers 3–10 are built in code in the Godot game (`game/gathering/vein_art.gd`, 2026-10-22), each with its own shape, from this section. Drawn models can still replace them.
- **Rock colour can change per tier (Decided, D-017).** Veins don't have to share one rock colour. Stylized Ore's purple-grey and Crystals and Ores' slate blue both fit, and so do other tinted rocks. Keep every vein's rock tinted (section 5) and calmer than its ore, so the ore stays the accent.

### 9.2 Farming and crops
*References: Stylized Garden Crop Grades, Stylized Farm Crops, Farm Crops.*

Farming is **not a decided activity** (`01-activities.md` is Not started). These rules only say how crops look if farming is added.

- **Each growth stage has its own clear silhouette.** The references use four or five stages (seed or sprout, young plant, growing, ripe, and in one pack dead). A player should tell the stages apart from the camera without reading a label.
- **The crop is the accent.** Leaves are a calm green. The tomato, pumpkin or carrot is the saturated colour, and slightly oversized.
- **Cheap to draw in bulk.** Fields mean many copies, so use the gradient-atlas method (section 6) and low triangle counts (section 10). Stylized Farm Crops is built for exactly this.
- **Planters and soil are chunky.** Thick wooden boards and soft, raised mounds of soil (Farm Crops, Stylized Garden Crop Grades).
- **Watch for:** Farm Crops (Black House) is the most realistic of the three: thinner leaves and finer textures. Take its layouts and planter ideas. Take the look from the other two.

### 9.3 Structures and props
*References: Stylized Stone Walls, Stylized Tavern, Halloween Pack, Stylized Town, STYLIZED MEDIEVAL VILLAGE, Stylized barrels, Stylized Chests, Stylized Gravestones Pack, Stylized House – 1 Material.*

- **Storybook medieval.** Timber frames filled with warm plaster, stone bases, steep roofs of chunky, uneven tiles, oversized chimneys. The house reads as a stack: stone at the bottom, timber in the middle, roof on top.
- **Nothing is square.** Roof ridges sag a little, walls lean, beams are slightly crooked, tiles are each a little different (Stylized House, Stylized Tavern).
- **Life on the building.** Flower boxes, vines, hanging signs, banners, small mushrooms at the base. Use them sparingly, to make a building feel lived in.
- **Lit windows glow warm yellow** (emissive), so buildings read from far away and at dusk.
- **Props are oversized and bevelled.** Barrels have fat metal bands and thick staves. Chests have big hinges and clasps. Each prop has a clean, broken or variant version where useful (Stylized barrels ships an intact and a broken barrel).
- **Colour variants by material, not by model.** Stylized Chests has ten chests and a material system that recolours them. Reuse one model with several colourways before making a new model.
- **Modular kits.** Walls, fences and buildings are built from snapping pieces (Stylized Stone Walls, Stylized Tavern, Stylized Town). This keeps the look consistent and the asset count low.
- **The furnace and the anvil** in the build are made from boxes in code (**test art**). Drawn versions should follow this section.
- **Watch for:** the Halloween Pack is seasonal decoration. Seasonal events are **not decided**. Stylized Gravestones are closer to realistic sculpture with 4K textures. Take the shapes, not the texture detail.

### 9.4 Environment and nature
*References: Stylized Environment Pack, Stylized Rocks, Stylized Trees, Stylized Plants, Stylized MEGA PACK, Stylized Desert, Stylized Forest, Stylized Swamp Forest, Stylized "Underworld", Stylized Autumn Forest, Coral Reef Stylized Pack Plant, Stylized Stone Rock Pack, Stylized waterfall.*

- **Trees are blobs on chunky trunks.** The canopy is a few big, soft clumps of leaves, not individual leaves (Stylized Trees, Stylized Environment Pack). Trunks are thick, flare at the root and twist a little.
- **Canopy colour sets the mood.** The same tree shape in green, orange, yellow, pink or teal changes the biome (Stylized Trees). Reuse shapes, change colours.
- **Rocks follow the vein rules.** Big bevelled facets, tinted grey, lighter on top. Stylized Rocks ships each rock in four skins (basic, snowy, tropical, savannah): again, one shape, many colourways. Mossy tops are a cheap way to tie rocks into grass.
- **Ground is soft and lumpy.** No perfectly flat floors. Gentle rises, worn paths, scattered pebbles.
- **Grass is bright and dense near the camera.** It is the brightest green in the scene. Flowers and mushrooms add small, saturated dots of colour (Stylized Plants).
- **Water is turquoise with white foam.** Clear and bright near the shore, deeper teal further out. Waterfalls are bands of turquoise with a white, cloudy splash at the bottom (Stylized waterfall, Stylized Autumn Forest).
- **Caves.** Dark, warm rock walls with big vertical facets and stalactites. Light comes from lava, glowing plants and crystals (Stylized "Underworld"). This fits the cave test scene in the build.
- **Biomes.** The references show meadow and forest, autumn, swamp, desert, underwater reef and an underworld cave. Which biomes the game has is an **open question**.
- **Watch for:** Stylized Stone Rock Pack is about 200,000 polygons for the pack, sculpted in ZBrush, with 2K textures. Far too heavy for a browser game as it is. Take its layered, stacked-slab shapes only. The Coral Reef pack has 4K textures and about 34,000 polygons. Same advice.

### 9.5 Creatures
*References: Stylized Spider, Stylized Werewolf, Animated Stylized Cat, RPG Monster Wave Bundle, Stylized Fantasy Dragons Pack.*

**The Implingz are already done (Decided, D-016).** This section does not apply to them. Do no art work on Implingz. These rules are for any other creature in the world.

- **Readable from the camera.** Big heads and eyes, clear silhouettes, chunky limbs. You can tell what a creature is and which way it faces at a glance.
- **Eyes carry the character.** Big, bright eyes on friendly creatures (Animated Stylized Cat). Glowing eyes, often yellow or red, on hostile ones (RPG Monster Wave, Stylized Spider, Stylized Werewolf).
- **Simple, bold colour blocks.** Two or three main colours per creature, one accent. RPG Monster Wave's thirty monsters each read from colour and silhouette alone.
- **Colour variants through tint masks.** Stylized Spider ships four skins, RPG Monster Wave uses a tint-mask material, the Dragons pack has six painted skins. Plan creatures so one model can wear several colourways.
- **Animation sells the cartoon.** The references animate idle, walk, run, attack, hit and death, with squash-and-stretch on the cuter ones. Exaggerated poses and timing over realistic motion.
- **The cute-to-menacing range.** The creature references cover a wide range. At one end: round, chibi (big head, small body) monsters and a cute cat. At the other: a lanky werewolf, a spider and painted dragons with realistic proportions. Where other creatures sit on this range is an **open question**.
- **Watch for:** the Dragons pack is the least cartoon of the creature references (realistic anatomy, dark palette).

---

## 10. Web budgets and file rules (Proposed)

IMPLINGZ is a browser game (D-001). Most references were made for Unreal Engine on desktop PCs. Take their look, not their cost.

### Budgets per asset
Where a reference lists its numbers, they are shown.

| Asset type | Triangles | Texture | Reference numbers |
|---|---|---|---|
| Small plant, flower, crop stage | 100–700 | Shared gradient atlas | Stylized Plants: 89–678 triangles each |
| Small prop (barrel, chest, nugget) | 300–2,000 | 512 or a shared atlas | Stylized barrels: 609 and 801 triangles; textures at 512, 1K and 2K |
| Ore vein | 500–3,000 | 512–1024 | n/a |
| Tree | 1,000–5,000 | Shared atlas | n/a |
| Building | 3,000–12,000 | One 1024 trim sheet | Stylized House: one material |
| Small creature | 1,000–5,000 | Shared 512 atlas | RPG Monster Wave: one 512×512 atlas for 30 monsters |
| Large creature or the player | 5,000–10,000 | 1024 | Stylized Spider: 8,702 triangles |

These are starting budgets. They should be checked against the frame rate in the real scene before they become rules.

### Files
- **Format:** `.glb` (glTF binary). The game loads glTF with `GLTFLoader`. The tin vein is still `.fbx`, which works, but new assets should be `.glb`.
- **Units and axes:** metres, Y up, facing +Z.
- **Origin:** at the bottom centre of the object, so it sits on the ground at height 0.
- **Scale:** check against the 1.15 m character (section 4) before export.
- **Materials:** as few as possible, named for what they are (`Rock`, `Crystal`, `Wood`), so the code can recolour parts the way `models/pickaxe-skins.json` does.
- **Textures:** PNG or JPG, power-of-two sizes (512, 1024). 2048 only for terrain or very large surfaces.

---

## 11. Reference library (Decided list, D-014)

The user chose these 32 listings on 2026-10-14. The list is the decision. The notes on what to take and what to watch for are **Proposed**.

**These are style references only (Decided, D-018).** Our assets are made by us, not bought. Don't copy a listing's models or textures. Use them to judge shape, colour and finish. The format and licence notes below are kept for the record.

### Ores
| # | Listing | By | Take from it | Watch for |
|---|---|---|---|---|
| 1 | [Crystals and Ores](https://www.fab.com/listings/3cdb09b5-b851-400d-9afb-45f62b3e68e5) | Nemek Graphics | The clearest example of the whole look: slate-blue faceted rocks, two-tone glowing crystals, chunky ingots and nuggets, coloured shadows. Ships nuggets, ores, crystals, bare rocks, an ingot and a pickaxe. | Files include FBX, OBJ and Blender. |
| 2 | [Stylized Ore](https://www.fab.com/listings/7dfcd47e-6e2e-49e3-a4f5-23fa6eca7b71) | Stylized Craft | Ore chunks set into tall purple-grey rocks. Each ore in three sizes. | Unreal-only files. |

### Farming
| # | Listing | By | Take from it | Watch for |
|---|---|---|---|---|
| 3 | [Stylized Garden Crop Grades](https://www.fab.com/listings/bac9d56e-c09e-42b4-b62c-18f684117554) | Stylized Craft | Four growth grades per crop, bright crops on calm leaves, chunky vegetable beds. | The fences and trees in its previews are not in the pack. Unreal-only files. |
| 4 | [Stylized Farm Crops – Ultimate Low Poly Asset Pack](https://www.fab.com/listings/9558dd18-c3ab-4794-84e7-515f57472ad2) | NewLua Studios | Five growth stages, gradient-atlas texturing, very light models. The best model for crops in a browser. | Has FBX, Blender and Unity files. |
| 5 | [Farm Crops](https://www.fab.com/listings/4383fc53-eab7-47da-9652-ea00e6f70c30) | Black House | Field layouts, modular planter boxes, five stages including "dead". | The most realistic farming reference. Take layouts, not texture detail. Unreal-only. |

### Structures
| # | Listing | By | Take from it | Watch for |
|---|---|---|---|---|
| 6 | [Stylized Stone Walls](https://www.fab.com/listings/e80f1f6f-6648-4fbc-817f-69c832858c0b) | Stylized Craft | Modular stone walls and columns, chunky blocks, warm roof caps. | Unreal-only. |
| 7 | [Stylized Tavern](https://www.fab.com/listings/a6e8c97b-f66d-4a6a-9076-1b24a66c0916) | Stylized Craft | A modular storybook building: plaster, timber, tiles, a big metal still, vines. | Unreal-only. |
| 8 | [Halloween Pack](https://www.fab.com/listings/5bf3d44b-a6f6-406c-b48d-ab816e5a0564) | Stylized Craft | Seasonal props in the same style: pumpkins, brooms, hats, banners. | Seasonal events are not decided. Unreal-only. |
| 9 | [Stylized Town](https://www.fab.com/listings/4121695a-563b-488b-911d-2a3fbda98634) | Hivemind | A whole town at golden hour: enterable buildings, warm light, dense foliage, smoke and firefly effects. | Large Unreal scene. Take the mood and the lighting, not the scale. |
| 10 | [STYLIZED MEDIEVAL VILLAGE](https://www.fab.com/listings/d228c635-fecb-4b22-a773-11ff3494f8a6) | Stylized Medieval Village | Village layout, red tile roofs, half-timbered walls, props. | Sold under the "UE Marketplace License", not the standard licence the other listings use. Check what it allows before buying. Unreal-only. |
| 11 | [Stylized barrels](https://www.fab.com/listings/0aaf9b50-181e-434a-b05c-6cdeb1ffb115) | FairyCoon | A textbook stylised prop: fat staves and bands, painted wood, an intact and a broken version, about 600–800 triangles. | Has FBX and OBJ. |
| 12 | [Stylized Chests](https://www.fab.com/listings/c82b09b1-991a-4061-bd6a-95ecd3a33f85) | Project Zima | Ten hand-painted chests, chunky metal trims, one material system for many colourways, rigged and animated lids. | Unreal and Unity. |
| 13 | [Stylized Gravestones Pack](https://www.fab.com/listings/cda1e628-827b-4437-b3e9-8c3c40b5c2ca) | Typical Tris | Variety of simple, readable gravestone shapes. | 4K textures and a realistic stone finish. Take shapes only. |
| 14 | [Stylized House – 1 Material](https://www.fab.com/listings/61d087f5-7e41-43f8-b3ec-52faf30adf76) | Agustin Honnun | A whole house from one painted material. The best example of the painted look and of saving draw calls. | Free, and its description allows commercial use. |

### Environment
| # | Listing | By | Take from it | Watch for |
|---|---|---|---|---|
| 15 | [Stylized Environment Pack](https://www.fab.com/listings/422ae4e1-9441-47b1-8f61-545f764ee502) | Stylized Craft | Blob-canopy trees, rolling hills, soft sky. | Unreal-only. |
| 16 | [Stylized Rocks](https://www.fab.com/listings/df9b8291-c78d-45e7-ba0b-6c099e4e5a04) | Stylized Craft | Faceted rocks in four skins (basic, snowy, tropical, savannah): one shape, many colourways. | Unreal-only. |
| 17 | [Stylized Trees](https://www.fab.com/listings/4e2a785f-bc2a-4651-9e4a-2add2cec30dc) | Stylized Craft | Clumpy canopies in many colours, twisted trunks, stumps, logs, bushes. | Unreal-only. |
| 18 | [Stylized Plants](https://www.fab.com/listings/ff0a2076-98b8-4f5f-b24f-9a4f90b7d29e) | Stylized Craft | Flowers, shrubs and mushrooms at 89–678 triangles. Bright accent colours. | Unreal-only. |
| 19 | [Stylized MEGA PACK – Stylized Nature Environment](https://www.fab.com/listings/f8b6394b-ce09-46b3-94f6-212d95804fff) | So Stylized | The full outdoor mood: lakes, cliffs, haze, autumn and summer palettes, time of day and weather. | A large Unreal bundle built on Unreal-only systems. Take the mood. |
| 20 | [Stylized Desert – Oasis Nature Environment](https://www.fab.com/listings/bef25c2d-6732-4d70-b0fd-271cbd45093d) | So Stylized | Pink-red layered cliffs, peach sand, turquoise oasis water, palms. | Biomes are not decided. Unreal-only. |
| 21 | [Stylized Forest](https://www.fab.com/listings/09110800-689b-471a-8009-ed2f3f7cbf6d) | TomkaGS | Bright meadow greens, soft haze, chunky round trees, worn dirt paths. | Unreal-only. |
| 22 | [Stylized Swamp Forest](https://www.fab.com/listings/57931089-a9fd-4d7c-920f-b6cabdecf51c) | AleksandrIvanov | Calm blue-green palette, still water, fallen logs, blue haze. | Unreal-only. |
| 23 | [Stylized "Underworld"](https://www.fab.com/listings/cf3cb54a-8b38-4f83-822d-a2ef56dbcbd4) | AleksandrIvanov | A cave lit by its accents: lava, glowing plants, dark warm rock, stalactites. The closest reference for the cave and mining areas. | Unreal-only. |
| 24 | [Stylized Autumn Forest](https://www.fab.com/listings/b66f549f-59e2-4e0b-b3c3-503c69fbeb98) | TomkaGS | Orange and gold canopies, a waterfall, a small log hut by a river. | Unreal-only. |
| 25 | [Coral Reef Stylized Pack Plant](https://www.fab.com/listings/0d532a28-2162-4550-986f-bf9b1c009205) | Stylized Texture | Tube corals and sea plants in saturated orange and yellow. | About 34,000 polygons and 4K textures. Too heavy as it is. |
| 26 | [Stylized Stone Rock Pack](https://www.fab.com/listings/c9483ba9-744c-43d1-8cb3-cebdfeacb323) | Stylized Texture | Stacked, layered slab shapes for cliffs and ledges. | About 200,000 polygons. Take the shapes only. |
| 27 | [Stylized waterfall](https://www.fab.com/listings/cd3d1edd-ee4a-4c0e-88cd-cf46bdf8c7d5) | 12HZ | Turquoise water with white foam and splash. The seller describes it as imitating Genshin Impact. | An Unreal shader and particle effect. It would need rebuilding for Three.js. |

### Creatures
| # | Listing | By | Take from it | Watch for |
|---|---|---|---|---|
| 28 | [Stylized Spider](https://www.fab.com/listings/9461f8be-5ef5-4e6f-84ba-a8cf1aa2b9a5) | Stylized Craft | Glowing markings and eyes, four skins on one model, 8,702 triangles, eight animations. | Unreal-only. |
| 29 | [Stylized Werewolf](https://www.fab.com/listings/570d917b-1bd0-4ff7-81a7-eb26ca12b518) | Game-Ready Characters | A menacing creature that is still low poly and readable: hunched pose, long arms, glowing eyes. | The least cartoon proportions after the dragons. Unreal-only. |
| 30 | [Animated Stylized Cat](https://www.fab.com/listings/ea55043b-17b9-4caa-8428-4addc5e18be9) | Frostydrop | A friendly, cute creature: big eyes, soft fur shapes, blink, several colourways. | Unreal-only. |
| 31 | [RPG Monster Wave Bundle PBR](https://www.fab.com/listings/82259e53-fe38-4eab-93b6-1a28c3a311e5) | Dungeon Mason | Thirty round, chibi monsters that read from colour and silhouette alone. One 512×512 atlas for all of them. A tint mask for colourways. | Has FBX. The seller names Three.js among the engines it supports. |
| 32 | [Stylized Fantasy Dragons Pack](https://www.fab.com/listings/d2cd19c2-0452-416f-ad8e-6bdb27ab4fff) | N-Hance Studio | Painted skins on one model (six colours), wings and horns with strong silhouettes. | **The seller asks NFT and blockchain projects to contact them before using any of their assets.** IMPLINGZ is an NFT game (D-001). The most realistic creature reference. |

---

## 12. Review checklist (Proposed)

Run this on every 3D asset before its PR is marked ready. Note the result in the PR.

**Look**
- [ ] The silhouette reads clearly when filled black.
- [ ] Shapes are chunkier than real life. Nothing is thinner than about 2 cm against the 1.15 m character.
- [ ] Hard edges are bevelled. Big facets, not surface noise.
- [ ] Neutral colours are tinted (blue, purple or warm). No pure grey.
- [ ] The texture or vertex colours are lighter at the top and darker at the base.
- [ ] The brightest, most saturated colour is on the part that matters (ore, crop, eye, window).
- [ ] No photo textures, no outlines, no toon bands, no pixel-art textures.

**Fits the game**
- [ ] If the item also has a 2D icon, its main colours come from that icon (section 2).
- [ ] Placed in the real scene next to the character and the existing assets, it looks like the same game.
- [ ] It looks right under the scene's lighting, with blue or purple shadows, not grey.

**Tech**
- [ ] `.glb`, metres, Y up, origin at the bottom centre.
- [ ] Within the budget for its type (section 10), or the PR explains why not.
- [ ] As few materials as possible, with clear names.
- [ ] `MeshStandardMaterial`. Metalness only on metal. Emissive only on things that glow.

**Source**
- [ ] Made by us (D-018). Not bought, and not copied from a reference listing.

---

## Open questions

1. **Which biomes does the game have?** The references show meadow, forest, autumn, swamp, desert, reef and an underworld cave.
2. **Which times of day?** Bright midday, golden afternoon, or a day–night cycle?
3. **Do you agree with the budgets in section 10** as a starting point, until they are measured in the real scene?
4. **Where do creatures other than Implingz sit on the cute-to-menacing range** (section 9.5)?

Answered on 2026-10-15: Implingz are already done (D-016), veins can differ in colour (D-017), and the references are style only, with our own assets made by us (D-018).

Answered on 2026-10-20: the world stays stylised cartoon, like the Godot test project's assets. Items and enemies are Blockbench models with a slight voxel feel (D-047).

## Pass history
| Pass | Change |
|---|---|
| User addition, 2026-10-14 | Doc created from the user's 32 reference listings. Cartoon stylised 3D world (D-014) and the 2D-icons / 3D-world split (D-015) recorded. Everything else Proposed. Status Draft. |
| User addition, 2026-10-15 | Implingz left out of the art work (D-016). Veins can differ in colour (D-017). References are style only; assets are made by us (D-018). Open questions 1, 4 and 5 answered and removed. The user owns a Stylized Ore licence, and veins should look like it (D-019). |
| User addition, 2026-10-20 | Note added at the top: Godot (D-037) and Blockbench voxel models for tools, weapons, creatures and items (D-044). Open question 5 (world style) added, then answered the same day (D-047) and removed. Nothing else changed. |
