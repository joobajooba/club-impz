# Update Posters

> Status: draft v1 · Owner: J00BA · Last updated: 2026-11-17
>
> How Claude makes a PNG **update poster** for Club Impz: a one-image summary of what a game update adds (new biomes, items, tools, Impz cosmetics, events), the kind of roadmap poster big games post for a new season. Any prompt that asks for a poster follows this doc exactly.
>
> This doc must agree with `game_direction.md`, `game_menus.md` (section 5, the menu look) and `ART-DIRECTION.md` (section 2, 2D vs 3D). Where they differ, `game_direction.md` wins.
>
> Labels: **Decided** means J00BA asked for it (2026-11-17, the request for this doc) or it is already decided in another doc. **Proposed** is Claude's suggestion, waiting for J00BA. **Open question** is not settled.

---

## 1. What a poster is

| Rule | Label |
| --- | --- |
| A poster is **one PNG** that shows what an update adds. It is made by a Claude prompt, from code, with no paid or outside art. | Decided |
| **Layout and styling** follow the big-studio season roadmap poster: a big title and date, hero characters on one side, a grid of labelled picture tiles grouped under section headers, timing tags on tiles. | Decided |
| **The art** follows the game's **2D pixel-art menu look** (`game_menus.md` section 5.2), not the painted or photo look of the reference posters. | Decided |
| Posters are **simple, engaging and fun**: few words, big pictures, bright accents, one glance tells you what is new. | Decided |
| Copy **only the layout pattern** from the reference posters. Never copy their logos, names, characters, art, fonts, slogans or rating boxes. Every picture on a poster is Club Impz's own art. | Decided |
| A poster only shows content that is **built, in a staging PR, or decided** in the docs. Never invent a feature, item, biome or date to fill a tile. If something is planned but not decided, it does not go on the poster unless J00BA names it in the prompt. | Proposed (follows `docs/CLAUDE.md`: never present a guess as a decision) |

---

## 2. Read before making a poster

1. This doc, all of it.
2. `game_menus.md` section 5 (the menu look: frame, colours, font, pixel scale, what to avoid).
3. `game_direction.md` (names of skills, tiers, ores, gems, trees) and `game_worlds.md` sections 3 and 4 (hub landmarks, the seven biomes and their look).
4. `godot-game/ui/ui_kit.gd`: the exact colours (`BG`, `SLOT`, `GOLD`, `OUTLINE`, `MUTED`, `GOOD`, `SHORT`, `RARE`, `ENERGY`, `KEY`) and how the frame, corner studs and slots are drawn. The poster draws them the same way.
5. The pictures the poster will use (section 6). Open every icon you place. The picture is the source of truth for how an item looks (`docs/CLAUDE.md`, Item pictures). Do not pick an icon from its filename alone.
6. What the update actually contains: the prompt's list from J00BA, plus the merged and open staging PRs and `BUILD-ROADMAP.md` to check each item is real.

---

## 3. Size and pixel scale

| Format | Art canvas | Saved PNG | Use | Label |
| --- | --- | --- | --- | --- |
| Wide (default) | 640 × 360 | 1920 × 1080 | Website, X / Twitter, Discord | Proposed |
| Square | 360 × 360 | 1080 × 1080 | Instagram, Discord thumbnails | Proposed |

- **Draw everything on the small art canvas, then scale it up ×3 with nearest-neighbour.** That is the same 3 screen pixels per art pixel as the game's menus (`UIKit.PX := 3`, `game_menus.md` section 5.2). It keeps every pixel square and sharp.
- **One pixel scale for the whole poster.** No element is drawn at the final 1920 size, and nothing is scaled by a non-whole amount (`game_menus.md` section 5.1 and 5.3).
- **No anti-aliasing, no blur, no soft gradients.** Shading is done with bands of flat colour (dithering is fine). Turn text anti-aliasing off (`ImageDraw.fontmode = "1"` in Pillow).
- Icons (48 × 48) go on the art canvas at **1× or 2×** only (`game_menus.md` section 5.2, Icons). Impz (64 × 64) go at **1×, 2× or 3×**.

---

## 4. The layout

### 4.1 Wide poster (Proposed)

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ CLUB IMPZ                        ┌ NEW BIOME ─────────┐ ┌ NEW ITEMS ─────────┐ │
│ FROST UPDATE                     │ ┌────────────────┐ │ │ ┌────┐┌────┐┌────┐ │ │
│ 1 DECEMBER                       │ │  frost scene   │ │ │ │icon││icon││icon│ │ │
│                                  │ │      [OUT NOW] │ │ │ └────┘└────┘└────┘ │ │
│        ▲ ▲                       │ └ FROST ─────────┘ │ │ FROSTBLOOM  PIKE…  │ │
│      ( Imp  )   ( Imp )          └────────────────────┘ └────────────────────┘ │
│      (hero  )   (hero )          ┌ NEW TOOLS ─────────┐ ┌ EVENTS ────────────┐ │
│       big, 3×    2×              │ ┌────┐┌────┐┌────┐ │ │ ┌────────────────┐ │ │
│                                  │ │icon││icon││icon│ │ │ │ event picture  │ │ │
│                                  │ └────┘└────┘└────┘ │ │ │ [MID DECEMBER] │ │ │
│ ┌──────────────────────────────┐ └────────────────────┘ │ └ SNOW FIGHT ────┘ │ │
│ │       PLAY FREE · IMPZ.CLUB  │                        └────────────────────┘ │
│ └──────────────────────────────┘                                               │
└────────────────────────────────────────────────────────────────────────────────┘
```

- **Left 40%: title and heroes.** The title block sits top left: "CLUB IMPZ" small in muted text, the **update name** big in gold, the **date** under it in off-white. One to three Impz stand below it as the heroes, the front one biggest. A call-to-action bar along the bottom ("PLAY FREE", the site address).
- **Right 60%: the content grid.** Two or three columns of **section panels**. Each panel has a header and one or more tiles.
- **Square poster:** the title runs across the top, one hero Imp sits bottom left, and the grid fills the rest in two columns.

### 4.2 Section headers (Proposed)

Group tiles under short headers in capitals. Use only the sections the update needs, in this order, and leave out empty ones:

| Header | What goes in it |
| --- | --- |
| NEW BIOME / RETURNING BIOME | A biome of the resource world (`game_worlds.md` section 4.3) |
| NEW IN THE HUB | Hub landmarks, NPCs, shops (`game_worlds.md` section 3.3) |
| NEW ITEMS | Ores, gems, ingots, logs, plants, fish, hides, bundles |
| NEW TOOLS | Pickaxes, axes, sickles, rods, bows |
| NEW CREATURES | Animals and mobs |
| IMPZ COSMETICS | Trait cosmetics, skins (holder content, `game_direction.md` section 2) |
| CHALLENGES & TROPHIES | New challenges, titles, emblems |
| EVENTS | Hub events (`game_worlds.md` section 3.2) |
| GAMES & BATTLES | Minigames, battles, taming |

A header with a count reads well when it is true: "3 NEW TOOLS", "10 NEW FISH".

### 4.3 Tiles (Proposed)

- Every tile is a **panel drawn like the menu kit**: dark blue-black fill (`BG`), a bevelled **gold frame** (`GOLD`), a **corner stud** in each corner, a dark outline (`OUTLINE`), light edge top left and dark edge bottom right.
- The **picture** fills the tile inside the frame. The **label** sits in a dark strip along the bottom of the tile: the thing's name in capitals, off-white.
- **Big tiles** (biome, event, hub landmark) are a small pixel-art scene. **Small tiles** (items, tools) are a recessed slot (`SLOT`, dark top-left edge) with one icon centred at 1× or 2×.
- A **section header** is a gold tab stuck on the top-left of its panel, like a menu title: gold text with the 2-pixel dark drop shadow (`game_menus.md` section 5.2, Font).
- The section that matters most gets the biggest tile. One hero section per poster.
- Between 4 and 12 tiles per poster. More than 12 and nothing reads.

### 4.4 Timing tags (Proposed)

- A **tag** is a small raised pill in the tile's top-right corner, like a menu button with its lip: "OUT NOW", "COMING SOON", "EARLY DEC", "MID DEC", "LATE DEC", "WEEK 2".
- Colours by meaning, the same way the menus use colour (`game_menus.md` section 5.1):
  - **OUT NOW**: green (`GOOD`).
  - A date (EARLY / MID / LATE month): amber (`ENERGY`).
  - **COMING SOON**: muted (`MUTED`).
  - **HOLDERS**: bright gold (`RARE`) with a small gem, for holder-only content.
- Tags only appear when the timing is known. If the whole update lands on one day, the date in the title is enough and the tiles have no tags.

---

## 5. The look

### 5.1 Colours (Proposed, from `ui_kit.gd` and `game_menus.md` section 5.2)

| Role | Colour |
| --- | --- |
| Panel fill | `BG` dark blue-black |
| Slot fill | `SLOT` |
| Frame metal, headers, update name | `GOLD` `#c99a4a`, studs `#fff2c4` |
| Outlines | `OUTLINE` `#0b0c10` |
| Body text, labels | Off-white (`KEY`) |
| Small text ("CLUB IMPZ", site address) | `MUTED` |
| Rare, holder | `RARE` |

- **The background** behind the panels carries the update's theme: a flat pixel-art scene in the colours of the update's main biome (`game_worlds.md` section 4.8 for each biome's look; `ART-DIRECTION.md` section 5 swatches as a start). Dark and calm, so the gold panels and the Impz stand out. Big flat bands of colour, a few stars, snowflakes, leaves or crystals, no busy detail.
- **Accents carry the colour** (`ART-DIRECTION.md` section 5): the icons, gems and Impz are the brightest things on the poster. The background stays 20–40% less saturated.

### 5.2 Text (Proposed)

- Font: **Pixelify Sans** (`godot-game/ui/fonts/PixelifySans.ttf`, SIL Open Font Licence), the game's font, for every word. No second font.
- On the 640 × 360 art canvas, use only the sizes that land on whole pixels: **12** (tags, labels), **16** (section headers), **24** (date), **32 or 48** (update name). Size 8 breaks up; do not use it.
- Capitals for the title, headers, labels and tags.
- At most about **40 words** on the whole poster. Labels are names, never sentences.
- Every heading and the title get the 2-pixel dark drop shadow, as in the menus.

### 5.3 What to avoid (Proposed, from `game_menus.md` section 5.3)

- Blurry or mixed pixel sizes, smooth gradients, glows drawn as blur.
- 3D renders or screenshots of the 3D world on the poster. The poster is 2D pixel art, like the menus.
- Walls of text, long descriptions, legal small print.
- Anything taken from another game or brand.

---

## 6. Where the pictures come from

| Picture | Source | How to use it |
| --- | --- | --- |
| Impz (heroes) | `docs/imp-traits/bodies/` (one real Imp per body colour, 64 × 64) and `docs/imp-traits/layers/` (each trait on its own, 64 × 64, transparent) | Body PNGs have the collection's flat purple background (`#584869`) and darker corners. Key it out (flood-fill from the edges) to get a cut-out hero, or keep it inside a gold frame as a portrait card. For a holder cosmetic tile, stack a body and the trait layer from `layers/`. Scale only ×1, ×2 or ×3. Never redraw or change an Imp's art. |
| Items and tools | `godot-game/assets/sprites/source/items/` (48 × 48) and `godot-game/assets/sprites/source/pickaxes/` | Place as is, in a slot, at 1× or 2×. Open each one first. |
| Prestige icons | `prestige_0.png` to `prestige_5.png` in the items folder | Only on a poster about levels or prestige. |
| Biome, hub and event scenes | Drawn in code for the poster | A small pixel-art scene in the biome's colours and shapes from `game_worlds.md` section 4.8 (for Frost: snow, ice, a frozen lake, blue light). Flat bands of colour, simple silhouettes, a few accent pixels. Put the biome's own icons (its ore, plant, fish) into the scene so it reads as ours. |
| Frames, slots, tags, buttons | Drawn in code | The same shapes as `ui_kit.gd`: bevelled gold frame, corner studs, recessed slots, raised pill with a lip. |

**Open question:** the White Imp (the free base Imp, `game_direction.md` section 2) has no 2D 64 × 64 picture yet. Until it does, the cleanest base Imp is `body_silver_1870.png` (no head, back or clothing trait). Does J00BA want a 2D White Imp drawn for posters?

---

## 7. How to build one

1. **List the content.** From the prompt, write the update name, the date, and every tile: section, label, picture, timing tag. Check each against the docs and PRs (section 1, last rule). If the prompt gives no date or update name, ask J00BA.
2. **Write the script** `tools/posters/<update_name>_poster.py` (Proposed location). Python with Pillow. It reads the icon and Imp PNGs from the repo, draws the poster on the art canvas, then saves it ×3 with `Image.NEAREST`. The script is the source of the poster, so it can be fixed and run again.
3. **Save the PNG** to `docs/images/posters/<update_name>_poster.png` (Proposed location), plus `<update_name>_poster_square.png` if a square one was asked for. Names lowercase with `_` (`game_direction.md` section 11).
4. **Check it** against section 8, then show J00BA the PNG.
5. Commit on a `staging/poster-<update_name>` branch and open a draft PR, following the root `CLAUDE.md`.

---

## 8. Checklist before showing a poster

- [ ] Saved at exactly 1920 × 1080 (or 1080 × 1080), drawn on the art canvas and scaled ×3 with nearest-neighbour.
- [ ] No blurred or half-scaled pixels anywhere, text included (zoom to 400% to check).
- [ ] Every frame, slot and tag matches `ui_kit.gd`'s colours and bevel direction (light top left).
- [ ] Pixelify Sans only, at sizes 12, 16, 24, 32 or 48 on the art canvas.
- [ ] Update name and date are the biggest text. About 40 words or fewer in total.
- [ ] Every tile is real content (built, in a PR, or decided), named as the docs name it.
- [ ] Every icon was opened and matches its label. Impz art is unchanged.
- [ ] Timing tags use the right colours and only appear when timing is known.
- [ ] Nothing copied from another game: no logos, names, characters, fonts or slogans.
- [ ] Holder-only content is tagged HOLDERS, so free players are not misled (`game_direction.md` section 2).
- [ ] Simple and fun at a glance: shrink it to 25% and the update name, heroes and section headers still read.

---

## 9. Open questions

1. Is there a **Club Impz logo** for posters? Until there is, the title block uses "CLUB IMPZ" in Pixelify Sans.
2. Should posters show the **site address** and a "PLAY FREE" bar, and what is the address to show?
3. Should a **2D White Imp** be drawn for posters (section 6)?
4. Are the two sizes in section 3 the right ones, or are other platforms needed (a tall 1080 × 1920 story)?
5. Do hub posters get a lighter, more playful frame, matching the open question in `game_menus.md` section 6.3?
