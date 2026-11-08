# XP System

> Status: draft v1 · Owner: xpelicious · Last updated: 2026-11-08
>
> How players earn XP, how it turns into skill levels, the player level and prestige, how levelling is shown, and how XP is kept safe on the server. This doc must agree with `game_direction.md`. Where the two differ, `game_direction.md` wins until it is updated.
>
> Every rule here is labelled. **Decided** means it is already in `game_direction.md`, `resource_gathering.md` or `DECISIONS.md`. **Proposed** is Claude's suggestion, waiting for the collaborators. **Open question** is not settled.

---

## 1. What is already decided

| Rule | Where it is decided |
| --- | --- |
| Every action earns **XP**, for the player level and for the matching skill. | `game_direction.md` section 5, step 5 |
| There are **two tracks**: the **player level** (1 to 50, with prestige) and five **skill levels** (1 to 100 each). | `game_direction.md` section 6 |
| The five skills are **Mining, Lumbering, Foraging, Hunting and Fishing**. | `game_direction.md` section 6.2 |
| At player level 50 a player **can choose to prestige**: the player level goes back to 1, the prestige icon goes up by one, and an **exclusive prestige badge** is awarded. Prestige resets **only the player level**. Skills, items and cosmetics are kept. | `game_direction.md` section 6.1 |
| Six prestige icons, `prestige_0.png` (new player) to `prestige_5.png` (max prestige), drawn by J00BA. | `game_direction.md` section 6.1 |
| Every skill uses the **same XP curve**: the RuneScape curve extended to level 100 (14,391,160 XP for level 100). | `resource_gathering.md` section 3 |
| Target pace: **level 100 in about 2.5 months of nonstop gathering**. | `resource_gathering.md` section 3.1 |
| XP per ore, per gem (double its ore) and per log. | `resource_gathering.md` sections 4 and 5 |
| Skill levels **unlock tool recipes** (bronze at 5, iron at 15 … stellarite at 90) through the skill tree. Resources have no level requirement; the tool is the only gate. | `resource_gathering.md` sections 2.1 and 2.2 |
| Battle animals have **their own XP and levels**, separate from the player. | D-091, `05-skirmish.md` |

**What is built today:** nothing for player or skill XP. `GameData.SKILLS` lists the five skills and their stations, but no XP is earned or saved. Battle animals have XP on TEST numbers (`Stable.xp_to_next` is `50 × level`). The profile menu prompt (PR #57) shows player level, prestige and skill levels as TEST data only, because this system was not designed yet.

**Still open in the decided docs:** `resource_gathering.md` open question 1 asks how much **player level XP** each gather gives. Section 3.2 answers it (Decided, D-121).

---

## 2. What other games do

From Claude's knowledge of these games, not sources checked in this pass.

| Game | How XP works | Take for Club Impz |
| --- | --- | --- |
| Old School RuneScape | Every skill has its own XP and the same curve. XP drops float up as it is earned. **Total level** (all skills added up) is the main boast. Skill XP keeps counting past the max level, up to 200 million. | Per-skill XP with one curve (already decided). XP drops. Total level on the profile. XP that keeps counting at max level. |
| Call of Duty | A player level with **prestige**: reset to 1 for a new icon. Prestige gives looks, not power. | Prestige gives looks only (already decided). The prestige moment needs to feel big. |
| Stardew Valley | Few levels, each one shown with a full-screen "level up" card that lists what it unlocked. | Every level-up says **what it unlocked** ("New recipe: Iron pickaxe"). |
| Valheim | Skills lose XP when the player dies. | Never take XP away. Club Impz has no losing state for skills. |
| Minecraft | XP is a currency spent on enchanting. | **Don't.** XP is progress, never spent. Spending XP would make levels go down and blur the show-off value. |

---

## 3. Where XP comes from

### 3.1 Skill XP (Proposed)

- **Only gathering gives skill XP.** Mining a rock gives Mining XP, chopping gives Lumbering XP, and so on, using the per-resource values in `resource_gathering.md`. A gem gives its own XP on top (Decided, `resource_gathering.md` section 4.2).
- **Processing and crafting give no skill XP.** The 2.5-month pace in `resource_gathering.md` section 3.2 is worked out from gathering alone. Adding XP for smelting or sawing would make every skill faster than its target and the table would need redoing. Open question: whether that is wanted later.
- **A cancelled gather gives nothing** (walking away, starting another action).
- Foraging, Fishing and Hunting XP values wait for their tables (`resource_gathering.md` sections 6 to 8), and are set with the same method as section 3.2 there.

### 3.2 Player XP (Decided, D-121)

The sources and amounts in this section were accepted by the user on 2026-11-08.

The player level is the "how much have you played" track. Skills already show "how far have you progressed". So player XP is based on **time spent playing**, not on resource tier.

| Source | Player XP | Why |
| --- | --- | --- |
| A finished gather | **1 per second the gather took**, after tool and skill tree speed bonuses | About **3,600 per hour** for everyone, at every tier |
| A gem from that gather | The same amount again | A lucky moment should feel lucky on both bars |
| Processing (furnace, sawbench, any station) | **10% of the base gather seconds** of the raw items used, rounded down | Small, and capped by what was gathered, so it can't be farmed on its own |
| Crafting a tool for the **first time** | **500 × the tool tier** (bronze 1 … stellarite 8) | A milestone reward. Only the first craft of each tool counts, so crafting and selling tools can't be farmed |
| A challenge | Set per challenge in `challenges.md`. Suggested bands: easy 1,000, medium 5,000, hard 20,000 | Challenges pay once each |
| A battle (later update) | 100 for a win, 30 for a loss, for the **first 10 battles per energy reset** | Matches the 10-win coin cap (D-092) so battles can't replace gathering |

**Why seconds and not the resource's base time.** If player XP used the resource's base gather time, a stellarite pickaxe on coal (30s cut to 18s) would earn 6,120 player XP an hour, against 3,840 for mining stellarite itself. Top players would farm coal for their player level. Paying by real seconds makes every tier worth the same per hour, so players gather what's best for their skills.

**Nothing else gives XP.** No XP for chatting, emotes, logging in, walking, buying, selling or trading. Each of these can be spammed or bought. Coins never buy XP.

### 3.3 Holder bonuses (Open question, with a recommendation)

`game_direction.md` section 8 says holder bonuses are still to be decided. **Recommendation: no XP multipliers for Imp holders.** Player level, prestige and total level are the game's main ways of showing off. If holding an Imp made them faster, they would show who bought an NFT, not who played. That also clashes with the IMPLINGZ pillar "Fair to free players … never more power" (D-085). Holder bonuses that don't touch XP (skins, traits, mint tokens) avoid the problem.

---

## 4. Skill levels (Proposed on top of the decided curve)

- **The curve is decided** (`resource_gathering.md` section 3). The full table is **generated in code from the formula**, once, and the game and the server use the same function.
- **Store XP, never the level.** The level is worked out from XP. That way a level can never drift from its XP, and changing the pace later (the "× 0.8" note in `resource_gathering.md` section 3.2) only changes the XP values per gather.
- **XP keeps counting after level 100.** It is shown on the profile and can be ranked on later. The level stays at 100.
- **Total level**: the five skill levels added up, 5 to 500. Shown on the profile next to the player level.
- **Skill tree unlocks** come from the skill level (Decided). Which node sits at which level goes in `skill_trees.md`. This doc only promises that every tool recipe level (5, 15, 25, 35, 45, 55, 70, 90) is a node.

---

## 5. Player level and prestige (Proposed on top of the decided rules)

### 5.1 The player level curve

XP to go from level L to L + 1 = **100 × L + 5 × L²**. Level 50 takes **324,625 player XP** in total.

| Reach level | Total player XP | Hours of gathering (about 3,700 XP an hour) |
| --- | --- | --- |
| 2 | 105 | 2 minutes |
| 5 | 1,150 | 20 minutes |
| 10 | 5,925 | 1.6 |
| 20 | 31,350 | 8.5 |
| 30 | 86,275 | 23 |
| 40 | 180,700 | 49 |
| **50** | **324,625** | **about 88** |

- **Why this shape:** the first levels come within minutes, so a new player sees the bar move in their first session. The later ones take a few hours each, so level 50 means something.
- **Why 88 hours:** a player who plays 2 hours a day reaches their first prestige in about 6 weeks. Six full runs (level 50 at prestige 5) take about **530 hours**, roughly 9 months at 2 hours a day. That is slower than a first prestige but faster than one skill to 100 (about 15 months at 4 hours a day, `resource_gathering.md` section 3.2). Prestige stays a long goal without being out of reach.
- It uses its own curve, not the skill curve. The RuneScape curve gets about 10% steeper every level, so on it levels 43 to 50 cost as much XP as levels 1 to 43 together. That is a wall at the end of every run, on a track the player resets five times.

### 5.2 Prestige

- **At level 50 the player XP bar stops.** Extra player XP still counts toward a **lifetime player XP** total on the profile, but not toward the next run. Holding off on prestige gives no head start.
- **Prestiging is a button on the profile**, with one confirm ("Your level goes back to 1. Your skills, items and cosmetics are kept."). It can't be undone.
- **Prestige n** shows `prestige_n.png` next to the player level everywhere it appears, and gives **prestige badge n** in the Collection tab. A new player shows `prestige_0.png` (Decided).
- **After prestige 5**, reaching level 50 again is the end of the track: the profile says **Max prestige**, and player XP keeps counting only in the lifetime total.
- **Prestige gives no power.** No XP boost, no extra energy, no better drops. Only the icon and the badge (Decided that those are the rewards; the "no power" part is Proposed).

---

## 6. How XP is shown (Proposed)

These follow `game_menus.md` (HUD section 3.1, profile section 3) where it already covers them.

| Moment | What the player sees |
| --- | --- |
| Every gather | An **XP drop** above the pickup line: "+32 Mining XP" (`game_menus.md` section 3.1). Player XP is not dropped, to keep the drops short. |
| Always, on the HUD | **Lv 12** and the prestige icon in the top-left box, with a thin player XP bar under it. Hovering it shows "4,210 / 6,620 XP". |
| Skill level-up | A toast: "Mining level 15", a short sound, and the `level_up_burst` effect over the Imp (`blockbench_detailed_prompts.md`), which nearby players see too. If the level unlocked a recipe, a second line: "New recipe at the anvil: Iron pickaxe". |
| Player level-up | A bigger toast, a different sound, the burst, and the level on the name tag updates. |
| Level 50 | A toast that points to the profile: "Level 50! You can prestige from your profile (P)." |
| Big milestones | A line in **global chat** (PR #56) for skill levels 50, 90 and 100, every prestige, and the **first player on the server** to reach 100 in a skill. This is a social game, so showing off is the point. |
| Profile, Stats tab | The five skills with level, XP, XP to next level and a bar; total level; lifetime player XP (`game_direction.md` section 9). |

- **Level-ups never stop play.** No pop-up that has to be closed, no pause. A player mid-gather keeps gathering.
- **Name tags** show the player level and prestige icon, so other players can see them in the hub.

---

## 7. Keeping XP safe (Proposed)

The pace target is "nonstop, 24 hours a day". **Only bots play nonstop.** So the players who actually reach the decided pace will be scripts unless the server stops them. Fixing this later means resetting progress, which players hate, so it has to be in from the start.

- **The server grants all XP.** The game asks; the server checks and answers. This is the same check the mint token roll already needs: "every gathering action the server accepts" (D-078, `ACCOUNTS-AND-DATA.md`).
- **A gather is accepted only if:** it was started at a real node, the player was in reach, the tool is good enough for the tier, and at least the gather time has passed (with a small allowance for lag). Anything faster is refused and logged.
- **Each gather is started by the player.** No auto-repeat. Pressing F once per gather keeps idle macros from running for hours unnoticed.
- **Flag, don't ban automatically.** An account that gathers more than about 16 hours in any 24 is put on a list for a person to look at. Real players do play long sessions, so a human decides.
- **The browser can only read XP.** Every write goes through a server function, as `ACCOUNTS-AND-DATA.md` already proposes for every game table.

### 7.1 Data (Proposed)

Columns only. Table names follow the lowercase rule (`game_direction.md` section 11).

| Table | One row per | Columns |
| --- | --- | --- |
| `player_progress` | Account | `account_id`, `player_xp`, `prestige` (0 to 5), `lifetime_player_xp`, `updated_at` |
| `skill_xp` | Account and skill | `account_id`, `skill` (`mining`, `lumbering`, `foraging`, `hunting`, `fishing`), `xp`, `updated_at` |
| `tool_first_crafts` | Account and tool | `account_id`, `tool_id`, `crafted_at`. Stops the first-craft bonus paying twice |

- XP columns are **bigint** (whole numbers, no decimals).
- Levels are never stored (section 4).
- **Until the server exists**, the game saves XP in `user://save.json` like everything else, labelled **TEST** in the code and the UI.

---

## 8. Building it (Proposed)

For whoever builds it in Godot. Only decided or approved rules get built (`BUILD-ROADMAP.md`); until then anything built from this doc is labelled TEST.

- One autoload, `godot-game/autoload/progress.gd`, holding `skill_xp`, `player_xp`, `prestige` and `lifetime_player_xp`, saved by `Save`.
- Static functions `skill_level(xp)` and `player_level(xp)`, using tables built once at start from the formulas in sections 4 and 5.1.
- One entry point per source: `add_gather(skill, item_id, seconds, gem)`, `add_processing(...)`, `add_first_craft(tool_id)`. No other code changes XP.
- Signals `xp_gained(skill, amount)`, `skill_level_up(skill, level)`, `player_level_up(level)` and `prestiged(n)`. The HUD, toasts, chat lines and effects listen to them. The XP logic knows nothing about the UI.
- A headless test that checks the curve against the decided table (`resource_gathering.md` section 3: level 2 is 83 XP, level 100 is 14,391,160).

---

## 9. Open questions

1. ~~**Player XP amounts.**~~ *Answered (D-121): the sources and amounts in section 3.2 are accepted.*
2. **Processing XP.** Should processing ever give skill XP? Today the pace is worked out from gathering only.
3. **Holder bonuses.** Is "no XP multipliers for holders" (section 3.3) accepted?
4. **XP events.** Can a world event (like the ore events in PR #50) give bonus XP? If yes, only to players who join it in the world, never to everyone online.
5. **Leaderboards.** Are XP leaderboards wanted (per skill, total level, lifetime player XP)? This doc stores what they would need.
6. **The other doc set.** The IMPLINGZ docs say "there are no skill levels" and gate gathering with energy. See section 10.

---

## 10. Where the two doc sets disagree

Not fixed here. Which set wins is an Open question for the two collaborators (`docs/README.md`).

| Topic | J00BA's docs | IMPLINGZ docs | Effect on XP |
| --- | --- | --- | --- |
| Skill levels | Five skills, 1 to 100, with skill trees (`game_direction.md` section 6.2) | "There are no skill levels" (`01-activities.md` question 3) | This doc only works with J00BA's set |
| Energy | Not mentioned. The pace is worked out for nonstop play | 100 energy, 5 per gather, reset twice a day (D-008, D-061); sessions of 10 to 20 minutes twice a day (D-084) | With energy, a player gets 40 gathers a day. Claude's model of that (best tier at each level, every gather used) puts Mining 100 at about **180 days**, not 75. And at the top tiers, 20 gathers of 1,000 seconds take over 5 hours, so the "10 to 20 minute session" can't hold either. The two sets need one answer before XP values are final |
| Resource tables | Coal to Stellarite, Pine to Worldbark, 10 tiers each | Different trees (Ash, Oak, D-105), 10 plants (D-062), 16 animals (D-068), 10 fish (D-109) | Foraging, Fishing and Hunting XP can't be set until one table is chosen per skill |
