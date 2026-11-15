-- Draws each activity's tier table as one picture, in the layout of the team's mining sheet:
-- a purple title band, a dark header row, and a row per tier with its item icons.
-- Run from the repo root after the icon scripts:
--   aseprite -b --script sprites/build_item_tables.lua
-- Options: --script-param table=hunting (one table only), --script-param dir=<folder> (default docs).

local DIR = app.params.dir or "docs"
local ONLY = app.params.table
local ITEMS = app.params.items or "sprites/items"
local F = dofile((debug.getinfo(1, "S").source:match("^@(.*[/\\])") or "") .. "pixel_font.lua")

local function snake(s) return (s:lower():gsub(" ", "_")) end

-- each column: header, width, kind ("text", "icon" or "icontext"), and fn(row, tier)
-- returning the text, the icon file name, or both
local TABLES = {
  {
    id = "foraging",
    title = "Foraging - All Plants + Bundles",
    rows = { "Nettle", "Marigold", "Bluebell", "Thornroot", "Sunpetal",
             "Nightshade", "Frostbloom", "Bloodcap", "Voidlily", "Starmoss" },
    cols = {
      { "Name", 200, "text", function(r) return r end },
      { "Tier", 70, "text", function(_, i) return "T" .. i end },
      { "Plant", 84, "icon", function(r) return "plant_" .. snake(r) end },
      { "Bundle", 92, "icon", function(r) return "bundle_" .. snake(r) end },
      { "Seed", 84, "icon", function(r) return "seed_" .. snake(r) end },
      { "Chance", 100, "text", function(_, i) return string.format("%d%%", 11 - i) end },
    },
  },
  {
    id = "hunting",
    title = "Hunting - All Animals + Leathers",
    rows = {
      { "Hare", "Lucky Foot" }, { "Fox", "Brush Tail" }, { "Boar", "Boar Tusk" }, { "Wolf", "Wolf Fang" },
      { "Goldhorn Stag", "Golden Antler" }, { "Shadowcat", "Shadow Claw" }, { "Frostmane Yeti", "Frozen Heart" },
      { "Cinder Salamander", "Ember Scale" }, { "Voidstalker", "Void Eye" }, { "Starwyrm", "Star Horn" },
      { "Stormhorn Ram", "Thunder Curl" }, { "Tidecrest Serpent", "Abyss Pearl" }, { "Mossmane Behemoth", "Verdant Mane" },
      { "Crystalback Basilisk", "Prism Shard" }, { "Sunfeather Griffin", "Sun Feather" }, { "Eclipse Dragon", "Eclipse Crown" },
    },
    cols = {
      { "Name", 270, "text", function(r) return r[1] end },
      { "Tier", 70, "text", function(_, i) return "T" .. i end },
      { "Hide", 78, "icon", function(r) return "hide_" .. snake(r[1]) end },
      { "Leather", 104, "icon", function(r) return "leather_" .. snake(r[1]) end },
      { "Trophy", 248, "icontext", function(r) return "trophy_" .. snake(r[2]), r[2] end },
      { "Chance", 100, "text", function(_, i) return string.format("%.1f%%", 10 - (i - 1) * 0.6) end },
    },
  },
}

local rgba = app.pixelColor.rgba
local C = {
  sheet  = rgba(181, 181, 181, 255),
  title  = rgba(155, 134, 201, 255),
  head   = rgba(64, 64, 66, 255),
  cell   = rgba(196, 196, 198, 255),
  line   = rgba(52, 52, 56, 255),
  ink    = rgba(16, 16, 20, 255),
  white  = rgba(255, 255, 255, 255),
}

local S, TITLE_S = 2, 3      -- text scales
local ICON = 48
local ROW, HEAD = 58, 46     -- row and header heights
local PAD, MARGIN = 12, 40

local function draw(t)
  local tableW = 0
  for _, c in ipairs(t.cols) do tableW = tableW + c[2] end
  local titleH = F.capHeight * TITLE_S + 16
  local top = MARGIN + titleH + 24
  local W = math.max(tableW, F.width(t.title, TITLE_S, true) + 16) + MARGIN * 2
  local H = top + HEAD + ROW * #t.rows + MARGIN
  local img = Image(W, H, ColorMode.RGB)

  local function rect(x, y, w, h, c)
    for yy = y, y + h - 1 do for xx = x, x + w - 1 do img:drawPixel(xx, yy, c) end end
  end
  local function paste(name, x, y)
    local icon = Image { fromFile = ITEMS .. "/" .. name .. ".png" }
    for yy = 0, icon.height - 1 do
      for xx = 0, icon.width - 1 do
        local p = icon:getPixel(xx, yy)
        if app.pixelColor.rgbaA(p) > 0 then img:drawPixel(x + xx, y + yy, p) end
      end
    end
  end
  -- text with its capitals centred on a band of height h starting at y
  local function label(str, x, y, h, c, bold)
    F.draw(img, str, x, y + math.floor((h - F.capHeight * S) / 2), S, c, bold)
  end

  rect(0, 0, W, H, C.sheet)
  rect(MARGIN - 8, MARGIN, F.width(t.title, TITLE_S, true) + 16, titleH, C.title)
  F.draw(img, t.title, MARGIN, MARGIN + 8, TITLE_S, C.ink, true)

  local x = MARGIN
  for _, c in ipairs(t.cols) do
    rect(x, top, c[2], HEAD, C.head)
    label(c[1], x + math.floor((c[2] - F.width(c[1], S, true)) / 2), top, HEAD, C.white, true)
    x = x + c[2]
  end

  for i, r in ipairs(t.rows) do
    local y = top + HEAD + (i - 1) * ROW
    local iy = y + math.floor((ROW - ICON) / 2)
    x = MARGIN
    for _, c in ipairs(t.cols) do
      rect(x, y, c[2], ROW, C.cell)
      local a, b = c[4](r, i)
      if c[3] == "text" then
        label(a, x + PAD, y, ROW, C.ink)
      elseif c[3] == "icon" then
        paste(a, x + math.floor((c[2] - ICON) / 2), iy)
      else
        paste(a, x + 6, iy)
        label(b, x + 6 + ICON + 6, y, ROW, C.ink)
      end
      x = x + c[2]
    end
  end

  -- grid lines, 2 px, over the cell edges
  local bottom = top + HEAD + ROW * #t.rows
  x = MARGIN
  for _, c in ipairs(t.cols) do rect(x - 1, top, 2, bottom - top, C.line); x = x + c[2] end
  rect(x - 1, top, 2, bottom - top + 1, C.line)
  rect(MARGIN - 1, top - 1, tableW + 2, 2, C.line)
  for i = 0, #t.rows do rect(MARGIN - 1, top + HEAD + i * ROW - 1, tableW + 2, 2, C.line) end

  img:saveAs(DIR .. "/" .. t.id .. "-table.png")
end

for _, t in ipairs(TABLES) do
  if not ONLY or ONLY == t.id then draw(t) end
end
