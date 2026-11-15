// The teleport menu (T): a "tp" is taken as a jump, but only once every 3 s; a plain far move is still pulled back.
import { spawn } from "node:child_process";
import { WebSocket } from "ws";

const PORT = 18094;
const server = spawn(process.execPath, ["server.mjs"], { env: { ...process.env, PORT: String(PORT) }, stdio: ["ignore", "pipe", "inherit"] });
await new Promise((ok) => server.stdout.on("data", (d) => String(d).includes("Club Impz beta") && ok()));

function player(device) {
  const ws = new WebSocket(`ws://localhost:${PORT}/ws`);
  const got = [];
  ws.on("message", (d) => got.push(JSON.parse(String(d))));
  const opened = new Promise((ok) => ws.on("open", ok));
  return { ws, got, opened, hello: () => ws.send(JSON.stringify({ t: "hello", world: "hub", p: [0, 0, 0], y: 0, m: 0, look: {}, device })) };
}
const wait = (ms) => new Promise((ok) => setTimeout(ok, ms));
let failed = 0;
const check = (ok, what) => { console.log(`${ok ? "ok  " : "FAIL"} ${what}`); if (!ok) failed++; };
const seen = (b, id) => b.got.filter((m) => m.t === "states").flatMap((m) => m.s).filter((r) => r[0] === id).pop();

const a = player("a".repeat(32)), b = player("b".repeat(32));
await a.opened; a.hello(); await wait(300);
await b.opened; b.hello(); await wait(300);
const ida = a.got.find((m) => m.t === "welcome").id;

a.ws.send(JSON.stringify({ t: "tp", p: [500, 10, 40], y: 1 }));
await wait(250);
let st = seen(b, ida);
check(st && st[1] === 500 && st[3] === 40, `a teleport lands where it says (${JSON.stringify(st)})`);
a.ws.send(JSON.stringify({ t: "tp", p: [900, 10, 40], y: 1 }));
await wait(250);
a.ws.send(JSON.stringify({ t: "s", p: [900, 10, 40], y: 1, m: 0 }));
await wait(250);
st = seen(b, ida);
check(st && st[1] < 520, `a second teleport within 3 s is refused and the move pulled back (${JSON.stringify(st)})`);
await wait(3000);
a.ws.send(JSON.stringify({ t: "tp", p: [900, 10, 40], y: 1 }));
await wait(250);
st = seen(b, ida);
check(st && st[1] === 900, `after 3 s it may teleport again (${JSON.stringify(st)})`);

a.ws.close(); b.ws.close();
server.kill();
console.log(failed ? `${failed} failed` : "all passed");
process.exit(failed ? 1 : 0);
