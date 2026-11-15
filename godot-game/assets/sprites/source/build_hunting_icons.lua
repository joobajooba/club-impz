-- Draws the hunting inventory icons: a hide_, leather_ and trophy_ PNG per tier,
-- 48x48 pixel art in the style of the mining icons (dark outline, lit from the top left).
-- Run from the repo root:
--   aseprite -b --script-param out=sprites/items --script sprites/build_hunting_icons.lua
-- Add --script-param preview=<file.png> to also write a 4x contact sheet.

local OUT = app.params.out or "sprites/items"
local PREVIEW = app.params.preview
local K = dofile((debug.getinfo(1, "S").source:match("^@(.*[/\\])") or "") .. "pixel_icons.lua")
local N, PI, WHITE, px = K.N, K.PI, K.WHITE, K.px
local hex, ramp, mix, lum = K.hex, K.ramp, K.mix, K.lum
local get, set, ellipse, leaf, bez, stroke, edgeOf = K.get, K.set, K.ellipse, K.leaf, K.bez, K.stroke, K.edgeOf
local sparkle, spiral, wisp, srand, rnd, texture = K.sparkle, K.spiral, K.wisp, K.srand, K.rnd, K.texture

---------------------------------------------------------------- colours

local STAR, STAR2 = hex("#ffd84a"), hex("#fff6b0")
local CYAN = hex("#a8f4ff")

local R = {
  hare     = ramp { "#3a2414", "#5e3c22", "#8a5e3a", "#b08460", "#d4ae8a" },
  cream    = ramp { "#7a6450", "#a88e74", "#cdb698", "#e8d8c0", "#fff6e8" },
  fox      = ramp { "#5a1e08", "#94360e", "#c85a1a", "#e8843a", "#f8b070" },
  boar     = ramp { "#22140c", "#3a2416", "#563822", "#765034", "#98704e" },
  wolf     = ramp { "#2a2a30", "#45464e", "#666870", "#8c8e96", "#b8bac0" },
  stag     = ramp { "#5a3a14", "#8a5e26", "#b8863c", "#dcae5c", "#f4d48a" },
  gold     = ramp { "#8a4a06", "#c87a0a", "#f0a818", "#ffd040", "#fff28a" },
  shadow   = ramp { "#120a1c", "#22143a", "#36205a", "#4e3480", "#7050a8" },
  glow     = ramp { "#3a1a6a", "#5a2aa0", "#7a48c8", "#a070e8", "#c8a0ff" },
  frost    = ramp { "#4e5a8a", "#7c88c0", "#aab4e6", "#d4dcff", "#ffffff" },
  ice      = ramp { "#2a6a8a", "#3c96b8", "#6cc4e0", "#a8ecff", "#ffffff" },
  ember    = ramp { "#4a0a0e", "#7a1218", "#ac1e22", "#d83a30", "#f2705a" },
  fire     = ramp { "#c84a10", "#f07a18", "#ffb030", "#ffe070", "#fff8c0" },
  void     = ramp { "#0c0814", "#1a1028", "#2a1a40", "#3e2860", "#5a3c88" },
  star     = ramp { "#0a1030", "#14224e", "#1e3674", "#2c4e9a", "#4a72c4" },
  storm    = ramp { "#1e2228", "#323a44", "#4a5666", "#687888", "#90a0b0" },
  bolt     = ramp { "#a07a08", "#d8b010", "#ffe040", "#fff490", "#ffffff" },
  teal     = ramp { "#062a2e", "#0c4a50", "#167078", "#2a9aa0", "#5ccac8" },
  pearl    = ramp { "#5a8a90", "#8abcc0", "#b8e0e0", "#e0f6f4", "#ffffff" },
  emerald  = ramp { "#0c3a1e", "#14582c", "#1e7a3c", "#2ea050", "#5cd070" },
  prism    = ramp { "#4a0a3a", "#7a1460", "#b0228a", "#e04cb8", "#ff90e0" },
  sun      = ramp { "#8a6a2a", "#c09a48", "#e6c878", "#f8e8b8", "#ffffff" },
  eclipse  = ramp { "#060508", "#121016", "#1e1a24", "#2c2634", "#40384a" },
  bone     = ramp { "#6a5a48", "#9a8670", "#c4b298", "#e2d4bc", "#fff4e0" },
  strap    = ramp { "#24160c", "#3a2616", "#543822", "#704c30", "#8e6644" },
  twine    = ramp { "#5a3a1a", "#7e5628", "#a4783c", "#c89c58", "#e8c27c" },
}

-- tanned look for leather: a little greyer and warmer than the hide
local function tanned(r)
  local out = {}
  for i, c in ipairs(r) do
    local g = lum(c)
    out[i] = mix(mix(c, { g, g, g }, 0.1), { 120, 80, 50 }, 0.12)
  end
  return out
end

---------------------------------------------------------------- helpers

local function line(pts, rr, r, o)
  for i = 1, #pts - 1 do
    local a, b = pts[i], pts[i + 1]
    stroke(a, { (a[1] + b[1]) / 2, (a[2] + b[2]) / 2 }, b, rr, rr, r, o)
  end
end

local function ring(cx, cy, rr, c, from, to)
  for i = 0, 95 do
    local a = i / 96 * 2 * PI
    if not from or (a >= from and a <= to) then set(cx + math.cos(a) * rr, cy + math.sin(a) * rr, c) end
  end
end

local function glint(x, y, c)
  set(x, y, c); set(x + 1, y, c); set(x, y + 1, mix(c, WHITE, 0.3))
end

-- brick-like rows of scales over every pixel drawn in ramp r
local function scales(r)
  for k, c in pairs(px) do
    for i, rc in ipairs(r) do
      if c == rc then
        local x, y = k % N, k // N
        local sy, sx = y % 4, (x + ((y // 4) % 2) * 2) % 4
        if (sy == 3 and sx ~= 0) or (sx == 0 and sy > 0 and sy < 3) then px[k] = r[math.max(i - 1, 1)] end
        break
      end
    end
  end
end

local onSkin = function(x, y) return get(x, y) ~= nil end

---------------------------------------------------------------- hides

-- one stretched-pelt shape for every tier: four leg flaps, a head and a tail
-- o.marks draws the tier's markings, o.scales swaps fur for scales, o.after adds sparkles and the like
-- knocks out some edge pixels so fur looks ragged
local function fringe(prob)
  local cut = {}
  for k in pairs(px) do
    local x, y = k % N, k // N
    if not (get(x + 1, y) and get(x - 1, y) and get(x, y + 1) and get(x, y - 1)) and rnd() < prob then
      cut[#cut + 1] = k
    end
  end
  for _, k in ipairs(cut) do px[k] = nil end
end

local function hide(r, o)
  o = o or {}
  local flat = { vein = false, edge = false }
  for _, l in ipairs { { 16, 19, 4, 9 }, { 32, 19, 44, 9 }, { 16, 32, 4, 43 }, { 32, 32, 44, 43 } } do
    leaf(l[1], l[2], l[3], l[4], 4.6, r, flat)
  end
  leaf(24, 16, 24, 5, 5.5, r, { shape = "oval", vein = false, edge = false })
  leaf(21, 8, 18, 2, 2, r, { shape = "thorn", vein = false, edge = false })
  leaf(27, 8, 30, 2, 2, r, { shape = "thorn", vein = false, edge = false })
  leaf(24, 36, 27, 47, 2.2, r, flat)
  ellipse(24, 26, 12, 12.5, r, { edge = false })
  srand(o.seed or 5)
  if not o.scales then fringe(0.3) end
  if o.marks then o.marks() end
  if o.scales then scales(r) else texture(px, r, o.up or 0.22, o.down or 0.12) end
  for _, t in ipairs(o.tex or {}) do texture(px, t) end
  if o.after then o.after() end
end

local soft = { edge = false, clip = onSkin }

local HIDES = {
  hare = function()
    hide(R.hare, { marks = function() ellipse(24, 27, 5, 8, R.cream, soft) end, tex = { R.cream } })
  end,
  fox = function()
    hide(R.fox, {
      marks = function()
        ellipse(24, 27, 5, 9, R.cream, soft)
        ellipse(25, 45, 3, 2.5, R.cream, soft)
      end,
      tex = { R.cream },
    })
  end,
  boar = function()
    hide(R.boar, {
      up = 0.3, down = 0.2,
      marks = function() stroke({ 24, 5 }, { 24, 22 }, { 24, 40 }, 1.6, 1.6, R.boar, { edge = false, lift = -0.35 }) end,
    })
  end,
  wolf = function()
    hide(R.wolf, {
      marks = function()
        ellipse(24, 30, 5, 7, R.cream, soft)
        ellipse(24, 19, 9, 6, R.wolf, { edge = false, clip = onSkin, lift = -0.25 })
      end,
      tex = { R.cream },
    })
  end,
  goldhorn_stag = function()
    hide(R.stag, {
      marks = function()
        for _, s in ipairs { { 19, 18 }, { 28, 16 }, { 22, 24 }, { 30, 23 }, { 18, 30 }, { 27, 31 }, { 23, 36 } } do
          ellipse(s[1], s[2], 1.5, 1.3, R.cream, soft)
        end
      end,
      after = function() sparkle(41, 26, 2, R.gold[5], WHITE); sparkle(6, 25, 1, R.gold[5], WHITE) end,
    })
  end,
  shadowcat = function()
    hide(R.shadow, {
      marks = function()
        for _, s in ipairs { { 19, 17 }, { 29, 18 }, { 23, 25 }, { 17, 32 }, { 30, 31 }, { 24, 37 }, { 12, 10 }, { 37, 40 } } do
          ellipse(s[1], s[2], 2.2, 2, R.shadow, { edge = false, clip = onSkin, lift = -0.4 })
          set(s[1], s[2], R.glow[3])
        end
      end,
    })
  end,
  frostmane_yeti = function()
    hide(R.frost, {
      up = 0.3, down = 0.22, seed = 9,
      after = function()
        sparkle(41, 25, 2, R.frost[4], WHITE); sparkle(6, 26, 1, R.frost[4], WHITE)
        set(20, 18, WHITE); set(29, 29, WHITE); set(14, 38, WHITE)
      end,
    })
  end,
  cinder_salamander = function()
    hide(R.ember, {
      scales = true,
      after = function()
        local o = { edge = false, lift = 0.1 }
        line({ { 19, 14 }, { 22, 20 }, { 19, 27 } }, 0.6, R.fire, o)
        line({ { 29, 15 }, { 27, 22 }, { 31, 29 }, { 28, 35 } }, 0.6, R.fire, o)
        line({ { 23, 31 }, { 25, 37 } }, 0.6, R.fire, o)
        set(38, 4, R.fire[4]); set(9, 5, R.fire[3]); set(42, 20, R.fire[4])
      end,
    })
  end,
  voidstalker = function()
    hide(R.void, {
      after = function()
        spiral(24, 25, 7, 2.3, R.glow[3]); set(24, 25, R.glow[5])
        wisp(3, 22, R.glow[3]); wisp(42, 23, R.glow[3])
      end,
    })
  end,
  starwyrm = function()
    hide(R.star, {
      scales = true,
      after = function()
        sparkle(20, 19, 2, STAR, STAR2); sparkle(29, 31, 2, STAR, STAR2)
        for _, d in ipairs { { 28, 15 }, { 17, 30 }, { 24, 26 }, { 10, 11 }, { 38, 41 }, { 24, 6 }, { 31, 22 } } do set(d[1], d[2], STAR) end
      end,
    })
  end,
  stormhorn_ram = function()
    hide(R.storm, {
      up = 0.28, down = 0.16,
      after = function()
        line({ { 27, 11 }, { 20, 23 }, { 27, 24 }, { 19, 38 } }, 1, R.bolt, { edge = false, lift = 0.2 })
        sparkle(40, 24, 1, R.bolt[4], WHITE); sparkle(7, 27, 1, R.bolt[4], WHITE)
      end,
    })
  end,
  tidecrest_serpent = function()
    hide(R.teal, {
      scales = true,
      marks = function() ellipse(24, 26, 4, 12, R.pearl, soft) end,
      after = function() glint(18, 16, R.pearl[5]) end,
    })
  end,
  mossmane_behemoth = function()
    hide(R.emerald, {
      up = 0.28, down = 0.16,
      after = function()
        for _, s in ipairs { { 19, 17, 15, 12 }, { 30, 28, 35, 24 }, { 21, 34, 17, 38 } } do
          leaf(s[1], s[2], s[3], s[4], 1.8, R.emerald, { vein = false, lift = 0.3 })
        end
        set(26, 18, R.gold[4]); set(17, 27, R.gold[4]); set(31, 36, R.pearl[5])
      end,
    })
  end,
  crystalback_basilisk = function()
    hide(R.prism, {
      scales = true,
      after = function()
        for _, s in ipairs { { 24, 12, 7 }, { 24, 20, 6 }, { 24, 28, 5 } } do
          leaf(s[1] - 3, s[2] + 3, s[1] + 1, s[2] - s[3] + 3, 2.2, R.prism, { shape = "crystal", contrast = 0.3, lift = 0.25 })
        end
        set(22, 9, WHITE); set(22, 17, CYAN); sparkle(41, 25, 1, R.prism[5], WHITE)
      end,
    })
  end,
  sunfeather_griffin = function()
    hide(R.sun, {
      marks = function()
        for row = 0, 4 do
          for col = -1, 1 do
            local x, y = 24 + col * 6, 15 + row * 5
            set(x - 2, y, R.sun[2]); set(x - 1, y + 1, R.sun[2]); set(x, y + 2, R.sun[2])
            set(x + 1, y + 1, R.sun[2]); set(x + 2, y, R.sun[2])
          end
        end
      end,
      up = 0.15, down = 0.06,
      after = function() sparkle(41, 25, 2, R.gold[4], WHITE); sparkle(6, 25, 1, R.gold[4], WHITE) end,
    })
  end,
  eclipse_dragon = function()
    hide(R.eclipse, {
      scales = true,
      after = function()
        ellipse(24, 25, 5, 5, R.eclipse, { lift = -0.4 })
        ring(24, 25, 6, R.sun[4])
        ring(24, 25, 6, WHITE, PI * 0.9, PI * 1.6)
      end,
    })
  end,
}

---------------------------------------------------------------- leathers

-- one rolled-and-strapped shape for every tier; accent(A, mx, my) adds the tier's mark
local function leather(r, accent)
  local A, B = { 13, 35 }, { 36, 13 }
  local lr = tanned(r)
  stroke(A, { (A[1] + B[1]) / 2, (A[2] + B[2]) / 2 }, B, 7, 7, lr)
  local ux, uy = B[1] - A[1], B[2] - A[2]
  local l = math.sqrt(ux * ux + uy * uy)
  ux, uy = ux / l, uy / l
  local nx, ny = -uy, ux
  local mx, my = A[1] + (B[1] - A[1]) * 0.58, A[2] + (B[2] - A[2]) * 0.58
  stroke({ mx - nx * 8, my - ny * 8 }, { mx, my }, { mx + nx * 8, my + ny * 8 }, 1.7, 1.7, R.strap)
  ellipse(mx + nx * 5, my + ny * 5, 2, 2, R.gold, { lift = 0.1 })
  ellipse(A[1], A[2], 6.4, 6.4, lr, { lift = 0.15 })
  spiral(A[1] + 0.5, A[2] + 0.5, 5.2, 2.3, lr[2])
  if accent then accent(A, mx, my) end
end

local LEATHERS = {
  hare = function() leather(R.hare) end,
  fox = function() leather(R.fox) end,
  boar = function() leather(R.boar) end,
  wolf = function() leather(R.wolf) end,
  goldhorn_stag = function()
    leather(R.stag, function()
      set(30, 14, WHITE); set(22, 23, WHITE); set(35, 10, WHITE)
      sparkle(41, 27, 2, R.gold[5], WHITE)
    end)
  end,
  shadowcat = function()
    leather(R.shadow, function() set(30, 15, R.glow[4]); set(22, 22, R.glow[4]); set(34, 11, R.glow[3]) end)
  end,
  frostmane_yeti = function()
    leather(R.frost, function()
      set(30, 14, WHITE); set(23, 22, WHITE); set(34, 10, WHITE)
      sparkle(41, 27, 2, R.frost[4], WHITE)
    end)
  end,
  cinder_salamander = function()
    leather(R.ember, function()
      line({ { 20, 26 }, { 24, 23 }, { 27, 19 } }, 0.55, R.fire, { edge = false, lift = 0.1 })
      line({ { 31, 14 }, { 35, 11 } }, 0.55, R.fire, { edge = false, lift = 0.1 })
    end)
  end,
  voidstalker = function()
    leather(R.void, function(A)
      spiral(A[1] + 0.5, A[2] + 0.5, 5.2, 2.3, R.glow[3])
      wisp(40, 26, R.glow[3])
    end)
  end,
  starwyrm = function()
    leather(R.star, function()
      for _, d in ipairs { { 30, 14 }, { 22, 23 }, { 34, 9 }, { 26, 20 }, { 38, 15 } } do set(d[1], d[2], STAR) end
      sparkle(41, 27, 1, STAR, STAR2)
    end)
  end,
  stormhorn_ram = function()
    leather(R.storm, function()
      line({ { 33, 9 }, { 29, 15 }, { 33, 15 }, { 28, 21 } }, 0.55, R.bolt, { edge = false, lift = 0.2 })
    end)
  end,
  tidecrest_serpent = function() leather(R.teal) end,
  mossmane_behemoth = function()
    leather(R.emerald, function(_, mx, my)
      leaf(mx + 2, my - 2, mx + 9, my - 9, 2, R.emerald, { vein = false, lift = 0.3 })
    end)
  end,
  crystalback_basilisk = function()
    leather(R.prism, function() set(30, 13, WHITE); set(31, 13, CYAN); set(22, 22, WHITE) end)
  end,
  sunfeather_griffin = function()
    leather(R.sun, function()
      set(30, 14, WHITE); set(22, 23, WHITE)
      sparkle(41, 27, 2, R.gold[4], WHITE); sparkle(40, 5, 1, R.gold[4], WHITE)
    end)
  end,
  eclipse_dragon = function()
    leather(R.eclipse, function(A)
      ellipse(A[1], A[2], 3, 3, R.eclipse, { lift = -0.4 })
      ring(A[1], A[2], 4.5, R.sun[4])
      ring(A[1], A[2], 4.5, WHITE, PI * 0.9, PI * 1.6)
    end)
  end,
}

---------------------------------------------------------------- trophies

local TROPHIES = {}

TROPHIES.hare = function() -- Lucky Foot
  leaf(24, 43, 24, 12, 9.5, R.hare, { shape = "drop", vein = false })
  for _, c in ipairs { { 19, 42, 18, 46 }, { 24, 43, 24, 47 }, { 29, 42, 30, 46 } } do
    leaf(c[1], c[2], c[3], c[4], 1.4, R.bone, { shape = "thorn", vein = false })
  end
  srand(21); texture(px, R.hare)
  ellipse(24, 13, 4.5, 2.5, R.gold)
  ring(24, 7, 3.2, R.gold[4])
end

TROPHIES.fox = function() -- Brush Tail
  stroke({ 10, 43 }, { 12, 18 }, { 34, 10 }, 3, 7.5, R.fox)
  ellipse(37, 8, 6, 6, R.cream, soft)
  srand(22); texture(px, R.fox); texture(px, R.cream)
end

TROPHIES.boar = function() -- Boar Tusk
  stroke({ 12, 40 }, { 12, 14 }, { 38, 8 }, 5, 0.8, R.bone)
  ellipse(12, 41, 5.5, 3.2, R.boar)
  for _, d in ipairs { { 15, 26 }, { 14, 27 }, { 18, 18 }, { 17, 19 } } do set(d[1], d[2], R.bone[2]) end
end

TROPHIES.wolf = function() -- Wolf Fang
  stroke({ 4, 6 }, { 24, 22 }, { 44, 6 }, 0.7, 0.7, R.twine)
  leaf(24, 15, 25, 45, 6.5, R.bone, { shape = "thorn", vein = false })
  ellipse(24, 15, 5, 2.6, R.wolf, { lift = 0.1 })
end

TROPHIES.goldhorn_stag = function() -- Golden Antler
  local p0, p1, p2 = { 16, 45 }, { 14, 26 }, { 30, 5 }
  stroke(p0, p1, p2, 3.2, 1.3, R.gold)
  for _, t in ipairs { { 0.18, -9, -5 }, { 0.42, 10, -5 }, { 0.66, 9, -3 } } do
    local x, y = bez(p0, p1, p2, t[1])
    stroke({ x, y }, { x + t[2] * 0.5, y + t[3] * 0.2 - 2 }, { x + t[2], y + t[3] - 4 }, 2, 0.8, R.gold)
  end
  ellipse(16, 44, 4.5, 2.5, R.stag)
  sparkle(41, 10, 2, R.gold[5], WHITE); sparkle(7, 14, 1, R.gold[5], WHITE); sparkle(37, 36, 1, R.gold[5], WHITE)
end

TROPHIES.shadowcat = function() -- Shadow Claw
  for i = 0, 2 do
    local p0, p1, p2 = { 11 + i * 9, 43 }, { 9 + i * 9, 22 }, { 21 + i * 9, 6 }
    stroke(p0, p1, p2, 3.6, 0.6, R.shadow)
    stroke({ p0[1] + 1.5, p0[2] - 3 }, { p1[1] + 1.8, p1[2] }, { p2[1], p2[2] + 1.5 }, 0.5, 0.4, R.glow, { edge = false, lift = 0.2 })
    set(p2[1], p2[2], R.glow[5])
  end
end

TROPHIES.frostmane_yeti = function() -- Frozen Heart
  ellipse(17, 19, 8.5, 8.5, R.frost)
  ellipse(31, 19, 8.5, 8.5, R.frost, { edge = false })
  leaf(24, 20, 24, 43, 14.5, R.frost, { shape = "thorn", vein = false, edge = false })
  local o = { edge = false, lift = 0.4 }
  line({ { 24, 24 }, { 16, 13 } }, 0.5, R.frost, o)
  line({ { 24, 24 }, { 31, 13 } }, 0.5, R.frost, o)
  line({ { 24, 24 }, { 24, 38 } }, 0.5, R.frost, { edge = false, lift = -0.2 })
  ellipse(24, 25, 4, 4, R.ice)
  set(23, 23, WHITE)
  sparkle(42, 6, 2, R.frost[4], WHITE); sparkle(6, 36, 1, R.frost[4], WHITE)
end

TROPHIES.cinder_salamander = function() -- Ember Scale
  leaf(24, 4, 24, 44, 13, R.ember, { shape = "drop", vein = false })
  stroke({ 24, 8 }, { 24, 24 }, { 24, 40 }, 0.8, 0.6, R.ember, { edge = false, lift = 0.25 })
  local o = { edge = false, lift = 0.1 }
  line({ { 16, 13 }, { 20, 20 }, { 17, 27 } }, 0.6, R.fire, o)
  line({ { 31, 12 }, { 28, 20 }, { 32, 27 }, { 29, 33 } }, 0.6, R.fire, o)
  line({ { 21, 30 }, { 23, 36 } }, 0.6, R.fire, o)
  set(40, 5, R.fire[4]); set(8, 8, R.fire[3]); set(42, 19, R.fire[4])
end

TROPHIES.voidstalker = function() -- Void Eye
  leaf(5, 24, 43, 24, 12, R.void, { shape = "almond", vein = false })
  ellipse(24, 24, 8.5, 9, R.glow)
  stroke({ 24, 16 }, { 24, 24 }, { 24, 32 }, 1.4, 1.4, R.void, { edge = false, lift = -0.5 })
  set(20, 19, WHITE); set(21, 19, WHITE); set(20, 20, R.glow[5])
  wisp(4, 6, R.glow[3]); wisp(40, 5, R.glow[3]); wisp(40, 39, R.glow[2])
end

TROPHIES.starwyrm = function() -- Star Horn
  local p0, p1, p2, r0, r1 = { 13, 44 }, { 14, 22 }, { 34, 4 }, 5.5, 0.7
  stroke(p0, p1, p2, r0, r1, R.star)
  for t = 0.12, 0.8, 0.11 do
    local ax, ay = edgeOf(p0, p1, p2, r0, r1, t, 1)
    local bx, by = edgeOf(p0, p1, p2, r0, r1, t + 0.05, -1)
    stroke({ ax, ay }, { (ax + bx) / 2, (ay + by) / 2 }, { bx, by }, 0.45, 0.45, R.star, { edge = false, lift = -0.35 })
  end
  ellipse(13, 42, 6, 2.6, R.gold)
  sparkle(16, 28, 1, STAR, STAR2); set(24, 15, STAR); set(19, 21, STAR)
  sparkle(38, 26, 2, STAR, STAR2); sparkle(6, 14, 1, STAR, STAR2)
end

TROPHIES.stormhorn_ram = function() -- Thunder Curl: a curled ram's horn
  local cx, cy, pts = 23, 24, {}
  for i = 0, 48 do
    local t = i / 48
    local a = -PI * 0.15 + t * 1.4 * 2 * PI
    local rr = 16 * (1 - t * 0.7)
    pts[#pts + 1] = { cx + math.cos(a) * rr, cy + math.sin(a) * rr, 4.6 * (1 - t * 0.78) }
  end
  for i = #pts - 1, 1, -1 do
    local a, b = pts[i + 1], pts[i]
    stroke({ a[1], a[2] }, { (a[1] + b[1]) / 2, (a[2] + b[2]) / 2 }, { b[1], b[2] }, a[3], b[3], R.storm, { edge = false, lift = 0.08 })
  end
  -- ridges across the horn
  for i = 3, #pts - 6, 4 do
    local p, q = pts[i], pts[i + 1]
    local tx, ty = q[1] - p[1], q[2] - p[2]
    local l = math.sqrt(tx * tx + ty * ty)
    local nx, ny = -ty / l * p[3] * 0.85, tx / l * p[3] * 0.85
    stroke({ p[1] - nx, p[2] - ny }, { p[1], p[2] }, { p[1] + nx, p[2] + ny }, 0.45, 0.45, R.storm, { edge = false, lift = -0.4 })
  end
  line({ { 30, 7 }, { 26, 12 }, { 30, 12 }, { 25, 18 } }, 0.7, R.bolt, { edge = false, lift = 0.2 })
  sparkle(42, 40, 1, R.bolt[4], WHITE); sparkle(5, 8, 1, R.bolt[4], WHITE); set(43, 9, R.bolt[4])
end

TROPHIES.tidecrest_serpent = function() -- Abyss Pearl
  ellipse(24, 23, 16, 10, R.teal, { clip = function(x, y) return y <= 23 end, lift = 0.05 })
  ellipse(24, 32, 18, 11, R.teal, { clip = function(x, y) return y >= 32 end })
  for i = -3, 3 do
    stroke({ 24, 33 }, { 24 + i * 2.3, 37 }, { 24 + i * 4.6, 42 }, 0.45, 0.45, R.teal, { edge = false, lift = -0.3 })
  end
  ellipse(24, 28, 8, 8, R.pearl)
  glint(20, 24, WHITE)
  ring(39, 9, 1.6, R.pearl[4]); set(42, 4, R.pearl[4]); ring(8, 12, 1.2, R.pearl[3])
end

TROPHIES.mossmane_behemoth = function() -- Verdant Mane
  local ends = { { 20, 44 }, { 28, 44 }, { 35, 41 }, { 40, 35 }, { 43, 27 } }
  for i, e in ipairs(ends) do
    stroke({ 13, 10 }, { 13 + (e[1] - 13) * 0.2 + 8, 10 + (e[2] - 10) * 0.6 - 4 + i }, e, 2.8, 0.6, R.emerald)
  end
  srand(24); texture(px, R.emerald, 0.15, 0.08)
  leaf(15, 8, 24, 3, 2.4, R.emerald, { vein = false, lift = 0.25 })
  leaf(12, 7, 5, 2, 2, R.emerald, { vein = false, lift = 0.25 })
  ellipse(13, 10, 4.5, 4.5, R.gold)
  set(11, 8, WHITE)
end

TROPHIES.crystalback_basilisk = function() -- Prism Shard
  leaf(19, 42, 8, 17, 5, R.prism, { shape = "crystal", contrast = 0.3 })
  leaf(29, 42, 40, 19, 5, R.prism, { shape = "crystal", contrast = 0.3 })
  leaf(24, 43, 24, 4, 7, R.prism, { shape = "crystal", contrast = 0.3, lift = 0.05 })
  ellipse(24, 43, 13, 4, R.storm, { clip = function(x, y) return y >= 41 end })
  set(22, 14, WHITE); set(22, 15, CYAN); set(21, 18, CYAN); set(11, 24, WHITE); set(36, 25, CYAN)
  sparkle(41, 8, 1, R.prism[5], WHITE); sparkle(7, 8, 1, R.prism[5], WHITE)
end

TROPHIES.sunfeather_griffin = function() -- Sun Feather
  leaf(14, 37, 36, 5, 8, R.sun, { saw = 9, veinC = R.sun[2] })
  stroke({ 11, 45 }, { 12, 41 }, { 15, 36 }, 1, 0.9, R.sun, { lift = 0.3 })
  ellipse(33, 9, 5.5, 5.5, R.gold, { edge = false, clip = onSkin })
  sparkle(41, 22, 2, R.gold[4], WHITE); sparkle(9, 13, 1, R.gold[4], WHITE); sparkle(38, 38, 1, R.gold[4], WHITE)
end

TROPHIES.eclipse_dragon = function() -- Eclipse Crown
  local spikes = { { 9, 18 }, { 16.5, 12 }, { 24, 5 }, { 31.5, 12 }, { 39, 18 } }
  for _, s in ipairs(spikes) do
    leaf(s[1], 35, s[1], s[2], 3.4, R.eclipse, { shape = "thorn", vein = false })
  end
  for _, s in ipairs(spikes) do ellipse(s[1], s[2], 1.7, 1.7, R.gold, { lift = 0.1 }) end
  stroke({ 7, 37 }, { 24, 41 }, { 41, 37 }, 4, 4, R.gold)
  ellipse(24, 26, 5.5, 5.5, R.eclipse, { lift = -0.3 })
  ring(24, 26, 6.5, R.sun[4])
  ring(24, 26, 6.5, WHITE, PI * 0.9, PI * 1.6)
  for _, g in ipairs { { 15, 38 }, { 33, 38 } } do ellipse(g[1], g[2], 1.6, 1.6, R.pearl, { lift = 0.1 }) end
end

---------------------------------------------------------------- output

-- tier order, with each trophy's file name
local ORDER = {
  { "hare", "lucky_foot" }, { "fox", "brush_tail" }, { "boar", "boar_tusk" }, { "wolf", "wolf_fang" },
  { "goldhorn_stag", "golden_antler" }, { "shadowcat", "shadow_claw" }, { "frostmane_yeti", "frozen_heart" },
  { "cinder_salamander", "ember_scale" }, { "voidstalker", "void_eye" }, { "starwyrm", "star_horn" },
  { "stormhorn_ram", "thunder_curl" }, { "tidecrest_serpent", "abyss_pearl" }, { "mossmane_behemoth", "verdant_mane" },
  { "crystalback_basilisk", "prism_shard" }, { "sunfeather_griffin", "sun_feather" }, { "eclipse_dragon", "eclipse_crown" },
}

local made = {}
for _, t in ipairs(ORDER) do
  local id, trophy = t[1], t[2]
  made[#made + 1] = {
    K.render(HIDES[id], OUT .. "/hide_" .. id .. ".png"),
    K.render(LEATHERS[id], OUT .. "/leather_" .. id .. ".png"),
    K.render(TROPHIES[id], OUT .. "/trophy_" .. trophy .. ".png"),
  }
end
if PREVIEW then K.sheet(made, PREVIEW) end
