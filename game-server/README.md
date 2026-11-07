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

## Put it online (Render)

The beta runs on Render as one **Starter** web service, a fixed price of about $7 a month. It uses a ready-made image, so Render never has to build the game:

1. **GitHub builds it.** Every push to the default branch, or to `staging/multiplayer-beta`, runs `.github/workflows/beta.yml`. You can also start it by hand from **Actions → Beta → Run workflow**. It:
   - exports the game (a release build),
   - packs it with this server (`Dockerfile`),
   - pushes the result to `ghcr.io/joobajooba/club-impz-beta:latest`.
2. **Render runs it.** The service is set up once in Render's dashboard:
   - **New → Web Service → Existing Image**, with image URL `ghcr.io/joobajooba/club-impz-beta:latest`.
   - **Instance type: Starter.** Don't use Free: it sleeps after 15 minutes and drops everyone.
   - **Health check path:** `/healthz`.
   - **Region:** Frankfurt, the closest to the UK.
3. **Updates go out automatically.** Copy the service's **Deploy Hook** (Settings) into the repo secret `RENDER_DEPLOY_HOOK`. After that, each build tells Render to deploy itself.
4. **Optional: your own address.** In Render, open **Settings → Custom Domains** and add `play.impz.club`, then add the CNAME record it shows to impz.club's DNS. Render sets up HTTPS for you.

Keep it to one instance: the room lives in that instance's memory, so two instances would split the players. Deploying restarts the room, and players reconnect after a few seconds. `/healthz` reports `{ok, online}`.

## Capacity (`npm run load`)

The load test runs 100 players all walking at once for 20 s on this PC:

- **CPU:** about 2% of one core.
- **Delay:** moves arrive about 70 ms later (the 10-a-second tick is most of that).
- **Traffic:** about 18 Mbit/s goes out, which is about 8 GB an hour with all 100 moving nonstop. Real players stand still a lot and send nothing then, so it's much less in practice. Still, watch the traffic allowance in Render if many people play for hours.

The first visit downloads the game, about 115 MB. Returning players skip it unless the game changed.
