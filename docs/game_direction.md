# game_direction

> status: draft v1 · owner: j00ba · last updated: 2026-10-28
>
> this is the top-level direction for club impz. it describes what the game is, who it is for and how the core loop works. detailed specs (resources, mobs, crafting, web3, bonuses) will live in their own docs and must agree with this one.

---

## 1. the pitch

club impz is a small, browser-based **social mmo** for the implingz community, in the spirit of **club penguin** (hang out, chat, show off) and **runescape** (gather, skill up, craft, progress).

players drop into a shared world, talk to each other, show off their imp and gear, and grind skills to craft better tools, weapons and armour.

**two halves of the game:**

| half | feel | where |
| --- | --- | --- |
| social | club penguin: chat, emotes, npcs, showing off cosmetics | hub world |
| grind | runescape: gather resources, level skills, craft, progress tool tiers | resource world |

---

## 2. who can play

- **anyone can play for free.** every player gets a **base imp** to play as. no wallet or nft is needed.
- **imp holders** (owners of an implingz nft) get extras on top:
  - use their owned imp as a **skin**.
  - unlock **trait cosmetics**: each trait on an imp they own becomes a cosmetic item they can mix and match on their in-game imp.
  - receive **holder bonuses** (see section 7).
- non-holders can never use nft skins or nft trait cosmetics.

---

## 3. the implingz nft

| field | value |
| --- | --- |
| collection | implingz ("impz") |
| supply | 2222 |
| chains | eth / robinhood |
| contract | `0x81D2D1f0e92285CdD22Aa3cbc6956B6E1724d029` |
| key trait | `tier`: tier_1, tier_2 or tier_3 (tier_3 is the highest) |

ownership and traits are read from the player's **connected wallet**. full details go in a separate `web3_integration.md`.

> naming note: the contract address keeps its original mixed case because ethereum uses it as a checksum. it is the only exception to the lowercase rule.

---

## 4. the world

the world is split into two areas.

### 4.1 hub world (social)

- every player **spawns here**.
- the main hangout: chat, show off skins and items, meet other players.
- home to the **npcs** (shops, quest givers, crafting stations, etc.).
- players can also chat in any other part of the map, not only the hub.

### 4.2 resource world (grind)

- an explorable area where all gatherable resources live: ores, trees, plants, fish and mobs.
- higher tier resources need higher tier tools, so progression naturally pushes players deeper into the world.

---

## 5. core game loop

```
            ┌─────────────────────────────────────────────────────┐
            │                                                     │
            ▼                                                     │
   ┌────────────────┐   ┌────────────────┐   ┌──────────────────┐ │
   │ gather         │──▶│ process        │──▶│ items            │─┼──▶ sell or trade (coins)
   │ spends energy  │   │ at stations    │   │ ore, logs, fish, │ │
   └────────────────┘   └────────────────┘   │ hides, plants    │ │
            ▲                                └──────────────────┘ │
            │                                   │          │      │
   ┌────────────────┐   ┌────────────────┐      │          │      │
   │ better tools   │◀──│ craft          │◀─────┘          │      │
   │ higher tiers   │   │ pickaxes, axes │                 ▼      │
   └────────────────┘   │ rods, bows,    │       ┌──────────────────┐
                        │ weapons, armour│       │ tame animals     │
                        └────────────────┘       │ with plant       │
                                                 │ bundles          │
                                                 └──────────────────┘
                                                          │
                                                          ▼
                                                 ┌──────────────────┐
                                                 │ battles + games  │
                                                 │ rewards and rank │
                                                 └──────────────────┘
```

1. **gather**: mine, chop, forage, fish or hunt in the resource world. gathering spends **energy**.
2. **process**: turn raw resources into usable materials at stations (ore → ingot, log → planks).
3. **items**: processed materials, plus raw items like fish and hides.
4. from items, a player can:
   - **craft** better tools, weapons and armour → reach **higher tier** resources → back to gather.
   - **sell or trade** for **coins**.
   - **tame animals** using plant bundles → use them in **battles and games** for rewards and rank.
5. every action earns **xp** (player level + the matching skill).
6. **imp holders**: every gathering action also has a chance to find a **mint token**.
7. between grinding sessions, players return to the hub to socialise and show off what they earned.

---

## 6. progression

there are two separate progression tracks.

### 6.1 player level + prestige

- players start at **level 1**, max is **level 50**.
- xp comes from gathering resources and from general play.
- at level 50 a player can choose to **prestige**: their level resets to 1 and their prestige icon goes up by one.
- prestige icons run from **prestige_0** (new player) up to **prestige_5** (max).
- the prestige icon is shown as the player's **emblem** on their profile.

### 6.2 skill levels

each skill levels on its own, from **1 to 100**.

| skill | what you do | main resource |
| --- | --- | --- |
| mining | mine ores | ores, ingots, gems |
| lumbering | chop trees | logs, planks |
| foraging | pick plants | plants (used for plant bundles) |
| hunting | hunt mobs | hides, mob drops |
| fishing | catch fish | fish |

- each skill has its own **skill tree**. skill levels unlock more of the tree.
- skill tree nodes give **buffs for that skill** (for example faster gathering or better drop chances). nodes are unlocked left to right in a chain.

### 6.3 resource tiers + tool gating

- every resource has a **resource tier** from **t1 to t10**.
- each resource needs a **minimum tool** to gather it.
- each new tier of tool is crafted from the previous tier's materials, which creates the progression ladder.

> naming note: "resource tier" (t1 to t10) and "imp tier" (tier_1 to tier_3) are two different things. this doc always says which one it means.

#### mining: ores, ingots + time

| ore | tier | ingot | time to mine | minimum pickaxe |
| --- | --- | --- | --- | --- |
| coal | t1 | coal | 30s | stone_pickaxe |
| tin | t2 | tin_ingot | 45s | stone_pickaxe |
| copper | t3 | copper_ingot | 45s | stone_pickaxe |
| iron | t4 | iron_ingot | 60s | bronze_pickaxe |
| gold | t5 | gold_ingot | 120s | iron_pickaxe |
| obsidian | t6 | obsidian_ingot | 240s | gold_pickaxe |
| titanite | t7 | titanite_ingot | 300s | obsidian_pickaxe |
| dreadstone | t8 | dreadstone_ingot | 300s | titanite_pickaxe |
| voidstone | t9 | voidstone_ingot | 600s | dreadstone_pickaxe |
| stellarite | t10 | stellarite_ingot | 1000s | void_pickaxe |

#### mining: gems

each ore has a chance to drop a gem while being mined.

| gem | tier | found when mining | chance |
| --- | --- | --- | --- |
| diamond | t1 | coal | 1/50 |
| topaz | t2 | tin | 1/10 |
| sapphire | t3 | copper | 1/12 |
| amethyst | t4 | iron | 1/15 |
| ruby | t5 | gold | 1/20 |
| emerald | t6 | obsidian | 1/25 |
| jade | t7 | titanite | 1/30 |
| painite | t8 | dreadstone | 1/50 |
| arcanium | t9 | voidstone | 1/60 |
| eclipsium | t10 | stellarite | 1/75 |

#### lumbering: logs, planks + time

| tree | tier | processed | time to chop | minimum axe |
| --- | --- | --- | --- | --- |
| pine | t1 | pine_planks | 30s | stone_axe |
| birch | t2 | birch_planks | 45s | stone_axe |
| oak | t3 | oak_planks | 45s | stone_axe |
| maple | t4 | maple_planks | 60s | bronze_axe |
| hickory | t5 | hickory_planks | 120s | iron_axe |
| frostbark | t6 | frostbark_planks | 240s | gold_axe |
| titanwood | t7 | titanwood_planks | 300s | obsidian_axe |
| runewood | t8 | runewood_planks | 300s | titanite_axe |
| gembark | t9 | gembark_planks | 600s | dreadstone_axe |
| worldbark | t10 | worldbark_planks | 1000s | void_axe |

foraging, fishing and hunting tables will be added in `resources.md`.

---

## 7. holder bonuses

holder bonuses scale with:

1. **how many impz** the player owns, and
2. the **imp tier** of those impz (tier_3 is the strongest).

exact bonuses are **to be decided** and will go in `holder_bonuses.md`. known so far:

- nft skins + trait cosmetics (section 2).
- chance to find a **mint token** on every gathering action (section 5).

---

## 8. player profile

each player has a profile card that others can view.

- **left panel**: player name, player level (star), the imp they are wearing, their **emblem** (prestige icon) and their **title**.
- **tabs**:
  - **stats**: skill levels for all five skills, plus the skill tree for the selected skill.
  - **trophies**: achievements.
  - **collection**: owned cosmetics, skins and items.
  - **information**: general player info.

---

## 9. tech stack

| tool | used for |
| --- | --- |
| godot | game engine (browser / web export) |
| blockbench | 3d models |
| aseprite | 2d art (sprites, icons, ui) |
| supabase | database (accounts, inventory, progression) |
| apechain | web3, using **glyph** for wallet connect |
| github | code + file repository |
| claude | coding |

---

## 10. naming rules

- every file, folder, id and asset name is **lowercase**.
- use `_` instead of spaces (for example `stone_pickaxe`, `game_direction.md`).
- the only exception is data that breaks if changed, like wallet or contract addresses.

---

## 11. planned docs

| doc | covers |
| --- | --- |
| `resources.md` | every resource for all five skills, tiers, times, drops |
| `crafting.md` | recipes, stations, tool / weapon / armour progression |
| `world_mobs.md` | mobs, hunting, taming |
| `web3_integration.md` | wallet connect, nft reading, skins, traits, mint tokens |
| `holder_bonuses.md` | bonuses by imp count and imp tier |
| `skill_trees.md` | every node in every skill tree |

---

## 12. open questions

- 2d or 3d, and what camera view?
- what energy is, how it refills, and whether holders get more.
- what a mint token is and what it does.
- what carries over when a player prestiges.
- how impz on eth / robinhood are read through glyph on apechain.
- whether players can trade with each other directly.
