# 04: Trade system

| Status | Last pass | Depends on |
|---|---|---|
| Draft | User additions, 2026-10-21 | 00, 02 |

> Must agree with [00-overview](00-overview.md) and [02-resources](02-resources.md).
> Labels: **Decided** (in `DECISIONS.md`) · **Proposed** (Claude's suggestion) · **Open question**

**Purpose of this doc:** How items and coins move between players.

---

## 1. Role in the core loop
Trade turns items into coins and coins into items between players (D-086). It gives every item a price set by players, next to the merchant's fixed price (D-074). Its 5% fee is a coin sink (D-100).

## 2. Player experience
**Proposed:** a player who has too much Bluebell and needs Iron ingots can sort it out in a minute, at the market board or with a friend. Prices feel fair because anyone can list. Scams are hard because the game does the swap, not the players.

## 3. Rules & mechanics

### Decided (D-081, D-099 to D-102)
- **In-game only.** Nothing leaves the game, and mint tokens can't be traded (D-039, D-081).
- **Two ways to trade:** a **market board** and **direct trades** (D-099).
- **Fee:** **5%** of the coins in every market sale and every direct trade. The seller pays it and it is destroyed. Item-for-item swaps pay nothing (D-100).
- **Who can trade:** accounts at least **7 days old that have made some progress**. Direct trades need both players nearby (D-101).
- **Tamed animals can't be traded** (D-102).

### The market board (Proposed)
- A seller lists a stack of items with a price per item in coins. The items leave their inventory until the listing sells or is cancelled.
- A listing lasts **48 hours**, then the items go back to the seller.
- **At most 10 listings** per player at a time.
- A buyer pays the full price. The seller gets the price minus 5% (D-100).
- The board shows the last few sale prices for each item, so players can price sensibly.
- **Price floor:** an item can't be listed below the merchant's sell price (D-074). Nobody would sell that low except to move coins between their own accounts, which is the wash-trading this rule is meant to stop.

### Direct trades (Proposed)
- Both players open a trade window. Each puts in items and/or coins. Both must press **Accept** twice (once to lock, once to confirm) before anything moves.
- The server swaps everything in one step, so a trade can't half-complete.
- If coins are in the trade, 5% of them is destroyed (D-100).

### "Some progress" (Proposed, D-101)
The account owns the **Iron pickaxe**. That takes a few days of real play and is hard for a throwaway bot account to reach.

## 4. Inputs & outputs
| Takes in | Gives out | Notes |
|---|---|---|
| Items listed with a price | Coins, minus 5% | **Decided** (D-099, D-100). Listing rules **Proposed**. |
| Coins | Listed items | **Decided** (D-099). |
| Items and/or coins in a direct trade | The other player's items and/or coins, minus 5% of any coins | **Decided** (D-099 to D-101). |

## 5. NFT touchpoints
- **Decided (D-081):** trade is in-game only. Items, coins and mint tokens never leave the game.
- Imps are traded on NFT marketplaces, outside the game. When an Imp is sold, the new owner plays as it and the old owner goes back to the basic Imp (ACCOUNTS-AND-DATA, section 4).

## 6. Risks
- **Bots selling to players** (real-money trading outside the game). Handled in part by the 7-day and progress rule (D-101) and the 5% fee. Watch the market for accounts that only ever sell.
- **Wash trading and moving coins between accounts.** The price floor (Proposed) and the fee make it costly.
- **Scams in direct trades.** The double accept and the one-step swap (Proposed).
- **Multi-accounting.** One wallet per account (ACCOUNTS-AND-DATA). Accounts without wallets can still be farmed; the progress rule slows that down.
- **Legal (flag only, not legal advice):** coins came partly from staking an NFT, and items have player-set coin prices. As long as nothing can be cashed out (D-081), the risk is low. Get advice before anything in the game can be exchanged for crypto or money.

## 7. Smallest first version (Proposed)
The market board only, with listings, the 5% fee, the 48-hour expiry and the price floor. Direct trades come next.

## 8. Done when…
*The conditions for the user to sign this off. Agreed with the user.* **Proposed:** the listing rules and the progress check are approved, and the fee has been checked against the coin sources in 02.

---

## Questions this doc must answer
1. Direct player-to-player trade, a marketplace/auction house, or both? *Answered (D-099): both.*
2. In-game only, or linked to an external NFT marketplace? *Answered (D-081): in-game only.*
3. Fees or taxes on trades, which are a key resource sink. *Answered (D-100): 5%, destroyed.*
4. Anti-abuse: scams, bot-to-player selling, wash trading, multi-accounting. *Answered in part (D-101). The rest is Proposed in sections 3 and 6.*
5. Can Implingz themselves be traded, and does their progress go with them? *Tamed animals can't be traded (D-102). Imps are NFTs and trade outside the game.*
6. What legal/regulatory points need checking? *Flagged in section 6.*

## Pass history
| Pass | Change |
|---|---|
| 0 | Template created with the questions to answer. |
| User additions, 2026-10-21 | In-game trade with a fee (D-081), market and direct trades (D-099), 5% destroyed fee (D-100), 7 days and progress before trading (D-101), animals can't be traded (D-102). Listing rules, the price floor and the progress check are Proposed. Status Draft. |
