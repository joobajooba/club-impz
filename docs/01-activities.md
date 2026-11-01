# 01: Activities

| Status | Last pass | Depends on |
|---|---|---|
| Draft | User additions, 2026-10-21 | 00, 02 |

> Must agree with [00-overview](00-overview.md) and [02-resources](02-resources.md).
> Labels: **Decided** (in `DECISIONS.md`) · **Proposed** (Claude's suggestion) · **Open question**

**Purpose of this doc:** What players do in the world from moment to moment, and what each activity produces.

---

## 1. Role in the core loop
Activities are the start of the loop (D-086). They take in **energy** (one shared pool, D-061) and **tools**, and give out **items** for processing, crafting, selling, trading and taming.

## 2. Player experience
**Proposed:** a calm, satisfying routine: log in, spend a bar of energy on whichever skill you're pushing, and see a tool or tier get closer. Every skill plays the same way at its core (walk up, press F), so the variety comes from what each skill feeds.

## 3. Rules & mechanics
*How it works, precise enough for a developer to build from.*

### Activity list (Decided, D-036)

The game is a grinding, resource-gathering game that keeps growing. These are its gathering activities. More can be added later.

| Activity | Design | Where |
|---|---|---|
| Mining | Decided (D-005 to D-013, D-020, D-054 to D-060) and built in Godot (COLLAB_IMPZ PR #36) | [02](02-resources.md#mining-tiers-decided-d-005) |
| Foraging | Decided (D-022 to D-027, D-061 to D-066) | [02](02-resources.md#foraging-tiers-decided-d-022-to-d-027) |
| Hunting | Decided (D-028 to D-035, D-067 to D-072) | [02](02-resources.md#hunting-tiers-decided-d-028-to-d-035) |
| Lumbering | Decided (D-105 to D-108) | [02](02-resources.md#lumbering-tiers-decided-d-105-to-d-108) |
| Fishing | Decided (D-109 to D-112) | [02](02-resources.md#fishing-tiers-decided-d-109-to-d-112) |
| Farming | Proposed only (D-065 decides seeds go here) | [below](#farming-proposed) |

**Mint tokens (Decided, D-040, D-045):** any gathering action by an **Imp holder** has a chance to find a mint token. In the first phase only mining can. See [ACCOUNTS-AND-DATA.md](ACCOUNTS-AND-DATA.md#6-mint-tokens-decided-d-040-d-045-rules-proposed).

### Farming (Proposed)

Farming isn't designed yet. Only one thing is decided: seeds are planted in farming to grow their plant (D-065). **Proposed**, for the user to decide:

- Each player has a small farm with **6 plots**.
- Planting a seed costs **no energy**. The plant grows in real time: **2 hours** for tier 1 up to **12 hours** for tier 10, so a harvest lines up with the twice-a-day check-in (D-084).
- **Harvesting costs 5 energy** from the shared pool and gives **3 to 5 plants** of that tier. It needs the sickle for that tier (D-024), so farming adds no new tool line.
- A harvest can give the seed back, at the seed chances (D-025).
- Harvesting counts as a gathering action, so it can roll mint tokens once farming joins mining in finding them (D-040).
- **Where (added 2026-10-22):** a fenced farm patch at the camp, next to the drying rack, so a harvest goes straight to drying. **Extra plots** are bought like inventory rows (D-077): the same doubling series and cap as the prices proposed in 02. That makes 6 plots grow to 10.
- **What can be planted:** any seed you hold. Harvesting a plant needs the sickle for its tier (D-024), so a high seed found early waits until you have the sickle for it.
- **Nothing is lost:** a ripe plant waits in its plot until it's harvested. It doesn't wither, so players who check in twice a day (D-084) aren't punished for being late.
- **Server check:** planting time and ripeness are checked by the server once accounts exist (G6), the same way the energy reset is (ACCOUNTS-AND-DATA, section 8). Until then, the build would use the player's clock as a TEST.


## 4. Inputs & outputs
| Takes in | Gives out | Notes |
|---|---|---|
| | | |

## 5. NFT touchpoints
*Where the NFT or the blockchain is involved, and where it deliberately isn't.*

- **Decided (D-040, D-045):** gathering by Imp holders can find mint tokens (mining only, at first).
- **Decided (D-038):** the player can gather as their Imp.
- Gathered items and coins are not on-chain (D-039).

## 6. Risks
*Abuse, balance or scope risks, and how we handle each.*

## 7. Smallest first version
*The least we could build to test whether this system is fun.*

## 8. Done when…
*The conditions for the user to sign this off. Agreed with the user.*

---

## Questions this doc must answer
1. What activities exist at launch (mining, foraging, fishing, crafting…)? The prototype already has ore veins. *Answered (D-036): mining, foraging, hunting, lumbering, fishing and farming. Farming is only Proposed so far.*
2. What does each activity output, and which resource in `02-resources.md` is it? *Answered: the tier tables in 02 for each activity.*
3. How does an activity get better over time (skill levels, tools, Impling help)? *Answered: better tools open higher tiers (D-006, D-024, D-034, D-106, D-110). A tamed animal helps hunting (D-072). There are no skill levels.*
4. What stops bots from farming an activity 24/7? (Critical if resources have real-money value.) *Answered in part: the energy limit (D-008, D-061), server-checked actions (ACCOUNTS-AND-DATA, section 8), and mint tokens for holders only (D-045).*
5. Are there limits per day (energy, cooldowns), and do they feel fair? *Answered (D-008, D-057, D-061, D-076): one shared 100-energy pool, reset twice a day, and at most one refill per reset.*
6. Does owning an Impling change or boost activities? *Answered (D-045, D-085): holders can find mint tokens. Nothing else changes, so free players aren't held back.*

## Pass history
| Pass | Change |
|---|---|
| 0 | Template created with the questions to answer. |
| User addition, 2026-10-20 | Activity list (D-036) and mint tokens (D-040) added. Question 1 answered. Status Draft. |
| User additions, 2026-10-21 | Lumbering (D-105 to D-108) and fishing (D-109 to D-112) designed in 02. Farming Proposed. Sections 1 and 2 filled. Every question answered. Mint token link fixed. |
| User addition, 2026-10-22 | Farming Proposed further: where the farm is, extra plots, what can be planted, ripe plants wait, server check. |
