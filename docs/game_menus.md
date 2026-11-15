# Game Menus

> Status: draft v1 · Owner: J00BA · Last updated: 2026-11-07
>
> A study of how survival, crafting and skilling games build their menus, and what Club Impz should take from them: the menu types, the layouts, how to make menus fast to use, and the art style. This doc must agree with `game_direction.md`. Where the two differ, `game_direction.md` wins until it is updated.
>
> Every rule here is labelled. **Decided** means it is already in `game_direction.md` or `DECISIONS.md`. **Proposed** is Claude's suggestion from the study, waiting for J00BA. **Open question** is not settled.

---

## 1. What the menus must agree with

These are already decided. Every menu in this doc follows them.

| Rule | Where it is decided |
| --- | --- |
| Menus, the HUD, inventory icons, titles, emblems and prestige icons are **2D**. The world is 3D. | `game_direction.md` section 4, D-015 |
| 2D art is **pixel art**, made in **Aseprite**. Item icons are **48×48 PNGs**. | `game_direction.md` section 10, D-015, `ART-DIRECTION.md` section 2 |
| No 3D renders as icons. Icons stay hand-made pixel art. | `ART-DIRECTION.md` section 2 |
| Floating text (name tags, "F Mine Tin", "+1 Iron ore") is UI and follows the 2D look. | `ART-DIRECTION.md` section 2 |
| The inventory is a **6-column, 8-row grid**. The top-left slots are for the selected tool. More space is bought **one row of 6 at a time**. | D-008, D-077 |
| The game runs **in the browser**, **desktop first**. The interface stays phone friendly so touch can be added later. | D-046, D-083 |
| The **player profile** has a left panel (name, level, prestige icon, imp, emblem, title) and four tabs: Stats, Trophies, Collection, Information. | `game_direction.md` section 9 |
| Players can chat in **both worlds**. There is no player-to-player trading. | `game_worlds.md` section 1, `game_direction.md` section 5 |

**What is built today** (from `godot-game/ui/`): a shared pixel UI kit (`ui_kit.gd`) that draws a dark panel with a bevelled gold frame and corner studs, recessed slots, raised buttons and shaded bars, all at 3 screen pixels per art pixel, in the **Pixelify Sans** font. The HUD (`hud.gd`) has a top-left box with the held tool, coins and energy, a key hint line ("I inventory · Q switch tool"), an interaction prompt with key caps at the bottom centre, and pickup lines above it. There are separate menus for the inventory, stations, the merchant, the stable, battles and the dig, and a profile panel for the account and wallet. Built keys: I (inventory), F (interact), Q (switch tool), T (tame).

---

## 2. The games studied

Each game below is read for the same four things: **layout**, **what works**, **what doesn't**, and **art style**. The last row of each table is what Club Impz should take from it.

### 2.1 Minecraft

The genre's baseline. Most players already know its menus, so copying its *controls* costs players nothing to learn.

| | |
| --- | --- |
| Layout | One inventory screen: 4 armour slots and an off-hand slot beside the character, a 2×2 crafting grid, a 27-slot backpack, and the **9-slot hotbar** at the bottom, repeated on the HUD. A crafting table opens a 3×3 grid on top of the same backpack. Every container (chest, furnace) opens **above** the player's own inventory, so the player's items are always in the same place. |
| HUD | Very small: crosshair, hotbar at the bottom centre, hearts and hunger just above it, an XP bar between them. Nothing else unless something changes. |
| What works | **Shift-click** moves a stack between the container and the inventory. **Number keys 1–9** over a slot swap that item into the hotbar. **Right-click** splits a stack, **drag** spreads it across slots, **double-click** gathers every matching item into one stack. The **recipe book** (a green book button beside the grid) lists recipes, has a "show craftable only" toggle and a search box, and clicking a recipe fills the grid for you. Item tooltips show the name on hover and nothing else until asked. The pause menu is short: Back to Game, Advancements, Statistics, Options, Save and Quit. |
| What doesn't | The 3×3 grid makes players remember recipes, which is why the recipe book had to be added later. No sort button. Tooltips hide stats unless advanced tooltips are on. |
| Art style | Flat grey panels with a 1-pixel light top-left edge and dark bottom-right edge, 16×16 item icons, one pixel font, a GUI scale setting that only allows **whole-number** scales so pixels never blur. |
| **Take for Club Impz** | The control set (shift-click, number keys, right-click split, double-click collect). Containers open above the player's inventory. A recipe list, not a recipe grid. Whole-number UI scaling. |

### 2.2 Valheim

The closest match to Club Impz's gather → process → craft loop at stations.

| | |
| --- | --- |
| Layout | Tab opens the inventory: an **8×4 grid** whose **top row is the hotbar** (keys 1–8), the character with armour slots, and carry weight. Standing at a station adds a **crafting panel** beside the inventory with **Craft** and **Upgrade** tabs, a recipe list on the left, and the selected item's picture, stats and **required materials with counts** on the right. Building uses the hammer: right-click opens a **build menu** with category tabs, and each piece shows its cost in a tooltip. |
| HUD | Health and stamina near the bottom; the stamina bar **only appears while it is draining**. A minimap top right with status-effect icons under it. The whole HUD can be hidden for screenshots. |
| What works | Crafting is **tied to standing at the station**, so the menu only shows what that station makes. Upgrade is a separate tab, not a separate recipe. Requirements show "have / need" so the player sees at a glance what is missing. Contextual bars keep the HUD clean. |
| What doesn't | No sort or quick-stack in the base game (the most common mods add them: Equipment and Quick Slots, Auga, Jatify UI, ZenUI). Weight plus 32 slots means constant inventory juggling. Chests have "Take all" but no "Store matching". |
| Art style | Dark, translucent panels over the world, carved wood and iron frames, a Norse runic-flavoured title font with a plain body font, muted gold highlights. Strong theme, but low contrast in places. |
| **Take for Club Impz** | The station panel: recipe list left, selected item and "have / need" right, Craft and Upgrade as tabs. Contextual HUD bars. A hide-HUD key. Add sort and store-matching from day one, since players mod them in anyway. |

### 2.3 Hytale

Hytale is a direct reference for Club Impz's world style (`game_worlds.md` section 2). Early access launched on 13 January 2026.

| | |
| --- | --- |
| Layout | Reviewers note the inventory is close to Minecraft's: a **9-slot hotbar along the bottom** with a utility (shield) slot to its left, and chests look the same as the player inventory. Crafting happens at many separate benches (workbench, furniture bench, anvil, tanning rack, armourer's bench, builder's bench, furnace, campfire and more), and benches are upgraded to unlock recipes. |
| What works | **Chests placed next to a workbench feed its recipe list**, so players don't carry materials to craft. Known recipes are listed at the bench. The 2018 UI blog said the team wanted crafting and processing **inside the inventory screen** for quick gear changes, and tooltips that **compare gear** so players can judge it on the spot. The engine splits UI into three kinds: **windows** (item grids: containers, benches), **pages** (dialogs, shops, settings) and the **HUD** (always on: health, hotbar, compass). |
| What doesn't | Kotaku counted eight stations in two hours, each one big, so the "chests next to the bench" idea breaks when the benches don't fit beside the chests. Too many stations means too many menus. |
| Art style | Clean dark panels, item icons drawn to match the voxel models, readable text over a colourful world. |
| **Take for Club Impz** | Stations read from nearby storage. Tooltips compare an item with the one equipped. The windows / pages / HUD split as a way to organise our UI code. Keep the station count low. |

### 2.4 RuneScape: Dragonwilds

The other half of Club Impz's world style (`game_worlds.md` section 2), and from the RuneScape family the game's grind is modelled on.

| | |
| --- | --- |
| Layout | The HUD on first spawn: hydration, sustenance and rest icons **bottom left**, health and stamina bars **bottom middle**, the hotbar **top right**, a compass **top middle**, a sundial for the time of day **top right**, an aiming reticle in the centre, and a **quick action bar bottom right** that shows the key for each menu: Chat (Enter), Map (M), Quests (Q), Build (B), Inventory (Tab). Keys can be rebound. |
| Inventory | Drag to move. The stack count sits bottom right of each slot. Small **corner badges** mark special items (container, blueprint, drink, quest item). Stack limits are 1, 25, 50, 99 or 999. A **weight bar** turns red past 400, and the player walks slower. |
| Crafting | Two kinds of station. **Recipe benches** (Blacksmith's Bench, Rune Altar) list unlocked recipes and craft them. **Processing stations** (Furnace, Loom, Sawmill) take raw items by hand. A chest marked **Linked** lets every bench within about 12 metres use its contents, and a **golden particle trail** shows a station is in range. |
| Other menus | A build menu (B) with structure categories. A quick spells menu holding 12 spells, filled by dragging from the main spell book once the skill level is met. A map with up to 100 pins and right-click markers for ores, plants, trees and bases. |
| What doesn't | Reviewers report menus that respond late on controllers and feel sluggish when the host lags, and one menu that froze. |
| Art style | RuneScape fantasy: warm, painted, readable icons over a stylised world. |
| **Take for Club Impz** | The quick action bar that **shows the key** for each menu, which teaches the keys for free. Corner badges on slots. The recipe bench vs processing station split (our furnace is a processing station, the anvil is a recipe bench). Linked storage with a visible "in range" cue. Menus must respond instantly even with a slow connection (section 4.4). |

### 2.5 Old School RuneScape

Not on the brief's list, but `game_direction.md` names RuneScape as the model for the grind, and its skilling menus are the most tested in the genre.

| | |
| --- | --- |
| Layout | A fixed **side panel with icon tabs**: inventory (**28 slots, 4×7**), equipment, skills, quests, prayer, magic, friends, settings. A minimap with small **orbs** for health, prayer, run energy and special attack. The chat box is bottom left. |
| What works | The **skills tab** is a grid of every skill with its level; hovering shows XP and XP to the next level. **Left-click does the most likely action** and right-click opens a list of every action, with "Examine" always last. **XP drops** float up from the minimap when XP is earned. The bank has **tabs, search and placeholders** (an empty slot that remembers an item's spot). |
| **Take for Club Impz** | The skills grid with hover detail for the Stats tab. Left-click default, right-click for more. XP drops. Placeholders if a bank or storage is added. The orb idea for energy. |

### 2.6 Stardew Valley

The best reference for **pixel-art menus** that feel warm and are fast to use.

| | |
| --- | --- |
| Layout | One **game menu with tabs along the top**: Inventory, Skills, Social, Map, Crafting, Animals, Powers, Collections, Options, Exit. The toolbar holds 12 items; the backpack grows from 12 to 24 to 36 slots, bought in steps. |
| What works | Every big menu is a tab in **one window**, so there is one key to learn and one place to look. Crafting greys out what can't be made and shows the recipe on hover. An **Organize** button sorts. A trash can sits beside the grid. Bought backpack space is the same idea as D-077's bought rows. |
| Art style | Warm wooden frames with a light inner bevel, cream parchment backgrounds, a chunky pixel font with a dark shadow, every icon at the same pixel scale. |
| **Take for Club Impz** | One tabbed game menu. A sort button. Uncraftable recipes greyed but visible, so players see what to work towards. |

### 2.7 Terraria

| | |
| --- | --- |
| What works | The crafting list only shows recipes the player **can make right now with the stations nearby**, so the list is always short. **Quick stack to nearby chests** sends every item that already has a home into the right chest in one click. **Favourite** an item (Alt-click) and sort and quick stack leave it alone. |
| **Take for Club Impz** | Quick stack to storage. Favourite (lock) slots so sorting never moves a player's tools or a prized gem. |

### 2.8 Club Penguin

Not a survival game, but `game_direction.md` names it as the model for the hub, and its menus are built for social play.

| | |
| --- | --- |
| What works | One **toolbar along the bottom** with the chat box, emotes, actions, the map and the player's own card. **Clicking another player opens their player card**, with their outfit and buttons to add them as a friend. The **map** is a picture of the island that teleports you on click. |
| **Take for Club Impz** | Click a player to open their profile card (`game_direction.md` section 9). An emote wheel next to chat. A picture map for travel in the hub. |

---

## 3. The menu set for Club Impz

These are the menus the study says Club Impz needs, built from the patterns above. Keys are **Proposed**. Keys already used by the build are marked *(built)*.

| Menu | Opens with | What it holds | Pattern from | Status |
| --- | --- | --- | --- | --- |
| Title screen | On load | Play, Settings, Log in / Account, Credits. The 3D hub slowly turning behind it. | Minecraft panorama | Proposed |
| HUD | Always | See section 3.1 | Minecraft, Valheim, Dragonwilds | Partly built |
| Game menu | Esc | Resume, Settings, Help (controls), Log out. The game **does not pause**: it is an MMO. | Minecraft pause, Valheim | Proposed |
| Inventory | I *(built)* | The 6×8 grid (D-008), bought rows (D-077), tool slots top left, sort, trash, the imp with equipped gear | Minecraft, Stardew | Built, layout Proposed |
| Station window | F at a station *(built)* | Processing (furnace): input, fuel, output, progress. Recipe (anvil, workbench): see section 3.2. Always opens beside the inventory. | Valheim, Dragonwilds | Built, layout Proposed |
| Merchant | F at the merchant *(built)* | Buy and Sell tabs, coin total, sell-all-of-this-kind | Stardew | Built, layout Proposed |
| Profile | P | Left panel and the four tabs from `game_direction.md` section 9. The same card opens when clicking another player. | Club Penguin, OSRS skills tab | Partly built (account and wallet panel); tabs Proposed |
| Skills | K, or the profile's Stats tab | Five skills, levels, XP to next level on hover, the skill tree for the selected skill | OSRS | Open question (separate key or tab only) |
| Challenges | J | Active challenges, progress bars, the trophy each one gives | Dragonwilds quests | Proposed |
| Map | M | Hub: picture map with landmarks. Resource world: biomes, where the player is, pins. | Club Penguin, Dragonwilds | Proposed |
| Chat | Enter | Chat box bottom left, fades when idle, emote wheel button | Club Penguin, OSRS | Proposed |
| Character customizer | C | Body, Head, Eyes, Clothing and Back tabs, a turning 3D preview of the Imp, and the builds saved on impz.club. See section 3.5. | impz.club Imp Customization, Minecraft skin screen | Built (prototype), layout Proposed |
| Settings | From title or game menu | See section 3.4 | All | Proposed |

### 3.1 HUD layout (Proposed)

The HUD is the menu players look at most. Keep it to what the player needs **right now**, and put each thing where the genre has trained players to look.

```
┌──────────────────────────────────────────────────────────────┐
│ [tool] Stone pickaxe   ◉ 1,240   Lv 12 ★2       (compass)  [minimap]│
│        ⚡ ████████░░ 80/100                                         │
│                                                                    │
│                                                                    │
│                            ·                                       │
│                                                     +1 Tin ore     │
│                                                     +12 Mining XP  │
│ [chat, fades]                [F] Mine Tin                          │
│                        ▓▓▓▓▓▓▓▓░░░░ 62%            [I][M][J][P]   │
└──────────────────────────────────────────────────────────────┘
```

| Area | Holds | Why |
| --- | --- | --- |
| Top left | Held tool, coins, player level and prestige icon, energy bar | Already built there. Status lives top left in OSRS and our build. |
| Top right | Minimap or compass (resource world only) | Valheim, Dragonwilds and OSRS all put it here. |
| Centre | A small dot crosshair, only if the camera needs aiming | Minecraft, Dragonwilds |
| Bottom centre | The interaction prompt with its key cap, and the **gather progress bar** (`resource_gathering.md` section 2) | Built prompt. The bar sits under the prompt so the eye doesn't move. |
| Right, above the bar | Pickup lines and **XP drops** stacking upwards, fading after 3 seconds. Rare drops (gems, mint tokens) in gold with a sound. | OSRS XP drops, built pickup lines |
| Bottom left | Chat, fading to transparent when idle | OSRS, Club Penguin |
| Bottom right | **Quick action bar** of menu buttons, each showing its key | Dragonwilds. Doubles as touch buttons later (D-083). |

HUD rules (Proposed):

- **Show it only when it changes.** Like Valheim's stamina bar, the energy bar can shrink to an icon and number when full, and grow when it drops.
- **The hub HUD is lighter.** No minimap or gather bar in the hub; chat and the quick action bar stay.
- **One key hides the whole HUD** for screenshots (players show off in a social game).
- **Never cover the centre third** of the screen with HUD.

### 3.2 Station and crafting window (Proposed)

The window players will use most after the inventory. Built from Valheim's station panel and the Dragonwilds bench split.

```
┌───────────── Anvil ─────────────┐ ┌──────── Inventory ────────┐
│ [Craft] [Upgrade]   🔍 search    │ │ [tool][tool][  ][  ][  ][  ]│
│ ☐ Show craftable only            │ │ [  ][  ][  ][  ][  ][  ]    │
│ ▸ Pickaxes                       │ │ ...                         │
│   ■ Stone pickaxe        ✓       │ │                             │
│   ■ Bronze pickaxe       ✓       │ │  [Sort]   [Store matching]  │
│   ■ Iron pickaxe   (Mining 15) 🔒│ └─────────────────────────────┘
│ ▸ Axes                           │
│ ─────────────────────────────── │
│ [ big icon ]  Bronze pickaxe     │
│  Gathers up to T4. Faster on T1–T3│
│  Tin ingot     3 / 2   ✓         │
│  Copper ingot  1 / 2   ✗         │
│  [ Craft ]  [ Craft ×5 ]         │
└──────────────────────────────────┘
```

- **Recipe list left, details right.** Categories collapse. The list is short because each station only lists its own recipes.
- **Three recipe states, three looks.** Can craft: full colour with a tick. Missing materials: full colour, the missing rows in red. Locked by skill level: greyed with a lock and the level needed ("Mining 15"), so players see what to work towards (Stardew, Valheim).
- **"Have / need" on every material**, coloured green or red.
- **Craft one, or craft many.** A ×5 or "Craft all" button, and hold-to-repeat on the Craft button, so processing 40 ore is not 40 clicks.
- **The inventory is open beside it**, in the same place as always, with sort and store-matching.
- **Linked storage** (if storage chests are added): the station reads materials from chests in range and the window says "using 3 chests nearby". Open question, since storage is not designed.

### 3.3 Inventory (Proposed, on top of D-008 and D-077)

- The grid stays **6 × 8** (D-008). Bought rows (D-077) appear under it, and the grid scrolls (as built).
- **Locked rows are shown greyed**, with a coin price on the next row to buy. The player sees the upgrade without opening the merchant.
- **Sort** button (by kind, then tier, then count). **Favourite / lock** a slot with Alt-click so sorting leaves it alone (Terraria).
- **Shift-click** moves a stack to the open station, merchant or storage. **Number keys** over a slot put that tool in hand. **Right-click** splits. **Double-click** collects matching items (Minecraft).
- **Count bottom right, badge top right** (Dragonwilds): a small gem dot on gems, a token mark on mint tokens, an "N" on items picked up since the inventory was last opened.
- **Tooltips** (section 4.3).

### 3.4 Settings (Proposed)

Tabs: **Display, Audio, Controls, Interface, Account.**

| Tab | Must have |
| --- | --- |
| Display | Fullscreen toggle, quality preset (low for weak laptops, since it runs in a browser), view distance, FPS cap |
| Audio | Master, music, effects, UI sounds, ambient, each a slider |
| Controls | Every key rebindable, mouse sensitivity, invert Y, a "reset to default" button |
| Interface | **UI scale in whole steps only (×2, ×3, ×4)**, chat opacity, hide-HUD key, show/hide key hints, colour-blind friendly rarity colours |
| Account | Username, linked wallet (D-041), log out |

Settings **save to the account** (Supabase) so they follow the player between browsers. Open question: whether that is wanted or local storage is enough.

### 3.5 Character customizer (Proposed, following `game_direction.md` section 2)

The in-game version of the **Imp Customization** page on impz.club (`/imp-customization`). Both use the same trait models (`godot-game/assets/models/impz/`) and the same trait ids (`<slot>_<name>`, e.g. `head_afro`), so a look built on the website loads in the game and the other way round.

**Who gets what (Decided, `game_direction.md` section 2).** Every player gets the **base imp** (Green body, no traits). An Imp holder unlocks each trait of every Imp they own as a cosmetic, to mix and match. A non-holder can never wear a trait.

**Layout (Proposed).** One modal window, the same frame as every other menu (section 5.2):

```
┌ Customize your Imp ──────────────────────────────── [Close] ┐
│ [Body][Head][Eyes][Clothing][Back][Saved]  │                 │
│ ┌────────────────────────────────────────┐ │   (3D Imp,      │
│ │ ● Green                         wearing│ │    turning)     │
│ │   Blue                                 │ │                 │
│ │   Gold                         🔒 locked│ │                 │
│ │   ...                                  │ │ drag to turn,   │
│ └────────────────────────────────────────┘ │ wheel to zoom   │
│ 0x12…ab · 3 Impz · traits from your Impz    │ [Spin]          │
│ [Random] [Reset]                  [Cancel] [Wear it]          │
└──────────────────────────────────────────────────────────────┘
```

- **Tabs:** Body, Head, Eyes, Clothing, Back (the five model slots), then **Saved**. Head, Eyes, Clothing and Back have a **None** row at the top. Body has no None.
- **Rows** are text only, like the website (J00BA's choice for the website menu, 2026-11-06). The worn trait is marked, and locked traits are greyed with a lock, so players can see what other Impz would unlock.
- **Preview:** the Imp in a turning 3D view on the right. Drag turns it, the wheel zooms, and a Spin button stops or starts the turning. Every change shows at once.
- **Wear it** puts the look on the player's Imp and saves it. **Cancel**, Esc or C closes and keeps the old look. **Random** picks from unlocked traits only. **Reset** goes back to the base imp.
- **Saved:** the builds the wallet saved on impz.club, each with **Load**. Saving a new build stays on the website for now, because it needs a wallet signature (Open question below).
- **Eyes:** pupil colours (Red, Gold, Purple, Ghostly) are a texture painted over the body's face. Eyewear (Shades, 3D Glasses, ...) is a model over the face and brings its own pupil colour, as on the website.
- **The player can't move** while the window is open, like every modal.

**Ownership (Proposed).** When a wallet is linked (the Profile panel), the game asks impz.club (`/api/imps?wallet=`) which Impz the wallet holds and which traits they give. The website reads that from the Imp contract on the server, never from the browser. If the wallet no longer holds an Imp, its traits lock again and the worn look falls back to the base imp for those slots.

**Test switch (labelled TEST).** Debug builds have an **"All traits (TEST)"** toggle so the customizer can be tried without a wallet. Release builds never show it.

Open questions for the customizer:

1. Should the worn look also **save to the account** (Supabase `saved_imps` or the profile), so it follows the player between browsers? Today it is saved on this device only (`user://save.json`).
2. Should **saving a build** be possible in the game, with a wallet signature as on the website?
3. The web build calls `impz.club/api/imps` from another site, so that API needs a **CORS** header allowing the game's site before ownership works in the browser build.
4. Does the **NFT skin** (D-038, play as your own Imp exactly as minted) become a one-click "Wear my Imp #123" row in the Saved tab?

---

## 4. Rules for fast menus (Proposed)

The patterns every studied game shares, or that players add with mods when a game leaves them out.

### 4.1 Opening and closing

- **One key opens a menu and the same key closes it.** Esc closes any menu. Opening a menu over another replaces it; there is never a stack of three windows.
- **Browser catch:** in a web build, the browser uses **Esc to release the mouse** and leave fullscreen. So Esc should close the top menu first, and the game menu should only open on Esc when no menu is open. Never bind browser shortcuts (Ctrl+W, Ctrl+T, Ctrl+N, F5, F11 for anything but fullscreen).
- **Show the key on every button** (Dragonwilds quick bar), so players learn keys by looking.
- **The world keeps running** behind every menu (it is an MMO), so menus are see-through at the edges and never black out the screen.

### 4.2 Moving items

- Every action that takes a drag also has a **one-click** way: shift-click to move, a button to sort, a button to store matching (Minecraft, Terraria).
- **Bulk actions:** sell all of one kind, craft ×5 / all, take all from a container.
- **Undo the risky ones:** selling and deleting ask once, or have a short "undo" on the pickup line. Rare items (gems, mint tokens) always ask.

### 4.3 Tooltips

- Appear after **about 0.3 seconds** of hover, beside the cursor, never covering the slot.
- **Order:** name (coloured by rarity or tier) → kind and tier ("T4 Ore") → one line of what it does → numbers → sell price → where it comes from.
- **Compare:** a tool's tooltip shows how it differs from the held tool ("+20% speed", "gathers T5") in green or red (Hytale blog).
- Hold Shift for more detail (gem chance, XP per gather). Keep the short tooltip short.

### 4.4 Responsiveness

- **Every click answers in the same frame**: a press sound and the button's pressed look, even while the server confirms. If the server says no, the item snaps back with a short message. Dragonwilds' laggy menus are the warning.
- Menus never wait on a download to open. Icons are loaded once at start.

### 4.5 Keyboard, mouse and touch

- Desktop first (D-083): keyboard and mouse are the main controls.
- **Touch friendly from the start:** slots and buttons at least **44 screen pixels**, no action that only works on hover, the quick action bar works as on-screen buttons. A phone layout later needs no redesign, just bigger scale.
- Controller support is not planned. Open question.

---

## 5. Art style for the menus

### 5.1 What the studied games share

- **The frame carries the theme, the inside stays plain.** Valheim's carved wood, Stardew's wooden boards, Minecraft's grey bevel: all put style in the border and keep the background calm so icons read.
- **One light direction.** Light edge top left, dark edge bottom right, on every frame, slot and button. Raised things (buttons) are light on top; sunken things (slots) are dark on top.
- **Two fonts at most**: a characterful one for titles, a plain readable one for body text and numbers.
- **One pixel scale** for every piece of art on screen. Mixing a 2× icon with a 3× frame is what makes pixel UI look cheap.
- **Colour means something.** Rarity and tier colours, green for "can", red for "can't", gold for rare, used the same way in every menu.

### 5.2 The Club Impz menu look (Proposed)

The built UI kit is already close to the best references. The proposal is to keep it and write its rules down so new menus match.

| Part | Rule | Today in `ui_kit.gd` |
| --- | --- | --- |
| Panels | Dark blue-black fill, a bevelled **gold frame** with a **corner stud** in each corner, a dark outline outside | Built (`panel`) |
| Small boxes | The same frame, thinner, no studs, for the HUD and pickup lines | Built (`panel(small)`) |
| Slots | Recessed: dark at top and left, light at bottom and right. The held tool's slot gets a thicker gold rim. | Built (`slot`) |
| Buttons | Raised with a lip that disappears when pressed. Three states: normal, hover (lighter), pressed (no lip). Add a **disabled** look (greyed, no lip). | Built except disabled |
| Bars | Recessed track with a shaded fill; energy yellow, gather progress white or the skill's colour | Built (`bar`) |
| Font | **Pixelify Sans** (SIL Open Font Licence) for everything. Titles in gold with a 2-pixel dark drop shadow. Font sizes only in steps that land on whole pixels. | Built |
| Icons | 48×48 hand-made pixel art (D-015), shown at **1× or 2×**, never in between | Partly. Inventory slots are 52 px with the icon stretched to fit; check the icon is drawn at 48 px, not scaled |
| Pixel scale | Every frame, slot and button drawn at **3 screen pixels per art pixel**; whole-number UI scale only | Built (`PX := 3`) |
| Filtering | Nearest filter on all UI textures, never on 3D world textures (`ART-DIRECTION.md` section 2) | Built |

Colour roles (Proposed, matching the built constants):

| Role | Colour | Use |
| --- | --- | --- |
| Frame metal | Gold `#c99a4a` | Panel frames, held-tool rim |
| Panel fill | Dark blue-black, 96% opaque | Every window |
| Text | Off-white | Body text |
| Muted text | Warm grey | Key hints, secondary lines |
| Good / can | Soft green | "Have / need" met, upgrades in tooltips |
| Short / can't | Soft red | Missing materials, downgrades |
| Rare | Bright gold | Gems, mint tokens, rare drops |
| Energy | Amber | Energy bar and bolt icon |

- **Tier colours:** each resource tier T1–T10 gets one colour, taken from its icon (the same "icon is the source of truth" rule as `ART-DIRECTION.md`), used for the item name in tooltips and a thin slot rim. Open question: J00BA to approve the ten colours once drawn.
- **Hub vs resource world:** same kit in both. Open question: whether the hub's menus get a lighter, more playful frame (Club Penguin feel) while the resource world keeps the gold metal frame.
- **Motion:** menus open with a quick scale from 95% to 100% and fade (about 0.1 seconds), slots bounce a pixel when an item lands, rare drops shine once. Nothing slower than 0.2 seconds, so fast players never wait.
- **Sound:** a soft click for buttons, a pickup pop, a heavier sound for crafting, a sparkle for rare items. Every sound has its own slider (section 3.4).

### 5.3 What to avoid

- Blurry pixels from non-whole scaling or linear filtering.
- 3D renders or screenshots used as icons (`ART-DIRECTION.md`).
- Photo textures or gradients that aren't drawn as pixels.
- Walls of text. If a menu needs a paragraph to explain, the layout is wrong.
- Too many stations, each with its own menu (Hytale's problem). Group recipes by station kind instead.

---

## 6. Open questions

1. Is **Skills** its own key, or only the profile's Stats tab?
2. Do settings **save to the account** or only in the browser?
3. Do hub menus get a **lighter frame** than the resource world?
4. Will there be **storage chests**, and do stations read from them (linked storage)?
5. Is a **minimap** wanted in the resource world, or only a compass?
6. Is **controller** support ever planned?
7. Which keys are final? The table in section 3 is a proposal; the build already uses I, F, Q, T and C (customizer).
8. The character customizer's own questions are listed at the end of section 3.5.

---

## 7. Sources

- Minecraft inventory and controls: [Minecraft Wiki, Inventory](https://breezewiki.discard.no/minecraft/wiki/Inventory)
- Valheim menus redesign study: [asgamedesign, Valheim Menus](https://asgamedesign.blogspot.com/2021/03/valheim-menus.html)
- Valheim UI mods (what players add): [Jatify UI](https://thunderstore.io/c/valheim/p/Jatify/JatifyUI/), [Auga](https://new.thunderstore.io/c/valheim/p/RandyKnapp/Auga/v/1.1.3/), [ZenUI](https://thunderstore.io/c/valheim/p/ZenDragon/ZenUI/changelog)
- Hytale UI goals: [A sneak peek at Hytale's user interface (2018)](https://hytale.com/news/2018/12/a-sneak-peek-at-hytale-s-user-interface)
- Hytale early access crafting and inventory: [Kotaku](https://kotaku.com/hytale-minecraft-hypixel-crafting-workbench-quests-2000660135), [Hytale is finally here](https://hytale.com/news/2026/1/hytale-is-finally-here)
- Hytale UI structure (windows, pages, HUD): [Hytale GUI docs](https://hytale-docs.pages.dev/gui)
- Dragonwilds HUD and inventory: [Dragonwilds Wiki, Interface](https://dragonwilds.runescape.wiki/w/Interface)
- Dragonwilds stations and linked chests: [All Things How](https://allthings.how/runescape-dragonwilds-how-linked-chests-and-crafting-stations-work/)
- Dragonwilds menu responsiveness: [TheSixthAxis review](https://www.thesixthaxis.com/2026/10/05/runescape-dragonwilds-review/)
- Stardew Valley inventory: [Stardew Valley Wiki, Inventory](https://stardewvalleywiki.com/Inventory)
- Old School RuneScape, Terraria and Club Penguin rows are from Claude's knowledge of those games, not a source checked in this pass.
