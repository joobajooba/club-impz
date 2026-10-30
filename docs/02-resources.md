# 02: Resources & economy

| Status | Last pass | Depends on |
|---|---|---|
| Draft | 0 | 00 |

> Must agree with [00-overview](00-overview.md) and [02-resources](02-resources.md).
> Labels: **Decided** (in `DECISIONS.md`) · **Proposed** (Claude's suggestion) · **Open question**

**Purpose of this doc:** Everything that can be gathered, earned, spent or traded, and where it enters (sources) and leaves (sinks) the game.

**Read the pictures.** The mining items live as 48×48 PNGs in `sprites/items/`. When this doc is used, open every file in that folder and match it to the tables below. The picture decides what the item looks like. A filename is only the label. If a filename and a picture disagree, trust the picture and say so.

---

## 1. Role in the core loop
*What this system takes in, what it gives out, and where it sits in the loop in the overview.*

## 2. Player experience
*What it should feel like, in 2–3 sentences.*

## 3. Rules & mechanics
*How it works, precise enough for a developer to build from.*

### Mining tiers (Decided, D-005)

The user set this table on 2026-10-12. It is the list of ores that can be mined, the ingot icon that belongs to each, and the one gem that can come with that ore. Ten tiers, lowest to highest. One gem per tier. No tier shares a gem.

The **Chance for Gem** column was empty on the user's table. The user set it on 2026-10-13 (**Decided, D-012**): 10% for Tin, falling 1% per tier to 1% for Stellarite. The chance is rolled each time a vein breaks, and the gem comes on top of the ore. While the player holds the Stellarite pickaxe, every gem chance is doubled (**Decided, D-059**): 20% for Tin down to 2% for Stellarite.

Which pickaxe mines which ore, and what a crafted pickaxe costs, is decided in D-006, D-011 and D-060 below. How the furnace turns ore into ingots, what it burns, and how players get hilts are decided in D-054 to D-058 (see [Smelting, fuel and hilts](#smelting-fuel-and-hilts-decided-d-054-to-d-058)). The build still uses the D-013 test values until it is updated. Other blacksmithing, other crafting, and selling are **not decided**. Do not fill those in.

What mining gives: one ore item for that tier (the `nugget_` picture) every time a vein breaks (D-007, D-010), and sometimes the paired gem (D-012). Ingots come only from the furnace, never straight from mining.

| Tier | Name | Ore picture | Ingot picture | Gem | Gem picture | Gem chance (D-012) |
|---|---|---|---|---|---|---|
| 1 | Tin | `sprites/items/nugget_tin.png` | `sprites/items/ingot_tin.png` | Topaz | `sprites/items/gemstone_topaz.png` | 10% |
| 2 | Copper | `sprites/items/nugget_copper.png` | `sprites/items/ingot_copper.png` | Sapphire | `sprites/items/gemstone_sapphire.png` | 9% |
| 3 | Iron | `sprites/items/nugget_iron.png` | `sprites/items/ingot_iron.png` | Amethyst | `sprites/items/gemstone_amethyst.png` | 8% |
| 4 | Coal | `sprites/items/nugget_coal.png` | none | Ruby | `sprites/items/gemstone_ruby.png` | 7% |
| 5 | Gold | `sprites/items/nugget_gold.png` | `sprites/items/ingot_gold.png` | Emerald | `sprites/items/gemstone_emerald.png` | 6% |
| 6 | Obsidian | `sprites/items/nugget_obsidian.png` | `sprites/items/ingot_obsidian.png` | Jade | `sprites/items/gemstone_jade.png` | 5% |
| 7 | Titanite | `sprites/items/nugget_mithril.png` | `sprites/items/ingot_mithril.png` | Diamond | `sprites/items/gemstone_diamond.png` | 4% |
| 8 | Dreadstone | `sprites/items/nugget_adamantite.png` | `sprites/items/ingot_adamantite.png` | Painite | `sprites/items/gemstone_painite.png` | 3% |
| 9 | Void Stone | `sprites/items/nugget_void.png` | `sprites/items/ingot_void.png` | Arcanium | `sprites/items/gemstone_arcanium.png` | 2% |
| 10 | Stellarite | `sprites/items/nugget_stellarite.png` | `sprites/items/ingot_stellarite.png` | Eclipsium | `sprites/items/gemstone_eclipsium.png` | 1% |

File names that do not match the display name:

- Void Stone uses `void`, not `void_stone`.
- Titanite uses `mithril` (D-020).
- Dreadstone uses `adamantite` (D-020).
- Coal has an ore picture only. There is no `ingot_coal.png`. The table still showed a second coal icon in the Ingot column. That file was not in the asset folder. Do not invent one.

What the pictures actually show (open the file if you need the exact pixels):

- `nugget_` files are the ore rocks. Tin is a pale grey chunk. Coal is a black jagged lump. Void Stone is a dark purple spiral, not a bar. The others follow the same rock shape, coloured for that tier.
- `ingot_` files are bars. Stellarite is a blue bar with yellow stars. Void Stone is a dark bar with a purple spiral. Tin is a plain silver bar.
- Gems are cut stones. Topaz is an orange round gem. Arcanium is a purple four-point star. Eclipsium is a black sphere with a white four-point glint. The other gems match their names: blue sapphire, purple amethyst, red ruby, green emerald, green jade, white diamond, red painite cluster.

These pictures are inventory icons. They are not the 3D ore vein in the walk scene (`models/tin_orevein.fbx`).

### Pickaxes (Decided, D-006)

The user set these two tables on 2026-10-12. The first says which pickaxe mines which ore. The second says what a crafted pickaxe takes. There is no Steel ore and no Steel ingot. The Steel pickaxe is made from iron ingots.

The mine table names **one** pickaxe per ore. The user added on 2026-10-13 that a pickaxe also mines **every ore below** its named ore (**Decided, D-011**). So the Gold pickaxe mines Obsidian and everything below it, and upgrading never locks a player out of the lower ores.

Stellarite is mined with the Void pickaxe. The Stellarite pickaxe is crafted, and the table does not name an ore for it. **Proposed:** it mines everything the Void pickaxe does (all ten ores), because D-011 makes a stronger pickaxe mine what a weaker one can. Its advantage is gems: while the player holds it, every gem chance is doubled (**Decided, D-059**), for example 20% for Tin and 2% for Stellarite.

The Stone pickaxe mines Tin and Copper. It has **no row** on the craft table. Do not invent a Stone recipe.

Hilts are ingredients only (**Decided, D-058**). Ash Wood and Oak Wood hilts are made from 5 Ash or Oak planks (D-107). The blacksmith crafts the Void Hilt and the Cosmic Hilt from ingots and a gem (see [Smelting, fuel and hilts](#smelting-fuel-and-hilts-decided-d-054-to-d-058)). There is no picture for a hilt in `sprites/items/`.

| Ore | Gem | Mined with |
|---|---|---|
| Tin | Topaz | Stone Pickaxe |
| Copper | Sapphire | Stone Pickaxe |
| Iron | Amethyst | Bronze Pickaxe |
| Coal | Ruby | Iron Pickaxe |
| Gold | Emerald | Steel Pickaxe |
| Obsidian | Jade | Gold Pickaxe |
| Titanite | Diamond | Obsidian Pickaxe |
| Dreadstone | Painite | Titanite Pickaxe |
| Void Stone | Arcanium | Dreadstone Pickaxe |
| Stellarite | Eclipsium | Void Pickaxe |

| Pickaxe | Crafted using |
|---|---|
| Stone Pickaxe | No craft row |
| Bronze Pickaxe | 5 Tin Ingot, 5 Copper Ingot, 1 Ash Wood Hilt |
| Iron Pickaxe | 5 Iron Ingot, 1 Ash Wood Hilt |
| Steel Pickaxe | 10 Iron Ingot, 1 Ash Wood Hilt |
| Gold Pickaxe | 10 Gold Ingot, 1 Ash Wood Hilt |
| Obsidian Pickaxe | 10 Obsidian Ingot, 1 Oak Wood Hilt |
| Titanite Pickaxe | 10 Titanite Ingot, 1 Oak Wood Hilt (D-060) |
| Dreadstone Pickaxe | 10 Dreadstone Ingot, 1 Oak Wood Hilt |
| Void Pickaxe | 10 Void Ingot, 1 Void Hilt |
| Stellarite Pickaxe | 10 Stellarite Ingot, 1 Cosmic Hilt |

The Titanite row first said 10 Obsidian Ingot, the same as the Obsidian row. On 2026-10-21 the user confirmed that was a mistake: it takes 10 Titanite ingots (**Decided, D-060**, superseding that row of D-006). The build still uses Obsidian ingots until it is updated.

Coal is not an ingredient in any pickaxe. It is furnace fuel (D-055). Coal still has no ingot file.

The walk scene has all ten pickaxes as skins (`models/pickaxe-skins.json`). Stone, Bronze and Iron have drawn sprites. Steel to Stellarite are **test placeholders**: their sprites in `sprites/pickaxes/` are the iron sprite recoloured with each ingot's colours, and the handle coloured for its hilt. They should be replaced with drawn art.

### Smelting, fuel and hilts (Decided, D-054 to D-058)

The user set these on 2026-10-21. They replace the D-013 test values, except for wood hilts (below).

- The **furnace** turns ore into **1 ingot** of the same metal. Higher tiers take more ore (D-054).
- It burns **Coal** as fuel from Gold upward (D-055). Coal itself can't be smelted, because it has no ingot.
- Smelting and crafting **cost no energy** (D-056). Energy is spent only on gathering.

| Ingot | Ore per ingot (D-054) | Coal per ingot (D-055) |
|---|---|---|
| Tin | 2 | 0 |
| Copper | 2 | 0 |
| Iron | 3 | 0 |
| Gold | 3 | 1 |
| Obsidian | 4 | 1 |
| Titanite | 4 | 1 |
| Dreadstone | 5 | 2 |
| Void Stone | 5 | 2 |
| Stellarite | 5 | 2 |

Iron ingots must not need Coal: Coal is mined with the Iron pickaxe, which is made from Iron ingots.

Hilts (D-058). The blacksmith makes the two gem hilts:

| Hilt | Used in | How the player gets it |
|---|---|---|
| Ash Wood Hilt | Bronze, Iron, Steel and Gold pickaxes, sickles and axes | 5 Ash planks, at the blacksmith (D-107) |
| Oak Wood Hilt | Obsidian, Titanite and Dreadstone pickaxes, sickles and axes | 5 Oak planks, at the blacksmith (D-107) |
| Void Hilt | Void pickaxe | 2 Void ingots + 1 Arcanium, at the blacksmith |
| Cosmic Hilt | Stellarite pickaxe | 2 Stellarite ingots + 1 Eclipsium, at the blacksmith |

**Until lumbering exists**, the build keeps supplying wood hilts for free, as a labelled **test value**. D-013 still applies to wood hilts only.

**What this costs a player** (worked out from D-006, D-012, D-054, D-055, D-058 and D-060; not a decision): every pickaxe from Bronze to Stellarite, plus the two gem hilts, takes about **345 ore and 98 Coal, about 443 mines**. At 20 mines per energy reset that is about 22 resets, or 11 days for a player who uses both resets every day. Gems add to that, and they are random. Arcanium (2%) takes about 50 Void Stone mines on average, most of which the Void pickaxe needs anyway. Eclipsium (1%) takes about 100 Stellarite mines on average, against the 60 Stellarite ore the Stellarite pickaxe and Cosmic Hilt need. About 1 player in 3 needs more than 100 Stellarite mines to find one, and about 1 in 20 needs more than 300.

The build today still runs on the D-013 test values: 2 ore make 1 ingot with no Coal, and the blacksmith supplies every hilt. Those are not the design.

### Foraging tiers (Decided, D-022 to D-027)

The user set the foraging rules on 2026-10-17 and asked Claude to make up the plant names (D-026). Ten tiers, lowest to highest, the same count as mining. The tiers are **for now** and may change.

What foraging gives: a picked plant for that tier (the `plant_` picture), and sometimes that plant's seed (D-025). A **drying rack** turns plants into a **dried bundle** of the same tier (the `bundle_` picture), the way the furnace turns ore into ingots (D-022). Bundles are used for **potions, Impling food and crafting ingredients** (D-023).

Plants are picked with **sickles**, one per tier. A sickle picks its own tier's plant and every lower tier, the same rule as pickaxes (D-024).

| Tier | Name | Plant picture | Bundle picture | Seed picture | Seed chance (D-025) |
|---|---|---|---|---|---|
| 1 | Nettle | `sprites/items/plant_nettle.png` | `sprites/items/bundle_nettle.png` | `sprites/items/seed_nettle.png` | 10% |
| 2 | Marigold | `sprites/items/plant_marigold.png` | `sprites/items/bundle_marigold.png` | `sprites/items/seed_marigold.png` | 9% |
| 3 | Bluebell | `sprites/items/plant_bluebell.png` | `sprites/items/bundle_bluebell.png` | `sprites/items/seed_bluebell.png` | 8% |
| 4 | Thornroot | `sprites/items/plant_thornroot.png` | `sprites/items/bundle_thornroot.png` | `sprites/items/seed_thornroot.png` | 7% |
| 5 | Sunpetal | `sprites/items/plant_sunpetal.png` | `sprites/items/bundle_sunpetal.png` | `sprites/items/seed_sunpetal.png` | 6% |
| 6 | Nightshade | `sprites/items/plant_nightshade.png` | `sprites/items/bundle_nightshade.png` | `sprites/items/seed_nightshade.png` | 5% |
| 7 | Frostbloom | `sprites/items/plant_frostbloom.png` | `sprites/items/bundle_frostbloom.png` | `sprites/items/seed_frostbloom.png` | 4% |
| 8 | Bloodcap | `sprites/items/plant_bloodcap.png` | `sprites/items/bundle_bloodcap.png` | `sprites/items/seed_bloodcap.png` | 3% |
| 9 | Voidlily | `sprites/items/plant_voidlily.png` | `sprites/items/bundle_voidlily.png` | `sprites/items/seed_voidlily.png` | 2% |
| 10 | Starmoss | `sprites/items/plant_starmoss.png` | `sprites/items/bundle_starmoss.png` | `sprites/items/seed_starmoss.png` | 1% |

What the pictures show:

- `plant_` files are the plants as picked. Nettle is a green sprig with jagged leaf pairs. Marigold is an orange many-petalled flower with a brown centre. Bluebell is an arching stem with three hanging blue bells. Thornroot is a forked brown root with pale thorns and a small sprout. Sunpetal is a pointed gold flower with sparkles. Nightshade is a bunch of dark purple berries with one purple flower. Frostbloom is a pale icy six-point crystal flower with frost sparkles. Bloodcap is a red mushroom with cream spots and a small one beside it. Voidlily is a near-black lily with a glowing purple spiral centre and wisps. Starmoss is a dark blue moss clump with yellow star specks.
- `bundle_` files are one shape for every tier: dried stems tied with twine, the leafy end in that tier's colour. Like the ingots, the higher tiers carry their plant's mark: sparkles (Sunpetal), berries (Nightshade), frost (Frostbloom), spots (Bloodcap), a spiral (Voidlily), stars (Starmoss).
- `seed_` files are the seeds, one different shape per plant, like the gems. Nettle: three olive teardrop seeds. Marigold: three long dark seeds with pale tips. Bluebell: a green pod split open on blue-black seeds, two loose beside it. Thornroot: a brown burr with pale spikes. Sunpetal: a big striped gold seed with sparkles. Nightshade: two glossy purple seeds. Frostbloom: a pale ice crystal with a blue core. Bloodcap: three red spore balls with cream specks (a mushroom has spores, not seeds). Voidlily: a dark oval seed with a glowing purple spiral. Starmoss: a dark blue spore ball with yellow stars.
- Tiers 5 to 10 reuse the colours of the same mining tiers (gold, dark purple, pale lilac, red, void purple, starry blue), so a colour means the same rarity in both activities.

The icons are drawn by `sprites/build_foraging_icons.lua` in Aseprite (`aseprite -b --script-param out=sprites/items --script sprites/build_foraging_icons.lua`), using the shared helpers in `sprites/pixel_icons.lua`. They can be hand-edited in Aseprite afterwards.

The whole table as one picture, in the layout of the mining sheet, is [`foraging-table.png`](foraging-table.png). It is drawn by `sprites/build_item_tables.lua` in Aseprite, the same as the hunting table.

#### Picking, drying and sickles (Decided, D-061 to D-066)

The user set these on 2026-10-21.

- **Energy:** picking a plant costs **5 energy** from the same 100-energy pool as mining. Every gathering skill shares that one pool (D-061).
- **Regrowth:** a picked plant grows back after **10 seconds**, like an ore vein (D-064).
- **Drying rack:** plants become 1 dried bundle of the same plant. It burns no fuel and costs no energy (D-062).
- **Seeds** are planted in **farming** to grow that plant (D-065). Farming is not designed yet.
- **Potions** are **short gathering boosts**, for example a higher gem or seed chance for a few minutes (D-066).

| Tier | Plant | Plants per bundle (D-062) | Sickle (D-063) | Sickle costs (same as that pickaxe) |
|---|---|---|---|---|
| 1 | Nettle | 2 | Stone | Nothing: every player starts with it |
| 2 | Marigold | 2 | Bronze | 5 Tin Ingot, 5 Copper Ingot, 1 Ash Wood Hilt |
| 3 | Bluebell | 3 | Iron | 5 Iron Ingot, 1 Ash Wood Hilt |
| 4 | Thornroot | 3 | Steel | 10 Iron Ingot, 1 Ash Wood Hilt |
| 5 | Sunpetal | 4 | Gold | 10 Gold Ingot, 1 Ash Wood Hilt |
| 6 | Nightshade | 4 | Obsidian | 10 Obsidian Ingot, 1 Oak Wood Hilt |
| 7 | Frostbloom | 5 | Titanite | 10 Titanite Ingot, 1 Oak Wood Hilt |
| 8 | Bloodcap | 5 | Dreadstone | 10 Dreadstone Ingot, 1 Oak Wood Hilt |
| 9 | Voidlily | 5 | Void | 10 Void Ingot, 1 Void Hilt |
| 10 | Starmoss | 5 | Stellarite | 10 Stellarite Ingot, 1 Cosmic Hilt |

A sickle picks its own tier's plant and every lower tier (D-024). Because sickles cost the same as pickaxes, a player who wants every pickaxe **and** every sickle needs about twice the ore: roughly 886 mines instead of 443 (worked out from the tables, not a decision). That gives mined ore a second big use.

**Not decided:** which potions exist, what each does, how long it lasts and which bundles it takes (D-066). What Impling food does, which waits on the skirmish design, because whether an Imp battles is still overview question 1. Which bundles are crafting ingredients, and for what. How farming works.

**Potions (Proposed, 2026-10-22).** A gathering boost per skill, as D-066 describes:

| Potion | Boosts | Bundles |
|---|---|---|
| Prospector's Draught | Mining: the gem chance | 3 bundles of one plant |
| Green Thumb Tonic | Foraging: the seed chance | 3 bundles |
| Tracker's Brew | Hunting: the trophy chance | 3 bundles |
| Woodsman's Draught | Lumbering: the sap chance | 3 bundles |
| Angler's Tonic | Fishing: the pearl chance | 3 bundles |

- **Strength by bundle tier.** A potion multiplies its rare chance by **1.1 + 0.05 × the bundle's tier**: ×1.15 from Nettle, up to ×1.6 from Starmoss. That gives every plant tier a use.
- **10 minutes**, real time. One potion per skill at a time, and drinking another replaces it.
- **Brewed at a cauldron** at the camp. It costs no energy, like every other station (D-056, D-062).
- **Limits (Proposed, to protect D-045 and D-076):** a potion **never** changes the mint token chance, never gives energy, and never makes an action faster. With the Stellarite pickaxe's ×2 (D-059), the gem chance is capped at **×2.5** in total.

**Impling food: Open question.** D-023 lists bundles for "Impling food". Since then, the Imp has become the trainer and tamed animals do the fighting (D-080), and cooked fish already feeds battle animals (D-111). So "Impling food" has no clear job. Two options:
- **A (Proposed):** dried bundles become **treats for tamed animals**, giving XP at half the rate of cooked fish of the same tier. Foraging then feeds the battle loop too. The item could keep the name "Impling food" or be renamed.
- **B:** Impling food is cosmetic. Feeding the Imp plays an emote and gives a short glow, with no stats.

This touches D-023, so the user decides.

### Hunting tiers (Decided, D-028 to D-035)

The user set the hunting rules on 2026-10-17 and asked Claude to name the animals and trophies (D-032). **Sixteen tiers**, lowest to highest. That is more than mining and foraging, which have ten each.

What hunting gives: a defeated animal goes **"poof"** in a cartoon way, drops its **hide** (the `hide_` picture) and respawns (D-028, D-029). Sometimes it also drops its **trophy** (D-031). A **tanning rack** turns hides into **leather** of the same tier (the `leather_` picture), the way the furnace turns ore into ingots (D-029). Animals can also be **tamed** (D-028), and a tamed animal **helps track** other animals (D-035).

Animals are hunted with **bows**, one per tier (D-030). A bow hunts its own tier and every lower tier, the same rule as pickaxes (D-034).

The **Trophy chance** is decided (D-033). The gem and seed ladder (10% falling 1% per tier) would go below zero before tier 16, so trophies start at 10% and fall 0.6% per tier, reaching 1% at tier 16.

| Tier | Animal | Hide picture | Leather picture | Trophy | Trophy picture | Trophy chance (D-033) |
|---|---|---|---|---|---|---|
| 1 | Hare | `sprites/items/hide_hare.png` | `sprites/items/leather_hare.png` | Lucky Foot | `sprites/items/trophy_lucky_foot.png` | 10.0% |
| 2 | Fox | `sprites/items/hide_fox.png` | `sprites/items/leather_fox.png` | Brush Tail | `sprites/items/trophy_brush_tail.png` | 9.4% |
| 3 | Boar | `sprites/items/hide_boar.png` | `sprites/items/leather_boar.png` | Boar Tusk | `sprites/items/trophy_boar_tusk.png` | 8.8% |
| 4 | Wolf | `sprites/items/hide_wolf.png` | `sprites/items/leather_wolf.png` | Wolf Fang | `sprites/items/trophy_wolf_fang.png` | 8.2% |
| 5 | Goldhorn Stag | `sprites/items/hide_goldhorn_stag.png` | `sprites/items/leather_goldhorn_stag.png` | Golden Antler | `sprites/items/trophy_golden_antler.png` | 7.6% |
| 6 | Shadowcat | `sprites/items/hide_shadowcat.png` | `sprites/items/leather_shadowcat.png` | Shadow Claw | `sprites/items/trophy_shadow_claw.png` | 7.0% |
| 7 | Frostmane Yeti | `sprites/items/hide_frostmane_yeti.png` | `sprites/items/leather_frostmane_yeti.png` | Frozen Heart | `sprites/items/trophy_frozen_heart.png` | 6.4% |
| 8 | Cinder Salamander | `sprites/items/hide_cinder_salamander.png` | `sprites/items/leather_cinder_salamander.png` | Ember Scale | `sprites/items/trophy_ember_scale.png` | 5.8% |
| 9 | Voidstalker | `sprites/items/hide_voidstalker.png` | `sprites/items/leather_voidstalker.png` | Void Eye | `sprites/items/trophy_void_eye.png` | 5.2% |
| 10 | Starwyrm | `sprites/items/hide_starwyrm.png` | `sprites/items/leather_starwyrm.png` | Star Horn | `sprites/items/trophy_star_horn.png` | 4.6% |
| 11 | Stormhorn Ram | `sprites/items/hide_stormhorn_ram.png` | `sprites/items/leather_stormhorn_ram.png` | Thunder Curl | `sprites/items/trophy_thunder_curl.png` | 4.0% |
| 12 | Tidecrest Serpent | `sprites/items/hide_tidecrest_serpent.png` | `sprites/items/leather_tidecrest_serpent.png` | Abyss Pearl | `sprites/items/trophy_abyss_pearl.png` | 3.4% |
| 13 | Mossmane Behemoth | `sprites/items/hide_mossmane_behemoth.png` | `sprites/items/leather_mossmane_behemoth.png` | Verdant Mane | `sprites/items/trophy_verdant_mane.png` | 2.8% |
| 14 | Crystalback Basilisk | `sprites/items/hide_crystalback_basilisk.png` | `sprites/items/leather_crystalback_basilisk.png` | Prism Shard | `sprites/items/trophy_prism_shard.png` | 2.2% |
| 15 | Sunfeather Griffin | `sprites/items/hide_sunfeather_griffin.png` | `sprites/items/leather_sunfeather_griffin.png` | Sun Feather | `sprites/items/trophy_sun_feather.png` | 1.6% |
| 16 | Eclipse Dragon | `sprites/items/hide_eclipse_dragon.png` | `sprites/items/leather_eclipse_dragon.png` | Eclipse Crown | `sprites/items/trophy_eclipse_crown.png` | 1.0% |

What the pictures show:

- `hide_` files are one stretched-pelt shape for every tier: four pointed legs, a head with ears and a tail, in the animal's colours. Fur hides have a ragged edge. Scaled animals (Cinder Salamander, Starwyrm, Tidecrest Serpent, Crystalback Basilisk, Eclipse Dragon) have rows of scales instead. Each carries its animal's mark: a pale belly (Hare, Fox, Wolf), a dark spine stripe (Boar), pale spots (Goldhorn Stag), glowing rosettes (Shadowcat), frost (Frostmane Yeti), glowing cracks (Cinder Salamander), a void spiral (Voidstalker), stars (Starwyrm), a lightning bolt (Stormhorn Ram), a pearly belly (Tidecrest Serpent), moss sprigs (Mossmane Behemoth), crystal spines (Crystalback Basilisk), a feather pattern (Sunfeather Griffin), an eclipse ring (Eclipse Dragon).
- `leather_` files are one rolled leather shape with a strap and gold buckle, recoloured per tier, like the ingots. Higher tiers carry the same marks as their hides.
- `trophy_` files are each their own shape, like the gems. Lucky Foot: a furry foot on a gold keyring. Brush Tail: a bushy orange tail with a white tip. Boar Tusk: a curved ivory tusk. Wolf Fang: a fang on a cord. Golden Antler: a branching gold antler. Shadow Claw: three dark claws with glowing edges. Frozen Heart: an ice-crystal heart. Ember Scale: a red scale with glowing cracks. Void Eye: a dark eye with a glowing purple iris and slit pupil. Star Horn: a ridged blue horn with stars. Thunder Curl: a curled grey ram's horn with a lightning bolt. Abyss Pearl: a pearl in an open teal shell. Verdant Mane: green mane strands in a gold clasp. Prism Shard: a cluster of pink crystals. Sun Feather: a pale gold feather. Eclipse Crown: a black and gold crown with a dark orb ringed in light.

The icons are drawn by `sprites/build_hunting_icons.lua` in Aseprite (`aseprite -b --script-param out=sprites/items --script sprites/build_hunting_icons.lua`). It shares its drawing helpers with the foraging script through `sprites/pixel_icons.lua`.

The whole table as one picture, in the layout of the mining sheet, is [`hunting-table.png`](hunting-table.png). It is drawn by `sprites/build_item_tables.lua` in Aseprite (`aseprite -b --script sprites/build_item_tables.lua`, which redraws every table picture), with the labels in a small pixel font (`sprites/pixel_font.lua`). Re-run it after changing an icon.

#### Hunting, tanning, bows and taming (Decided, D-067 to D-072)

The user set these on 2026-10-21.

- **The hunt:** walk up to an animal, press F, shoot **3 times**, and it goes poof. It costs **5 energy** from the shared pool. Animals don't run away or fight back. They respawn after **10 seconds** (D-067).
- **Tanning rack:** hides become 1 leather of the same animal. It burns no fuel and costs no energy (D-068).
- **Bows** are made from the leather of the tier below: 10 leather each. Everyone starts with the tier 1 bow (D-069). A bow hunts its own tier and every lower tier (D-034).
- **Arrows** are not used up (D-070).
- **Taming:** feed an animal a dried bundle of its tier. The bundle is used up either way. Every animal can be tamed. No energy. One tamed animal follows you at a time (D-071).
- **Tracking:** while a tamed animal follows you, trophy chances are ×1.5 for animals of its tier and below (D-072).

**Bow names are Proposed**: each bow is named after the animal it is made to hunt. The user asked Claude to propose them.

| Tier | Animal | Hides per leather (D-068) | Bow (Proposed name) | Bow costs (D-069) | Tame with, chance (D-071) | Trophy chance → with a tracker (D-033, D-072) |
|---|---|---|---|---|---|---|
| 1 | Hare | 2 | Hare Bow | Nothing: every player starts with it | Nettle bundle, 50% | 10% → 15% |
| 2 | Fox | 2 | Fox Bow | 10 Hare leather | Marigold bundle, 47% | 9.4% → 14.1% |
| 3 | Boar | 2 | Boar Bow | 10 Fox leather | Bluebell bundle, 44% | 8.8% → 13.2% |
| 4 | Wolf | 3 | Wolf Bow | 10 Boar leather | Thornroot bundle, 41% | 8.2% → 12.3% |
| 5 | Goldhorn Stag | 3 | Goldhorn Stag Bow | 10 Wolf leather | Sunpetal bundle, 38% | 7.6% → 11.4% |
| 6 | Shadowcat | 3 | Shadowcat Bow | 10 Goldhorn Stag leather | Nightshade bundle, 35% | 7% → 10.5% |
| 7 | Frostmane Yeti | 4 | Frostmane Yeti Bow | 10 Shadowcat leather | Frostbloom bundle, 32% | 6.4% → 9.6% |
| 8 | Cinder Salamander | 4 | Cinder Salamander Bow | 10 Frostmane Yeti leather | Bloodcap bundle, 29% | 5.8% → 8.7% |
| 9 | Voidstalker | 4 | Voidstalker Bow | 10 Cinder Salamander leather | Voidlily bundle, 26% | 5.2% → 7.8% |
| 10 | Starwyrm | 4 | Starwyrm Bow | 10 Voidstalker leather | Starmoss bundle, 23% | 4.6% → 6.9% |
| 11 | Stormhorn Ram | 5 | Stormhorn Ram Bow | 10 Starwyrm leather | Starmoss bundle, 20% | 4% → 6% |
| 12 | Tidecrest Serpent | 5 | Tidecrest Serpent Bow | 10 Stormhorn Ram leather | Starmoss bundle, 17% | 3.4% → 5.1% |
| 13 | Mossmane Behemoth | 5 | Mossmane Behemoth Bow | 10 Tidecrest Serpent leather | Starmoss bundle, 14% | 2.8% → 4.2% |
| 14 | Crystalback Basilisk | 5 | Crystalback Basilisk Bow | 10 Mossmane Behemoth leather | Starmoss bundle, 11% | 2.2% → 3.3% |
| 15 | Sunfeather Griffin | 5 | Sunfeather Griffin Bow | 10 Crystalback Basilisk leather | Starmoss bundle, 8% | 1.6% → 2.4% |
| 16 | Eclipse Dragon | 5 | Eclipse Dragon Bow | 10 Sunfeather Griffin leather | Starmoss bundle, 5% | 1% → 1.5% |

**What this costs a player** (worked out from the tables, not a decision): crafting all 15 bows takes **560 hunts**, about 28 energy resets if the player only hunted. All gathering shares one energy pool (D-061), so that time adds to mining and foraging. Taming a top animal is expensive on purpose: at 5%, an Eclipse Dragon takes 20 Starmoss bundles on average, which is 100 Starmoss picks.

**Decided since (D-103, D-104, D-095):** trophies go in a **trophy cabinet** on the player's profile, and a full set unlocks a cosmetic and a title. **Leather crafts cosmetic outfits** for the Imp, and Eclipse Dragon leather makes the top set. Tamed animals live in a **stable** of 6 slots to start, and they can't be traded (D-102).

**Not decided:** which outfits exist and what they cost in leather. Which trophy sets exist. Whether a tamed animal can be released.

### Lumbering tiers (Decided, D-105 to D-108)

The user set the lumbering rules on 2026-10-21 and asked Claude to name the trees and their rare drops (D-105, D-108). Ten tiers, like mining and foraging.

- **Chopping:** 5 energy per chop from the shared pool. A tree grows back after 10 seconds (D-105).
- **Axes** are metal, named like the pickaxes, and cost **half that pickaxe's ingots** plus its hilt (D-106). An axe chops its own tier and every lower tier (the D-011 rule). **Proposed:** halves are rounded up, so the Bronze axe takes 3 Tin and 3 Copper ingots.
- **Sawbench:** logs become planks, no energy (D-107).
- **Wood hilts:** the blacksmith makes an **Ash Wood Hilt from 5 Ash planks** and an **Oak Wood Hilt from 5 Oak planks**. The merchant stops selling wood hilts once lumbering is live (D-107).
- **Rare drop:** each tree has a sap or amber, at the gem chances (D-108).

| Tier | Tree | Logs per plank (D-107) | Axe (D-106) | Axe costs | Rare drop (D-108) | Chance |
|---|---|---|---|---|---|---|
| 1 | Ash | 2 | Stone | Nothing: every player starts with it | Ash Sap | 10% |
| 2 | Birch | 2 | Bronze | 3 Tin Ingot, 3 Copper Ingot, 1 Ash Wood Hilt | Birch Sap | 9% |
| 3 | Oak | 3 | Iron | 3 Iron Ingot, 1 Ash Wood Hilt | Oak Resin | 8% |
| 4 | Pine | 3 | Steel | 5 Iron Ingot, 1 Ash Wood Hilt | Pine Resin | 7% |
| 5 | Goldleaf | 4 | Gold | 5 Gold Ingot, 1 Ash Wood Hilt | Golden Amber | 6% |
| 6 | Ebony | 4 | Obsidian | 5 Obsidian Ingot, 1 Oak Wood Hilt | Ebony Amber | 5% |
| 7 | Silverbark | 5 | Titanite | 5 Titanite Ingot, 1 Oak Wood Hilt | Silver Amber | 4% |
| 8 | Bloodwood | 5 | Dreadstone | 5 Dreadstone Ingot, 1 Oak Wood Hilt | Blood Amber | 3% |
| 9 | Voidwood | 5 | Void | 5 Void Ingot, 1 Void Hilt | Void Amber | 2% |
| 10 | Starwood | 5 | Stellarite | 5 Stellarite Ingot, 1 Cosmic Hilt | Star Amber | 1% |

**Why Ash is tier 1 and Oak tier 3:** everyone starts with the free Stone axe, and the first crafted axe (Bronze) needs an Ash Wood Hilt. If Ash weren't tier 1, nobody could ever make it. Oak Wood Hilts are first needed for the Obsidian tools, and Oak can be chopped with the Iron axe, well before that.

Tiers 5 to 10 reuse the colours of the same mining tiers (gold, dark purple, pale lilac, red, void purple, starry blue), as foraging does.

**What this costs a player** (worked out from the tables, not a decision): every Ash and Oak hilt for the pickaxes, sickles and axes (12 Ash and 9 Oak) takes about **255 chops**. All ten axes add about 240 mines on top of the 886 for pickaxes and sickles.

**Icons (D-105):** `log_<tree>.png`, `plank_<tree>.png` and `sap_<tree>.png` in `sprites/items/` (for example `log_ash.png`). A log lies diagonally with its rings facing you, and has bark in that tree's colour (Birch has black marks). Planks are a stack of two. Saps are a glossy drop. Tiers 5 to 10 carry the same marks as foraging: sparkles, a purple glint, frost, spots, a spiral, stars.

### Fishing tiers (Decided, D-109 to D-112)

The user set the fishing rules on 2026-10-21 and asked Claude to name the fish and pearls (D-109, D-112). Ten tiers.

- **Cast and bite:** walk to water, press F to cast, then press F again when a fish bites, inside a short timing window. 5 energy per catch from the shared pool. A fishing spot refreshes after 10 seconds (D-109).
- **Rods** are made from planks: the rod for tier N costs **10 planks of tree tier N−1**. The first rod is free (D-110). A rod catches its own tier and every lower tier (the D-011 rule).
- **Campfire:** raw fish become cooked fish, burning logs as fuel (D-111).
- **Cooked fish is food for battle animals** (D-111). **Proposed:** it gives one animal XP (05-skirmish).
- **Rare drop:** each fish has a pearl, at the gem chances (D-112).

| Tier | Fish | Fish per cooked fish (D-111) | Logs burned per cooked fish (Proposed) | Rod (Proposed name) | Rod costs (D-110) | Pearl (D-112) | Chance |
|---|---|---|---|---|---|---|---|
| 1 | Minnow | 2 | 0 | Driftwood Rod | Nothing: every player starts with it | River Pearl | 10% |
| 2 | Perch | 2 | 0 | Ash Rod | 10 Ash planks | Sand Pearl | 9% |
| 3 | Trout | 3 | 0 | Birch Rod | 10 Birch planks | Moss Pearl | 8% |
| 4 | Catfish | 3 | 1 | Oak Rod | 10 Oak planks | Black Pearl | 7% |
| 5 | Goldfin Carp | 4 | 1 | Pine Rod | 10 Pine planks | Golden Pearl | 6% |
| 6 | Shadow Eel | 4 | 1 | Goldleaf Rod | 10 Goldleaf planks | Shadow Pearl | 5% |
| 7 | Frostscale Pike | 5 | 1 | Ebony Rod | 10 Ebony planks | Frost Pearl | 4% |
| 8 | Bloodfin Snapper | 5 | 2 | Silverbark Rod | 10 Silverbark planks | Blood Pearl | 3% |
| 9 | Void Angler | 5 | 2 | Bloodwood Rod | 10 Bloodwood planks | Void Pearl | 2% |
| 10 | Starfin Koi | 5 | 2 | Voidwood Rod | 10 Voidwood planks | Star Pearl | 1% |

**Logs burned (Proposed):** any kind of log, following the Coal pattern (D-055): none for tiers 1–3, 1 log for tiers 4–7 and 2 logs for tiers 8–10.

**What this costs a player** (worked out, not a decision): all nine crafted rods take about **330 chops** of logs for their planks. Starwood planks aren't used by any rod.

**Icons (D-109):** `fish_<fish>.png`, `cooked_<fish>.png` and `pearl_<pearl>.png` in `sprites/items/` (for example `fish_goldfin_carp.png`, `pearl_golden.png`). Each fish has its own body shape and details: Perch has bars, Trout a pink stripe, Catfish whiskers, Void Angler a glowing lure, Starfin Koi white patches. Cooked fish is the same fish, browned, with grill marks and steam. A pearl sits in an open shell.

All lumbering and fishing icons are drawn by `sprites/build_lumber_fishing_icons.lua` in Aseprite (`aseprite -b --script-param out=sprites/items --script sprites/build_lumber_fishing_icons.lua`), using the shared helpers in `sprites/pixel_icons.lua`.

### Currencies: IMP coins and mint tokens (Decided, D-039, D-040, D-042, D-073 to D-078)

| Currency | What it is | Where it comes from | What it's for | Stored |
|---|---|---|---|---|
| **IMP coins** | The in-game coin. Not a crypto token (D-039). | Staking Imps on impz.club, carried into the game (D-042); staking is finished for now (D-050). **Selling items to the merchant** (D-073). | Cosmetics, extra inventory space, energy refills and wood hilts (D-075). | The player's account in Supabase (D-043) |
| **Mint tokens** | A record on the player's account. Not a crypto token. | A **0.1%** chance on each gathering action, for Imp holders only (D-045, D-078). Mining only in phase one (D-040). Never from refilled energy (D-076). | Claiming a mint on impz.club: **1 token per mint** (D-040, D-078). | The player's account in Supabase (D-043) |

#### The merchant (Decided, D-073 to D-077)

The user set these on 2026-10-21.

**Selling (D-074).** The merchant buys every gathered item at a fixed price:

| Kind | Examples | Sell price |
|---|---|---|
| Raw | Ore, plants, hides | Base price × tier |
| Processed | Ingots, dried bundles, leather | The raw items it took, plus 25% |
| Rare drop | Gems, seeds, trophies | 10 × that tier's raw item |

The base price is **not decided**. It will be set once the size of the staked balances is known, so old coins and new coins are worth the same. Each skill uses its own tier number, so a tier 16 hide sells for more than tier 10 Stellarite ore.

**Buying (D-075).**

| Item | Rule | Price |
|---|---|---|
| Cosmetics | Tool skins, outfits, emotes and the like. They make no one stronger. | Not decided |
| Extra inventory space | One row of 6 slots at a time. Each row costs twice the last, up to a cap (D-077). | First row and cap not decided |
| Energy refill | Refills energy to 100. At most 1 per energy reset. Costs more than that energy could earn by selling. Actions on refilled energy never roll mint tokens (D-076). | Not decided |
| Ash Wood Hilt, Oak Wood Hilt | Sold until lumbering is live, then no longer (D-107). The merchant sells no other materials. | Not decided |

**Why the refill limits matter:** without them, coins would turn into extra gathering, and extra gathering into more coins and more mint token rolls. Big stakers and bots would then turn coins into NFT mints. With the limits, a refill is a convenience, not a loop. To keep that true, the refill price has to be checked again whenever sell prices change.

#### Prices (Proposed, 2026-10-22)

The user asked for real prices to be proposed in place of the build's TEST numbers. Only the base price waits on the staked balances. **Proposed:** every other price is a fixed multiple of the base price (**b**), so setting that one number later rescales the whole merchant at once and the D-076 rule can't break by accident.

| Price | Proposed | Why |
|---|---|---|
| Base price **b** | **1 coin** as the placeholder until the staked balances are known (the build uses 2, TEST). The final value is an **Open question**. | One number to set later. |
| What a full bar earns | Not a price, a check: 20 actions × tier × b × up to 1.25 (processed), plus rare drops. That is about **250 b** at tier 10 and about **450 b** at tier 16 hunting (16 b × 1.25 per hide, plus the Eclipse Crown at 1.5% with the best bow). | The ceiling the refill has to stay above (D-076). |
| Energy refill | **500 b** | Above the best bar in the game (about 450 b), so a refill never pays for itself by selling. Re-check if a skill gets a tier above 16. |
| Extra inventory row | **50 b**, then 100 b, 200 b, 400 b. **Cap: 4 rows** (the bag grows from 8 rows to 12). | Doubling (D-077). The cap keeps the bag a choice, not a coin sink with no end. |
| Extra stable slot | **The same series as rows:** 50 b, 100 b, 200 b, 400 b, cap 4 (6 slots grow to 10) | D-095 says slots are priced like inventory rows. |
| Ash Wood Hilt | **25 b** | About twice what its 5 Ash planks sell for (12.5 b), so making it yourself stays cheaper once lumbering is live (D-107). |
| Oak Wood Hilt | **110 b** | The same rule: 5 Oak planks sell for about 56 b (Oak is lumbering tier 3, 3 logs per plank). |
| Cosmetics | **100 b to 1,000 b**, by rarity | **Open question:** which cosmetics exist. They never make anyone stronger (D-075). |

**Coins per battle win** follow the rule in 05 (5 raw items of the opponent's tier) and so also scale with b.

**Proposed:** anything the merchant sells costs more than the merchant pays for it, so nothing can be bought and sold back for a profit.

**Mint tokens (D-078).** At 0.1%, a player who uses every action (40 a day) finds about 1 token every 25 days. One token claims one mint. How tokens are stored and spent is in [ACCOUNTS-AND-DATA.md](ACCOUNTS-AND-DATA.md#6-mint-tokens-decided-d-040-d-045-rules-proposed).

**Not decided:** the base sell price; the prices of cosmetics, inventory rows, refills and wood hilts; the inventory cap; which cosmetics exist; whether tools can be sold; whether players can trade with each other (the trade doc, 04).

How coins and tokens are stored and protected is **Proposed** in [ACCOUNTS-AND-DATA.md](ACCOUNTS-AND-DATA.md). The overview guardrail "one currency unless this doc proves otherwise" is in question: see the 2026-10-20 report.

### Prestige icons (not part of the mining table)

These six files were in the same folder. They are **not** ores, ingots or gems, and the user has not said what they are for. Do not attach them to a tier.

| File | What the picture is |
|---|---|
| `sprites/items/prestige_0.png` | Gold star medal with a red and blue ribbon |
| `sprites/items/prestige_1.png` | Red eye with a yellow slit pupil on a black winged shape |
| `sprites/items/prestige_2.png` | Green dragon head with yellow horns and spines |
| `sprites/items/prestige_3.png` | Red horned helmet with a dark visor |
| `sprites/items/prestige_4.png` | Gold beast face with a mane and an open mouth |
| `sprites/items/prestige_5.png` | Gold crown floating over a blue glowing ring |

## 4. Inputs & outputs
| Takes in | Gives out | Notes |
|---|---|---|
| Breaking one vein of any tier, and 5 energy | 1 ore of that tier (`nugget_` icon) in the inventory menu | **Decided** (D-005, D-007, D-008, D-010). The scene has a vein for every tier. Tin uses `models/tin_orevein.fbx` and Copper uses `models/copper_vein.glb`. Iron to Stellarite use the copper vein recoloured per tier: **test art** until each has its own model. |
| Breaking one vein of any tier | That tier's gem, sometimes | **Decided** (D-005, D-012). 10% for Tin down to 1% for Stellarite, rolled once per vein. |
| Mining any vein | Costs 5 energy | **Decided** (D-008). Energy max is 100. Below 5 energy nothing can be mined. Energy resets to 100 every 12 hours, at **00:00 and 12:00 UTC** for every player (D-009, D-057), with no slow refill. The build still uses the player's own clock and saves energy in the browser, until it is updated. |
| Time | A broken vein grows back after 10 seconds | **Decided** (D-007), for now. Applies to every vein. |
| The pickaxe named for that ore, or a stronger one | The right to mine that ore | **Decided** (D-006, D-011). Every player starts with Stone. |
| Ingots and one hilt, in the amounts in the pickaxe table | That crafted pickaxe, from the blacksmith | **Decided** (D-006, D-060). Stone has no craft cost. Crafting costs no energy (D-056). |
| Ingots and a gem, at the blacksmith | A Void Hilt or a Cosmic Hilt | **Decided** (D-058): 2 Void ingots + 1 Arcanium, or 2 Stellarite ingots + 1 Eclipsium. Ash Wood and Oak Wood hilts are made from 5 planks (D-107). The build supplies wood hilts for free as a test until lumbering is built. |
| Ore and Coal, at the furnace | 1 ingot of that metal | **Decided** (D-054, D-055, D-056): 2 to 5 ore per ingot by tier, Coal from Gold upward, no energy. See the smelting table. The build still uses the D-013 test recipe. |
| Picking one plant, and 5 energy from the shared pool | 1 plant of that tier, and sometimes its seed | **Decided** (D-022, D-025, D-061). The plant grows back after 10 seconds (D-064). |
| Plants, at the drying rack | 1 dried bundle of that plant | **Decided** (D-062): 2 to 5 plants by tier, no fuel, no energy. |
| Ingots and one hilt, at the blacksmith | A sickle | **Decided** (D-063): the same cost as the pickaxe of the same name. |
| Hunting one animal: 3 shots and 5 energy from the shared pool | 1 hide of that animal, and sometimes its trophy | **Decided** (D-028, D-031, D-067). The animal respawns after 10 seconds. |
| Hides, at the tanning rack | 1 leather of that animal | **Decided** (D-068): 2 to 5 hides by tier, no fuel, no energy. |
| 10 leather of the tier below | The next bow | **Decided** (D-069). |
| 1 dried bundle of the animal's tier | A chance to tame it (50% down to 5%) | **Decided** (D-071). The bundle is used up either way. No energy. |
| Any gathered item, sold to the merchant | IMP coins | **Decided** (D-073, D-074): base price × tier for raw items, +25% for processed, 10× for rare drops. The base price is **not decided**. |
| IMP coins, at the merchant | Cosmetics, inventory rows, an energy refill, wood hilts | **Decided** (D-075 to D-077). Prices **not decided**. A refill never rolls mint tokens. |
| Chopping one tree, and 5 energy from the shared pool | 1 log of that tier, and sometimes its sap | **Decided** (D-105, D-108). The tree grows back after 10 seconds. |
| Logs, at the sawbench | 1 plank of that tree | **Decided** (D-107): 2 to 5 logs by tier, no energy. |
| Catching one fish (cast and bite), and 5 energy | 1 raw fish of that tier, and sometimes its pearl | **Decided** (D-109, D-112). The spot refreshes after 10 seconds. |
| Raw fish and logs, at the campfire | 1 cooked fish | **Decided** (D-111): 2 to 5 fish by tier. Logs per cooked fish **Proposed**. |
| Ingots and a hilt / planks | An axe / a fishing rod | **Decided** (D-106, D-110). |
| A PvE battle win (first 10 per reset) | XP and coins | **Decided** (D-092, D-093). See 05. |
| Minigames | Coins, cosmetics, items capped per day | **Decided** (D-097, D-098). See 03. |
| Coins in a market sale or direct trade | 5% destroyed | **Decided** (D-100), a coin sink. See 04. |
| Coins | Extra stable slots | **Decided** (D-095), priced like inventory rows. |
| Leather | Cosmetic outfits | **Decided** (D-104). Recipes not decided. |
| Other blacksmithing, other crafting | Not decided | Still unset. |
| Any gathering action the server accepts, by an Imp holder | Sometimes, 1 mint token on the account | **Decided** (D-040, D-045, D-078): a 0.1% chance. Mining only in phase one. Never on refilled energy (D-076). |
| Staked IMP coins on impz.club, claimed once | That many IMP coins in the game | **Decided** (D-042). The claim method is **Proposed** in ACCOUNTS-AND-DATA, section 6. |

## 5. NFT touchpoints
*Where the NFT or the blockchain is involved, and where it deliberately isn't.*

- **Decided (D-040):** mint tokens found while gathering are spent on impz.club to claim NFT mints.
- **Decided (D-039):** IMP coins, ores, plants, hides and every other item stay in the game. None of them is on-chain.

## 6. Risks
*Abuse, balance or scope risks, and how we handle each.*

## 7. Smallest first version
*The least we could build to test whether this system is fun.*

## 8. Done when…
*The conditions for the user to sign this off. Agreed with the user.*

---

## Questions this doc must answer
1. Full list of resources and currencies, grouped by tier/rarity.
2. Source for each: which activity, game or skirmish reward creates it?
3. Sink for each: what spends or destroys it? Every resource needs at least one sink, or it inflates and becomes worthless.
4. Which resources are tradeable, and which are on-chain? (Depends on overview question 3.)
5. How many currencies? (Guardrail: one, unless this doc proves otherwise.)
6. How do we watch and rebalance the economy after launch?

## Pass history
| Pass | Change |
|---|---|
| 0 | Template created with the questions to answer. |
| User addition, 2026-10-12 | Mining tier table and `sprites/items/` catalog recorded (D-005). Status set to Draft. Smelt, blacksmith, craft and sell left unset on purpose. |
| User addition, 2026-10-12 | Pickaxe mine list and pickaxe craft costs recorded (D-006). Smelter recipes for ingots still unset. |
| User addition, 2026-10-12 | Copper mining reward, energy cost and 10-second respawn recorded (D-007). Built into the game as a test. |
| User addition, 2026-10-12 | 5 energy per mine for every ore, 12-hour energy reset, 6×8 inventory menu (D-008). |
| User addition, 2026-10-13 | Tin gives tin ore (D-010). A pickaxe mines its named ore and every ore below (D-011). Gem chance 10% down to 1% by tier (D-012). Test smelting and hilt values for the build (D-013). Stellarite ingot picture description corrected: it is a bar, not a chest. |
| User addition, 2026-10-16 | Mithril renamed Titanite, Adamantite renamed Dreadstone (D-020). File names still use `mithril` and `adamantite`. |
| User addition, 2026-10-17 | Foraging tier table and rules recorded (D-022 to D-026), with plant and bundle icons. |
| User addition, 2026-10-17 | Seed icons added to the foraging table (D-027). |
| User addition, 2026-10-17 | Hunting tier table and rules recorded (D-028 to D-032), 16 tiers, with hide, leather and trophy icons. |
| User addition, 2026-10-21 | Mining rules finished: ore per ingot by tier (D-054), Coal as furnace fuel (D-055), no energy for smelting or crafting (D-056), energy reset at 00:00 and 12:00 UTC (D-057), hilts (D-058), the Stellarite pickaxe doubles gem chances (D-059), the Titanite pickaxe takes Titanite ingots (D-060). Smelting section rewritten from test values to decided rules. |
| User addition, 2026-10-21 | Foraging mechanics: one energy pool, 5 per plant (D-061), plants per bundle (D-062), sickles (D-063), 10-second regrowth (D-064), seeds go to farming (D-065), potions are gathering boosts (D-066). Foraging rows added to Inputs & outputs. |
| User addition, 2026-10-21 | Hunting mechanics: 5 energy and 3 shots per animal, 10-second respawn (D-067), hides per leather (D-068), bows from the tier below's leather (D-069), arrows not used up (D-070), taming with bundles (D-071), tracking raises trophy chance ×1.5 (D-072). Bow names Proposed. Hunting rows added to Inputs & outputs. |
| User addition, 2026-10-21 | Economy: coins from selling to a merchant (D-073), sell prices by tier and kind (D-074), what coins buy (D-075), limits on energy refills (D-076), inventory rows that double in price (D-077), mint token chance 0.1% and 1 token per mint (D-078). Currencies section rewritten with a merchant subsection. |
| User additions, 2026-10-21 | Lumbering (D-105 to D-108) and fishing (D-109 to D-112) tier tables, with tree, sap, fish and pearl names by Claude. Wood hilts from planks (D-107). Trophy cabinet (D-103), leather outfits (D-104), stable (D-095). Inputs & outputs rows for lumbering, fishing, battles, minigames, trade and the stable. |
| User addition, 2026-10-17 | Trophy chance ladder (D-033), bows hunt lower tiers (D-034), tamed animals help track (D-035). |
| User addition, 2026-10-17 | Foraging table picture added (`foraging-table.png`). Both table pictures now come from `sprites/build_item_tables.lua`. |
| User addition, 2026-10-20 | Currencies section: IMP coins (D-039, D-042) and mint tokens (D-040, D-045). Two input and output rows. NFT touchpoints filled in. |
| User addition, 2026-10-22 | Prices Proposed as multiples of one base price (refill, rows, stable slots, wood hilts, cosmetics). Potions Proposed. Impling food raised as an Open question with two options. |
