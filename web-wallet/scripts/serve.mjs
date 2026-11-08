// Serves the Godot web export on http://localhost:8060 for testing the wallet connection.
// - Static files from godot-game/export/web (run `npm run export` first).
// - /api/imps and /api/profile are forwarded to https://www.impz.club, which sends no CORS header, so the
//   game asks its own site instead and gets the wallet's Impz and traits (autoload/look.gd) and its
//   impz.club account (ui/profile/account_panel.gd) through here. The sign-in header goes along.
// No COOP/COEP headers: the export is single-threaded, and Glyph's login popup needs window.opener.
import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { dirname, extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../../godot-game/export/web");
const port = Number(process.env.PORT || 8060);
const API = "https://www.impz.club";
const TYPES = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".wasm": "application/wasm",
  ".pck": "application/octet-stream", ".png": "image/png", ".svg": "image/svg+xml", ".json": "application/json",
  ".ico": "image/x-icon",
};

if (!existsSync(join(root, "index.html"))) {
  console.error(`No export at ${root}. Run \`npm run export\` first.`);
  process.exit(1);
}

createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${port}`);
  try {
    if (url.pathname === "/api/imps" || url.pathname === "/api/profile") {
      const headers = { Accept: "application/json", "Content-Type": "application/json" };
      if (req.headers["x-impz-session"]) headers["x-impz-session"] = req.headers["x-impz-session"];
      const upstream = await fetch(API + url.pathname + url.search, {
        method: req.method,
        headers,
        body: req.method === "GET" || req.method === "HEAD" ? undefined : req,
        duplex: "half",
      });
      res.writeHead(upstream.status, { "Content-Type": upstream.headers.get("content-type") || "application/json", "Cache-Control": "no-store" });
      res.end(Buffer.from(await upstream.arrayBuffer()));
      console.log(`api ${req.method} ${url.pathname}${url.search} -> ${upstream.status}`);
      return;
    }
    const file = normalize(join(root, decodeURIComponent(url.pathname === "/" ? "/index.html" : url.pathname)));
    if (!file.startsWith(root) || !existsSync(file) || !statSync(file).isFile()) {
      res.writeHead(404).end("Not found");
      return;
    }
    res.writeHead(200, { "Content-Type": TYPES[extname(file)] || "application/octet-stream", "Cache-Control": "no-cache" });
    createReadStream(file).pipe(res);
  } catch (error) {
    console.error(error);
    res.writeHead(502, { "Content-Type": "application/json" }).end(JSON.stringify({ error: String(error.message || error) }));
  }
}).listen(port, "localhost", () => console.log(`Club Impz web build: http://localhost:${port}`));
