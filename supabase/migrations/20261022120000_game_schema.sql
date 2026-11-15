-- IMPLINGZ game schema (ACCOUNTS-AND-DATA.md, sections 4, 8 and 9). Proposed: NOT applied yet.
-- Review it, then run it once in the Supabase SQL editor (or `supabase db push`). See ../README.md.
--
-- Rules it sets up:
--   * Game tables live in their own schema, `game`, apart from the website's `public` tables.
--   * The browser can only READ its own rows (RLS). Nothing in the browser can write coins,
--     items, tools, energy or mint tokens: no insert/update/delete policy exists for them.
--     Every change will go through a server function (section 9), added in later migrations.
--   * A player row is made by the database when someone signs up, from the username they chose.

create schema if not exists game;

-- --- accounts -------------------------------------------------------------------------

create table game.players (
  id               uuid primary key references auth.users (id) on delete cascade,
  username         text not null check (username ~ '^[A-Za-z0-9_]{3,20}$'),
  created_at       timestamptz not null default now(),
  character_imp_id text                       -- the chosen Imp's token id; null = the basic Imp (D-049)
);
create unique index players_username_ci on game.players (lower(username));   -- unique, any case

create table game.wallets (
  player_id uuid primary key references game.players (id) on delete cascade,   -- one wallet per account
  address   text not null unique check (address = lower(address)),            -- one account per wallet
  linked_at timestamptz not null default now()
);

create table game.wallet_nonces (
  id         bigint generated always as identity primary key,
  player_id  uuid not null references game.players (id) on delete cascade,
  nonce      text not null unique,
  expires_at timestamptz not null,
  used_at    timestamptz
);

create table game.nft_contracts (
  chain   text not null check (chain in ('robinhood', 'apechain')),
  address text not null,
  active  boolean not null default true,
  primary key (chain, address)
);
insert into game.nft_contracts (chain, address)
values ('robinhood', lower('0x81D2D1f0e92285CdD22Aa3cbc6956B6E1724d029'));   -- D-050

create table game.owned_imps (
  player_id  uuid not null references game.players (id) on delete cascade,
  chain      text not null,
  token_id   text not null,
  checked_at timestamptz not null default now(),
  primary key (player_id, chain, token_id)
);

-- --- economy ----------------------------------------------------------------------------

create table game.balances (
  player_id uuid primary key references game.players (id) on delete cascade,
  coins     bigint not null default 0 check (coins >= 0)
);

create table game.coin_ledger (                 -- add rows only; the balance is their sum
  id        bigint generated always as identity primary key,
  player_id uuid not null references game.players (id) on delete cascade,
  amount    bigint not null,
  reason    text not null,                      -- 'legacy_claim', 'sell', 'refill', ...
  ref       text,
  at        timestamptz not null default now()
);

create table game.mint_tokens (                 -- never deleted: spending changes the status (section 6)
  id            uuid primary key default gen_random_uuid(),
  player_id     uuid not null references game.players (id) on delete restrict,
  found_by      text not null,                  -- activity and tier, e.g. 'mining:7'
  found_at      timestamptz not null default now(),
  status        text not null default 'unspent' check (status in ('unspent', 'spent')),
  spent_on_mint text,
  spent_wallet  text,
  spent_at      timestamptz
);

-- --- what a player has --------------------------------------------------------------------

create table game.inventory (
  player_id uuid not null references game.players (id) on delete cascade,
  item_id   text not null,
  qty       integer not null check (qty > 0),
  primary key (player_id, item_id)
);

create table game.tools (
  player_id uuid not null references game.players (id) on delete cascade,
  tool_id   text not null,                      -- the game's tool id, e.g. 'bronze_pickaxe'
  primary key (player_id, tool_id)
);

create table game.energy (
  player_id     uuid primary key references game.players (id) on delete cascade,
  energy        integer not null default 100 check (energy between 0 and 100),
  refilled      integer not null default 0,     -- energy bought this reset: never rolls mint tokens (D-076)
  last_reset_at timestamptz not null default now()
);

create table game.items (                       -- item types, filled from the game's tables later
  id    text primary key,
  name  text not null,
  tier  integer not null,
  skill text,
  kind  text,
  icon  text
);

-- --- who can read what (RLS) --------------------------------------------------------------

grant usage on schema game to anon, authenticated;

do $$
declare t text;
begin
  foreach t in array array['players', 'wallets', 'owned_imps', 'balances', 'coin_ledger',
                           'mint_tokens', 'inventory', 'tools', 'energy'] loop
    execute format('alter table game.%I enable row level security', t);
    execute format('grant select on game.%I to authenticated', t);
    execute format(
      'create policy "read own" on game.%I for select to authenticated using (%s = auth.uid())',
      t, case when t = 'players' then 'id' else 'player_id' end);
  end loop;
end $$;

alter table game.wallet_nonces enable row level security;    -- server functions only: no policies

alter table game.nft_contracts enable row level security;
alter table game.items enable row level security;
grant select on game.nft_contracts, game.items to anon, authenticated;
create policy "read all" on game.nft_contracts for select using (true);
create policy "read all" on game.items for select using (true);

-- --- sign-up --------------------------------------------------------------------------------

-- Is this username free? Checks the game's players (any case) and, for now, the old impz.club
-- profiles, so old holders can claim their names after launch (section 4, Proposed).
create or replace function game.username_free(p_username text)
returns boolean
language plpgsql stable security definer set search_path = ''
as $$
begin
  if p_username !~ '^[A-Za-z0-9_]{3,20}$' then
    return false;
  end if;
  if exists (select 1 from game.players where lower(username) = lower(p_username)) then
    return false;
  end if;
  return not exists (select 1 from public.profiles where lower(username) = lower(p_username));
end $$;
grant execute on function game.username_free(text) to anon, authenticated;

-- Makes the player's rows when someone signs up. A missing or taken username stops the sign-up.
create or replace function game.on_sign_up()
returns trigger
language plpgsql security definer set search_path = ''
as $$
declare wanted text := new.raw_user_meta_data ->> 'username';
begin
  if wanted is null or not game.username_free(wanted) then
    raise exception 'username missing or taken';
  end if;
  insert into game.players (id, username) values (new.id, wanted);
  insert into game.balances (player_id) values (new.id);
  insert into game.energy (player_id) values (new.id);
  return new;
end $$;

create trigger game_on_sign_up
after insert on auth.users
for each row execute function game.on_sign_up();

-- --- reading your own state ------------------------------------------------------------------

-- Everything the game needs at log-in, in one call: Api.rpc_call("load_state").
create or replace function game.load_state()
returns jsonb
language sql stable security definer set search_path = ''
as $$
  select jsonb_build_object(
    'username',    p.username,
    'coins',       coalesce(b.coins, 0),
    'energy',      e.energy,
    'last_reset',  e.last_reset_at,
    'items',       coalesce((select jsonb_object_agg(i.item_id, i.qty) from game.inventory i where i.player_id = p.id), '{}'::jsonb),
    'tools',       coalesce((select jsonb_agg(t.tool_id) from game.tools t where t.player_id = p.id), '[]'::jsonb),
    'mint_tokens', (select count(*) from game.mint_tokens m where m.player_id = p.id and m.status = 'unspent'),
    'wallet',      (select w.address from game.wallets w where w.player_id = p.id)
  )
  from game.players p
  left join game.balances b on b.player_id = p.id
  left join game.energy e on e.player_id = p.id
  where p.id = auth.uid()
$$;
revoke execute on function game.load_state() from public, anon;
grant execute on function game.load_state() to authenticated;
