# game-server: the Club Impz live beta

One small Node program (`server.mjs`) that runs the beta on a single web address:

- **The game:** it serves the Godot web build (`godot-game/export/web`).
- **Multiplayer:** `/ws` is the shared room. Everyone who opens the page joins the same game and sees the other Imps in their world (`godot-game/autoload/net.gd`).
- **impz.club:** `/api/imps` and `/api/profile` are forwarded to impz.club (wallet traits and the Profile account).

## Who players are

- **Signed in** (Profile menu: Glyph, then "Sign in with your wallet"): others see the impz.club username in gold, and only the traits that wallet's Impz have. The server checks both with impz.club. This needs impz-club PR #8 to be live.
- **Everyone else** plays as `Guest 1234` in the base green Imp. Anyone can join. There is nothing to sign up for.

## What the server checks

- Every position must be a real number.
- Each player sends at most 40 messages a second. More than that and the connection is closed.
- Each message is at most 8 KB.
- Players only receive moves from players in their own world.
- `MAX_PLAYERS` caps the room (default 100).

Each game moves its own Imp, so this isn't cheat-proof movement. That's fine for walking around together. Anything that is worth something (drops, coins) stays on impz.club and Supabase (ACCOUNTS-AND-DATA).

## Run it locally

```sh
cd web-wallet
npm start            # builds Glyph, exports the game, runs this server on http://localhost:8060
```

Open http://localhost:8060 in two tabs. Desktop games join it too (`godot-game/config/server.cfg`). For a second player without a browser:

```sh
godot --headless --path godot-game -- --bot=60
```

That one walks in circles near the spawn for 60 s. `npm test` (in this folder) checks the room rules.

## Put it online (Fly.io)

1. Install the Fly CLI and log in: `fly auth login`.
2. Make the app once: `fly apps create club-impz-beta`. If the name is taken, pick another and change `app` in `fly.toml`.
3. Export a **release** build, so the TEST trait switch is off: in `web-wallet`, run `npm run build && npm run export`.
4. Deploy: `npm run deploy` (in this folder). The beta is then at https://club-impz-beta.fly.dev.
5. Optional: use your own address, `play.impz.club`. Run `fly certs add play.impz.club`, then add the CNAME record it shows in your DNS.

Deploy again (steps 3 and 4) after every game change. Deploying restarts the room, so players reconnect after a few seconds.

Keep it to **one machine** (`--ha=false`), because the room lives in that machine's memory. `/healthz` reports `{ok, online}`.
