-- Generic assembler: reads <dir>/manifest.txt and <dir>/<Layer>_<frame>.png cels.
-- manifest lines:  size W H | layers a,b,c (bottom->top) | frames ms,ms,... | tag name from to
local dir = app.params["dir"]
local out = app.params["out"]
local W, H, layers, frames, tags = 0, 0, {}, {}, {}
local function split(s) local t = {} for v in s:gmatch("[^,]+") do t[#t+1] = v end return t end
for line in io.lines(dir .. "/manifest.txt") do
  local k, rest = line:match("^(%S+)%s+(.*)$")
  if k == "size" then local a, b = rest:match("(%d+)%s+(%d+)"); W, H = tonumber(a), tonumber(b)
  elseif k == "layers" then layers = split(rest)
  elseif k == "frames" then frames = split(rest)
  elseif k == "tag" then local n, a, b = rest:match("(%S+)%s+(%d+)%s+(%d+)"); tags[#tags+1] = { n, tonumber(a), tonumber(b) }
  end
end
local spr = Sprite(W, H, ColorMode.RGB)
for i = 2, #frames do spr:newEmptyFrame(i) end
for i, fr in ipairs(spr.frames) do fr.duration = tonumber(frames[i]) / 1000 end
spr.layers[1].name = layers[1]
for i = 2, #layers do spr:newLayer().name = layers[i] end
for li, name in ipairs(layers) do
  for f = 1, #frames do
    local path = dir .. "/" .. name .. "_" .. f .. ".png"
    if app.fs.isFile(path) then
      spr:newCel(spr.layers[li], f, Image { fromFile = path }, Point(0, 0))
    end
  end
end
for _, t in ipairs(tags) do spr:newTag(t[2], t[3]).name = t[1] end
spr:saveAs(out)
