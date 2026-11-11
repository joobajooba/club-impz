// Club Impz live beta server. One small Node program that does three things on one address:
//   1. Serves the Godot web build (index.html, .wasm, .pck, glyph-wallet.js) from WEB_ROOT.
//   2. Forwards /api/imps and /api/profile to impz.club, which sends no CORS header, so the game asks its
//      own site (autoload/look.gd, ui/profile/account_panel.gd).
//   3. Runs the multiplayer room on /ws (WebSocket): everyone who opens the page joins the same game and
//      sees the other Imps move around (autoload/net.gd in the game).
//
// The room is a relay with rules, not a physics server: each game moves its own Imp and sends where it
// is ~10 times a second; the server checks the numbers and passes them on to players in the same world.
// It decides who is who: a name only comes from a signed-in impz.club account (checked with impz.club),
// and traits only from Impz that account's wallet holds. Everyone else plays as "Guest 1234" in the
// base Imp (game_direction.md section 2). Nothing here touches the database or holds a secret.
//
// Settings (environment): PORT (8080), WEB_ROOT (../godot-game/export/web), SITE (https://www.impz.club),
// MAX_PLAYERS (100).
import { createReadStream, existsSync, readFileSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { dirname, extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { WebSocketServer } from "ws";
import { cleanChat, checkChat } from "./chat_filter.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT || process.argv[2] || 8080);   // `node server.mjs 8060` works too
const WEB_ROOT = resolve(process.env.WEB_ROOT || join(here, "../godot-game/export/web"));
const SITE = (process.env.SITE || "https://www.impz.club").replace(/\/$/, "");
const MAX_PLAYERS = Number(process.env.MAX_PLAYERS || 100);
const MANIFEST = process.env.MANIFEST || join(here, "../godot-game/data/impz/manifest.json");

// Ore events (voidstone and stellarite veins don't grow in the world, they appear as events): every
// EVENT_CHECK_MS each ore with no event running rolls its chance; a hit puts a vein on one of the game's
// EVENT_SPOTS spots (godot-game/scripts/world/resource_landmarks.gd) for its duration, and every player
// is told. EVENT_SCALE (env) speeds the clock up for testing: 60 makes a minute last a second.
const EVENT_SCALE = Number(process.env.EVENT_SCALE || 1);
const EVENT_CHECK_MS = 60 * 1000 / EVENT_SCALE;
const EVENT_SPOTS = 48;
const ORE_EVENTS = {
  void: { chance: 1 / 45, minutes: 15 },        // about once every 45 minutes
  stellarite: { chance: 1 / 120, minutes: 15 }, // about once every 2 hours
};

const TICK_MS = 100;                 // states go out 10 times a second
const MAX_MSGS_PER_SEC = 40;         // a game sends ~10; more than this is closed

// Anti-cheat and abuse limits. The game in the browser can be changed by whoever runs it, so the server
// never takes its word for anything that other players see without checking it first.
const MAX_SPEED = 10;                // m/s along the ground: sprint is 6.5, so a little slack for lag
const MAX_RISE = 12;                 // m/s upwards (a jump starts at 4.6)
const MAX_FALL = 60;                 // m/s downwards
const MOVE_SLACK = 3;                // metres a burst of late packets may catch up by
const MAX_PER_IP = Number(process.env.MAX_PER_IP || 4);   // open connections from one address
const CONNECTS_PER_MIN = Number(process.env.CONNECTS_PER_MIN || 20);   // new connections from one address per minute
const HELLO_WITHIN_MS = 20000;       // a connection that never says hello is closed
const WORLD_EVERY_MS = 3000;         // world changes (they take a loading screen, so never faster)
const CHECK_EVERY_MS = 3000;         // sign-in / look checks that ask impz.club: at most this often
const API_PER_MIN = 60;              // /api/imps and /api/profile requests from one address per minute
const WORLDS = new Set(["hub", "resource", "test"]);
const SLOTS = ["body", "head", "eyes", "clothing", "back"];
const BASE_LOOK = { body: "body_green", head: "", eyes: "", clothing: "", back: "" };
const WALLET = /^0x[0-9a-f]{40}$/;
const TYPES = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".wasm": "application/wasm",
  ".pck": "application/octet-stream", ".png": "image/png", ".svg": "image/svg+xml", ".json": "application/json",
  ".ico": "image/x-icon",
};

// Trait ids the game knows (built by build scripts/export_imp_customizer.py), to refuse made-up ones.
const KNOWN = {};
try {
  const manifest = JSON.parse(readFileSync(MANIFEST, "utf8"));
  for (const slot of SLOTS) KNOWN[slot] = new Set((manifest[slot] || []).map((e) => e.id));
} catch (error) {
  console.warn(`No trait manifest at ${MANIFEST}: every player shows the base Imp. (${error.message})`);
  for (const slot of SLOTS) KNOWN[slot] = new Set([BASE_LOOK[slot]].filter(Boolean));
}

// --- impz.club checks ---------------------------------------------------------------------------

// A signed-in account: the impz.club session the game got from the wallet signature. Answers
// { wallet, username } or null. Needs impz-club PR #8 (?me=1); before that every player is a guest.
async function checkAccount(wallet, session) {
  wallet = String(wallet || "").toLowerCase();
  if (!WALLET.test(wallet) || !session || String(session).length > 1000) return null;
  try {
    const res = await fetch(`${SITE}/api/profile?me=1&wallet=${wallet}`, {
      headers: { Accept: "application/json", "x-impz-session": String(session) },
      signal: AbortSignal.timeout(8000),
    });
    const data = await res.json().catch(() => null);
    if (!res.ok || !data || !Object.hasOwn(data, "profile")) return null;
    return { wallet, username: String(data.profile?.username || "").trim() };
  } catch {
    return null;
  }
}

const traitCache = new Map();          // wallet -> { at, traits }
async function walletTraits(wallet) {
  const hit = traitCache.get(wallet);
  if (hit && Date.now() - hit.at < 5 * 60 * 1000) return hit.traits;
  try {
    const res = await fetch(`${SITE}/api/imps?wallet=${wallet}`, { signal: AbortSignal.timeout(15000) });
    const data = await res.json();
    const traits = res.ok && data && typeof data.traits === "object" ? data.traits : {};
    traitCache.set(wallet, { at: Date.now(), traits });
    return traits;
  } catch {
    return {};
  }
}

// The look other players see: each trait must exist and be held by the player's checked wallet.
async function allowedLook(look, wallet) {
  const out = { ...BASE_LOOK };
  if (!look || typeof look !== "object") return out;
  const traits = wallet ? await walletTraits(wallet) : {};
  for (const slot of SLOTS) {
    const id = String(look[slot] ?? "");
    if (id === "") {
      if (slot !== "body") out[slot] = "";
      continue;
    }
    if (!KNOWN[slot].has(id)) continue;
    if (id === BASE_LOOK[slot] || traits?.[slot]?.[id]) out[slot] = id;
  }
  return out;
}

// --- the room -----------------------------------------------------------------------------------

const events = new Map();              // event id -> { id, ore, spot, until }
let nextEvent = 1;

function eventInfo(e) {
  return { id: e.id, ore: e.ore, spot: e.spot, left: Math.max(0, e.until - Date.now()) };
}

function startEvent(ore) {
  const taken = new Set([...events.values()].map((e) => e.spot));
  let spot = Math.floor(Math.random() * EVENT_SPOTS);
  for (let i = 0; i < EVENT_SPOTS && taken.has(spot); i++) spot = (spot + 1) % EVENT_SPOTS;
  const e = { id: nextEvent++, ore, spot, until: Date.now() + ORE_EVENTS[ore].minutes * 60 * 1000 / EVENT_SCALE };
  events.set(e.id, e);
  broadcast({ t: "ore_event", ev: eventInfo(e) });
  console.log(`ore event #${e.id}: ${ore} at spot ${spot} (${countReady()} online)`);
  return e;
}

setInterval(() => {
  const now = Date.now();
  for (const e of [...events.values()]) {
    if (now >= e.until) {
      events.delete(e.id);
      broadcast({ t: "ore_event_end", id: e.id });
    }
  }
  if (countReady() === 0) return;      // nobody to see it: don't waste the event
  for (const [ore, rule] of Object.entries(ORE_EVENTS)) {
    const running = [...events.values()].some((e) => e.ore === ore);
    if (!running && Math.random() < rule.chance * Math.min(EVENT_CHECK_MS, 1000) / EVENT_CHECK_MS) startEvent(ore);
  }
}, Math.min(EVENT_CHECK_MS, 1000));

const players = new Map();             // id -> player

// Global chat: everyone in every world sees it. Each message is cleaned (at most 100 characters), checked by
// chat_filter.mjs (slurs and abuse are refused, swearing starred out) and rate limited; the last CHAT_KEEP go to
// new players in the welcome.
const CHAT_KEEP = 30;
const chatLog = [];
let nextId = 1;

function publicInfo(p) {
  return { id: p.id, name: p.name, guest: p.guest, look: p.look, world: p.world, s: stateRow(p) };
}

function stateRow(p) {
  return [p.id, round(p.pos[0]), round(p.pos[1]), round(p.pos[2]), round(p.yaw, 1000), p.moving];
}

function round(n, k = 100) {
  return Math.round(n * k) / k;
}

function send(p, msg) {
  if (p.ws.readyState === 1) p.ws.send(typeof msg === "string" ? msg : JSON.stringify(msg));
}

function broadcast(msg, except = null) {
  const text = JSON.stringify(msg);
  for (const p of players.values()) if (p !== except && p.ready) send(p, text);
}

function guestName(id) {
  return `Guest ${String(1000 + ((id * 7919) % 9000))}`;
}

function finite(v, limit) {
  const n = Number(v);
  return Number.isFinite(n) ? Math.max(-limit, Math.min(limit, n)) : 0;
}

// A new position, as far as the player could really have got: a speed or teleport cheat is pulled back
// to the most an Imp can move since the last one, so other players only ever see an Imp moving normally.
// `jump` (hello, world change) takes the position as it is: that is where the player spawned.
function readState(p, msg, jump = false) {
  const now = Date.now();
  if (Array.isArray(msg.p) && msg.p.length === 3) {
    const want = msg.p.map((v) => finite(v, 20000));
    if (jump || !p.movedAt) {
      p.pos = want;
    } else {
      const dt = Math.min((now - p.movedAt) / 1000, 1);
      const dx = want[0] - p.pos[0], dz = want[2] - p.pos[2];
      const flat = Math.hypot(dx, dz);
      const most = MAX_SPEED * dt + MOVE_SLACK;
      const k = flat > most ? most / flat : 1;
      const dy = Math.max(-(MAX_FALL * dt + MOVE_SLACK), Math.min(MAX_RISE * dt + MOVE_SLACK, want[1] - p.pos[1]));
      if (k < 1 || dy !== want[1] - p.pos[1]) p.strikes = (p.strikes || 0) + 1;
      p.pos = [p.pos[0] + dx * k, p.pos[1] + dy, p.pos[2] + dz * k];
    }
    p.movedAt = now;
  }
  if (msg.y != null) p.yaw = finite(msg.y, 1000);
  p.moving = [0, 1, 2].includes(msg.m) ? msg.m : 0;
  p.dirty = true;
}

// Runs a check that asks impz.club (sign-in, look) at most every CHECK_EVERY_MS per player: a burst
// keeps only the last request and runs it when the wait is over, so a quick click through traits still
// ends on the right look, but nobody can make the server hammer impz.club.
function throttled(p, key, run) {
  p.waits ??= {};
  const w = (p.waits[key] ??= { last: 0, next: null, timer: null });
  w.next = run;
  if (w.timer) return;
  const go = () => {
    w.timer = null;
    if (!players.has(p.id) || !w.next) return;
    const fn = w.next;
    w.next = null;
    w.last = Date.now();
    fn().catch((error) => console.error(error));
  };
  const wait = w.last + CHECK_EVERY_MS - Date.now();
  if (wait <= 0) go();
  else w.timer = setTimeout(go, wait);
}

// Who the player is: a checked account's username and wallet, or a guest.
async function identify(p, wallet, session) {
  const account = await checkAccount(wallet, session);
  if (!players.has(p.id)) return;
  p.wallet = account?.wallet || "";
  p.guest = !account?.username;
  p.name = account?.username || guestName(p.id);
}

async function setLook(p, look) {
  const shown = await allowedLook(look, p.wallet);
  if (players.has(p.id)) p.look = shown;
}

async function onMessage(p, msg) {
  switch (msg.t) {
    case "hello": {
      if (p.ready || p.greeting) return;
      p.greeting = true;
      p.world = WORLDS.has(msg.world) ? msg.world : "hub";
      readState(p, msg, true);
      await identify(p, msg.wallet, msg.session);
      await setLook(p, msg.look);
      if (!players.has(p.id)) return;
      p.ready = true;
      const others = [...players.values()].filter((o) => o !== p && o.ready).map(publicInfo);
      send(p, { t: "welcome", id: p.id, name: p.name, guest: p.guest, look: p.look, players: others, online: others.length + 1,
        events: [...events.values()].map(eventInfo), chat: chatLog });
      broadcast({ t: "join", player: publicInfo(p) }, p);
      broadcast({ t: "online", n: countReady() });
      console.log(`join #${p.id} ${p.name}${p.wallet ? " " + p.wallet.slice(0, 8) : ""} (${countReady()} online)`);
      const now = process.env.ORE_EVENT_NOW;
      if (now && ORE_EVENTS[now] && ![...events.values()].some((e) => e.ore === now)) startEvent(now);
      return;
    }
    case "s":
      if (p.ready) readState(p, msg);
      return;
    case "world":
      if (!p.ready || !WORLDS.has(msg.world) || msg.world === p.world) return;
      if (Date.now() - (p.worldAt || 0) < WORLD_EVERY_MS) return;   // world hopping is a teleport
      p.worldAt = Date.now();
      p.world = msg.world;
      readState(p, msg, true);
      broadcast({ t: "update", id: p.id, world: p.world, s: stateRow(p) }, p);
      return;
    case "look":
      if (!p.ready) return;
      throttled(p, "look", async () => {
        await setLook(p, msg.look);
        if (players.has(p.id)) broadcast({ t: "update", id: p.id, look: p.look });
      });
      return;
    case "chat": {
      if (!p.ready) return;
      const now = Date.now();
      p.chatTimes = (p.chatTimes || []).filter((t) => now - t < 5000);
      if (p.chatTimes.length >= 3 || now - (p.chatTimes.at(-1) || 0) < 700) {
        send(p, { t: "chat_blocked", why: "slow" });          // 3 messages per 5 s at most
        return;
      }
      const text = cleanChat(msg.text);
      if (!text) return;
      const res = checkChat(text);
      if (!res.ok) {
        send(p, { t: "chat_blocked", why: res.why });
        console.log(`chat refused from #${p.id} ${p.name}`);
        return;
      }
      p.chatTimes.push(now);
      const line = { t: "chat", id: p.id, name: p.name, guest: p.guest, text: res.text };
      chatLog.push(line);
      if (chatLog.length > CHAT_KEEP) chatLog.shift();
      broadcast(line);
      return;
    }
    case "auth": {
      // signed in or out in the Profile menu: the name and the traits follow
      if (!p.ready) return;
      throttled(p, "auth", async () => {
        await identify(p, msg.wallet, msg.session);
        await setLook(p, msg.look);
        if (players.has(p.id)) broadcast({ t: "update", id: p.id, name: p.name, guest: p.guest, look: p.look });
      });
      return;
    }
  }
}

function countReady() {
  let n = 0;
  for (const p of players.values()) if (p.ready) n++;
  return n;
}

// Every tick, each world's new moves are written once and the same message goes to everyone in that
// world (their own row included: the game skips it). One JSON per world, not one per player, so 100
// players cost about the same as 10.
setInterval(() => {
  const byWorld = new Map();
  for (const p of players.values()) {
    if (!p.ready || !p.dirty) continue;
    p.dirty = false;
    if (!byWorld.has(p.world)) byWorld.set(p.world, []);
    byWorld.get(p.world).push(stateRow(p));
  }
  const text = new Map([...byWorld].map(([world, rows]) => [world, JSON.stringify({ t: "states", s: rows })]));
  for (const p of players.values()) {
    if (p.ready && text.has(p.world)) send(p, text.get(p.world));
  }
}, TICK_MS);

// --- http ---------------------------------------------------------------------------------------

// The player's address. Render's proxy puts the address it saw first in X-Forwarded-For; without a
// proxy (local runs) it is the socket's own.
function addressOf(req) {
  const fwd = String(req.headers["x-forwarded-for"] || "").split(",")[0].trim();
  return fwd || req.socket.remoteAddress || "?";
}

// Counts per address in a rolling minute (connections, API calls).
const perMinute = new Map();           // "kind address" -> { start, n }
function overLimit(kind, ip, limit) {
  const key = kind + " " + ip;
  const now = Date.now();
  const c = perMinute.get(key);
  if (!c || now - c.start > 60000) {
    perMinute.set(key, { start: now, n: 1 });
    return false;
  }
  return ++c.n > limit;
}
setInterval(() => {
  const now = Date.now();
  for (const [k, c] of perMinute) if (now - c.start > 60000) perMinute.delete(k);
}, 60000);

async function proxy(req, res, url) {
  const headers = { Accept: "application/json", "Content-Type": "application/json" };
  if (req.headers["x-impz-session"]) headers["x-impz-session"] = req.headers["x-impz-session"];
  const upstream = await fetch(SITE + url.pathname + url.search, {
    method: req.method,
    headers,
    body: req.method === "GET" || req.method === "HEAD" ? undefined : req,
    duplex: "half",
    signal: AbortSignal.timeout(30000),
  });
  res.writeHead(upstream.status, {
    "Content-Type": upstream.headers.get("content-type") || "application/json",
    "Cache-Control": "no-store",
  });
  res.end(Buffer.from(await upstream.arrayBuffer()));
}

// Static files. A ready-made .gz next to a file (made by the Dockerfile) is sent when the browser
// accepts gzip; ETags let a returning player skip the big download when nothing changed.
function serveFile(req, res, url) {
  const file = normalize(join(WEB_ROOT, decodeURIComponent(url.pathname === "/" ? "/index.html" : url.pathname)));
  if (!file.startsWith(WEB_ROOT) || !existsSync(file) || !statSync(file).isFile() || file.endsWith(".gz")) {
    res.writeHead(404, { "Content-Type": "text/plain" }).end("Not found");
    return;
  }
  const gz = /\bgzip\b/.test(req.headers["accept-encoding"] || "") && existsSync(file + ".gz") ? file + ".gz" : "";
  const stat = statSync(gz || file);
  const etag = `"${stat.size.toString(36)}-${Math.floor(stat.mtimeMs).toString(36)}${gz ? "-gz" : ""}"`;
  const headers = {
    "Content-Type": TYPES[extname(file)] || "application/octet-stream",
    "Cache-Control": "no-cache",
    ETag: etag,
    Vary: "Accept-Encoding",
  };
  if (req.headers["if-none-match"] === etag) {
    res.writeHead(304, headers).end();
    return;
  }
  if (gz) headers["Content-Encoding"] = "gzip";
  headers["Content-Length"] = stat.size;
  res.writeHead(200, headers);
  if (req.method === "HEAD") res.end();
  else createReadStream(gz || file).pipe(res);
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  try {
    if (url.pathname === "/healthz") {
      res.writeHead(200, { "Content-Type": "application/json" }).end(JSON.stringify({ ok: true, online: countReady() }));
    } else if (url.pathname === "/api/imps" || url.pathname === "/api/profile") {
      if (overLimit("api", addressOf(req), API_PER_MIN)) {
        res.writeHead(429, { "Content-Type": "application/json", "Retry-After": "60" }).end(JSON.stringify({ error: "too many requests" }));
        return;
      }
      await proxy(req, res, url);
    } else {
      serveFile(req, res, url);
    }
  } catch (error) {
    console.error(error);
    if (!res.headersSent) res.writeHead(502, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: String(error.message || error) }));
  }
});

const wss = new WebSocketServer({ server, path: "/ws", maxPayload: 8 * 1024 });

wss.on("connection", (ws, req) => {
  if (players.size >= MAX_PLAYERS) {
    ws.send(JSON.stringify({ t: "full", max: MAX_PLAYERS }));
    ws.close(1013, "full");
    return;
  }
  // One person can't fill the room or flood it with reconnects.
  const ip = addressOf(req);
  let fromHere = 0;
  for (const o of players.values()) if (o.ip === ip) fromHere++;
  if (fromHere >= MAX_PER_IP || overLimit("ws", ip, CONNECTS_PER_MIN)) {
    ws.close(1008, "too many connections");
    return;
  }
  const p = {
    ip, ws, id: nextId++, ready: false, name: "", guest: true, wallet: "", look: { ...BASE_LOOK },
    world: "hub", pos: [0, 0, 0], yaw: 0, moving: 0, dirty: false, alive: true, window: Date.now(), count: 0,
  };
  p.name = guestName(p.id);
  players.set(p.id, p);
  setTimeout(() => {
    if (!p.ready && !p.greeting && players.has(p.id)) ws.close(1008, "no hello");
  }, HELLO_WITHIN_MS);
  ws.on("pong", () => (p.alive = true));
  ws.on("message", (data) => {
    const now = Date.now();
    if (now - p.window > 1000) {
      p.window = now;
      p.count = 0;
    }
    if (++p.count > MAX_MSGS_PER_SEC) {
      ws.close(1008, "too many messages");
      return;
    }
    let msg;
    try {
      msg = JSON.parse(String(data));
    } catch {
      return;
    }
    if (msg && typeof msg === "object") onMessage(p, msg).catch((error) => console.error(error));
  });
  ws.on("close", () => {
    players.delete(p.id);
    for (const w of Object.values(p.waits || {})) clearTimeout(w.timer);
    if (p.strikes) console.log(`#${p.id} ${p.name}: ${p.strikes} moves pulled back (too fast)`);
    if (p.ready) {
      broadcast({ t: "leave", id: p.id });
      broadcast({ t: "online", n: countReady() });
      console.log(`leave #${p.id} ${p.name} (${countReady()} online)`);
    }
  });
});

// Drops players whose connection died without saying goodbye (closed laptop, lost Wi-Fi).
setInterval(() => {
  for (const p of players.values()) {
    if (!p.alive) {
      p.ws.terminate();
      continue;
    }
    p.alive = false;
    p.ws.ping();
  }
}, 20000);

server.listen(PORT, () => {
  console.log(`Club Impz beta on http://localhost:${PORT} (multiplayer on /ws)`);
  if (!existsSync(join(WEB_ROOT, "index.html"))) console.warn(`No web build at ${WEB_ROOT} yet: run \`npm run export\` in web-wallet.`);
});
