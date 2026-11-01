# 03: Games

| Status | Last pass | Depends on |
|---|---|---|
| Draft | User additions, 2026-10-21 | 00, 02 |

> Must agree with [00-overview](00-overview.md) and [02-resources](02-resources.md).
> Labels: **Decided** (in `DECISIONS.md`) · **Proposed** (Claude's suggestion) · **Open question**

**Purpose of this doc:** Minigames: short side activities that add variety and give rewards gathering and skirmish don't.

---

## 1. Role in the core loop
Minigames sit next to skirmish at the end of the loop (D-086). They need no energy, so they fill sessions after energy is spent (D-084). They give out coins, cosmetics and a capped amount of items (D-097), and competitive ones take a coin fee that is partly destroyed (D-098).

## 2. Player experience
**Proposed:** something quick and different from clicking veins. The dig is a one-minute daily surprise. Races are a light competition for your tamed animals. Mine rush and boss raid are the social moments, where players do something together.

## 3. Rules & mechanics

### Decided (D-096 to D-098)
- **Four minigames:** animal races, a daily treasure dig, mine rush and boss raid. **The dig is built first** (D-096).
- **Prizes:** coins, cosmetics and items. **Item prizes are capped per day** for each minigame and **never roll mint tokens** (D-097).
- **Fees:** solo and daily minigames are free. Competitive ones take a small coin fee, and part of it is destroyed. Prizes come from the game, never from other players' fees, so a minigame is never a bet (D-098).

### The four minigames (Proposed details)

| Minigame | Players | How it plays | Fee | Prizes |
|---|---|---|---|---|
| **Daily treasure dig** | Solo | Once per energy reset, a 5×5 grid of soil. Pick 3 squares. Each reveals a prize or nothing. About 1 minute. | Free | Coins, sometimes raw items of a tier the player can already gather, rarely a cosmetic |
| **Animal races** | Competitive, 4 to 6 players | Enter one tamed animal. The race is a short track with a few jumps and turns. Speed comes from the animal's level and Speed stat (05). Players press a button at the right moments for small boosts. | Small coin fee, half destroyed | Coins by place, race-only cosmetics. The prize amount is fixed by the game. |
| **Mine rush** | Co-op, everyone nearby | Sometimes a rich vein appears for a few minutes. Everyone nearby mines it together, and it pays out to all who helped. Mining it costs no energy. | Free | Ore of the vein's tier, capped per day (D-097) |
| **Boss raid** | Co-op, teams of players | Once a week, a big boss fought with skirmish rules. Each player brings a team of 3. | Free | Coins, raid-only cosmetics, items capped per week |

**The dig's board (Proposed, 2026-10-22).** It replaces the TEST numbers (9 coin squares, 2 item squares, 5 to 20 coins). The 25 squares are dealt at random each reset:

| Squares | What's under them |
|---|---|
| 12 | Nothing |
| 9 | Coins: **2 b to 8 b**, times the player's highest gathering tier, divided by 4, so it keeps pace with the merchant (b is the base price proposed in 02) |
| 3 | An item: 3 raw items of a tier the player can already gather, in a random skill |
| 1 | A rare find: a cosmetic, 1 chance in 20, otherwise one rare drop (gem, seed, sap, pearl or trophy) of a tier the player can already gather |

With 3 picks, a dig is worth about **3.6 b × the player's tier** on average, roughly **a sixth of a full bar of gathering** (20 to 25 b × tier), plus the small chance of a cosmetic. It's a reason to log in, not a second income. The item cap below still applies: after the first item, more item squares pay coins instead. **Rare finds never include mint tokens** (D-097).

**Daily item caps (Proposed):** the dig pays at most 1 item prize per reset. Mine rush pays at most 10 ore per day. The boss raid pays at most 1 item reward per week. These keep minigames from out-earning a bar of energy.

**Multiplayer:** races, mine rush and boss raid need other players to be online at the same time. The game has no multiplayer server yet (chat is local). They wait until the Godot build has one.

## 4. Inputs & outputs
| Takes in | Gives out | Notes |
|---|---|---|
| Nothing, once per reset | Dig prizes | **Decided** free (D-098), capped (D-097). The grid is **Proposed**. |
| A coin fee and one tamed animal | A race place, coins and cosmetics | **Decided** fee partly destroyed (D-098). The fee size and the destroyed half are **Proposed**. |
| Time with other players | Ore (mine rush), coins and cosmetics (boss raid) | **Decided** capped (D-097). Details **Proposed**. |

## 5. NFT touchpoints
- **Decided (D-097):** minigame prizes never roll mint tokens.
- Holders and non-holders play every minigame the same way (D-085).

## 6. Risks
- **Gambling.** A fee pool paid out to winners would be gambling with coins that came from staking. Handled: prizes come from the game, not from other players' fees (D-098).
- **Out-earning gathering.** Item prizes without a cap would get around the energy limit. Handled by the daily caps (D-097).
- **Scope.** Four minigames is a lot for two people, and three of them need multiplayer. **Proposed order:** dig, then races, then mine rush, then boss raid.
- **Bots in races.** The server decides the result from the animal's stats and the inputs it accepts, and race prizes are capped.

## 7. Smallest first version
**Decided (D-096):** the daily treasure dig. **Proposed:** a 5×5 grid, 3 picks, prizes of coins and tier 1–3 raw items, once per energy reset.

## 8. Done when…
*The conditions for the user to sign this off. Agreed with the user.* **Proposed:** the dig is built and played. The prize tables for all four minigames are approved. The prize caps have been checked against the energy limit.

---

## Questions this doc must answer
1. Which minigames, and why each one? What does it add that activities or skirmish don't? *Answered (D-096): dig (a daily surprise), races (competition for tamed animals), mine rush and boss raid (playing together).*
2. Solo, co-op or competitive? *Answered by the list: the dig is solo, races are competitive, mine rush and boss raid are co-op.*
3. Rewards: which resources, how much, and how often? Check against the sinks in `02-resources.md`. *Answered in part (D-097): coins, cosmetics and items, capped per day. Amounts Proposed.*
4. Entry costs (if any), which act as a resource sink. *Answered (D-098).*
5. Can Implingz take part, and do their stats matter? *Tamed animals race and fight raids. The Imp is the player's character (D-080).*
6. Smallest version worth building first. *Answered (D-096): the daily treasure dig.*

## Pass history
| Pass | Change |
|---|---|
| 0 | Template created with the questions to answer. |
| User additions, 2026-10-21 | Four minigames, dig first (D-096), prizes with daily item caps and no mint tokens (D-097), free daily games and partly-destroyed fees for competitive ones (D-098). How each minigame plays is Proposed. Status Draft. |
| User addition, 2026-10-22 | The dig's board Proposed: what the 25 squares hold, and what a dig is worth against a bar of gathering. |
