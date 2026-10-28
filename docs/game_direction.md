# Game Direction

> Status: v3 · Owner: J00BA · Last updated: 2026-10-28
>
> This is the top-level direction for Club Impz. It describes what the game is, who it is for and how the core loop works. Detailed specs (resources, mobs, crafting, web3, bonuses, challenges) will live in their own docs and must agree with this one.

---

## 1. The pitch

Club Impz is a small, browser-based **social MMO** for the Implingz community, in the spirit of **Club Penguin** (hang out, chat, show off) and **RuneScape** (gather, skill up, craft, progress).

Players drop into a shared 3D world, talk to each other, show off their imp, gear and achievements, and grind skills to craft better tools, weapons and armour.

**Two halves of the game:**

| Half | Feel | Where |
| --- | --- | --- |
| Social | Club Penguin and Call of Duty profiles: chat, NPCs, cosmetics, challenges, trophies, titles, emblems | Hub world |
| Grind | RuneScape: gather resources, level skills, craft, progress tool tiers | Resource world |

---

## 2. Who can play

- **Anyone can play for free.** Every player gets a **base imp** to play as. No wallet or NFT is needed.
- **Imp holders** (owners of an Implingz NFT) get extras on top:
  - Use their owned imp as a **skin**.
  - Unlock **trait cosmetics**: each trait on an imp they own becomes a cosmetic item they can mix and match on their in-game imp.
  - Receive **holder bonuses** (see section 8).
- Non-holders can never use NFT skins or NFT trait cosmetics.
- **Holder-only:** NFT skins, NFT trait cosmetics, mint tokens and holder bonuses. **Every other part of the game is open to all players.**

---

## 3. The Implingz NFT

| Field | Value |
| --- | --- |
| Collection | Implingz ("Impz") |
| Supply | 2222 |
| Chains | ETH / Robinhood |
| Contract | `0x81D2D1f0e92285CdD22Aa3cbc6956B6E1724d029` |
| Key trait | `tier`: Tier 1, Tier 2 or Tier 3 (Tier 3 is the highest) |

Players connect their wallet with **Glyph** (ApeChain). Glyph reads the ETH contract to check which impz the wallet owns and which traits those impz have. Full details go in `web3_integration.md`.

---

## 4. The world

The world is **3D**. Some assets are **2D**: inventory items, prestige icons, titles, emblems and other UI.

The world is split into two areas.

### 4.1 Hub world (social)

- Every player **spawns here**.
- The main hangout: chat, show off skins, items, trophies, titles and emblems, meet other players.
- Home to the **NPCs** (shops, challenge givers, crafting stations, etc.).
- Players can also chat in any other part of the map, not only the hub.

### 4.2 Resource world (grind)

- An explorable area where all gatherable resources live: ores, trees, plants, fish and mobs.
- Higher tier resources need higher tier tools, so progression naturally pushes players deeper into the world.

---

## 5. Core game loop

```
   ┌────────────────┐   ┌────────────────┐   ┌──────────────────┐
   │ Gather         │──▶│ Process        │──▶│ Items            │──▶ Sell for coins
   │ mine, chop,    │   │ at stations    │   │ ore, logs, fish, │
   │ forage, fish,  │   └────────────────┘   │ hides, plants    │
   │ hunt           │                        └──────────────────┘
   └────────────────┘                           │          │
            ▲                                   │          │
   ┌────────────────┐   ┌────────────────┐      │          ▼
   │ Better tools   │◀──│ Craft          │◀─────┘  ┌──────────────────┐
   │ higher tiers   │   │ pickaxes, axes,│         │ Tame animals *   │
   └────────────────┘   │ rods, bows,    │         │ with plant       │
                        │ weapons, armour│         │ bundles          │
                        └────────────────┘         └──────────────────┘
                                                            │
                                                            ▼
                                                   ┌──────────────────┐
                                                   │ Battles + games  │
                                                   │ rewards and rank │
                                                   └──────────────────┘

   * Taming, battles and games come in a later update.
```

1. **Gather**: mine, chop, forage, fish or hunt in the resource world.
2. **Process**: turn raw resources into usable materials at stations (ore → ingot, log → planks).
3. **Items**: processed materials, plus raw items like fish and hides.
4. From items, a player can:
   - **Craft** better tools, weapons and armour → reach **higher tier** resources → back to gather.
   - **Sell** to NPCs for **coins**. There is no player-to-player trading.
   - *(Later update)* **Tame animals** using plant bundles → use them in **battles and games** for rewards and rank.
5. Every action earns **XP** (player level and the matching skill).
6. **Imp holders**: gathering any resource has an extremely rare chance to drop a **mint token**, a random reward.
7. Between grinding sessions, players return to the hub to socialise, take on challenges and show off what they earned.

### 5.1 Social loop

```
Challenge ──▶ Trophy ──▶ Title / emblem ──▶ Equip on profile ──▶ Show off in the hub
```

---

## 6. Progression

There are two separate progression tracks.

### 6.1 Player level and prestige

- Players start at **level 1**, max is **level 50**.
- XP comes from gathering resources and from general play.
- At level 50 a player can choose to **prestige**: their level resets to 1 and their prestige icon goes up by one.
- Each prestige also awards an **exclusive prestige badge**.
- Prestige only resets the player level. Skill levels, items and cosmetics are kept.
- There are six prestige icons, `prestige_0.png` (new player) to `prestige_5.png` (max prestige). These are 2D images supplied by J00BA.

### 6.2 Skill levels

Each skill levels on its own, from **1 to 100**.

| Skill | What you do | Main resource |
| --- | --- | --- |
| Mining | Mine ores | Ores, ingots, gems |
| Lumbering | Chop trees | Logs, planks |
| Foraging | Pick plants | Plants (used for plant bundles) |
| Hunting | Hunt mobs | Hides, mob drops |
| Fishing | Catch fish | Fish |

- Each skill has its own **skill tree**. Skill levels unlock more of the tree.
- Skill tree nodes give **buffs for that skill** (for example faster gathering or better drop chances). Nodes unlock left to right in a chain.

### 6.3 Resource tiers and tool gating

- Every resource has a **resource tier** from **T1 to T10**.
- Each resource needs a **minimum tool** to gather it.
- **Stone tools are the starter tools.** Each new tier of tool is crafted from earlier materials, which creates the progression ladder.
- **Bronze** is an alloy made from **tin and copper** ingots. It has no ore of its own.

> Naming note: "resource tier" (T1 to T10) and "imp tier" (Tier 1 to Tier 3) are two different things. This doc always says which one it means.

#### Mining: ores, ingots and time

| Ore | Tier | Ingot | Time to mine | Minimum pickaxe |
| --- | --- | --- | --- | --- |
| Coal | T1 | Coal | 30s | Stone pickaxe |
| Tin | T2 | Tin ingot | 45s | Stone pickaxe |
| Copper | T3 | Copper ingot | 45s | Stone pickaxe |
| Iron | T4 | Iron ingot | 60s | Bronze pickaxe |
| Gold | T5 | Gold ingot | 120s | Iron pickaxe |
| Obsidian | T6 | Obsidian ingot | 240s | Gold pickaxe |
| Titanite | T7 | Titanite ingot | 300s | Obsidian pickaxe |
| Dreadstone | T8 | Dreadstone ingot | 300s | Titanite pickaxe |
| Voidstone | T9 | Voidstone ingot | 600s | Dreadstone pickaxe |
| Stellarite | T10 | Stellarite ingot | 1000s | Void pickaxe |

#### Mining: gems

Each ore has a chance to drop a gem while being mined. Gem rarity does not follow resource tier on purpose (for example diamond is rarer than topaz).

| Gem | Tier | Found when mining | Chance |
| --- | --- | --- | --- |
| Diamond | T1 | Coal | 1/50 |
| Topaz | T2 | Tin | 1/10 |
| Sapphire | T3 | Copper | 1/12 |
| Amethyst | T4 | Iron | 1/15 |
| Ruby | T5 | Gold | 1/20 |
| Emerald | T6 | Obsidian | 1/25 |
| Jade | T7 | Titanite | 1/30 |
| Painite | T8 | Dreadstone | 1/50 |
| Arcanium | T9 | Voidstone | 1/60 |
| Eclipsium | T10 | Stellarite | 1/75 |

#### Lumbering: logs, planks and time

| Tree | Tier | Processed | Time to chop | Minimum axe |
| --- | --- | --- | --- | --- |
| Pine | T1 | Pine planks | 30s | Stone axe |
| Birch | T2 | Birch planks | 45s | Stone axe |
| Oak | T3 | Oak planks | 45s | Stone axe |
| Maple | T4 | Maple planks | 60s | Bronze axe |
| Hickory | T5 | Hickory planks | 120s | Iron axe |
| Frostbark | T6 | Frostbark planks | 240s | Gold axe |
| Titanwood | T7 | Titanwood planks | 300s | Obsidian axe |
| Runewood | T8 | Runewood planks | 300s | Titanite axe |
| Gembark | T9 | Gembark planks | 600s | Dreadstone axe |
| Worldbark | T10 | Worldbark planks | 1000s | Void axe |

Foraging, fishing and hunting tables will be added in `resources.md`.

---

## 7. Challenges, trophies, titles and emblems

Inspired by Call of Duty calling cards and emblems.

- Players complete **challenges** (for example reach a skill level, gather a rare gem, win battles).
- Completing a challenge unlocks a **trophy**.
- Trophies can reward **titles** and **emblems**.
- Players **equip** one title and one emblem on their profile to show off, especially for difficult challenges.
- Titles and emblems are 2D assets.

The full challenge list goes in `challenges.md`.

---

## 8. Holder bonuses

Holder bonuses scale with:

1. **How many impz** the player owns, and
2. The **imp tier** of those impz (Tier 3 is the strongest).

Exact bonuses are **to be decided** and will go in `holder_bonuses.md`. Known so far:

- NFT skins and trait cosmetics (section 2).
- An extremely rare chance to find a **mint token** (a random reward) while gathering any resource (section 5).

---

## 9. Player profile

Each player has a profile card that others can view.

- **Left panel**: player name, player level and prestige icon, the imp they are wearing, their equipped **emblem** and **title**.
- **Tabs**:
  - **Stats**: skill levels for all five skills, plus the skill tree for the selected skill.
  - **Trophies**: trophies earned from challenges.
  - **Collection**: owned cosmetics, skins, titles, emblems, prestige badges and items.
  - **Information**: general player info.

---

## 10. Tech stack

| Tool | Used for |
| --- | --- |
| Godot | Game engine (browser / web export) |
| Blockbench | 3D models |
| Aseprite | 2D art (items, icons, titles, emblems, UI) |
| Supabase | Database (accounts, inventory, progression) |
| ApeChain | Web3, using **Glyph** for wallet connect and reading the ETH contract |
| GitHub | Code and file repository |
| Claude | Coding |

---

## 11. Naming rules

- Every **file and folder name** is **lowercase**, with `_` instead of spaces (for example `stone_pickaxe.png`, `game_direction.md`, `prestige_0.png`).
- In-game IDs follow the same rule (for example `stone_pickaxe`).
- Normal text, like the sentences in these docs, uses normal capitals.

---

## 12. Planned docs

| Doc | Covers |
| --- | --- |
| `resources.md` | Every resource for all five skills, tiers, times, drops |
| `crafting.md` | Recipes, stations, tool / weapon / armour progression |
| `world_mobs.md` | Mobs, hunting, taming (later update) |
| `challenges.md` | Challenges, trophies, titles, emblems |
| `web3_integration.md` | Wallet connect, NFT reading, skins, traits, mint tokens |
| `holder_bonuses.md` | Bonuses by imp count and imp tier |
| `skill_trees.md` | Every node in every skill tree |
