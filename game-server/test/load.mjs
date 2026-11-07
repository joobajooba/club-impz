// 100 pretend players walking at once for 20 s: reports the server's CPU use and how late moves arrive.
import { spawn } from "node:child_process";
import { WebSocket } from "ws";
const N = Number(process.argv[2] || 100), PORT = 18091, SECONDS = 20;
const server = spawn(process.execPath, ["server.mjs"], { env: { ...process.env, PORT: String(PORT), MAX_PLAYERS: "500" }, stdio: ["ignore", "pipe", "ignore"] });
await new Promise((ok) => server.stdout.on("data", (d) => String(d).includes("Club Impz beta") && ok()));
const bots = [];
let received = 0, bytes = 0, lateSum = 0, lateMax = 0, lateN = 0;
for (let i = 0; i < N; i++) {
  const ws = new WebSocket(`ws://localhost:${PORT}/ws`);
  await new Promise((ok) => ws.on("open", ok));
  ws.on("message", (d) => {
    received++; bytes += d.length;
    const m = JSON.parse(String(d));
    if (m.t === "states") for (const r of m.s) { const sent = r[3] * 1000; if (sent > 0) { const late = (Date.now() % 1e6) - sent; if (late >= 0 && late < 5000) { lateSum += late; lateN++; lateMax = Math.max(lateMax, late); } } }
  });
  ws.send(JSON.stringify({ t: "hello", world: "hub", p: [i, 0, 0], y: 0, m: 1 }));
  bots.push(ws);
}
const cpu0 = process.cpuUsage();
const start = Date.now();
// each bot sends its position 10x a second; z carries the send time (ms within the last 1000 s) to time the trip
const timer = setInterval(() => { for (const ws of bots) ws.send(JSON.stringify({ t: "s", p: [Math.random() * 10, 0, (Date.now() % 1e6) / 1000], y: 0, m: 1 })); }, 100);
const usage = [];
const probe = setInterval(async () => { usage.push(await fetch(`http://localhost:${PORT}/healthz`).then((r) => r.json())); }, 5000);
await new Promise((ok) => setTimeout(ok, SECONDS * 1000));
clearInterval(timer); clearInterval(probe);
// server CPU from the OS (Windows: tasklist has no CPU %, so use process time via PowerShell)
const { execSync } = await import("node:child_process");
const cpuSec = Number(execSync(`powershell -NoProfile -Command "(Get-Process -Id ${server.pid}).TotalProcessorTime.TotalSeconds"`).toString().trim());
console.log(`${N} players, ${SECONDS} s: online ${usage.at(-1)?.online}`);
console.log(`server CPU ${(cpuSec / SECONDS * 100).toFixed(1)}% of one core (including start-up)`);
console.log(`each player got ${(received / N / SECONDS).toFixed(1)} msgs/s, ${(bytes / N / SECONDS / 1024).toFixed(1)} KB/s; server sends ${(bytes / SECONDS / 1024 / 1024 * 8).toFixed(2)} Mbit/s total`);
console.log(`move delay: average ${(lateSum / lateN).toFixed(0)} ms, worst ${lateMax} ms (the tick alone adds up to 100 ms)`);
for (const ws of bots) ws.terminate();
server.kill();
process.exit(0);
