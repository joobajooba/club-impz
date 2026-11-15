// Ore events: starts the server with a fast clock and an event on the first join, and checks that every
// player hears about it, a late joiner gets it in the welcome, and everyone hears when it ends.
import { spawn } from "node:child_process";
import { WebSocket } from "ws";

const PORT = 18092;
// EVENT_SCALE 600: a 15 minute event lasts 1.5 s
const server = spawn(process.execPath, ["server.mjs"], {
  env: { ...process.env, PORT: String(PORT), EVENT_SCALE: "600", ORE_EVENT_NOW: "void" },
  stdio: ["ignore", "pipe", "inherit"],
});
await new Promise((ok) => server.stdout.on("data", (d) => String(d).includes("Club Impz beta") && ok()));

function join(name) {
  const ws = new WebSocket(`ws://localhost:${PORT}/ws`);
  const got = [];
  ws.on("message", (d) => got.push(JSON.parse(String(d))));
  ws.on("open", () => ws.send(JSON.stringify({ t: "hello", world: "resource", p: [0, 0, 0], y: 0, m: 0 })));
  return { ws, got, name };
}
const wait = (ms) => new Promise((ok) => setTimeout(ok, ms));
let failed = 0;
function check(ok, what) {
  console.log(`${ok ? "ok  " : "FAIL"} ${what}`);
  if (!ok) failed++;
}

const a = join("a");
await wait(400);
const b = join("b");                    // joins after the event started: gets it in the welcome
await wait(400);
const evA = a.got.find((m) => m.t === "ore_event");
check(evA && evA.ev.ore === "void" && evA.ev.spot >= 0 && evA.ev.spot < 48 && evA.ev.left > 0, "the first player is told a voidstone event started");
const welB = b.got.find((m) => m.t === "welcome");
check(welB && welB.events.length === 1 && welB.events[0].id === evA?.ev.id, "a late joiner gets the running event in the welcome");
check(!b.got.some((m) => m.t === "ore_event" && m.ev.id === evA?.ev.id), "...and is not told twice");
await wait(2000);
check(a.got.some((m) => m.t === "ore_event_end" && m.id === evA?.ev.id), "the first player is told it ended");
check(b.got.some((m) => m.t === "ore_event_end" && m.id === evA?.ev.id), "the second player is told it ended");

a.ws.close(); b.ws.close();
server.kill();
console.log(failed ? `${failed} failed` : "all passed");
process.exit(failed ? 1 : 0);
