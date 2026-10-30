# supabase

Supabase database setup. Follows the Supabase CLI layout: `migrations/` for SQL migrations, `functions/` for edge functions.

## The game schema

The game's accounts and saved progress live in the existing Supabase project, "Club Impz", in their own `game` schema (D-043; [ACCOUNTS-AND-DATA.md](../docs/ACCOUNTS-AND-DATA.md)).

**Status: Proposed, not applied.** Nothing here has been run against the real project yet.

### What's here
| File | What it does |
|---|---|
| `migrations/20261022120000_game_schema.sql` | The `game` tables from ACCOUNTS-AND-DATA section 8. Row-level security means a player can only **read** their own rows and nothing in the browser can write. Also creates the player row on sign-up and the `load_state()` and `username_free()` functions. |

Not written yet: the server functions that change things (`gather`, `sell`, `craft`, `link_wallet`, `spend_mint_token`, the energy reset) and the Edge Function that checks Imp ownership on chain. Each one comes in its own migration, with its own PR.

### Turning it on
1. Read the migration, then run it once in the Supabase dashboard: **SQL Editor** → paste → Run. A **backup** of the database first is strongly advised (ACCOUNTS-AND-DATA, section 2).
2. **Settings → API → Exposed schemas:** add `game`, so the game can call its functions.
3. **Authentication → Providers → Email:** on. Decide whether sign-ups must confirm their email (recommended). The game handles both.
4. Put the project URL and the **anon** key into `game/config/supabase.cfg`. **Never** the `service_role` key: it bypasses every rule (section 9).

While `game/config/supabase.cfg` is empty, the game plays offline and keeps progress on the device (`user://save.json`, TEST).
