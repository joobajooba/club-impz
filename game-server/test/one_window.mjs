// One game per player: a second window from the same browser (device id) replaces the first, which is
// told and closed with 4001; a different browser on the same address is left alone.
import { spawn } from "node:child_process";
import { WebSocket } from "ws";

const PORT = 18093;
const server = spawn(process.execPath, ["server.mjs"], { env: { ...process.env, PORT: String(PORT) }, stdio: ["ignore", "pipe", "inherit"] });
await new Promise((ok) => server.stdout.on("data", (d) => String(d).includes("Club Impz beta") && ok()));

function player(device) {
  const ws = new WebSocket(`ws://localhost:${PORT}/ws`);
  const got = [];
  let closed = 0;
  ws.on("message", (d) => got.push(JSON.parse(String(d))));
  ws.on("close", (code) => (closed = code));
  const opened = new Promise((ok) => ws.on("open", ok));
  return { ws, got, opened, closed: () => closed,
    hello: () => ws.send(JSON.stringify({ t: "hello", world: "hub", p: [0, 0, 0], y: 0, m: 0, look: {}, device })) };
}
const wait = (ms) => new Promise((ok) => setTimeout(ok, ms));
let failed = 0;
const check = (ok, what) => { console.log(`${ok ? "ok  " : "FAIL"} ${what}`); if (!ok) failed++; };

const A = "a".repeat(32), B = "b".repeat(32);
const first = player(A);
await first.opened; first.hello(); await wait(300);
const other = player(B);
await other.opened; other.hello(); await wait(300);
check(first.ws.readyState === WebSocket.OPEN, "another browser on the same address is allowed");
const second = player(A);
await second.opened; second.hello(); await wait(400);
check(first.got.some((m) => m.t === "replaced"), "the first window is told it was replaced");
check(first.closed() === 4001, `...and closed with 4001 (${first.closed()})`);
check(second.got.some((m) => m.t === "welcome"), "the second window plays");
check(other.ws.readyState === WebSocket.OPEN, "the other browser still plays");
second.ws.close(); other.ws.close();
server.kill();
console.log(failed ? `${failed} failed` : "all passed");
process.exit(failed ? 1 : 0);
