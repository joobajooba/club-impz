# Report: Tool crafting mechanics, stage 2 (2026-11-22)

## In short
At the user's request, the tool crafting mechanics are taken one stage further, with the animations left alone. The new section 3.6 of `TOOL-CRAFTING-ROADMAP.md` adds five mechanics around the stage 1 crafting rules, and it settles the "ideas for later" that were left in the tree sections. Everything is **Proposed**. Four new calls (9 to 12) wait on the user.

## What changed
| Area | Change |
|---|---|
| Docs | `TOOL-CRAFTING-ROADMAP.md`: new section 3.6 (E1 to E5, plus considered and dropped); a header note; the ideas for later in 3.1 to 3.3 now point to 3.6; the stage 2 items are added to passes T0, T2, T4, T6 and T7, to build steps B3 and B6, and to 6.3 (the tool rack); calls 9 to 12. Status stays **Draft**. `ROADMAP.md`: row 32 updated, row 36 added, one pass-log row. `TOOL-ANIMATIONS.md` is unchanged. |
| Decisions | None |
| Folder | Added `docs/reports/2026-11-22-tool-mechanics-stage-2.md`. Changed `docs/TOOL-CRAFTING-ROADMAP.md` and `docs/ROADMAP.md`. |

**The five mechanics (all Proposed):**
- **E1. One mechanic at a time.** The first craft is one button that makes any missing parts, then assembles. Part rows, re-haft, take apart and the socket each appear the first time they can matter. The shopping list says where a missing raw material comes from.
- **E2. One cap for every boost.** The Stellarite pickaxe (D-059), tracking (D-072), potions and inlays multiply, capped at ×2.5 for all five rare drops. Without a cap, a Tin vein would pay 5× its ore's value; with it, 3.5×. Mint token chances never change.
- **E3. Pearls fit the socket.** Pearls have the gem chances (D-112) and no use besides selling. They now fill a socket like a gem, so fishing feeds every tool the way mining does.
- **E4. The reel sets the bite window.** The window narrows 4% a fish tier, and the reel wins it back (Tin ×1.1, Copper ×1.25, Bronze ×1.4). The newest fish you can catch stays between 0.90 and 1.06 of the base window, and older fish get easier.
- **E5. The tool rack.** Owned tools show on the rack beside the hub workbench and on the profile. Owning every tier of one kind at once gives a cosmetic and a title, like a trophy set. This turns take apart into a choice, and brings back some hilt demand.

**Dropped, with reasons in 3.6:** the sickle edge, axe heads for felling, a trophy in the legendary bows, the arrow-head slot, the bait slot (still blocked) and wear and repair.

## Evidence
- **GitHub:** Open draft PRs: #100, #103 to #110. This work is on `staging/design-tool-mechanics-evolution`, branched from `staging/design-tool-crafting-mechanics` (#110, head 0630711), as a stacked draft PR on #110. No merges and no backup tags since the last report.
- **Claude:** The 2026-11-21 roadmap (PR #108), the 2026-11-22 mechanics and animations (PR #110) and the godot imports (PR #109) are earlier sessions. This session added stage 2 only. Before writing, it read `DECISIONS.md` (D-006 to D-124 where relevant), `resource_gathering.md` sections 2, 5, 7 and 8, the potions in `02-resources.md`, and the fishing expansion report. All 223 item pictures were checked in the previous session. This session confirmed that the ten `pearl_*` icons and the `tool_rack` model exist.
- **Folder structure:** `git diff --stat` against #110: `docs/TOOL-CRAFTING-ROADMAP.md` +115/−11 lines (most of it section 3.6), `docs/ROADMAP.md` +4/−1, plus this report.

## Consistency check
- **The potion cap.** `02-resources.md` caps only the gem chance at ×2.5. E2 applies the same cap to every rare drop. `02-resources.md` is not changed. If call 9 is a yes, its potion limits line needs updating.
- **Fishing isn't built in Godot.** No fishing script exists (only `held_tool.gd` mentions fish), so the base window W in E4 has no build value. The curve is relative until it does.
- **What pearls and sap are for.** This is an open question in `resource_gathering.md` 5.1. E3 answers it for pearls only, and that doc is not changed. If call 10 is a yes, its open question narrows to sap.
- **The tool rack and the Steel tier.** A full pickaxe, axe or sickle rack means "every tier you can own", so it follows whichever ladder wins: `DECISIONS.md` (with Steel) or `resource_gathering.md` 2.1 (without it).
- No other mismatches found.

## Suggestions (not applied)
- If call 9 is a yes, show the current total multiplier (for example "×2.25 of ×2.5") on the potion and socket tooltips, so the cap is never a surprise.
- When fishing is built, measure the round-trip time on the web build before setting W (E4, push-back).

## What's next
Pass T1 still waits on calls 1 to 4. Stage 2 slots into passes already planned: E1 with T2 (the pilot tree and its menu), E4 with T4 (rods), E5 with T6 (re-haft and take apart), and E2 and E3 with T7 (inlays). No new pass is needed.

## What I need from you
1. **One cap for every boost** (call 9): ×2.5 for all five rare drops?
2. **Pearls in the socket** (call 10)?
3. **The reel sets the bite window** (call 11), or one window for every fish?
4. **The tool rack** (call 12): a full rack gives a cosmetic and a title?
