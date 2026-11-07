SQL scripts to run in Supabase (project "Club Impz", phlixtsxxuicatmrmdou)
===========================================================================

How: Supabase dashboard -> SQL Editor -> New query -> open a file below, copy everything, paste, Run.
Run them in number order, each once. Both are safe to run again (they skip what already exists),
except that 02 renames clashing usernames again if new clashes appear.

01_saved_imps.txt
  The table for Impz saved in the website's Imp builder (/imp-customization).
  The site currently answers "saved_imps table is missing" until this is run.
  Source: impz-club repo, supabase/saved_imps.sql (PR #7, already live).

02_profile_accounts.txt
  Unique usernames, and a private table for emails (the game's Profile menu).
  Before it adds the unique rule it renames the newer of the two "j00ba" accounts to
  j00ba_<last 4 of its wallet>. Run it before merging impz-club PR #8.
  Source: impz-club repo, supabase/profile_accounts.sql (PR #8).

These are copies. The originals live in the impz-club repo, next to the code that uses them.
If one changes there, copy it here again.

Not included: supabase/migrations/20261022120000_game_schema.sql (the old email-and-password
account plan, D-041). The game now uses the website's account instead, so don't run it.
