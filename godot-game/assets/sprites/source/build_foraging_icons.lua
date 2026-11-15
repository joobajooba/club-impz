-- Draws the foraging inventory icons: a plant_, bundle_ and seed_<name>.png per tier,
-- 48x48 pixel art in the style of the mining icons (dark outline, lit from the top left).
-- Run from the repo root:
--   aseprite -b --script-param out=sprites/items --script sprites/build_foraging_icons.lua
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
local GLOW = { hex("#4a2a8a"), hex("#7a48c8"), hex("#b088f4") }

local R = {
  leaf      = ramp { "#1f4a24", "#2f6e2e", "#46943a", "#6bbd4a", "#a5e06a" },
  stem      = ramp { "#24401a", "#3a6324", "#538a33", "#74ad46", "#9dcf66" },
  darkleaf  = ramp { "#132a1a", "#1f4226", "#305e36", "#457c46", "#64a05a" },
  marigold  = ramp { "#8a2e0c", "#c4500f", "#ec7a1a", "#ffa630", "#ffd36a" },
  marigoldIn= ramp { "#a83c0c", "#dc6414", "#f7922a", "#ffbc4a", "#ffe08a" },
  seedhead  = ramp { "#3a1a08", "#5a2c10", "#7e441c", "#a0622c", "#c48440" },
  bluebell  = ramp { "#1c2470", "#2c3ca8", "#4462d8", "#6e92f0", "#a8c4ff" },
  root      = ramp { "#33200f", "#55361c", "#78512c", "#9c7044", "#c09462" },
  bone      = ramp { "#6a5a48", "#9a8670", "#c4b298", "#e2d4bc", "#fff4e0" },
  sun       = ramp { "#8a4a06", "#c87a0a", "#f0a818", "#ffd040", "#fff28a" },
  sunIn     = ramp { "#c87a0a", "#f0a818", "#ffd040", "#fff28a", "#ffffff" },
  berry     = ramp { "#1a0e2a", "#2e1848", "#4a2a70", "#6e4498", "#a27ad0" },
  nsStem    = ramp { "#1c1a22", "#2e2a38", "#443c52", "#5c526c", "#786c88" },
  frost     = ramp { "#4e5a8a", "#7c88c0", "#aab4e6", "#d4dcff", "#ffffff" },
  ice       = ramp { "#2a6a8a", "#3c96b8", "#6cc4e0", "#a8ecff", "#ffffff" },
  frostStem = ramp { "#24484a", "#356a68", "#4e908a", "#74b8ae", "#a8e0d4" },
  cap       = ramp { "#4a0a0e", "#7a1218", "#ac1e22", "#d83a30", "#f2705a" },
  gills     = ramp { "#3a1a1a", "#5a2a26", "#7a3e34", "#9a5444", "#b86c56" },
  stalk     = ramp { "#7a6a58", "#a8947c", "#cdb89c", "#e8d8be", "#fff6e4" },
  void      = ramp { "#0c0814", "#1a1028", "#2a1a40", "#3e2860", "#5a3c88" },
  voidStem  = ramp { "#0e0a16", "#1c1428", "#2c2040", "#3e2e58", "#544074" },
  moss      = ramp { "#0a1030", "#14224e", "#1e3674", "#2c4e9a", "#4a72c4" },
  twine     = ramp { "#5a3a1a", "#7e5628", "#a4783c", "#c89c58", "#e8c27c" },
  dry       = ramp { "#4a3a1e", "#6e5830", "#94784a", "#b89c66", "#dcc48a" },
  nettleSeed= ramp { "#2e3a16", "#4a5a22", "#6e7e34", "#94a24c", "#bcc672" },
  blackSeed = ramp { "#140e0a", "#2a1e14", "#463222", "#664a32", "#8a6a4a" },
  pod       = ramp { "#3a4a28", "#5a6e38", "#7e9450", "#a4b870", "#cad898" },
  blueSeed  = ramp { "#0c0e1e", "#1a1e3a", "#2c3460", "#46508a", "#7080c0" },
}

-- a dried look for bundle foliage: a little greyer and warmer
local function dried(r)
  local out = {}
  for i, c in ipairs(r) do
    local g = lum(c)
    out[i] = mix(mix(c, { g, g, g }, 0.15), { 150, 110, 60 }, 0.08)
  end
  return out
end

---------------------------------------------------------------- plants

local function stemWithLeaves(r, leafR)
  stroke({ 24, 47 }, { 23, 40 }, { 24, 31 }, 1.5, 1.2, r)
  leaf(24, 42, 12, 35, 4, leafR or R.leaf)
  leaf(24, 40, 36, 33, 4, leafR or R.leaf)
end

local PLANTS = {}

PLANTS.nettle = function()
  stroke({ 23, 46 }, { 21, 26 }, { 25, 7 }, 1.6, 0.9, R.stem)
  local L = {
    { 22, 37, 7, 31, 5 }, { 23, 35, 39, 28, 5 },
    { 23, 26, 10, 19, 4.5 }, { 23, 24, 37, 16, 4.5 },
    { 24, 15, 15, 7, 3.6 }, { 24, 14, 33, 6, 3.6 },
    { 25, 11, 25, 2, 3 },
  }
  for _, l in ipairs(L) do leaf(l[1], l[2], l[3], l[4], l[5], R.leaf, { saw = 7 }) end
end

PLANTS.marigold = function()
  stemWithLeaves(R.stem)
  local cx, cy = 24, 18
  for i = 0, 11 do
    local a = i / 12 * 2 * PI + 0.13
    leaf(cx, cy, cx + math.cos(a) * 15, cy + math.sin(a) * 14, 3.8, R.marigold, { shape = "round", vein = false })
  end
  for i = 0, 7 do
    local a = i / 8 * 2 * PI + 0.4
    leaf(cx, cy, cx + math.cos(a) * 10, cy + math.sin(a) * 9.5, 3.6, R.marigoldIn, { shape = "round", vein = false })
  end
  ellipse(cx, cy, 4.2, 4.2, R.seedhead)
  set(cx - 2, cy - 2, R.seedhead[5]); set(cx - 1, cy - 2, R.seedhead[4])
end

PLANTS.bluebell = function()
  leaf(15, 46, 6, 24, 2.6, R.leaf)
  leaf(16, 46, 26, 27, 2.4, R.leaf)
  local p0, p1, p2 = { 15, 46 }, { 13, 6 }, { 38, 10 }
  stroke(p0, p1, p2, 1.3, 0.8, R.stem)
  for i, t in ipairs { 0.52, 0.74, 0.95 } do
    local x, y = bez(p0, p1, p2, t)
    local drop = ({ 3, 5, 3 })[i]
    stroke({ x, y }, { x + 1, y + drop / 2 }, { x + 1, y + drop }, 0.7, 0.7, R.stem)
    local bx, by = x + 1, y + drop
    ellipse(bx, by + 5, 3.8, 5, R.bluebell)
    ellipse(bx, by + 9.4, 5, 1.7, R.bluebell, { lift = 0.1 })
    for dx = -2, 2 do set(bx + dx, by + 10, R.bluebell[1]) end
    set(bx - 5, by + 10, R.bluebell[3]); set(bx + 4, by + 10, R.bluebell[3]); set(bx - 1, by + 11, R.bluebell[3])
    set(bx - 2, by + 2, R.bluebell[5])
  end
end

PLANTS.thornroot = function()
  leaf(24, 9, 17, 3, 3, R.leaf)
  leaf(24, 9, 31, 2, 3, R.leaf)
  local roots = {
    { { 24, 8 }, { 21, 20 }, { 24, 30 }, 3.0, 4.6 },
    { { 23, 29 }, { 14, 34 }, { 9, 44 }, 3.6, 1.0 },
    { { 25, 30 }, { 27, 38 }, { 25, 46 }, 3.4, 0.9 },
    { { 25, 29 }, { 34, 30 }, { 40, 39 }, 3.0, 0.9 },
  }
  for _, s in ipairs(roots) do stroke(s[1], s[2], s[3], s[4], s[5], R.root) end
  -- root hairs at the tips
  stroke({ 9, 44 }, { 7, 45 }, { 5, 46 }, 0.5, 0.5, R.root)
  stroke({ 40, 39 }, { 42, 40 }, { 43, 42 }, 0.5, 0.5, R.root)
  -- knots
  set(22, 17, R.root[1]); set(23, 17, R.root[1]); set(23, 18, R.root[2])
  set(25, 24, R.root[1]); set(25, 25, R.root[2])
  -- thorns on the edges of the roots
  local T = { { 1, 0.3, 1 }, { 1, 0.62, -1 }, { 1, 0.85, 1 }, { 2, 0.35, -1 }, { 2, 0.6, 1 },
              { 3, 0.5, -1 }, { 4, 0.35, -1 }, { 4, 0.7, 1 } }
  for _, t in ipairs(T) do
    local s = roots[t[1]]
    local x, y, nx, ny, tx, ty = edgeOf(s[1], s[2], s[3], s[4], s[5], t[2], t[3])
    leaf(x, y, x + nx * 5 + tx * 1.5, y + ny * 5 + ty * 1.5, 1.8, R.bone, { shape = "thorn", vein = false })
  end
end

PLANTS.sunpetal = function()
  stemWithLeaves(R.stem)
  local cx, cy = 24, 19
  for i = 0, 7 do
    local a = i / 8 * 2 * PI - PI / 2
    leaf(cx, cy, cx + math.cos(a) * 15, cy + math.sin(a) * 15, 4.4, R.sun, { vein = false })
  end
  for i = 0, 7 do
    local a = (i + 0.5) / 8 * 2 * PI - PI / 2
    leaf(cx, cy, cx + math.cos(a) * 9.5, cy + math.sin(a) * 9.5, 3.6, R.sunIn, { vein = false })
  end
  ellipse(cx, cy, 4, 4, R.sunIn, { lift = 0.15 })
  set(cx - 1, cy - 1, WHITE); set(cx - 2, cy - 1, WHITE); set(cx - 1, cy - 2, WHITE)
  sparkle(6, 6, 2, R.sun[5], WHITE)
  sparkle(42, 9, 2, R.sun[5], WHITE)
  sparkle(42, 33, 1, R.sun[5], WHITE)
  sparkle(6, 31, 1, R.sun[5], WHITE)
end

PLANTS.nightshade = function()
  stroke({ 12, 46 }, { 11, 20 }, { 30, 9 }, 1.4, 0.9, R.nsStem)
  leaf(12, 38, 2, 30, 4, R.darkleaf)
  leaf(12, 29, 3, 19, 3.6, R.darkleaf)
  leaf(22, 12, 40, 15, 3.8, R.darkleaf)
  stroke({ 19, 14 }, { 26, 17 }, { 27, 24 }, 0.8, 0.7, R.nsStem)
  local B = { { 24, 27, 4 }, { 31, 27, 4 }, { 21, 34, 3.6 }, { 33, 34, 3.6 }, { 27, 33, 4.2 }, { 27, 40, 3.4 } }
  for _, b in ipairs(B) do
    ellipse(b[1], b[2], b[3], b[3], R.berry)
    set(b[1] - 2, b[2] - 2, R.berry[5]); set(b[1] - 1, b[2] - 2, mix(R.berry[5], WHITE, 0.4))
  end
  for _, d in ipairs { { 26, 23 }, { 27, 23 }, { 28, 23 }, { 25, 24 }, { 29, 24 } } do set(d[1], d[2], R.darkleaf[3]) end
  -- flower: purple star with a yellow cone
  local fx, fy = 33, 7
  for i = 0, 4 do
    local a = i / 5 * 2 * PI - PI / 2
    leaf(fx, fy, fx + math.cos(a) * 5.5, fy + math.sin(a) * 5.5, 2.2, R.berry, { vein = false, lift = 0.15 })
  end
  ellipse(fx, fy, 1.7, 1.7, R.sun, { lift = 0.1 })
end

PLANTS.frostbloom = function()
  stemWithLeaves(R.frostStem, R.frostStem)
  set(12, 35, WHITE); set(13, 35, R.frost[4]); set(36, 33, WHITE); set(35, 33, R.frost[4])
  local cx, cy = 24, 19
  for i = 0, 5 do
    local a = i / 6 * 2 * PI - PI / 2
    leaf(cx, cy, cx + math.cos(a) * 16, cy + math.sin(a) * 15, 5.2, R.frost, { shape = "crystal", contrast = 0.26 })
  end
  for i = 0, 5 do
    local a = (i + 0.5) / 6 * 2 * PI - PI / 2
    leaf(cx, cy, cx + math.cos(a) * 10, cy + math.sin(a) * 10, 3.8, R.frost, { shape = "crystal", contrast = 0.26, lift = 0.08 })
  end
  ellipse(cx, cy, 3.4, 3.4, R.ice)
  set(cx - 1, cy - 1, WHITE)
  sparkle(6, 8, 1, R.frost[4], WHITE)
  sparkle(42, 6, 2, R.frost[4], WHITE)
  sparkle(42, 32, 1, R.frost[4], WHITE)
  set(5, 28, WHITE); set(40, 41, WHITE)
end

PLANTS.bloodcap = function()
  ellipse(24, 43, 6, 3, R.stalk)
  stroke({ 24, 43 }, { 23, 35 }, { 24, 27 }, 4.6, 3.4, R.stalk)
  ellipse(24, 27, 17, 3.4, R.gills)
  ellipse(24, 26, 19, 16, R.cap, { clip = function(x, y) return y <= 26 end })
  local onCap = function(x, y) return get(x, y) ~= nil and y < 26 end
  for _, s in ipairs { { 17, 15, 2.8, 2.1 }, { 28, 11, 3.2, 2.3 }, { 34, 19, 2.3, 1.8 }, { 11, 22, 1.9, 1.5 },
                       { 23, 20, 1.9, 1.6 }, { 38, 24, 1.5, 1.2 }, { 20, 9, 1.4, 1.1 } } do
    ellipse(s[1], s[2], s[3], s[4], R.stalk, { clip = onCap, lift = 0.1 })
  end
  -- a small one in front
  stroke({ 38, 46 }, { 38, 43 }, { 38, 40 }, 1.7, 1.3, R.stalk)
  ellipse(38, 40, 5, 1.2, R.gills)
  ellipse(38, 40, 5.6, 4.6, R.cap, { clip = function(x, y) return y <= 40 end })
  set(36, 37, R.stalk[4]); set(37, 37, R.stalk[4]); set(40, 38, R.stalk[3])
end

PLANTS.voidlily = function()
  stemWithLeaves(R.voidStem, R.void)
  local cx, cy = 24, 20
  for i = 0, 2 do
    local a = -PI / 2 + PI / 3 + i * 2 * PI / 3
    leaf(cx, cy, cx + math.cos(a) * 14, cy + math.sin(a) * 13, 5.6, R.void, { veinC = GLOW[1] })
  end
  for i = 0, 2 do
    local a = -PI / 2 + i * 2 * PI / 3
    leaf(cx, cy, cx + math.cos(a) * 16, cy + math.sin(a) * 15, 5.6, R.void, { veinC = GLOW[1], lift = 0.1 })
  end
  ellipse(cx, cy, 6, 6, R.void, { lift = -0.1 })
  spiral(cx, cy, 5.5, 2.2, GLOW[2])
  set(cx, cy, GLOW[3])
  for _, s in ipairs { { -6, -9 }, { 0, -11 }, { 6, -9 } } do
    stroke({ cx, cy - 3 }, { cx + s[1] / 2, cy + s[2] / 2 - 2 }, { cx + s[1], cy + s[2] }, 0.5, 0.5, R.void, { lift = 0.3, edge = false })
    set(cx + s[1], cy + s[2], GLOW[3])
  end
  wisp(5, 5, GLOW[2]); wisp(41, 6, GLOW[2]); wisp(41, 40, GLOW[1])
end

PLANTS.starmoss = function()
  srand(7)
  local keys = {}
  local function bump(x, y, rx, ry, first)
    for k in pairs(ellipse(x, y, rx, ry, R.moss, { edge = not first, edgeC = R.moss[2] })) do keys[k] = true end
  end
  bump(24, 37, 20, 8, true)
  bump(12, 31, 8, 7); bump(36, 30, 8, 7); bump(24, 27, 10, 8)
  bump(18, 22, 6, 5); bump(30, 22, 6, 5)
  texture(keys, R.moss)
  -- glowing sprouts
  for _, s in ipairs { { 17, 18, 15, 12 }, { 30, 18, 32, 11 }, { 24, 20, 24, 14 } } do
    stroke({ s[1], s[2] }, { (s[1] + s[3]) / 2, s[2] - 3 }, { s[3], s[4] }, 0.5, 0.5, R.moss, { lift = 0.25, edge = false })
    set(s[3], s[4], STAR2)
  end
  sparkle(15, 31, 2, STAR, STAR2)
  sparkle(31, 25, 2, STAR, STAR2)
  sparkle(27, 38, 1, STAR, STAR2)
  for _, d in ipairs { { 9, 36 }, { 21, 26 }, { 37, 34 }, { 33, 40 }, { 19, 41 }, { 41, 31 }, { 23, 32 }, { 12, 29 } } do
    set(d[1], d[2], STAR)
  end
end

---------------------------------------------------------------- bundles

-- one bundle shape for every tier: dried stems tied with twine, foliage in the tier's colour
-- accent(spots, top) gets a point on each foliage leaf and the top of the fan
local function bundle(fol, accent)
  local A, B = { 10, 42 }, { 26, 21 }
  local ax, ay = B[1] - A[1], B[2] - A[2]
  local al = math.sqrt(ax * ax + ay * ay)
  local ux, uy = ax / al, ay / al
  local nx, ny = -uy, ux
  local axis = math.atan(uy, ux)
  -- stems, fanning out from the cut ends
  for i = -3, 3 do
    local bx, by = A[1] + nx * i * 1.5, A[2] + ny * i * 1.5
    local tx, ty = B[1] + nx * i * 2.6, B[2] + ny * i * 2.6
    stroke({ bx, by }, { (bx + tx) / 2, (by + ty) / 2 }, { tx, ty }, 1.1, 0.9, R.dry)
  end
  for i = -3, 3 do set(A[1] + nx * i * 1.5 - ux, A[2] + ny * i * 1.5 - uy, R.dry[5]) end
  -- foliage: a wide fan of leaves, outer ones first, then a short inner layer on top
  local f = dried(fol)
  local spots = {}
  local function frond(i, len, w, lift)
    local sx, sy = B[1] + nx * i * 2.6 - ux * 3, B[2] + ny * i * 2.6 - uy * 3
    local a = axis + i * 0.28
    local ex, ey = sx + math.cos(a) * len, sy + math.sin(a) * len
    leaf(sx, sy, ex, ey, w, f, { shape = "round", lift = lift })
    spots[#spots + 1] = { math.floor(sx + (ex - sx) * 0.7), math.floor(sy + (ey - sy) * 0.7) }
  end
  for _, i in ipairs { -3, 3, -2, 2, -1, 1, 0 } do frond(i, 12, 3.4, 0) end
  for _, i in ipairs { -1.5, 1.5, -0.5, 0.5 } do frond(i, 8, 3, 0.08) end
  -- twine band with a knot and two loose ends
  local cx, cy = A[1] + ax * 0.4, A[2] + ay * 0.4
  local band = stroke({ cx - nx * 6.5, cy - ny * 6.5 }, { cx, cy }, { cx + nx * 6.5, cy + ny * 6.5 }, 2.4, 2.4, R.twine)
  for k, c in pairs(band) do
    local x, y = k % N, k // N
    if (x - y) % 3 == 0 and (c == R.twine[3] or c == R.twine[4] or c == R.twine[5]) then px[k] = R.twine[2] end
  end
  local kx, ky = cx + nx * 6, cy + ny * 6
  stroke({ kx, ky + 1 }, { kx - 1, ky + 4 }, { kx - 3, ky + 7 }, 0.6, 0.6, R.twine)
  stroke({ kx + 1, ky + 1 }, { kx + 3, ky + 3 }, { kx + 4, ky + 6 }, 0.6, 0.6, R.twine)
  ellipse(kx, ky, 2.2, 2.2, R.twine, { lift = 0.1 })
  if accent then accent(spots, { math.floor(B[1] + ux * 9), math.floor(B[2] + uy * 9) }) end
end

local function onFoliage(spots, fn)
  for _, s in ipairs(spots) do fn(s[1], s[2]) end
end

local BUNDLES = {
  nettle = function() bundle(R.leaf) end,
  marigold = function() bundle(R.marigold) end,
  bluebell = function() bundle(R.bluebell) end,
  thornroot = function() bundle(R.root) end,
  sunpetal = function()
    bundle(R.sun, function(spots)
      onFoliage(spots, function(x, y) set(x, y, WHITE) end)
      sparkle(42, 5, 2, R.sun[5], WHITE)
      sparkle(6, 22, 1, R.sun[5], WHITE)
    end)
  end,
  nightshade = function()
    bundle(R.berry, function(spots, top)
      for _, p in ipairs { { top[1] - 2, top[2] + 2 }, { top[1] + 2, top[2] + 3 }, { top[1], top[2] + 5 } } do
        ellipse(p[1], p[2], 1.8, 1.8, R.berry, { lift = 0.15 })
        set(p[1] - 1, p[2] - 1, R.berry[5])
      end
    end)
  end,
  frostbloom = function()
    bundle(R.frost, function(spots)
      onFoliage(spots, function(x, y) set(x, y, WHITE) end)
      sparkle(42, 5, 2, R.frost[4], WHITE)
    end)
  end,
  bloodcap = function()
    bundle(R.cap, function(spots)
      onFoliage(spots, function(x, y) set(x, y, R.stalk[4]); set(x + 1, y, R.stalk[3]) end)
    end)
  end,
  voidlily = function()
    bundle(R.void, function(spots, top)
      spiral(top[1], top[2] + 2, 3.5, 1.6, GLOW[2])
      wisp(41, 4, GLOW[2]); wisp(6, 20, GLOW[1])
    end)
  end,
  starmoss = function()
    bundle(R.moss, function(spots, top)
      onFoliage(spots, function(x, y) set(x, y, STAR) end)
      sparkle(top[1], top[2] + 2, 1, STAR, STAR2)
    end)
  end,
}

---------------------------------------------------------------- seeds

-- a glossy glint at the top left of a seed
local function glint(x, y, c)
  set(x, y, c); set(x + 1, y, c); set(x, y + 1, mix(c, WHITE, 0.3))
end

local SEEDS = {}

SEEDS.nettle = function()
  for _, s in ipairs { { 12, 36, 20, 16, 5 }, { 33, 38, 37, 18, 5 }, { 22, 43, 27, 21, 5.5 } } do
    leaf(s[1], s[2], s[3], s[4], s[5], R.nettleSeed, { shape = "drop", vein = false })
  end
  glint(15, 31, R.nettleSeed[5]); glint(34, 32, R.nettleSeed[5]); glint(23, 36, R.nettleSeed[5])
end

SEEDS.marigold = function()
  for _, s in ipairs { { 18, 43, 9, 11 }, { 30, 43, 39, 12 }, { 24, 44, 24, 6 } } do
    leaf(s[1], s[2], s[3], s[4], 2.6, R.blackSeed, { shape = "oval", vein = false, contrast = 0.25 })
    local tx, ty = s[1] + (s[3] - s[1]) * 0.78, s[2] + (s[4] - s[2]) * 0.78
    leaf(tx, ty, s[3], s[4], 2.2, R.bone, { shape = "oval", vein = false })
  end
end

SEEDS.bluebell = function()
  stroke({ 24, 12 }, { 24, 8 }, { 26, 4 }, 1, 0.7, R.stem)
  ellipse(24, 26, 11, 14, R.pod)
  ellipse(24, 27, 6, 10, R.blueSeed, { lift = -0.3 })
  for _, s in ipairs { { 24, 20 }, { 22, 25 }, { 26, 29 }, { 23, 33 } } do
    ellipse(s[1], s[2], 2.6, 2.6, R.blueSeed, { lift = 0.15 })
    set(s[1] - 1, s[2] - 1, R.blueSeed[5])
  end
  for _, s in ipairs { { 37, 42 }, { 43, 35 } } do
    ellipse(s[1], s[2], 2.6, 2.6, R.blueSeed, { lift = 0.15 })
    set(s[1] - 1, s[2] - 1, R.blueSeed[5])
  end
end

SEEDS.thornroot = function()
  local cx, cy = 24, 25
  for i = 0, 13 do
    local a = i / 14 * 2 * PI + 0.2
    leaf(cx + math.cos(a) * 8, cy + math.sin(a) * 8, cx + math.cos(a) * 18, cy + math.sin(a) * 18, 2, R.bone,
      { shape = "thorn", vein = false })
  end
  ellipse(cx, cy, 11, 11, R.root)
  srand(3)
  for _ = 1, 14 do
    local a, d = rnd() * 2 * PI, rnd() * 8
    set(cx + math.cos(a) * d, cy + math.sin(a) * d, R.root[1])
  end
  glint(cx - 5, cy - 6, R.root[5])
end

SEEDS.sunpetal = function()
  local x0, y0, x1, y1 = 15, 41, 31, 7
  leaf(x0, y0, x1, y1, 9, R.sun, { shape = "drop", vein = false })
  local dx, dy = x1 - x0, y1 - y0
  local l = math.sqrt(dx * dx + dy * dy)
  local nx, ny = -dy / l, dx / l
  for _, o in ipairs { -4.5, 0, 4.5 } do
    stroke({ x0 + nx * o * 0.5 + dx * 0.12, y0 + ny * o * 0.5 + dy * 0.12 },
           { x0 + nx * o + dx * 0.4, y0 + ny * o + dy * 0.4 },
           { x0 + nx * o * 0.4 + dx * 0.85, y0 + ny * o * 0.4 + dy * 0.85 }, 0.6, 0.5, R.sun, { lift = -0.35, edge = false })
  end
  glint(17, 28, WHITE)
  sparkle(40, 10, 2, R.sun[5], WHITE)
  sparkle(8, 12, 1, R.sun[5], WHITE)
  sparkle(39, 37, 1, R.sun[5], WHITE)
end

SEEDS.nightshade = function()
  leaf(14, 38, 24, 12, 7.5, R.berry, { shape = "oval", vein = false, contrast = 0.25 })
  leaf(25, 42, 37, 18, 7, R.berry, { shape = "oval", vein = false, contrast = 0.25 })
  glint(16, 20, mix(R.berry[5], WHITE, 0.3)); glint(28, 26, mix(R.berry[5], WHITE, 0.3))
end

SEEDS.frostbloom = function()
  leaf(24, 4, 24, 44, 11, R.frost, { shape = "crystal", contrast = 0.3 })
  leaf(24, 13, 24, 36, 4.5, R.ice, { shape = "crystal", contrast = 0.3, edge = false })
  sparkle(8, 10, 2, R.frost[4], WHITE)
  sparkle(40, 32, 2, R.frost[4], WHITE)
  set(39, 9, WHITE); set(9, 38, WHITE)
end

SEEDS.bloodcap = function()
  for _, s in ipairs { { 24, 17, 6 }, { 15, 31, 7.5 }, { 32, 33, 8 } } do
    ellipse(s[1], s[2], s[3], s[3], R.cap)
    glint(s[1] - math.floor(s[3] / 2), s[2] - math.floor(s[3] / 2), R.cap[5])
  end
  for _, d in ipairs { { 26, 15 }, { 22, 19 }, { 13, 33 }, { 18, 29 }, { 30, 36 }, { 35, 30 }, { 34, 38 } } do
    set(d[1], d[2], R.stalk[4])
  end
  for _, d in ipairs { { 8, 12 }, { 38, 14 }, { 41, 22 }, { 10, 21 }, { 6, 42 } } do set(d[1], d[2], R.cap[4]) end
end

SEEDS.voidlily = function()
  leaf(16, 41, 32, 7, 10, R.void, { shape = "oval", vein = false })
  spiral(24, 24, 7, 2.2, GLOW[2])
  set(24, 24, GLOW[3])
  glint(18, 18, GLOW[1])
  wisp(6, 6, GLOW[2]); wisp(40, 8, GLOW[2]); wisp(39, 39, GLOW[1])
end

SEEDS.starmoss = function()
  local keys = ellipse(24, 25, 14, 14, R.moss)
  srand(11)
  texture(keys, R.moss)
  sparkle(19, 21, 2, STAR, STAR2)
  sparkle(30, 31, 2, STAR, STAR2)
  for _, d in ipairs { { 28, 18 }, { 16, 30 }, { 24, 35 }, { 33, 23 }, { 21, 28 } } do set(d[1], d[2], STAR) end
  sparkle(6, 8, 1, STAR, STAR2); sparkle(42, 42, 1, STAR, STAR2); set(42, 10, STAR)
end

---------------------------------------------------------------- output

local ORDER = { "nettle", "marigold", "bluebell", "thornroot", "sunpetal",
                "nightshade", "frostbloom", "bloodcap", "voidlily", "starmoss" }

local made = {}
for _, id in ipairs(ORDER) do
  made[#made + 1] = {
    K.render(PLANTS[id], OUT .. "/plant_" .. id .. ".png"),
    K.render(BUNDLES[id], OUT .. "/bundle_" .. id .. ".png"),
    K.render(SEEDS[id], OUT .. "/seed_" .. id .. ".png"),
  }
end
if PREVIEW then K.sheet(made, PREVIEW) end
