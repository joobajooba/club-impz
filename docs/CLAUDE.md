# Design folder: rules for Claude

These rules apply to any work in `docs/`. They sit on top of the repo's root `CLAUDE.md`, and its GitHub workflow still applies: every change goes to a `staging/` branch and a draft PR, never straight to `main`.

## 1. What this folder is

The game design for **IMPLINGZ**, an NFT web game. The design is built as a **roadmap worked in passes** (scrum sprints). Each pass improves the docs. The passes repeat until **the user** says a doc is done.

| File | What it holds |
|---|---|
| `ROADMAP.md` | The passes, the status of every doc, and what the current pass is working on. **Read this first, every time.** |
| `BUILD-ROADMAP.md` | The playable game: what is built, what is in review, and the next milestones. Only decided rules get built. Read it before any code change. |
| `DECISIONS.md` | Every decision the user has made, with its date. These decisions are the source of truth. |
| `ART-DIRECTION.md` | The art style (D-014, D-015): cartoon stylised 3D for the world, 2D pixel art for menus and inventory, the reference listings, and the checklist every 3D asset must pass. |
| `GODOT.md` | The game is built in Godot (D-037): what carries over from the Three.js test, layout, import settings, milestones. Read it before any Godot work. |
| `ACCOUNTS-AND-DATA.md` | Accounts, wallets, IMP coins, mint tokens and the shared Supabase database (D-038 to D-043, D-045, D-048). Read it before any code that saves data or touches coins, tokens or wallets. |
| `MODELS-BLOCKBENCH.md` | Blockbench models with a slight voxel feel for tools, weapons, creatures and items, in a stylised world (D-044, D-047). Read it before any Blockbench work. |
| `00-overview.md` | The game's intent, core loop and the role of the NFT. Every other doc must agree with it. |
| `01`–`05` | One doc per system: activities, resources, games, trade, skirmish. |
| `reports/` | One report per pass, plus any report the user asks for. |
| `../sprites/items/` | 48×48 inventory PNGs. Not inside `docs/`, but part of the resources design. The catalog is in `02-resources.md`. |

## Item pictures

Before writing or changing anything about ores, gems, ingots, mining rewards or inventory icons, open every PNG in `sprites/items/` and read the catalog in `02-resources.md`. Match each file to that table. The picture is the source of truth for how an item looks. Do not describe an item from its filename alone.

`nugget_` is the ore rock you mine. `ingot_` is the bar picture. `gemstone_` is the gem that can come with that ore. Coal has no ingot file. `prestige_0.png` through `prestige_5.png` are in the same folder and are not mining rewards. Their use is not decided. Do not add them to a tier.

The gem chance is decided (D-012): 10% for Tin, falling 1% per tier to 1% for Stellarite. It is doubled while the player holds the Stellarite pickaxe (D-059).

Pickaxes are decided (D-006): which pickaxe mines which ore, and the ingots and hilt each crafted pickaxe takes. Record those exactly. The Titanite pickaxe takes Titanite ingots (D-060, superseding that row of D-006). A pickaxe also mines every ore below its named ore (D-011). Stone has no craft row. Do not invent a Stone recipe.

How the furnace works and how players get hilts are decided (D-054 to D-058): ore per ingot by tier, Coal as fuel from Gold up, no energy for smelting or crafting, and Void and Cosmic hilts from ingots and a gem. Ash Wood and Oak Wood hilts are made from 5 Ash or Oak planks (D-107). Until the build is updated it runs on labelled test values (D-013: 2 ore make 1 ingot, the blacksmith supplies hilts). Do not present those test values as the design. Other blacksmithing, other crafting, and selling are not decided. Do not invent them.

## 3D art

Before making, buying, editing or reviewing any 3D model, material, light or scene layout, read `ART-DIRECTION.md`. Anything in the world is 3D and follows that doc (D-014). Menus and inventory icons are 2D pixel art (D-015). Never put pixel-art textures on a 3D model, except Blockbench items and enemies (D-044, D-047), which follow `MODELS-BLOCKBENCH.md`. When an item has both an icon and a model, the model takes its colours from the icon. Run the doc's review checklist on every 3D asset and note the result in the PR.

## 2. Do not deviate

- Work **only** on what the user asked for in this session, or on the current pass's items in `ROADMAP.md` if the user says "continue the pass".
- Do **not** add, remove, rename or restructure files, sections, systems or features unless the user explicitly asks.
- Do **not** change a decision recorded in `DECISIONS.md`. If new work conflicts with one, stop and tell the user.
- If you think something should change, write it under **Suggestions** in the report. Do not put it in the docs. The user decides.
- If a request is unclear, ask one short question before writing. A wrong guess costs more than a question.

## 3. Quality first

- Quality matters more than speed or volume. Go one doc, or one section, at a time.
- No filler. Every line should say something a designer or developer could act on. Cut generic game-design padding.
- Never present a guess as a decision. Label every item as one of:
  - **Decided**: the user decided it. It is in `DECISIONS.md` (give the D-number).
  - **Proposed**: Claude's suggestion, waiting for the user.
  - **Open question**: not settled yet.
- Check consistency before finishing. Do resources named in one doc exist in `02-resources.md`? Does every system fit the core loop in `00-overview.md`? List any mismatch in the report. Do not quietly fix it in another doc.
- Push back honestly. If an idea has a real problem (economy inflation, bot farming, pay-to-win, scope too big for two people), say so plainly and explain why. Do not just agree.

## 4. Status rules

Docs move through these statuses. They are tracked in `ROADMAP.md`:

`Not started` → `Draft` → `In review` → `Signed off`

- Claude can move a doc up to **In review**.
- **Only the user can mark a doc `Signed off`.** Claude never does.
- If the user asks for changes to a signed-off doc, it goes back to `In review`.

## 5. Running a pass

1. Read `ROADMAP.md`, `DECISIONS.md` and the docs for the current pass.
2. Confirm the pass goal with the user in one or two lines, then work through its items.
3. Record any new user decisions in `DECISIONS.md` straight away.
4. Update the statuses and the pass log in `ROADMAP.md`.
5. Write the pass report (section 6).
6. Commit everything on a `staging/design-<topic>` branch and open a draft PR, following the root `CLAUDE.md`.

## 6. Reports

Write a report at the end of every pass, and whenever the user asks "what's been done?" or similar.

- File name: `reports/YYYY-MM-DD-pass-N.md`. For an extra report: `reports/YYYY-MM-DD-<topic>.md`.
- Use the template in `reports/_TEMPLATE.md`. Do not change its sections.
- Build the report from real evidence. Check all three sources:
  - **GitHub**: `git log`, branches, open and merged PRs (`gh pr list --state all`), backup tags.
  - **Claude**: what was done in this and earlier sessions, taken from previous reports, `DECISIONS.md` and the pass log.
  - **Folder structure**: which files were added, changed or removed (`git diff --stat`, `git status`).
- If a source can't be reached (for example, GitHub isn't connected), say so in the report. Do not guess.

## 7. Talking to the user

- Plain English, short sentences. Explain any game-design or blockchain term the first time you use it.
- Lead with the outcome. Then use this order: **What changed → Why → What's next → What I need from you.**
- Keep "What I need from you" to the few decisions that actually block progress, numbered so the user can answer quickly.
- Don't recap every step you took. The report holds the detail.
