// Global chat: messages reach everyone with the sender's name, are cut to 100 characters, slurs and abuse
// are refused, swearing is starred out, spam is slowed down and a late joiner gets the recent history.
import { spawn } from "node:child_process";
import { WebSocket } from "ws";
import { checkChat, cleanChat } from "../chat_filter.mjs";

const PORT = 18093;
const server = spawn(process.execPath, ["server.mjs"], {
  env: { ...process.env, PORT: String(PORT) },
  stdio: ["ignore", "pipe", "inherit"],
});
await new Promise((ok) => server.stdout.on("data", (d) => String(d).includes("Club Impz beta") && ok()));

function join(world) {
  const ws = new WebSocket(`ws://localhost:${PORT}/ws`);
  const got = [];
  ws.on("message", (d) => got.push(JSON.parse(String(d))));
  ws.on("open", () => ws.send(JSON.stringify({ t: "hello", world, p: [0, 0, 0], y: 0, m: 0 })));
  return { ws, got, say: (text) => ws.send(JSON.stringify({ t: "chat", text })) };
}
const wait = (ms) => new Promise((ok) => setTimeout(ok, ms));
let failed = 0;
function check(ok, what) {
  console.log(`${ok ? "ok  " : "FAIL"} ${what}`);
  if (!ok) failed++;
}
const chats = (c) => c.got.filter((m) => m.t === "chat");

// the filter on its own
for (const t of ["hello there", "class assessment on the grass", "we went to nigeria", "therapist", "as you wish", "raccoon", "Scunthorpe"])
  check(checkChat(cleanChat(t)).ok && checkChat(cleanChat(t)).text === cleanChat(t), `allowed untouched: "${t}"`);
for (const t of ["n i g g e r", "N1GG3R", "niiigger", "nig ger", "you f4g", "kill yourself", "KYS", "go back to your country",
  "women belong in the kitchen", "make me a sandwich", "heil hitler", "1488", "you whore", "you are retarded"])
  check(!checkChat(cleanChat(t)).ok, "refused (test phrase " + t.length + " chars)");
check(checkChat("what the fuck").text === "what the ****", "swearing is starred out");
check(cleanChat("x".repeat(150)).length === 100, "cut to 100 characters");

// over the network
const a = join("hub");
const b = join("resource");                       // another world: chat is global
await wait(400);
const nameA = a.got.find((m) => m.t === "welcome")?.name;
a.say("hello everyone");
await wait(300);
const seen = chats(b).find((m) => m.text === "hello everyone");
check(seen && seen.name === nameA, "a message reaches a player in another world, with the sender's name");
check(chats(a).some((m) => m.text === "hello everyone"), "...and comes back to the sender");
await wait(800);
a.say("y".repeat(140));
await wait(300);
check(chats(b).some((m) => m.text === "y".repeat(100)), "a long message is cut to 100 characters");
await wait(800);
a.say("you are a n1gger");
await wait(300);
check(a.got.some((m) => m.t === "chat_blocked" && m.why === "filter"), "a slur is refused and the sender is told");
check(!chats(b).some((m) => /n1gger/i.test(m.text)), "...and nobody else sees it");
await wait(800);
a.say("oh shit");
await wait(300);
check(chats(b).some((m) => m.text === "oh ****"), "swearing arrives starred out");
await wait(800);
for (const n of [1, 2, 3, 4]) a.say(`spam ${n}`);
await wait(300);
check(a.got.some((m) => m.t === "chat_blocked" && m.why === "slow"), "spam is slowed down");
check(chats(b).filter((m) => m.text.startsWith("spam")).length <= 2, "...and not all of it goes out");
const c = join("hub");
await wait(400);
const hist = c.got.find((m) => m.t === "welcome")?.chat || [];
check(hist.some((m) => m.text === "hello everyone"), "a late joiner gets the recent chat in the welcome");

a.ws.close(); b.ws.close(); c.ws.close();
server.kill();
console.log(failed ? `${failed} failed` : "all passed");
process.exit(failed ? 1 : 0);
