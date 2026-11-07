// Exports the Godot game for the web (the "Web" preset) and adds the Glyph wallet bundle next to it.
// Usage: npm run export   (set GODOT to the Godot editor exe if it isn't at the default path below)
import { execFileSync } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const game = resolve(here, "../../godot-game");
const out = join(game, "export/web");
const godot = process.env.GODOT || "C:/Users/lucas/Downloads/Godot_v4.7.2-stable_win64.exe/godot.exe.exe";
const bundle = resolve(here, "../dist/glyph-wallet.js");

if (!existsSync(bundle)) throw new Error("Run `npm run build` first: dist/glyph-wallet.js is missing.");
if (!existsSync(godot)) throw new Error(`Godot not found at ${godot}. Set GODOT to the editor exe.`);
mkdirSync(out, { recursive: true });
const mode = process.argv.includes("--debug") ? "--export-debug" : "--export-release";
console.log(`exporting ${mode.slice(9)} build to ${out} ...`);
execFileSync(godot, ["--headless", "--path", game, mode, "Web", join(out, "index.html")], { stdio: "inherit" });
copyFileSync(bundle, join(out, "glyph-wallet.js"));
console.log("done: export/web/index.html + glyph-wallet.js");
