// Starts the server on a spare port, joins two players, and checks they see each other move and leave.
import { spawn } from "node:child_process";
import { WebSocket } from "ws";

const PORT = 18090;
const server = spawn(process.execPath, ["server.mjs"], { env: { ...process.env, PORT: String(PORT) }, stdio: ["ignore", "pipe", "inherit"] });
await new Promise((ok) => server.stdout.on("data", (d) => String(d).includes("Club Impz beta") && ok()));

function player(label, extra = {}) {
  const ws = new WebSocket(`ws://localhost:${PORT}/ws`);
  const got = [];
  ws.on("message", (d) => got.push(JSON.parse(String(d))));
  const opened = new Promise((ok) => ws.on("open", ok));
  return { ws, got, opened, label, hello: () => ws.send(JSON.stringify({ t: "hello", world: "hub", p: [1, 2, 3], y: 0.5, m: 0, look: { body: "body_blue", head: "made_up" }, ...extra })) };
}
const wait = (ms) => new Promise((ok) => setTimeout(ok, ms));
let failed = 0;
const check = (ok, what) => { console.log(`${ok ? "ok  " : "FAIL"} ${what}`); if (!ok) failed++; };

const a = player("a"), b = player("b");
await a.opened; a.hello(); await wait(300);
await b.opened; b.hello(); await wait(300);
const wa = a.got.find((m) => m.t === "welcome"), wb = b.got.find((m) => m.t === "welcome");
check(wa && /^Guest \d{4}$/.test(wa.name), `guest name (${wa?.name})`);
check(wa?.look.body === "body_green" && wa?.look.head === "", "guests wear the base Imp, made-up traits refused");
check(wb?.players.length === 1 && wb.players[0].id === wa.id, "b sees a already there");
check(a.got.some((m) => m.t === "join" && m.player.id === wb.id), "a hears b join");
a.ws.send(JSON.stringify({ t: "s", p: [5, 0, -7], y: 1.25, m: 1 }));
await wait(250);
const st = b.got.filter((m) => m.t === "states").flatMap((m) => m.s).find((r) => r[0] === wa.id);
check(st && st[1] === 5 && st[3] === -7 && st[5] === 1, `b gets a's move (${JSON.stringify(st)})`);
a.ws.send(JSON.stringify({ t: "s", p: [1e99, "x", NaN], y: 0, m: 9 }));
await wait(250);
const bad = b.got.filter((m) => m.t === "states").flatMap((m) => m.s).filter((r) => r[0] === wa.id).pop();
check(bad[1] === 20000 && bad[2] === 0 && bad[5] === 0, "bad numbers are clamped");
a.ws.send(JSON.stringify({ t: "world", world: "resource", p: [0, 0, 0], y: 0 }));
await wait(100);
b.got.length = 0;
a.ws.send(JSON.stringify({ t: "s", p: [9, 9, 9], y: 0, m: 1 }));
await wait(250);
check(!b.got.some((m) => m.t === "states" && m.s.some((r) => r[0] === wa.id)), "players in another world aren't sent moves");
for (let i = 0; i < 60; i++) a.ws.send(JSON.stringify({ t: "s", p: [0, 0, 0] }));
await wait(300);
check(a.ws.readyState === WebSocket.CLOSED, "a flood of messages is cut off");
check(b.got.some((m) => m.t === "leave" && m.id === wa.id), "b hears a leave");
b.ws.close();
server.kill();
console.log(failed ? `${failed} failed` : "all passed");
process.exit(failed ? 1 : 0);
