-- Draws the lumbering and fishing inventory icons (D-104, D-107, D-108, D-111):
-- log_, plank_ and sap_<tree>.png, and fish_, cooked_ and pearl_<fish>.png per tier,
-- 48x48 pixel art in the style of the other item icons (dark outline, lit from the top left).
-- Run from the repo root:
--   aseprite -b --script-param out=sprites/items --script sprites/build_lumber_fishing_icons.lua
-- Add --script-param preview=<file.png> to also write a 4x contact sheet.

local OUT = app.params.out or "sprites/items"
local PREVIEW = app.params.preview
local K = dofile((debug.getinfo(1, "S").source:match("^@(.*[/\\])") or "") .. "pixel_icons.lua")
local N, WHITE, INK, px = K.N, K.WHITE, K.INK, K.px
local hex, ramp, mix, pick = K.hex, K.ramp, K.mix, K.pick
local get, set, ellipse, leaf, stroke = K.get, K.set, K.ellipse, K.leaf, K.stroke
local sparkle, spiral, srand, rnd, texture = K.sparkle, K.spiral, K.srand, K.rnd, K.texture

---------------------------------------------------------------- colours

local STAR, STAR2 = hex("#ffd84a"), hex("#fff6b0")
local GLOW = { hex("#4a2a8a"), hex("#7a48c8"), hex("#b088f4") }
local STEAM = hex("#d8dce4")

-- shared tier colours (tiers 5-10 match the mining tiers, as foraging does)
local T = {
  gold   = ramp { "#6a4a10", "#9a6e18", "#c89a2a", "#ecc448", "#fff08a" },
  ebony  = ramp { "#120c18", "#22182e", "#342446", "#4a3460", "#62487c" },
  lilac  = ramp { "#5e5a7a", "#8a84ac", "#b4aed4", "#d8d2f0", "#f4f0ff" },
  blood  = ramp { "#3e0a0c", "#6a1216", "#962022", "#c03430", "#e05c4c" },
  void   = ramp { "#0c0814", "#1a1028", "#2a1a40", "#3e2860", "#5a3c88" },
  star   = ramp { "#0a1030", "#14224e", "#1e3674", "#2c4e9a", "#4a72c4" },
}

local TREES = {
  { id = "ash",        bark = ramp { "#4a443c", "#6a6258", "#8c8478", "#aea696", "#d0c8b6" },
                       wood = ramp { "#8a7454", "#b09670", "#cfb68a", "#e6d2a6", "#f6e8c4" },
                       sap  = ramp { "#7a5a1a", "#a87c22", "#d4a636", "#f0cc5a", "#fff0a0" } },
  { id = "birch",      bark = ramp { "#6e6a64", "#a8a49c", "#d4d0c6", "#ece8de", "#ffffff" },
                       wood = ramp { "#8c7a4a", "#b49e62", "#d2bc7c", "#e8d498", "#f8ecbc" },
                       sap  = ramp { "#4a6e6e", "#6e9896", "#98c0bc", "#c4e4de", "#f0fffc" } },
  { id = "oak",        bark = ramp { "#3a2614", "#5a3c20", "#7a5430", "#9c7044", "#bc8e5c" },
                       wood = ramp { "#6e4a26", "#94683a", "#b88a52", "#d4a86c", "#ecc88e" },
                       sap  = ramp { "#5a2e08", "#8a4a10", "#b8701c", "#dc9a34", "#f4c460" } },
  { id = "pine",       bark = ramp { "#3a1e12", "#5c3020", "#7e4630", "#a05e40", "#c07a56" },
                       wood = ramp { "#8a6a3a", "#ae8a50", "#cca66a", "#e2c286", "#f4dca6" },
                       sap  = ramp { "#7a3a06", "#ac5a0e", "#d8821a", "#f4aa34", "#ffd470" } },
  { id = "goldleaf",   bark = T.gold,
                       wood = ramp { "#a07a2a", "#c89e3e", "#e6c25e", "#f8de88", "#fff4c0" },
                       sap  = T.gold },
  { id = "ebony",      bark = T.ebony,
                       wood = ramp { "#1e1424", "#2e2038", "#42304e", "#584268", "#705884" },
                       sap  = ramp { "#2a1430", "#46224e", "#663872", "#8a5498", "#b07cc0" } },
  { id = "silverbark", bark = T.lilac,
                       wood = ramp { "#7a7090", "#a49cbc", "#c8c0dc", "#e2dcf2", "#f8f4ff" },
                       sap  = T.lilac },
  { id = "bloodwood",  bark = T.blood,
                       wood = ramp { "#5a1416", "#86221e", "#ae3a2c", "#d05a42", "#ec8462" },
                       sap  = T.blood },
  { id = "voidwood",   bark = T.void,
                       wood = ramp { "#1a1030", "#2a1a48", "#3e2a66", "#584088", "#7a5cac" },
                       sap  = T.void },
  { id = "starwood",   bark = T.star,
                       wood = ramp { "#14224e", "#1e3674", "#2c4e9a", "#4a72c4", "#7a9ce0" },
                       sap  = T.star },
}

-- len and w shape the body; long fish are thinner
local FISH = {
  { id = "minnow",           body = ramp { "#3e4a52", "#5e6e78", "#84969e", "#aebec4", "#dae6ea" }, len = 28, w = 7.5,
    pearl = "river",  pearlC = ramp { "#7a7468", "#a8a294", "#cec8ba", "#ece6da", "#ffffff" } },
  { id = "perch",            body = ramp { "#3a4a14", "#5a6e1e", "#80962e", "#a8bc4a", "#d2e07a" }, len = 32, w = 9,
    pearl = "sand",   pearlC = ramp { "#7a6440", "#a48a5c", "#c8ae7c", "#e4cc9e", "#fcecc8" } },
  { id = "trout",            body = ramp { "#4a4a3a", "#6e6c52", "#94906e", "#bab48e", "#e0dab4" }, len = 34, w = 8.5,
    pearl = "moss",   pearlC = ramp { "#2e4a2a", "#4a6e40", "#6e945a", "#96ba7c", "#c4e0a6" } },
  { id = "catfish",          body = ramp { "#1e1a18", "#34302a", "#4e4840", "#6a6458", "#8a8474" }, len = 34, w = 9.5,
    pearl = "black",  pearlC = ramp { "#0e0e14", "#1e1e2a", "#30303f", "#484858", "#6a6a7e" } },
  { id = "goldfin_carp",     body = T.gold,  len = 34, w = 10,
    pearl = "golden", pearlC = T.gold },
  { id = "shadow_eel",       body = ramp { "#1a0e2a", "#2e1848", "#4a2a70", "#6e4498", "#a27ad0" }, len = 40, w = 5.5,
    pearl = "shadow", pearlC = ramp { "#1a0e2a", "#2e1848", "#4a2a70", "#6e4498", "#a27ad0" } },
  { id = "frostscale_pike",  body = ramp { "#4e5a8a", "#7c88c0", "#aab4e6", "#d4dcff", "#ffffff" }, len = 40, w = 6.5,
    pearl = "frost",  pearlC = ramp { "#4e5a8a", "#7c88c0", "#aab4e6", "#d4dcff", "#ffffff" } },
  { id = "bloodfin_snapper", body = T.blood, len = 34, w = 10,
    pearl = "blood",  pearlC = T.blood },
  { id = "void_angler",      body = T.void,  len = 32, w = 10.5,
    pearl = "void",   pearlC = T.void },
  { id = "starfin_koi",      body = T.star,  len = 36, w = 9.5,
    pearl = "star",   pearlC = T.star },
}

local SHELL = ramp { "#6a4a4e", "#9a7276", "#c49ea0", "#e6c8c6", "#fff0ec" }

---------------------------------------------------------------- helpers

-- the rarity marks the higher tiers carry, the same set foraging uses
local function mark(tier, x, y)
  if tier == 5 then
    sparkle(x, y, 2, STAR, WHITE)
  elseif tier == 6 then
    set(x, y, GLOW[3]); set(x + 1, y, GLOW[2]); set(x, y + 1, GLOW[2])
  elseif tier == 7 then
    sparkle(x, y, 2, hex("#d4dcff"), WHITE)
  elseif tier == 8 then
    for _, d in ipairs { { 0, 0 }, { 3, 2 }, { -2, 3 } } do set(x + d[1], y + d[2], hex("#ffd0b8")) end
  elseif tier == 9 then
    spiral(x, y, 4, 1.8, GLOW[2]); set(x, y, GLOW[3])
  elseif tier == 10 then
    sparkle(x, y, 2, STAR, STAR2)
    set(x + 5, y + 3, STAR); set(x - 4, y + 4, STAR)
  end
end

-- a plank: a lit top edge, a dark bottom edge, end grain on the left, wood grain lines
local function plank(x0, y0, x1, y1, r)
  for y = y0, y1 do
    for x = x0, x1 do
      local t = 0.66 - (y - y0) / (y1 - y0) * 0.36
      if y == y0 then t = 0.9 elseif y == y1 then t = 0.12 end
      if x == x1 then t = t - 0.15 end
      set(x, y, pick(r, t))
    end
  end
  for y = y0 + 1, y1 - 1 do set(x0, y, r[5]); set(x0 + 1, y, r[4]) end
  set(x0 + 1, math.floor((y0 + y1) / 2), r[2])
  for _ = 1, 4 do
    local y = y0 + 2 + math.floor(rnd() * (y1 - y0 - 3))
    local a = x0 + 4 + math.floor(rnd() * 12)
    local b = math.min(x1 - 2, a + 6 + math.floor(rnd() * 14))
    for x = a, b do set(x, y, r[2]) end
  end
end

-- ring pixels on an ellipse (end grain)
local function ring(cx, cy, rx, ry, c)
  for i = 0, 63 do
    local a = i / 64 * 2 * math.pi
    set(cx + math.cos(a) * rx, cy + math.sin(a) * ry, c)
  end
end

-- a little darker and browner, for cooked fish
local function cooked(r)
  local out = {}
  for i, c in ipairs(r) do out[i] = mix(mix(c, { 150, 92, 40 }, 0.32), { 40, 20, 10 }, 0.12) end
  return out
end

---------------------------------------------------------------- lumbering

local function drawLog(i, tr)
  local keys = stroke({ 15, 33 }, { 26, 23 }, { 38, 12 }, 8, 7.5, tr.bark)
  srand(100 + i)
  texture(keys, tr.bark, 0.22, 0.22)
  if tr.id == "birch" then
    for _, d in ipairs { { 24, 18 }, { 29, 21 }, { 33, 13 }, { 22, 27 }, { 36, 18 } } do
      for k = 0, 2 do set(d[1] + k, d[2] - k, INK) end
    end
  end
  -- a short branch stub on the top edge
  stroke({ 27, 16 }, { 28, 12 }, { 30, 9 }, 2.2, 1.6, tr.bark)
  -- end grain facing the viewer
  ellipse(13, 34, 7.5, 8.5, tr.wood, { lift = 0.1 })
  ring(13, 34, 5.2, 6.0, tr.wood[2])
  ring(13, 34, 2.8, 3.4, tr.wood[2])
  set(13, 34, tr.wood[1])
  mark(i, 30, 22)
end

local function drawPlanks(i, tr)
  srand(200 + i)
  plank(11, 12, 42, 20, tr.wood)
  plank(5, 24, 37, 32, tr.wood)
  mark(i, 26, 28)
end

-- a glossy drop of sap, resin or amber, tip up
local function drawSap(i, tr)
  leaf(24, 26, 24, 4, 7, tr.sap, { shape = "thorn", vein = false, contrast = 0.1 })
  ellipse(24, 31, 12, 12, tr.sap, { edge = false })
  ellipse(22, 29, 6, 6, tr.sap, { lift = 0.22, edge = false })
  set(18, 25, WHITE); set(19, 24, WHITE); set(18, 26, WHITE); set(20, 23, mix(tr.sap[5], WHITE, 0.5))
  set(29, 37, tr.sap[5]); set(30, 36, tr.sap[5])
  mark(i, 27, 33)
end

---------------------------------------------------------------- fishing

local function drawFish(i, f, r, isCooked)
  local x1 = 6 + f.len
  local x0 = x1 - f.len
  local cy = 25
  -- tail and fins go first, so the body overlaps them
  leaf(x0 + 4, cy, x0 - 4, cy - 9, 3.6, r, { shape = "leaf", contrast = 0.25 })
  leaf(x0 + 4, cy, x0 - 4, cy + 9, 3.6, r, { shape = "leaf", contrast = 0.25 })
  leaf(x0 + f.len * 0.38, cy - f.w + 2, x0 + f.len * 0.66, cy - f.w - 3, 3, r, { shape = "thorn", vein = false })
  local body = leaf(x0 + 2, cy + 1, x1, cy - 1, f.w, r, { shape = "almond", vein = false, contrast = 0.24 })
  srand(300 + i)
  texture(body, r, 0.12, 0.12)
  -- gill line, eye and mouth
  local gx = x1 - math.floor(f.len * 0.26)
  for y = cy - math.floor(f.w * 0.6), cy + math.floor(f.w * 0.5) do
    if get(gx, y) then set(gx, y, r[2]) end
  end
  local ex = x1 - math.floor(f.len * 0.13)
  set(ex, cy - 3, INK); set(ex + 1, cy - 3, INK); set(ex, cy - 2, INK); set(ex + 1, cy - 2, INK)
  set(ex, cy - 3, isCooked and r[4] or WHITE)
  set(x1 - 1, cy, r[1])
  -- per-fish details
  if f.id == "perch" then
    for k = 0, 3 do
      local bx = x0 + 9 + k * 5
      for y = cy - 6, cy + 4 do if get(bx, y) then set(bx, y, r[2]) end end
    end
  elseif f.id == "trout" then
    for x = x0 + 6, x1 - 8 do if get(x, cy) then set(x, cy, hex(isCooked and "#b0705a" or "#d07a8a")) end end
    for _, d in ipairs { { 12, -4 }, { 17, -5 }, { 22, -3 }, { 15, 3 } } do set(x0 + d[1], cy + d[2], r[1]) end
  elseif f.id == "catfish" then
    stroke({ x1, cy + 1 }, { x1 + 3, cy + 4 }, { x1 + 2, cy + 8 }, 0.7, 0.5, r)
    stroke({ x1 - 1, cy + 2 }, { x1, cy + 6 }, { x1 - 3, cy + 9 }, 0.7, 0.5, r)
  elseif f.id == "void_angler" then
    stroke({ x1 - 6, cy - f.w + 1 }, { x1 + 2, cy - f.w - 7 }, { x1 + 4, cy - f.w - 2 }, 0.7, 0.6, r)
    ellipse(x1 + 4, cy - f.w - 1, 2, 2, ramp { "#4a2a8a", "#7a48c8", "#b088f4", "#e0c8ff", "#ffffff" }, { lift = 0.3 })
  elseif f.id == "starfin_koi" then
    for _, d in ipairs { { 10, -3 }, { 18, 2 }, { 24, -4 } } do
      ellipse(x0 + d[1], cy + d[2], 2.2, 1.8, ramp { "#a8b4d8", "#c8d2ee", "#e4eaff", "#f4f6ff", "#ffffff" }, { edge = false })
    end
  end
  mark(i, x0 + math.floor(f.len * 0.45), cy + 1)
  if isCooked then
    -- grill marks across the body, and steam
    for k in pairs(body) do
      local x, y = k % N, k // N
      if (x + y) % 8 == 0 and x > x0 + 4 and x < x1 - 4 then px[k] = mix(r[1], INK, 0.3) end
    end
    for _, sx in ipairs { 17, 25 } do
      for k = 0, 7 do set(sx + ({ 0, 1, 1, 0, -1, -1, 0, 1 })[k + 1], 9 - k, STEAM) end
    end
  end
end

local function drawPearl(i, f)
  -- an open shell with the pearl sitting in it
  ellipse(24, 33, 19, 10, SHELL, { clip = function(_, y) return y >= 30 end })
  for _, x in ipairs { 12, 18, 24, 30, 36 } do
    for y = 35, 40 do if get(x, y) then set(x, y, SHELL[2]) end end
  end
  ellipse(24, 24, 11, 11, f.pearlC, { lift = 0.08 })
  set(19, 18, WHITE); set(20, 18, WHITE); set(19, 19, WHITE); set(18, 20, mix(f.pearlC[5], WHITE, 0.5))
  set(29, 29, f.pearlC[5])
  if f.pearl == "black" then
    set(27, 20, hex("#7a5ab8")); set(28, 21, hex("#4ab0a0")); set(21, 28, hex("#7a5ab8"))
  end
  mark(i, 27, 23)
end

---------------------------------------------------------------- output

local made = {}
for i, tr in ipairs(TREES) do
  made[#made + 1] = {
    K.render(function() drawLog(i, tr) end, OUT .. "/log_" .. tr.id .. ".png"),
    K.render(function() drawPlanks(i, tr) end, OUT .. "/plank_" .. tr.id .. ".png"),
    K.render(function() drawSap(i, tr) end, OUT .. "/sap_" .. tr.id .. ".png"),
  }
end
for i, f in ipairs(FISH) do
  local row = made[i]
  row[#row + 1] = K.render(function() drawFish(i, f, f.body, false) end, OUT .. "/fish_" .. f.id .. ".png")
  row[#row + 1] = K.render(function() drawFish(i, f, cooked(f.body), true) end, OUT .. "/cooked_" .. f.id .. ".png")
  row[#row + 1] = K.render(function() drawPearl(i, f) end, OUT .. "/pearl_" .. f.pearl .. ".png")
end
if PREVIEW then K.sheet(made, PREVIEW) end
