-- Accounts for the website and the Club Impz game (2026-11-07). Run once in the Supabase SQL editor.
-- An account is a `profiles` row, keyed by wallet. The game signs players in with Glyph and reads and
-- edits the same row through api/profile.js, so an account made on either one shows up in the other.
--
-- 1. Usernames are unique, ignoring capitals and spaces at the ends ("J00BA" and "j00ba " clash).
--    Two wallets already share a name, so before the rule goes on, every copy except the oldest gets
--    "_" and the last 4 characters of its wallet added (j00ba -> j00ba_1a2b). The SELECT below lists them.
-- 2. Emails are private, so they live in their own table, profile_private. Row-level security is on
--    and there are no policies, so the public anon key can't read them: only the site's server (the
--    secret key) can, and it gives a wallet's email only to that wallet's signed-in session.

-- See which names will be changed (optional):
-- select wallet, username, updated_at from public.profiles
-- where lower(btrim(username)) in (select lower(btrim(username)) from public.profiles
--   where coalesce(btrim(username), '') <> '' group by 1 having count(*) > 1)
-- order by lower(btrim(username)), updated_at nulls last, wallet;

with ranked as (
  select wallet,
         row_number() over (partition by lower(btrim(username)) order by updated_at nulls last, wallet) as n
  from public.profiles
  where coalesce(btrim(username), '') <> ''
)
update public.profiles p
set username = left(btrim(p.username), 19) || '_' || right(p.wallet, 4)
from ranked r
where r.wallet = p.wallet and r.n > 1;

create unique index if not exists profiles_username_unique
  on public.profiles (lower(btrim(username)))
  where coalesce(btrim(username), '') <> '';

create table if not exists public.profile_private (
  wallet text primary key check (wallet ~ '^0x[0-9a-f]{40}$'),
  email text check (email is null or (char_length(email) <= 254 and email ~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$')),
  updated_at timestamptz not null default now()
);

alter table public.profile_private enable row level security;
