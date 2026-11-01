-- Shared pixel-art helpers for the 48x48 inventory icon scripts (build_*_icons.lua).
-- Shapes are shaded from a 5-colour ramp, lit from the top left; where a new shape meets
-- an earlier one it gets a dark edge, and outline() adds the outer outline.

local N = 48
local PI = math.pi

local function hex(h)
  h = h:gsub("#", "")
  return { tonumber(h:sub(1, 2), 16), tonumber(h:sub(3, 4), 16), tonumber(h:sub(5, 6), 16) }
end
local function ramp(t)
  local r = {}
  for i, h in ipairs(t) do r[i] = hex(h) end
  return r
end
local function mix(a, b, k)
  return { a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k, a[3] + (b[3] - a[3]) * k }
end
local function lum(c) return c[1] * 0.3 + c[2] * 0.59 + c[3] * 0.11 end
local function clamp(v, a, b) if v < a then return a elseif v > b then return b end return v end

local INK = hex("#120a18")
local WHITE = hex("#ffffff")

local LX, LY = -0.6, -0.8 -- light from the top left
local px = {}

local function key(x, y) return y * N + x end
local function inb(x, y) return x >= 0 and y >= 0 and x < N and y < N end
local function get(x, y) if inb(x, y) then return px[key(x, y)] end end
local function set(x, y, c)
  x, y = math.floor(x), math.floor(y)
  if inb(x, y) then px[key(x, y)] = c end
end
local function pick(r, t) return r[clamp(math.floor(t * #r) + 1, 1, #r)] end
local function gy(y) return (24 - y) / 48 * 0.16 end

-- writes a shape's pixels; where it meets something already drawn, its border gets a dark line
local function commit(m, r, o)
  local out = {}
  for k, c in pairs(m) do
    local x, y = k % N, k // N
    if o.edge ~= false then
      for _, d in ipairs { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } } do
        local nx, ny = x + d[1], y + d[2]
        if inb(nx, ny) and not m[key(nx, ny)] and px[key(nx, ny)] then
          c = o.edgeC or mix(r[1], INK, 0.45)
          break
        end
      end
    end
    out[k] = c
  end
  for k, c in pairs(out) do px[k] = c end
  return out
end

local function ellipse(cx, cy, rx, ry, r, o)
  o = o or {}
  local m = {}
  for y = math.floor(cy - ry - 1), math.ceil(cy + ry + 1) do
    for x = math.floor(cx - rx - 1), math.ceil(cx + rx + 1) do
      local nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
      local d2 = nx * nx + ny * ny
      if inb(x, y) and d2 <= 1 and (not o.clip or o.clip(x, y)) then
        local t = 0.5 + 0.42 * (nx * LX + ny * LY) + gy(y) + (o.lift or 0)
        if d2 > 0.72 then t = t - 0.12 end
        m[key(x, y)] = pick(r, t)
      end
    end
  end
  return commit(m, r, o)
end

-- a leaf, petal or thorn from base (x0,y0) to tip (x1,y1), w = half width at its widest
local PROFILE = {
  leaf    = function(u) return math.sin(PI * u ^ 0.7) end,
  round   = function(u) return math.sin(PI * u ^ 1.4) ^ 0.6 end,
  crystal = function(u) return u < 0.35 and u / 0.35 or (1 - u) / 0.65 end,
  thorn   = function(u) return 1 - u end,
  oval    = function(u) return math.sqrt(math.max(0, 1 - (2 * u - 1) ^ 2)) end,
  drop    = function(u) return math.sin(PI * u ^ 0.55) end,
  almond  = function(u) return math.sin(PI * u) end,
}
local function leaf(x0, y0, x1, y1, w, r, o)
  o = o or {}
  local dx, dy = x1 - x0, y1 - y0
  local len = math.sqrt(dx * dx + dy * dy)
  local ux, uy = dx / len, dy / len
  local nx, ny = -uy, ux
  local lit = (nx * LX + ny * LY) >= 0 and 1 or -1
  local prof = PROFILE[o.shape or "leaf"]
  local m = {}
  for y = math.floor(math.min(y0, y1) - w - 1), math.ceil(math.max(y0, y1) + w + 1) do
    for x = math.floor(math.min(x0, x1) - w - 1), math.ceil(math.max(x0, x1) + w + 1) do
      local qx, qy = x + 0.5 - x0, y + 0.5 - y0
      local u = (qx * ux + qy * uy) / len
      local v = qx * nx + qy * ny
      if inb(x, y) and u >= 0 and u <= 1 then
        local hw = w * prof(u)
        if o.saw then hw = hw * (0.78 + 0.22 * ((u * o.saw) % 1)) end
        if hw > 0.35 and math.abs(v) <= hw then
          local side = (v * lit >= 0) and 1 or -1
          local t = 0.52 + (o.contrast or 0.2) * side + gy(y) + (o.lift or 0)
          if math.abs(v) > hw - 1 then t = t - 0.14 end
          local c = pick(r, t)
          if o.vein ~= false and math.abs(v) < 0.55 and u > 0.08 and u < 0.85 then
            c = o.veinC or pick(r, side > 0 and 0.42 or 0.18)
          end
          m[key(x, y)] = c
        end
      end
    end
  end
  return commit(m, r, o)
end

-- a tapered stroke along a quadratic curve p0 -> p2 bent towards p1, radius r0 -> r1
local function bez(p0, p1, p2, t)
  local a, b, c = (1 - t) ^ 2, 2 * (1 - t) * t, t * t
  return a * p0[1] + b * p1[1] + c * p2[1], a * p0[2] + b * p1[2] + c * p2[2]
end
local function stroke(p0, p1, p2, r0, r1, r, o)
  o = o or {}
  local S, x0, y0, x1, y1 = {}, 99, 99, -99, -99
  for i = 0, 48 do
    local t = i / 48
    local x, y = bez(p0, p1, p2, t)
    local rr = r0 + (r1 - r0) * t
    S[#S + 1] = { x, y, rr }
    x0, y0 = math.min(x0, x - rr), math.min(y0, y - rr)
    x1, y1 = math.max(x1, x + rr), math.max(y1, y + rr)
  end
  local m = {}
  for y = math.floor(y0) - 1, math.ceil(y1) + 1 do
    for x = math.floor(x0) - 1, math.ceil(x1) + 1 do
      local best, bs = 1e9, nil
      for _, s in ipairs(S) do
        local d = math.sqrt((x + 0.5 - s[1]) ^ 2 + (y + 0.5 - s[2]) ^ 2) - s[3]
        if d < best then best, bs = d, s end
      end
      if inb(x, y) and best <= 0 then
        local ox, oy = (x + 0.5 - bs[1]) / bs[3], (y + 0.5 - bs[2]) / bs[3]
        local t = 0.5 + 0.42 * (ox * LX + oy * LY) + gy(y) + (o.lift or 0)
        if bs[3] > 1.6 and best > -0.9 then t = t - 0.12 end
        m[key(x, y)] = pick(r, t)
      end
    end
  end
  return commit(m, r, o)
end

-- point and outward normal on a stroke's edge, for thorns
local function edgeOf(p0, p1, p2, r0, r1, t, side)
  local x, y = bez(p0, p1, p2, t)
  local tx = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])
  local ty = 2 * (1 - t) * (p1[2] - p0[2]) + 2 * t * (p2[2] - p1[2])
  local l = math.sqrt(tx * tx + ty * ty)
  local nx, ny = -ty / l * side, tx / l * side
  local rr = (r0 + (r1 - r0) * t) * 0.7
  return x + nx * rr, y + ny * rr, nx, ny, tx / l, ty / l
end

local function sparkle(x, y, s, c, core)
  for i = 1, s do
    set(x + i, y, c); set(x - i, y, c); set(x, y + i, c); set(x, y - i, c)
  end
  set(x, y, core or c)
end

local function spiral(cx, cy, rmax, turns, c, a0)
  for i = 0, 400 do
    local t = i / 400
    local a = t * turns * 2 * PI + (a0 or 0)
    set(cx + math.cos(a) * rmax * t, cy + math.sin(a) * rmax * t, c)
  end
end

-- small curl, like the wisps around the void ore
local function wisp(x, y, c)
  set(x, y, c); set(x + 1, y, c); set(x + 2, y + 1, c); set(x + 2, y + 2, c)
  set(x + 1, y + 3, c); set(x, y + 3, c); set(x - 1, y + 2, c); set(x, y + 1, c)
end

local seed = 1
local function srand(n) seed = n end
local function rnd()
  seed = (seed * 1103515245 + 12345) % 2147483648
  return seed / 2147483648
end

local function outline()
  local add = {}
  for y = 0, N - 1 do
    for x = 0, N - 1 do
      if not px[key(x, y)] then
        local best
        for _, d in ipairs { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } } do
          local c = get(x + d[1], y + d[2])
          if c and (not best or lum(c) < lum(best)) then best = c end
        end
        if best then add[key(x, y)] = mix(best, INK, 0.78) end
      end
    end
  end
  for k, c in pairs(add) do px[k] = c end
end

-- roughens a shape: some pixels a shade lighter or darker (fur, moss)
local function texture(keys, r, up, down)
  for k in pairs(keys) do
    local c = px[k]
    for i, rc in ipairs(r) do
      if c == rc then
        local v = rnd()
        if v < (up or 0.2) then px[k] = r[math.min(i + 1, #r)]
        elseif v < (up or 0.2) + (down or 0.1) then px[k] = r[math.max(i - 1, 1)] end
        break
      end
    end
  end
end

local function toImage()
  local img = Image(N, N, ColorMode.RGB)
  for k, c in pairs(px) do
    img:drawPixel(k % N, k // N, app.pixelColor.rgba(
      clamp(math.floor(c[1] + 0.5), 0, 255), clamp(math.floor(c[2] + 0.5), 0, 255),
      clamp(math.floor(c[3] + 0.5), 0, 255), 255))
  end
  return img
end

-- draws one icon with fn on a clear canvas, outlines it and saves it as path
local function render(fn, path)
  for k in pairs(px) do px[k] = nil end
  fn()
  outline()
  local img = toImage()
  img:saveAs(path)
  return img
end

-- saves a 4x contact sheet of rows of icons on a grey background
local function sheet(rows, path)
  local S, PAD = 4, 8
  local cell = N * S + PAD
  local cols = 0
  for _, row in ipairs(rows) do cols = math.max(cols, #row) end
  local img = Image(cols * cell + PAD, #rows * cell + PAD, ColorMode.RGB)
  local bg = app.pixelColor.rgba(181, 181, 181, 255)
  for y = 0, img.height - 1 do for x = 0, img.width - 1 do img:drawPixel(x, y, bg) end end
  for r, row in ipairs(rows) do
    for c, icon in ipairs(row) do
      local ox, oy = PAD + (c - 1) * cell, PAD + (r - 1) * cell
      for y = 0, N - 1 do
        for x = 0, N - 1 do
          local p = icon:getPixel(x, y)
          if app.pixelColor.rgbaA(p) > 0 then
            for dy = 0, S - 1 do for dx = 0, S - 1 do img:drawPixel(ox + x * S + dx, oy + y * S + dy, p) end end
          end
        end
      end
    end
  end
  img:saveAs(path)
end

return {
  N = N, PI = PI, INK = INK, WHITE = WHITE, px = px,
  hex = hex, ramp = ramp, mix = mix, lum = lum, clamp = clamp,
  key = key, inb = inb, get = get, set = set, pick = pick,
  ellipse = ellipse, leaf = leaf, bez = bez, stroke = stroke, edgeOf = edgeOf,
  sparkle = sparkle, spiral = spiral, wisp = wisp, srand = srand, rnd = rnd,
  texture = texture, outline = outline, render = render, sheet = sheet,
}
