# 00: Overview

| Status | Last pass | Depends on |
|---|---|---|
| In review | User additions, 2026-10-21 | n/a |

> Every other doc must agree with this one. If a system doc conflicts with it, the overview wins until the user decides otherwise.
>
> Labels: **Decided** (in `DECISIONS.md`) · **Proposed** (Claude's suggestion) · **Open question**

---

## 1. One-line pitch
**Proposed:** *Gather, craft and tame your way up a cartoon browser world as your own Imp, then battle your tamed animals and trade what you've earned.*

The first working version (*Collect, raise and battle your Implingz…*) no longer fits: the Imp is the player's character, and tamed animals battle (D-080).

## 2. What we know so far
- **Decided (D-001):** a web game built around the IMPLINGZ NFT collection.
- **Decided (D-002):** five systems: activities, resources, games, trade and skirmish.
- **Decided (D-036):** a grinding, resource-gathering game that keeps growing: mining, lumbering, hunting, fishing, farming and foraging, with more later.
- **Decided (D-037):** built in the **Godot** engine, in 3D. The Three.js build in this repo was a test; its decided rules carry over. See [GODOT.md](GODOT.md).
- **Decided (D-038, D-039):** NFT holders can play as their Imp. Little else touches crypto: a linked wallet and mint tokens. IMP coins are in-game only.
- **Decided (D-040):** gathering can find **mint tokens**, saved to the account and spent on impz.club to claim NFT mints. Mining only, at first.
- **Decided (D-041 to D-043):** email accounts with a username and a linked wallet (MetaMask or Rabby). Staked IMP coins carry into the game. One Supabase database is shared with impz.club. See [ACCOUNTS-AND-DATA.md](ACCOUNTS-AND-DATA.md).
- **Decided (D-045 to D-048):** only Imp holders can find mint tokens. The game is played in the browser. The world is stylised cartoon; items and enemies have a slight voxel feel. Implings are on Robinhood Chain and will move to ApeChain.
- **Decided (D-049, D-050):** players without an Imp play as a basic Imp model. Staking is finished for now.
- **Decided (D-080 to D-112, 2026-10-21):** tamed animals battle in turn-based skirmish and the Imp is the trainer. Players trade in-game with a 5% fee. Desktop first, two short check-ins a day. New pillars and core loop (sections 3 and 4). Skirmish, games and trade are drafted in 03–05. Lumbering and fishing are designed in 02.
- **The build:** the Three.js prototype proved a third-person world with gathering, jump and emotes (COLLAB_IMPZ PR #5). It was removed on 2026-10-22 (D-113). The Godot game in `godot-game/` has the walk, jump and all five gathering skills (BUILD-ROADMAP). Emotes and the chat panel are not rebuilt in Godot yet.

## 3. Design pillars
Pillars are the rules every feature is judged against. If a feature doesn't serve one, it gets cut.

**Decided (D-085):**
1. **Steady progress.** Every session moves you forward: a new tool, tier, tame or rank.
2. **Fun before finance.** The game must be worth playing with the NFT and mint tokens removed. If players only stay for money, the economy collapses when the price drops.
3. **Skills feed each other.** Small, deep loops: ore makes sickles, plants tame animals, animals battle, logs make rods. A new feature must plug into the others.
4. **Fair to free players.** Non-holders can play everything. Holders get their own Imp's look and mint tokens, never more power.

## 4. Core loop
The core loop is the cycle a player repeats every session. Each system doc must show where it sits in this loop.

**Decided (D-086):**

```
Gather (energy) ──► Process (furnace, drying, tanning, sawbench, campfire)
     ▲                         │
     │                         ▼
  Better tools ◄── Craft ◄── Items ──► Sell / trade ──► Coins
                               │
                               ▼
                    Tame animals ──► Skirmish & games
                                          │
                                          ▼
                             Rewards, rank, rare items

Imp holders: gathering can also find mint tokens.
```

1. **Activities** (mining, foraging, hunting, lumbering, fishing, later farming) spend energy and produce **items**.
2. Stations **process** them: ore into ingots, plants into bundles, hides into leather, logs into planks, fish into cooked fish.
3. Items **craft better tools**, are **sold** to the merchant or **traded** for coins, or **tame animals**.
4. Tamed animals fight in **skirmish** and race in **minigames**, for XP, coins and rank, with no energy (D-092).
5. Better tools open higher tiers, and the loop starts again.

## 5. Systems map
| System | Its job in the loop | Doc |
|---|---|---|
| Activities | Turns time into resources | [01](01-activities.md) |
| Resources | The economy everything else runs on: sources and sinks | [02](02-resources.md) |
| Games | Variety, plus rewards that activities can't give | [03](03-games.md) |
| Trade | Moves value between players and gives resources a price | [04](04-trade.md) |
| Skirmish | The main way to test and show off your tamed animals (D-080) | [05](05-skirmish.md) |

## 6. Target player and platform
**Decided:** fans of idle and grinding games, with Imp holders as the core community (D-082). The browser (D-046), desktop first and phones later (D-083). Two short check-ins a day of about 10–20 minutes (D-084).

## 7. Scope guardrails
**Proposed:** things we will *not* do in the first version unless the user says otherwise:
- No open-world MMO. Small shared spaces or instanced areas only.
- No real-time action combat. Skirmish is turn-based.
- No more than one currency until the economy doc proves it needs a second.

---

## Open questions
All answered on 2026-10-21, except the one-line pitch, which is Proposed in section 1.

1. **What is an Impling NFT in the game?** Is it the creature you battle with in skirmish, or an avatar, land or item? *Answered (D-038, D-080): holders play as their Imp, and the Imp is the trainer. Tamed animals battle.*
2. **Can people play without owning an NFT?** For example, a free starter Impling, or renting one. *Answered (D-049): yes, as a basic Imp model that isn't part of the collection. They can't find mint tokens (D-045).*
3. **Is there an earning layer?** Can resources or items leave the game as tokens or NFTs, or is trading only inside the game? This decides how much anti-bot and anti-inflation design we need. *Answered (D-039, D-040, D-081): items and coins never leave the game, and players trade them in-game with a fee. Mint tokens, spent on impz.club, are the only earning layer, so anti-bot design is still needed (ACCOUNTS-AND-DATA, section 8; 04).*
4. **Who is the target player?** NFT collectors, casual browser gamers or creature-collector fans? *Answered (D-082): fans of idle and grinding games, with Imp holders as the core community.*
5. **Platform and session length.** Desktop browser only, or mobile too? Do sessions last 5 minutes or 1 hour? *Answered (D-046, D-083, D-084): the browser, desktop first, phones later; two short check-ins a day.*
6. **Do you agree with the proposed pillars and core loop above?** Change, cut or add as you like. *Answered (D-085, D-086): new pillars and a revised loop.*

---

## Pass history
| Pass | Change |
|---|---|
| 0 | First draft. Pitch, pillars, loop and guardrails proposed; open questions listed. |
| User addition, 2026-10-20 | Section 2 updated with D-036 to D-050. Questions 1, 3 and 5 marked partly answered. Question 2 answered (D-049). |
| User additions, 2026-10-21 | Every open question answered (D-080 to D-086). Pillars and core loop Decided. New pitch Proposed. Status In review. |
