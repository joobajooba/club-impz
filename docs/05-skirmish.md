# 05: Skirmish system

| Status | Last pass | Depends on |
|---|---|---|
| Draft | User additions, 2026-10-21 | 00, 02 |

> Must agree with [00-overview](00-overview.md) and [02-resources](02-resources.md).
> Labels: **Decided** (in `DECISIONS.md`) · **Proposed** (Claude's suggestion) · **Open question**

**Purpose of this doc:** Pokémon-style turn-based battles, fought by the animals players tame while hunting.

---

## 1. Role in the core loop
Skirmish is where tamed animals are used (D-086). It takes in **tamed animals** (from hunting, D-071) and **cooked fish** (from fishing, D-111). It gives out **XP**, **coins** (capped) and, later, **rank**. It is the main thing to do once the day's energy is spent (D-084).

## 2. Player experience
**Proposed:** short, readable turn-based fights you can finish in two or three minutes. You win by planning your team and its types, not by spending money. Your team grows with you: the Hare you tamed on day one can still win against stronger animals if you pick its fights well.

## 3. Rules & mechanics

### Decided (D-080, D-088 to D-095, D-102, D-111)
- **Who fights:** tamed animals. The player's Imp is the trainer (D-080).
- **Format:** turn-based, a **team of 3** (D-088). Players take turns choosing moves and can swap animals.
- **Types:** eight of them (Beast, Fire, Water, Nature, Frost, Storm, Shadow, Light). Each animal has one type, and there is a type chart. Each animal knows **up to 4 moves** (D-089).
- **Opponents:** **PvE first** (wild animals and trainers). **Ranked PvP comes later** (D-090).
- **Progression:** animals earn **XP** and **level up**, which raises their stats and unlocks moves. An animal's tier sets its base stats. Nothing is written to the NFT (D-091).
- **Energy:** battles **cost no energy**. XP has no limit, but only the **first 10 PvE wins per energy reset** pay coins (D-092).
- **Rewards:** a PvE win pays **XP and coins**, and the coins scale with the opponent's tier (D-093).
- **Losing** costs nothing except the reward (D-094).
- **Stable:** **6 slots** to start. One animal follows you, and any 3 can battle. Extra slots cost coins, priced like inventory rows (D-095).
- **Tamed animals can't be traded** (D-102).
- **Cooked fish** is food for battle animals (D-111).

### Each animal's type (Proposed, D-089 asks Claude to propose)

| Tier | Animal | Type | | Tier | Animal | Type |
|---|---|---|---|---|---|---|
| 1 | Hare | Beast | | 9 | Voidstalker | Shadow |
| 2 | Fox | Fire | | 10 | Starwyrm | Light |
| 3 | Boar | Nature | | 11 | Stormhorn Ram | Storm |
| 4 | Wolf | Beast | | 12 | Tidecrest Serpent | Water |
| 5 | Goldhorn Stag | Light | | 13 | Mossmane Behemoth | Nature |
| 6 | Shadowcat | Shadow | | 14 | Crystalback Basilisk | Frost |
| 7 | Frostmane Yeti | Frost | | 15 | Sunfeather Griffin | Storm |
| 8 | Cinder Salamander | Fire | | 16 | Eclipse Dragon | Shadow |

Every type has two animals, except Shadow (three) and Water (one, at tier 12). **Open question:** should a lower-tier animal be Water, so new players meet it early?

### Type chart (Proposed)

A strong hit does **×2** damage. A resisted hit does **×0.5**. Everything else does ×1.

| Attacking type | Strong against | Resisted by |
|---|---|---|
| Beast | nothing | nothing (a steady all-rounder) |
| Fire | Nature, Frost | Water |
| Water | Fire | Nature, Storm |
| Nature | Water | Fire |
| Frost | Storm | Fire |
| Storm | Water | Frost |
| Shadow | Light | Shadow |
| Light | Shadow | Light |

### Stats, levels and moves (Proposed)
- **Four stats:** Health, Attack, Defence, Speed. Speed decides who moves first each turn.
- **Base stats grow with tier.** A tier 16 animal starts about three times as strong as a tier 1 animal. Exact numbers are set when the first battle is built and played.
- **Levels 1 to 50.** Each level adds a fixed share of the animal's base stats.
- **Moves:** each type has a list of moves. An animal learns its first move at level 1, then new ones at levels 10, 20 and 35, and keeps the best 4. Each move has a type, a power and sometimes an effect (lower Speed, heal a little). The move lists are written with the first build.
- **Moves at level 1 (Proposed, 2026-10-22).** Today an animal has one move until level 10, so its first battles have no choice in them. **Proposed:** a newly tamed animal knows **2 moves**: its type's first move and a plain Beast hit (Tackle). A Beast animal starts with its first two Beast moves (Tackle, Bite). It still learns at 10, 20 and 35, and keeps the best 4, so it is full at level 20 instead of 35. The TEST build gives 1 move at level 1.
- **Food (D-111):** feeding cooked fish to an animal gives it XP. Higher-tier fish give more. This gives fishing a steady use and lets players level an animal without fighting.
- **Wild battles:** wild animals of every tier you can hunt. **Trainers:** non-player characters with fixed teams, one per tier band, as a ladder of goals.
- **Coins per win (D-093):** worth what selling 5 raw items of the opponent's tier would pay (D-074). With the 10-win cap, a reset's battles are worth about as much as 50 items, which is less than a full bar of gathering.

## 4. Inputs & outputs
| Takes in | Gives out | Notes |
|---|---|---|
| A team of 3 tamed animals | A battle | **Decided** (D-088). No energy (D-092). |
| A PvE win | XP for the team, and coins for the first 10 wins per reset | **Decided** (D-092, D-093). The amount is **Proposed** above. |
| A loss | XP only | **Decided** (D-094). |
| Cooked fish | XP for one animal | **Decided** that fish is battle-animal food (D-111). XP as its effect is **Proposed**. |
| Coins | Extra stable slots | **Decided** (D-095). |

## 5. NFT touchpoints
- **Decided (D-080):** the Imp is the trainer. Holders and non-holders battle with the same tamed animals, so the NFT gives no battle power (pillar "Fair to free players", D-085).
- **Decided (D-091):** nothing in skirmish is written to the NFT.
- Holders can show their own Imp as the trainer (D-038).

## 6. Risks
- **Bots farming battles for coins.** Handled by the 10-win cap per reset (D-092). The server runs every battle and rolls every hit (ACCOUNTS-AND-DATA, section 8), so a client can't fake a win.
- **Pay-to-win.** Coins buy cosmetics, inventory rows, stable slots, energy refills and wood hilts (D-075, D-095), none of which make an animal stronger. Energy refills mean more hunting, so more chances to tame, but taming chance and levels still take play. **Acceptable** as it stands. Re-check this whenever something new is added to the merchant.
- **Balance.** Eight types and 16 animals are a lot to balance for two people. PvP waits until PvE has been played (D-090).
- **Scope.** A turn-based battle screen, AI opponents and move lists are a large build. See section 7.

## 7. Smallest first version (Proposed)
Wild battles only, against animals of tiers 1–4. Teams of 3, four stats, the type chart, two moves per animal, levels up to 10, and coins on win with the cap. No trainers, no PvP and no food yet. That is enough to find out whether battling your tamed animals is fun.

## 8. Done when…
*The conditions for the user to sign this off. Agreed with the user.* **Proposed:** the type chart, the animal types and the stat curve are approved. The first version has been played and judged fun. Coins from battles have been checked against the economy in 02.

---

## Questions this doc must answer
1. Battle format: 1v1 or teams? How many moves per Impling? *Answered (D-088, D-089): a team of 3 tamed animals, up to 4 moves each.*
2. Stats and types: which stats, and is there a type chart (rock-paper-scissors)? *Answered in part (D-089): 8 types and a chart. Stats and the chart itself are Proposed.*
3. Where do moves and stats come from: NFT traits, training, items or a mix? *Answered (D-091): tier and level. Not NFT traits.*
4. PvE (wild Implingz, bosses) and/or PvP (ranked)? *Answered (D-090): PvE first, ranked PvP later.*
5. Progression: XP, levels, evolutions? Do any of these write to the NFT? *Answered (D-091): XP and levels; nothing is written to the NFT. Evolutions aren't planned.*
6. Rewards and the costs of losing. Check against `02-resources.md`. *Answered (D-092 to D-094).*
7. Pay-to-win check: can money buy a battle advantage? If so, how much is acceptable? *Checked in section 6: no direct advantage.*

## Pass history
| Pass | Change |
|---|---|
| 0 | Template created with the questions to answer. |
| User additions, 2026-10-21 | Tamed animals battle (D-080). Turn-based teams of 3 (D-088), 8 types and 4 moves (D-089), PvE first (D-090), XP and levels (D-091), no energy with a 10-win coin cap (D-092), XP and coins (D-093), no loss (D-094), stable of 6 (D-095), animals can't be traded (D-102), cooked fish as food (D-111). Animal types, type chart, stats and the first version are Proposed. Status Draft. |
| User addition, 2026-10-22 | Proposed: a newly tamed animal knows 2 moves. |
