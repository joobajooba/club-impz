-- Saved Impz from the Imp builder (/imp-customization). Run once in the Supabase SQL editor.
-- Only the site's server (api/imps.js, with the secret key) reads or writes this table: row-level
-- security is on and there are no policies, so the public anon key can't touch it.
create table if not exists public.saved_imps (
  id bigint generated always as identity primary key,
  wallet text not null check (wallet ~ '^0x[0-9a-f]{40}$'),
  name text not null check (char_length(name) between 1 and 32),
  body text not null,
  head text,
  eyes text,
  clothing text,
  back text,
  -- the Imp each trait came from when it was saved, e.g. {"body": 12, "head": 40}
  source_imps jsonb not null default '{}'::jsonb,
  -- the message the wallet signed and its signature: proof the owner saved this build
  message text not null,
  signature text not null,
  nonce text not null unique,
  created_at timestamptz not null default now()
);

create index if not exists saved_imps_wallet_idx on public.saved_imps (wallet, created_at desc);

alter table public.saved_imps enable row level security;
