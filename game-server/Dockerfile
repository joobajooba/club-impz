# Club Impz live beta: the web build plus the multiplayer room, in one small image.
# Build from the repo root (fly.toml does this): export the web build first (web-wallet: npm run export).
FROM node:22-alpine
WORKDIR /app
COPY game-server/package.json game-server/package-lock.json ./game-server/
RUN cd game-server && npm ci --omit=dev --no-audit --no-fund
COPY game-server/*.mjs ./game-server/
COPY godot-game/data/impz/manifest.json ./godot-game/data/impz/manifest.json
COPY godot-game/data/chat_filter.json ./godot-game/data/chat_filter.json
COPY godot-game/export/web ./web
# gzip the big files once here, so each player downloads ~115 MB instead of ~200 MB
RUN for f in $(find web -type f \( -name '*.pck' -o -name '*.wasm' -o -name '*.js' -o -name '*.html' \)); do \
      gzip -6 -c "$f" > "$f.gz"; done
ENV NODE_ENV=production PORT=8080 WEB_ROOT=/app/web MANIFEST=/app/godot-game/data/impz/manifest.json
EXPOSE 8080
USER node
CMD ["node", "game-server/server.mjs"]
