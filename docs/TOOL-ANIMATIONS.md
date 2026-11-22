# Tool animations

> **Proposed** by Claude on 2026-11-22, at the user's request: a write-up on animations, to take the tool crafting work further. Nothing here is decided. It covers how the Imp uses each tool and the crafting moments from `TOOL-CRAFTING-ROADMAP.md`. Creature animations are in `MODELS-BLOCKBENCH.md` section 4.5. No model is changed (rule P8 in the roadmap).

**Labels:** **Decided** (in `DECISIONS.md`, with its D-number), **Proposed** (Claude's suggestion, waiting for you), **Open question** (not settled).

---

## 1. What is built

### 1.1 Use animations

The tool animations are poses keyed in code, not Blockbench animations: `ACTIONS` in `godot-game/scripts/player/imp_visual.gd:50-96`, built by J00BA (commits 70a2823 and 1124f11, 2026-11-07). Each key sets the right arm, the tool's angle and roll in the fist, the chest's twist and lean, the left arm's swing and a body dip. Between keys the pose eases in (a strike) or out (a wind-up) (`_run_action`, `:290-331`). Because the keys move bones, one set works for every Imp look.

| Kind | Length | Motion | Hits | Impact effect (`imp_visual.gd:335-347`) |
|---|---|---|---|---|
| Pickaxe | 0.95 s | Overhead wind-up, strike down | 1 | Grey stone chips and orange sparks |
| Axe | 0.9 s | Diagonal chop across the body | 1 | Wood chips |
| Sickle | 1.05 s | Two low sweeps, out and back | 2 | Grass bits |
| Rod | 1.45 s | Overhead cast and follow-through | 0 | None |
| Sword | 0.72 s | Side slash | 1 | White glints |
| Bow | | **No animation.** E with a bow in hand does nothing. | | |

- **Swing trail:** a fading ribbon behind the head (`scripts/player/tool_fx.gd:10-49`, 0.16 s). White for most tools; purple for Void, pale blue for Stellarite, orange for Dreadstone (`imp_visual.gd:265-273`).
- **The world reacts:** each hit fires `struck` (`imp_visual.gd:114`). Trees shake, then fall with a burst of wood (`tree_chopper.gd:160-216`). Ore veins throw chips in the ore's colours and burst when they give ore (`ore_miner.gd:199-223`).
- **Held tools:** the rod's line swings like a pendulum (`scripts/tools/held_tool.gd:25-40`). Void and Stellarite tools play the idle animations from their Blockbench files (`held_tool.gd:7-8`).
- **What starts them:** E or left click opens a shop, chops a tree or mines a vein; otherwise it swings the tool in hand (`imp_player.gd:96-101`). Mining keeps swinging while a bar fills; a better pickaxe fills it faster, with the same swing (`ore_miner.gd:5-13`).
- **The server judges.** The game plays the swing and asks the server what was found (`GODOT.md`).

### 1.2 Gaps

1. **No bow animation,** and the bow models have no string (`TOOL-CRAFTING-ROADMAP.md` 1.3).
2. **Fishing stops at the cast.** The cast-and-bite loop (D-109: F to cast, F again inside a short window when a fish bites) runs only in the test scene, on a separate rig (`characters/gatherer.gd`: 3 swings of 0.8 s, a 0.7 s cast, a bobber).
3. **Every tier swings the same.** Only the model, the trail colour (three tiers) and two idles tell a Stone pickaxe from a Stellarite one.
4. **Crafting has no animation.** Press Craft and the item appears (`ui/station_menu.gd:96`).
5. **Other players don't see your tool.** `remote_imp.gd` has no tool or action code, and the live room doesn't send them.
6. **Rare drops have no moment.** A gem goes straight into the bag with the ore (`ore_miner.gd:9`).

---

## 2. Rules (Proposed)

- **A1. Animation never sets the pace or the result.** Gather times, the bite window and drops stay where the design and the server put them. An animation fits inside its action's time, not the other way round. Crafting stays instant (roadmap M2); its animation plays alongside and can be skipped.
- **A2. One set of keys per tool kind,** shared by every tier and every Imp look: 6 kinds, not 58 tools.
- **A3. Tiers show through cheap effects.** The trail colour comes from the tier's icon for every tier (not three), impact bursts grow with tier, and tiers 9 and 10 add a glint. CPU particles and unshaded ribbons only, as in `tool_fx.gd`, so the web build stays light.
- **A4. Cartoon timing.** Anticipation, strike, follow-through, settle, with exaggerated poses (`ART-DIRECTION.md`: "animation sells the cartoon"). A short hit-stop on each strike: the swing holds for 40 to 60 ms (call A).
- **A5. Keys in code, models untouched.** New motions are new `ACTIONS` entries. Anything a model lacks is drawn in code, the way the rod's line already is.
- **A6. Multiplayer sends events, not frames:** the tool in hand and each action's name, so other players see the same swing (call D).
- **A7. Parts show in the crafting moments** (section 4), not in the models.

## 3. Use animations: taking each tool further

| Tool | Today | Proposed |
|---|---|---|
| Pickaxe | Overhead strike | Chips sized by tier (A3). **Gem pop:** when a gem comes, its icon (`gemstone_*.png`) pops out of the vein and arcs into the Imp with a glint in its colour. |
| Axe | Diagonal chop | **Felling blow:** the chop that drops the tree gets a bigger wind-up (`axe_fell`). **Sap pop** with the `sap_<tree>` icon (sap is Proposed, `resource_gathering.md` 5.1). |
| Sickle | Two sweeps at nothing | **Foraging:** the plant sways with each sweep and pops into its bundle icon; a seed pops on a seed find. Needs foraging in the live world. |
| Rod | The cast | **The full loop.** `rod_wait`: the float bobs on its pendulum line. `rod_bite`: the float dunks and the tip jerks; this is the cue for D-109's window, so it must read at a glance and has a sound too. `rod_strike`: a sharp upward flick on F. `rod_reel`: the wrist circles two or three times and the rod bends (wrist keys; the model's reel isn't a separate group). `rod_catch`: the fish's icon arcs out of the water into the Imp. On a miss, the line goes slack and the float pops up. |
| Bow | Nothing | `bow_draw` (0.4 to 0.6 s): the bow stays in the right fist where tools are held, the left hand pulls the string back, the chest twists. The string is a line drawn in code between the bow's tips, through the left hand while drawn. `bow_release`: the string snaps straight, a short arrow streak (a trail, 0.1 s) flies to the animal and puffs on it. Arrows aren't used up (D-070), so nothing is spent. |
| Sword | Side slash | No change until combat is designed (roadmap pass T9). |

The bow needs one rig change: the left arm today has a single swing angle (`larm`), and the draw needs a full arm key like the right arm's.

## 4. Crafting moments

### 4.1 At the station (3D)

When you press a craft button, the Imp plays a short loop at the station, about 1 s, while the menu stays open. A batch plays the loop once.

| Station | Makes (roadmap 2.4) | Motion | Effect |
|---|---|---|---|
| Anvil | Heads, blades, reels, hilts | Three hammer strikes (the pickaxe keys with a shorter arc) | Sparks in the metal's icon colours |
| Sawbench | Rod blanks, bow staves | Push and pull saw strokes (`saw`) | Sawdust in the wood's colour |
| Tanning rack | Bow wraps, leather strips | Downward scrapes (`scrape`) | Small flecks in the leather's colour |
| Drying rack | Nettle Cord | A two-handed twist (`twist`) | Green flecks |
| Workbench | Assembly | A short tap-and-turn of the finished tool, which then appears in hand with a glint | The 2D moment in 4.2 |

**Props:** a hammer and a saw are the only new models this would need (small Blockbench props, D-044, with the `ART-DIRECTION.md` checklist). Without them the held tool is hidden and the effects carry the motion (call C).

### 4.2 In the menu (2D)

These use the 48×48 pixel-art icons (D-015). A click skips any of them.

- **Assemble:** the three part icons slide to the centre, a flash, and the tool's icon appears. The first time, a reveal card shows the tool's name, what it reaches and its first-craft XP (roadmap M11).
- **Take apart:** the tool's icon splits. The used-up parts crumble to dust; the returned hilt, reel or stave slides into its bag slot (roadmap 3.4).
- **Re-haft:** take apart and assemble in one sequence, with the hilt, reel or stave visibly moving across (roadmap M7).
- **Inlay:** the gem's icon drops into the pip in the tool's corner with a sparkle in its colour (roadmap 3.5 and 6.2). From then on the held tool glints in that colour on each hit, and its rare drops pop in the same colour.

## 5. What needs to be made

| What | Where | Size |
|---|---|---|
| 13 new key sets: `bow_draw`, `bow_release`, `rod_wait`, `rod_bite`, `rod_strike`, `rod_reel`, `rod_catch`, `axe_fell`, `hammer`, `saw`, `scrape`, `twist`, `assemble` | `imp_visual.gd` `ACTIONS` | Small each |
| A full left-arm key for the bow draw | `imp_visual.gd` (`larm` is one angle today) | Small |
| The bow string drawn in code | `held_tool.gd`, like the rod's line | Small |
| Hit-stop, bursts sized by tier, trail colour from the icon for every tier | `imp_visual.gd`, `tool_fx.gd` | Small |
| The drop pop: an icon that arcs from the node into the Imp | `tool_fx.gd`; used by all five trees | Small |
| The 2D moments: assemble, reveal card, take apart, re-haft, inlay | The crafting menu (roadmap B3) | Medium |
| Sending the tool in hand and each action to other players | The live room and `remote_imp.gd` | Medium |
| Hammer and saw props (if call C is yes) | Blockbench | Small |
| A headless test: every `ACTIONS` entry runs from t = 0 to t = 1 with its keys in order, and every tool kind has one | Tests | Small |

## 6. Passes

Each pass is design first and needs your yes. Every one touches J00BA's animation code (`imp_visual.gd`), so it needs J00BA's yes too.

| Pass | Goal | Needs | Done when |
|---|---|---|---|
| **A0** ✔ | This write-up | Your request (2026-11-22) | This doc is in review |
| **A1** | Bow: draw, release, drawn string | Hunting in the live world; roadmap T5 | The bow has a use animation |
| **A2** | The fishing loop | D-109 in the live world | Cast to catch plays end to end |
| **A3** | Tier feel and drop pops | Rare drops in the live world | Each tier reads differently in use |
| **A4** | Station and menu moments | Roadmap B2 and B3 | Every part station has its loop |
| **A5** | Other players see your swings | The live room | Other Imps hold and swing their tools |
| **A6** | One rig | J00BA | The test scene's gatherer rig is retired or moved onto the Imp's keys |

## 7. Risks and calls

**Risks**

- **The bite cue is gameplay.** If the dunk is unclear, fishing feels unfair. It needs a sound as well, and its timing comes from the server's window, not the animation (A1).
- **Motion comfort.** Hit-stop on every swing can tire some players. A *Reduce motion* setting should turn it off.
- **Web build cost.** Bursts from many players in the hub add up. Other players' bursts should use half the particles.
- **Two rigs.** `gatherer.gd` (test scene) and `imp_visual.gd` (live) animate differently. Building on the test rig would be wasted work (pass A6).
- **Scope for two people.** Thirteen key sets is a lot of hand-tuning. A1 and A2 matter most: the bow is the one tool with no animation, and fishing is the only skill with a timing challenge.

**Calls for you**

- **A. Hit-stop** on strikes (40 to 60 ms), with a *Reduce motion* setting? Yes or no.
- **B. Station loops:** the Imp animates at the station behind the open menu (Proposed), or only the 2D moments in the menu?
- **C. Hammer and saw props** (two small new models), or hands only?
- **D. Other players see your swings** (A6, one small event per action)? Yes or no.
