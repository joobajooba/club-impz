// Chat filter: the word lists live in godot-game/data/chat_filter.json (shared with the game's
// scripts/chat_filter.gd, which checks a message before sending it; this one has the final say).
//   cleanChat(text) -> the text the server will consider: control and zero width characters removed,
//                      spaces collapsed, at most MAX_CHAT characters ("" means nothing to send)
//   checkChat(text) -> { ok: false, why } if the message must be refused, else { ok: true, text } with
//                      swearing starred out
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

export const MAX_CHAT = 200;
const here = dirname(fileURLToPath(import.meta.url));
const FILE = process.env.CHAT_FILTER || join(here, "../godot-game/data/chat_filter.json");
const LISTS = JSON.parse(readFileSync(FILE, "utf8"));
const LEET = { 0: "o", 1: "i", 3: "e", 4: "a", 5: "s", 7: "t", "@": "a", $: "s", "!": "i", "|": "i" };
const ALLOW = new Set(LISTS.allow);

export function cleanChat(text) {
  const s = String(text ?? "")
    .replace(/[\u0000-\u001f\u007f-\u009f​-‏‪-‮⁠-⁤﻿]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  return Array.from(s).slice(0, MAX_CHAT).join("").trim();
}

// lower case, accents and leetspeak undone, anything else that is not a letter becomes a space
function norm(s) {
  let out = "";
  for (const c of s.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase()) {
    const l = LEET[c] ?? c;
    out += l >= "a" && l <= "z" ? l : " ";
  }
  return out;
}

function words(s) {
  return norm(s).split(" ").filter(Boolean);
}

// letters spelled out one by one (n i g g a) are joined back into a word
function joinSingles(ws) {
  const out = [];
  let run = "";
  for (const w of ws) {
    if (w.length === 1) {
      run += w;
      continue;
    }
    if (run) out.push(run);
    run = "";
    out.push(w);
  }
  if (run) out.push(run);
  return out;
}

const squash = (w) => w.replace(/(.)\1+/g, "$1");

// long terms match inside a word (also with repeated letters squashed); short ones only the whole word
function hit(word, term, inside) {
  if (ALLOW.has(word)) return false;
  if (term.length >= inside) return word.includes(term) || squash(word).includes(squash(term));
  return word === term || word === term + "s" || word === term + "es" ||
    (word.length > term.length && squash(word) === squash(term));
}

export function checkChat(text) {
  const lower = text.toLowerCase();
  if (LISTS.raw_blocked.some((r) => lower.includes(r))) return { ok: false, why: "filter" };
  const ws = joinSingles(words(text));
  for (const w of ws) for (const t of LISTS.blocked) if (hit(w, t, 5)) return { ok: false, why: "filter" };
  // split up to dodge the filter ("nig ger"): the longer terms are looked for across the whole message
  const all = ws.filter((w) => !ALLOW.has(w)).join("");
  for (const t of LISTS.blocked) if (t.length >= 6 && (all.includes(t) || squash(all).includes(squash(t)))) return { ok: false, why: "filter" };
  const line = ` ${ws.join(" ")} `;
  for (const ph of LISTS.blocked_phrases) if (line.includes(` ${words(ph).join(" ")} `)) return { ok: false, why: "filter" };
  // swearing: starred out, word by word
  const out = text.split(" ").map((part) => {
    const w = words(part).join("");
    return w && LISTS.masked.some((m) => hit(w, m, 4)) ? "*".repeat(Array.from(part).length) : part;
  });
  return { ok: true, text: out.join(" ") };
}
