# IMPLINGZ: accounts, wallets and the database

| Status | Last pass | Depends on |
|---|---|---|
| Draft | User addition, 2026-10-20 | 00, 02, GODOT |

> Claude: read `docs/CLAUDE.md` before working from this file. Read this whole file before writing any code that saves player data, touches coins or mint tokens, links a wallet, or reads the Supabase database.
>
> Labels: **Decided** (in `DECISIONS.md`) · **Proposed** (Claude's suggestion) · **Open question**
>
> **This repo is public.** Never paste wallet addresses, usernames, emails, keys or real rows from the database into any file here. Describe tables by their columns only.

**Purpose of this doc:** how a player gets an account, links a wallet, keeps their coins and mint tokens, and how the Godot game and the website impz.club share one database.

**Words used here.**
- **Wallet:** a crypto app (MetaMask or Rabby) that holds the keys to a blockchain address. Linking it proves the player owns that address.
- **Signing a message:** the wallet shows a short text and the player presses "Sign". It costs nothing and moves nothing. It only proves "I own this address".
- **Supabase:** the hosted database impz.club already uses. Underneath it is **Postgres**, a normal SQL database, plus login, an API and server functions.
- **RLS (row level security):** Postgres rules that decide which rows each logged-in player may read or change.
- **Server function:** code that runs on Supabase, not on the player's computer. Anything worth money must be decided there.

---

## 1. What is decided

| Topic | Decision |
|---|---|
| Accounts | Sign up with email, pick a username, log in. Then link a wallet: MetaMask or Rabby (**D-041**). |
| Crypto scope | Very little: play as your Imp, link a wallet, mint tokens. IMP coins are in-game only (**D-039**). |
| Play as your Imp | NFT holders load their Imp's model as their character (**D-038**). |
| Mint tokens | Any gathering action can find one. Mining only in phase one. Saved to the account. Spent on impz.club to claim a mint (**D-040**). **Only Imp holders can find them (D-045).** |
| IMP coins | Coins earned by staking on impz.club carry into the game (**D-042**). |
| Database | One database for the game and impz.club, read and written by both. It is the existing Supabase project, with new game tables (**D-043**, Claude's choice at the user's request). |
| Platform | The game is played in the **browser** (**D-046**). |
| Chain | Implings are on **Robinhood Chain** today and will **move to ApeChain** (**D-048**). Contract on Robinhood Chain: `0x81D2D1f0e92285CdD22Aa3cbc6956B6E1724d029` (**D-050**). |
| Non-holders | Play as a basic Imp model that isn't part of the collection (**D-049**). |
| Staking | Finished for now. The 2026-10-04 snapshot is final (**D-050**). |

## 2. Why Supabase, and not a new SQL database (D-043)

Supabase **is** a SQL database (Postgres), so building another one would mean running a second server and copying data between two places. Reasons to stay:

1. **The website already uses it.** impz.club reads and writes it today. If the game uses the same project, the website sees game coins and mint tokens straight away, with no syncing.
2. **The old data is already there** (section 3). Nothing needs exporting.
3. **Godot can talk to it.** Supabase is reached over plain HTTPS. Godot's `HTTPRequest` node can call its login API and its data API (section 10).
4. **Email login is built in.** Supabase Auth handles sign-up, email confirmation, password reset and sessions.
5. **Security tools are built in.** RLS and server functions let us say "a player can read their coins but never change them".

**When we would leave Supabase (Proposed):** only if the game needs a live game server for many players in one world (real-time multiplayer). Even then, Supabase stays as the account and economy database.

**Is Supabase right for the long term? (Proposed: yes.)**
- **No lock-in.** It's standard Postgres. If we ever leave, a normal Postgres backup moves every table, row and function to any other Postgres host. Starting on Supabase loses nothing.
- **Running our own SQL server would add work, not safety.** We would have to build login, password reset, an API, backups, updates and security ourselves. The website's permission problem (section 3) would exist on our own server too: it comes from how permissions were set, not from Supabase.
- **It grows with us.** Paid plans add daily backups, more storage and bigger servers without changing any code.
- **Where it would stop being enough:** real-time multiplayer, where many players share one live world. That needs a separate game server, but Supabase stays as the accounts and economy database behind it.

**Cost (Open question):** the project is on the **free** plan today. The free plan pauses inactive projects and has small limits. A live game should be on a paid plan. Check Supabase's current prices before launch. **Proposed:** move to a paid plan before any real coins or mint tokens are at stake, mainly for **daily backups**. The project is marked Production, and a lost database would lose every player's coins.

## 3. What is in Supabase today

From the user's screenshots and a table export on 2026-10-20. Project "Club Impz", schema `public`. Website accounts today are **keyed by wallet address**. There is no email login yet.

| Table | One row per | Columns | What it does |
|---|---|---|---|
| `profiles` | Wallet | `wallet`, `username`, `pfp_id`, `rank`, `total_impz`, `imp_coins`, `account_age`, `updated_at`, `tier_1`, `tier_2`, `tier_3`, `bio`, `imp_coin_claimed` | The impz.club profile. `imp_coins` is the coin balance after claiming. `imp_coin_claimed` is true once the staking coins have been claimed. |
| `imp_coin_balances` | Wallet | `wallet_address`, `nickname`, `claimed_imp_coin`, `pending_imp_coin`, `portable_imp_coin`, `lifetime_earned`, `active_stakes`, `snapshot_at`, `imported_at` | A **snapshot** of the old staking system (taken 2026-10-04). `portable_imp_coin` = `claimed_imp_coin` + `pending_imp_coin`: the amount a wallet can carry over. Has 1 RLS policy. |
| `imp_coin_claims` | Claim | `wallet_address` (linked to another table), `amount`, `claimed_at` | A record of each wallet claiming its coins. `amount` equals that wallet's `portable_imp_coin`. |
| `wallet_connections` | n/a | n/a | **Will be removed** (D-050). The game does not use it. |

**How claiming works today:** on impz.club's **merchant tab**, a player claims their staked coins. The claim is saved by Supabase: the wallet's `portable_imp_coin` is written to `profiles.imp_coins`, `imp_coin_claimed` is set to true, and a row is added to `imp_coin_claims`. The website then reads the balance back from Supabase.

### Things noticed in the data (for checking)
- **One profile is marked claimed with no claim row.** Six profiles have `imp_coin_claimed = true` and a balance, but `imp_coin_claims` has five rows. One wallet got its coins some other way (perhaps by hand, before the claims table existed). Check that its balance is right before anything is moved.
- **Usernames aren't unique.** Two profiles share one username, and another differs by one letter. The game needs unique usernames (section 4).
- **A test row** (`username` "probe", a placeholder wallet) should be left out of any migration.
- **Some `imp_coins` values are empty (null)**, not 0. The migration must treat null as 0.
- **Many profiles were created by the staking import** (same `updated_at` as `imported_at`) and have never been used.
- **Check one detail of the claim.** The user confirmed the claim is saved by Supabase. There are two ways a website can do that, and only one is safe:
  - **Safe:** the page calls a Supabase **function** (a database function or Edge Function) that checks the wallet and writes the balance itself.
  - **Unsafe:** the page updates the `profiles` row directly with the Supabase library, and an RLS policy allows it. Then anyone with the browser console could write their own `imp_coins`.

  To check, either:
  - **Table Editor** → open `profiles` → the **RLS policy** button at the top right of the table. It lists every policy; look for one whose command is **UPDATE** (or **ALL**).
  - **SQL Editor** → run `select policyname, cmd, roles, qual, with_check from pg_policies where tablename = 'profiles';`. This only reads; it changes nothing.

  If an UPDATE or ALL policy applies to `anon` or `authenticated` and doesn't stop `imp_coins` being changed, it's the unsafe kind. Fix it before coins move into the game (section 7). If RLS is **off** for `profiles`, that's unsafe too.

  **What the check found (2026-10-20):** the website's table permissions needed fixing. **Fixed the same day:** browsers can now only read `profiles`, `imp_coin_balances` and `imp_coin_claims`; the website's server writes with a secret key kept in Vercel; and changing a username, picture or bio needs a wallet signature. **Proposed rule from now on:** the browser's roles (`anon`, `authenticated`) can only **read** game and profile tables. Every write goes through server code that uses a secret key kept only in the server's settings, never in code or in Git.

## 4. The account flow

### Sign up and log in (Decided, D-041; steps Proposed)

1. In the game: **Sign up** → email, password, username.
2. Supabase sends a confirmation email. The player clicks the link.
3. The game logs in and gets a **session** (an access token and a refresh token), so the player stays logged in.
4. The username is checked as unique (any letter case) and against a blocked-words list.

**The same login works on impz.club.** Because the game runs in the browser on impz.club (D-046), logging in on the website can log you into the game, and the other way round.

**Usernames from the old profiles (Proposed):** when a wallet is linked, if its old `profiles.username` is still free, offer it to the player. If it's taken, they pick another. Nobody can take a name that belongs to an unlinked old profile for the first months after launch, so old holders can claim their names.

### Link a wallet (Decided that it happens, D-041; method Proposed)

The game runs in the browser (D-046), so it can talk to MetaMask or Rabby **directly**. Godot's `JavaScriptBridge` calls the wallet extension on the page.

```
Godot game (in the browser)         Wallet (MetaMask / Rabby)      Supabase
───────────────────────────         ─────────────────────────      ────────
"Link wallet" ────────────────────────────────────────────────────► make a one-time message
                                                                   (random number, expires in 10 min)
asks the wallet to sign ──────────► "Sign this message?"
                                    player presses Sign
                        ◄────────── signature
sends address + signature ────────────────────────────────────────► checks the signature,
                                                                   saves the wallet on the account,
                                                                   moves the old coins (section 7)
"Wallet linked" ◄──────────────────────────────────────────────────
```

- **The message to sign** follows the "Sign-In with Ethereum" format (EIP-4361): it names impz.club, the account, a one-time random number and the time. That stops a signature from being reused.
- **Signing costs no gas and sends no transaction**, and it doesn't depend on which chain the wallet is set to. The same address owns Imps on Robinhood Chain and ApeChain. The screen must say this plainly, because scammers use "sign this" tricks.
- **On a phone,** wallet extensions don't exist. MetaMask's and Rabby's phone apps have their own built-in browser that works the same way. **Open question:** do we support phones at launch?

**Rules (Proposed):**
- **One wallet per account, and one account per wallet.** The database refuses a wallet that's already linked to another account. Without this, one wallet's coins and Imps could be used on several accounts.
- **Nothing ever asks for a seed phrase or private key.** Say so on the link screen.
- **Changing the wallet** is allowed, with a waiting period (for example 7 days) and an email to the player. **Open question:** the length.

## 5. Playing as your Imp (Decided, D-038; method Proposed)

1. Once a wallet is linked, a server function checks which Implings that wallet holds and saves them as `owned_imps` with a "checked at" time.
2. The player picks one of their Imps as their character.
3. **A player without an Imp** plays as the **basic Imp model**, which isn't part of the collection (D-049). It ships with the game.
4. The game downloads the chosen Imp's 3D model and loads it **while running**. See "Where the Imp models live" below (Godot's `GLTFDocument` loads `.glb` files at runtime). The test project already uses `characters/impling.glb`.
5. **Ownership is checked again at every login**, and before any mint token roll (section 6). If the Imp has been sold, the player can't use it any more and goes back to the basic Imp (D-049).

### Where the Imp models live (hosting Decided, D-051)

- **Today:** each Imp's 3D model is referenced in the Implings **metadata** (the NFT's description data) as an MML file. The models are also kept **locally as `.glb`** files.
- **Decided (D-051): the game loads the `.glb` from a Supabase Storage bucket**, not from the metadata link. One `.glb` per token, named by token ID, for example `imps/1234.glb` (naming Proposed). Reasons:
  - It's fast and always available. Metadata links (often IPFS) can be slow or blocked by the browser's cross-site rules (CORS).
  - Godot loads `.glb` at runtime. It doesn't read MML.
  - The metadata stays the public source of truth. The game copy is just a fast mirror.
- **Size matters in the browser.** Measure a typical Imp `.glb`. If they're more than a few MB, compress them (smaller textures, Draco or meshopt compression) before uploading.
- **The basic Imp (D-049)** is almost made: the model exists (`0.glb`, 3.66 MB) and needs its own texture, different from the collection's. It ships inside the game, not in storage.
- **3.66 MB per Imp** is workable in a browser, since a player loads only one Imp at a time. Compressing the textures (and the mesh with Draco or meshopt) could bring it under 1 MB, which helps first load. **Proposed:** test that on `0.glb` first.

### Robinhood Chain now, ApeChain later (Decided, D-048; method Proposed)

- **The contract on Robinhood Chain is `0x81D2D1f0e92285CdD22Aa3cbc6956B6E1724d029`** (D-050). It goes into `game.nft_contracts` as the first row.
- **Keep the chain and contract as settings, not code.** The ownership check reads a list of `(chain, contract)` pairs from the database. Moving to ApeChain is then a settings change, not a new game build.
- **During the move, count both.** While holders are moving their Imps across, an Imp counts if it's held on **either** chain. When the move is finished, remove the Robinhood Chain entry.
- **How ownership is read:** first check whether an NFT data service (Alchemy, Moralis, or the chain's own explorer API) supports each chain. If one doesn't, read the contract directly through the chain's public RPC (`balanceOf` and `ownerOf`, or the contract's transfer history).
- **Token IDs must stay the same across the move**, so a player's chosen Imp and its model still match. **Open question:** will the ApeChain contract keep the same token IDs?

**Open questions:**
- The ApeChain contract address, and when the move happens.
- Is there one 3D file per Imp, or one base model plus trait parts? Where are the files stored?
- Who makes the basic Imp model (D-049)? D-016 says the Implings are already done; is the basic model already done too?

## 6. Mint tokens (Decided, D-040, D-045; rules Proposed)

A mint token is a **database record**, not a crypto token. It belongs to one account. It can only be spent on impz.club.

**Who can find them (Decided, D-045):** only **Imp holders**. In practice: the account has a linked wallet, and that wallet held at least one Imp at the last ownership check (Proposed: checked within the last 24 hours).

**How one is found (Proposed):**
- Every gathering action the server accepts (section 9) rolls the mint token chance **on the server**, if the player is an Imp holder. The game is told "you found a mint token" and shows it.
- Phase one: mining only (D-040).
- The chance is **0.1%** per accepted action (**Decided, D-078**), well below the 1% gem chance at the top tier.
- Actions on energy bought with coins **never roll** (**Decided, D-076**). So the server has to know how much of the player's current energy came from a refill, and spend that energy first or last by a fixed rule (**Proposed:** spend refilled energy last, so normal play is never affected).

**How one is spent (Proposed):**
One mint costs **1 mint token** (**Decided, D-078**).

1. On impz.club, during a hosted mint, the player clicks "Claim with mint token".
2. A server function checks they have an unspent token, marks it **spent**, and records which mint and which wallet it was spent on.
3. That wallet gets the right to mint (for example, a place on the mint's allowlist, or a signed pass the mint contract accepts). **Open question:** how each mint contract checks this. New mints are expected on ApeChain (D-048).

**Rules (Proposed):**
- **Mint tokens can't be traded or moved between accounts.** If they could, bots would farm and sell them.
- **A token is never deleted.** Spending it changes its status, so there's always a record of where it came from and where it went.
- **Selling the Imp** stops new mint token finds, but tokens already found stay on the account. **Open question:** is that right?
- **Lending:** one Imp can only make one account an Imp holder at a time, because one wallet links to one account. Moving an Imp to a friend's wallet does make the friend a holder. That's normal NFT behaviour and is accepted.

## 7. Bringing old IMP coins across (Decided that they come across, D-042; method Proposed)

Coins are already claimed on impz.club's merchant tab (section 3). The game doesn't need its own claim codes. The **wallet link** carries them over:

1. The player links their wallet in the game (section 4). The signature proves they own it.
2. The link function looks up that wallet:
   - **Already claimed on the merchant tab** (`imp_coin_claimed = true`): it takes `profiles.imp_coins`.
   - **Not claimed yet:** it does the same claim the merchant tab does (writes the `imp_coin_claims` row and marks the profile claimed), using `imp_coin_balances.portable_imp_coin`. The player doesn't have to visit the merchant tab first.
3. It adds those coins to the player's game balance, writes a `legacy_claim` row in the coin ledger, and records on the profile which game account received them. The profile's `imp_coins` goes to 0, so the same coins can't be moved twice.
4. All of this happens in **one database step**, so two clicks at the same moment can't both succeed.

**After launch (Proposed):** the game balance is the only live coin balance. The merchant tab shows and spends the game balance of whoever is logged in, not `profiles.imp_coins`. One balance means nothing can get out of step.

**Why not claim codes:** your first idea was a code per old user. Every coin balance is already tied to a wallet, and the wallet signature proves ownership, so a code adds a step and a way to leak coins without adding safety. Codes stay available as a fallback if a wallet turns out to have no working owner.

**Staking is finished for now (D-050).** The snapshot is final, so the move only ever handles a fixed list of balances. If staking comes back later, new staking coins should go straight into the game balance.

**Open question:** the claimed profile with no claim row (section 3) needs checking before the move.

## 8. Database tables (Proposed)

New tables go in their own **`game` schema** (a folder of tables inside the same database), so they don't get mixed up with the website's tables in `public`.

| Table | One row per | Main columns | Who can write |
|---|---|---|---|
| `auth.users` | Login | Email, password (Supabase manages it) | Supabase Auth |
| `game.players` | Account | `id` (same as the login id), `username` (unique, any case), `created_at`, `character_imp_id` | Player can change username only, through a function |
| `game.wallets` | Linked wallet | `player_id`, `address` (lower case, **unique**), `linked_at` | Server function only |
| `game.wallet_nonces` | Link attempt | `player_id`, `nonce`, `expires_at`, `used_at` | Server function only |
| `game.nft_contracts` | Contract | `chain` (`robinhood`, `apechain`), `address`, `active` | Us, by migration |
| `game.owned_imps` | Imp held | `player_id`, `chain`, `token_id`, `checked_at` | Server function only |
| `game.balances` | Account | `player_id`, `coins` (whole numbers, never below 0) | Server function only |
| `game.coin_ledger` | Coin change | `player_id`, `amount` (+ or −), `reason` (`legacy_claim`, …), `ref`, `at` | Server function only, add rows only |
| `game.mint_tokens` | Mint token | `id`, `player_id`, `found_by` (activity and tier), `found_at`, `status` (`unspent` / `spent`), `spent_on_mint`, `spent_wallet`, `spent_at` | Server function only |
| `game.inventory` | Item stack | `player_id`, `item_id`, `qty` | Server function only |
| `game.tools` | Owned tool | `player_id`, `tool_id` (for example `pickaxe_bronze`) | Server function only |
| `game.energy` | Account | `player_id`, `energy`, `last_reset_at` | Server function only |
| `game.items` | Item type | `id`, `name`, `tier`, `icon`, drop chances | Us, by migration |
| `public.profiles` | (existing) | Add `moved_to_player`, `moved_at` | Server function only |

**RLS rules (Proposed):** a player can **read** their own rows. Nobody can **write** coins, mint tokens, inventory, tools or energy from the game or the website directly. Every change goes through a server function that checks the rules first.

**Item tables live in the database (Proposed).** The server rolls drops, so it needs the ore, plant and animal tables and their chances (D-005 to D-035). Keeping one copy in `game.items`, which the game also reads at start-up, means the game and the server can't disagree.

### How the website uses it (D-043)
impz.club reads the same tables with the same login: coin balance, unspent mint tokens, linked wallet, chosen Imp. It changes them only through the same server functions (for example `spend_mint_token`).

## 9. The client can't be trusted (Proposed, and important)

Anything that runs on the player's computer can be changed by the player. A browser game is even easier to change than a download. Mint tokens can be swapped for NFT mints, so people **will** try to cheat for them.

- **The server decides every drop.** The game says "I swung at Iron vein #12". A server function (for example `gather(node_id)`) checks the tool, the energy and the vein's 10-second regrow. Only then does it roll the ore, the gem and (for Imp holders) the mint token, and save them.
- **Speed limits.** A vein takes three swings. The server refuses gather calls faster than a human could swing.
- **Energy is the daily cap.** 100 energy, 5 per mine, reset every 12 hours (D-008, D-009) means at most 40 mines a day per account.
- **Imp holders only (D-045)** is the strongest protection against farming with many accounts: each mint-token account needs its own Imp, and one Imp's wallet can link to one account.
- **Never put the Supabase `service_role` key in the game or the website.** It skips every RLS rule. Only the public `anon` key goes in the browser.

This means saving moves from "the browser remembers it" (today's Three.js test) to "the server remembers it". That is BUILD-ROADMAP milestone M6 (Godot G6).

## 10. Calling Supabase from Godot (Proposed)

- **One autoload script, `Api`,** wraps every call: sign up, log in, refresh the session, call a server function, read a table. **Built (2026-10-22):** `game/autoload/api.gd`, using plain `HTTPRequest` so the game works on its own (see the open question below). It is offline while `game/config/supabase.cfg` is empty. The `game` schema is written in `supabase/migrations/` and is **not applied** yet.
- **Login** uses Supabase Auth's HTTP endpoints. **Data** uses its REST API, with the player's access token in each request.
- **Server functions** are Postgres functions (called through the REST API) or Supabase Edge Functions (small TypeScript programs). Postgres functions are enough for gather, link and spend. The NFT ownership check needs to call out to the chain, so it's an Edge Function.
- **In the browser,** the game can also use the official Supabase JavaScript library already on impz.club, through `JavaScriptBridge`, which shares the website's login. **Open question:** use the website's library, or plain `HTTPRequest` from GDScript? The first shares the login for free; the second keeps the game working on its own.

## 11. Open questions

1. **The claimed profile with no claim row:** is its balance right?
2. **Mint token chance**, and how many tokens a mint claim costs.
3. **ApeChain contract address**, when the move happens, and whether token IDs stay the same.
4. **Compressing the Imp `.glb` files** (about 3.7 MB each) before uploading: test on `0.glb`.
5. **The basic Imp's texture** (D-049): still to make.
6. **Selling an Imp:** do mint tokens already found stay on the account?
7. **Phones** at launch?
8. **Wallet change waiting period.**

Answered on 2026-10-20: mint tokens are for Imp holders only (D-045). The current Supabase schema was shared (section 3). The claim method now follows the merchant tab (section 7). The merchant claim is saved by Supabase. `wallet_connections` will be removed, staking is finished, and the Robinhood Chain contract is known (D-050). Non-holders play as a basic Imp (D-049). Imp models are referenced in the metadata as MML and kept locally as `.glb`; the basic Imp needs only its texture.

## Pass history
| Pass | Change |
|---|---|
| User addition, 2026-10-20 | Doc created. Accounts (D-041), Imp as character (D-038), crypto scope (D-039), mint tokens (D-040), staked coins carried over (D-042), one shared Supabase database (D-043). Flows, tables and anti-cheat rules are Proposed. Status Draft. |
| User addition, 2026-10-20 (later) | The user shared the Supabase tables. New section 3 (what exists today, with data issues to check). Mint tokens for Imp holders only (D-045). Browser game (D-046): the wallet links inside the game. Robinhood Chain now, ApeChain later (D-048). Old coins move on wallet link, following the merchant tab; claim codes kept only as a fallback. Open questions updated. |
| User addition, 2026-10-20 (later) | Basic Imp for non-holders (D-049). Staking finished, `wallet_connections` to be removed, Robinhood Chain contract recorded (D-050). The claim is saved by Supabase; how to check the `profiles` policy added. Open questions cut from eleven to nine. Then: where Imp models live and a hosting proposal; how to find the `profiles` policies. Then: the `profiles` policies recorded (RLS on, three `public` policies, Data API disabled) with two queries to confirm; basic Imp size (3.66 MB). Then: the check found the website's permissions need fixing (details kept out of this public repo); Imp models hosted in Supabase Storage (D-051); a section on Supabase in the long term. Then: the website's permissions fixed (browser read-only, server key, wallet signature for profile edits). |
