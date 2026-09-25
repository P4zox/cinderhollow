"""Bundle web/src/*.js + every Aseprite export in ../assets into one self-contained dist/index.html."""
import base64, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
subprocess.run([sys.executable, os.path.join(ROOT, "tools", "rooms.py")], check=True)
CACHE = os.path.join(HERE, ".pngcache"); os.makedirs(CACHE, exist_ok=True)
def packed_png(path):
    """Lossless re-encode: exact indexed palette (+ per-entry alpha) when a sheet has <= 256 colours. Cached by mtime/size."""
    st = os.stat(path); key = os.path.join(CACHE, f"{os.path.basename(path)}.{int(st.st_mtime)}.{st.st_size}")
    if os.path.exists(key): return open(key, "rb").read()
    raw = open(path, "rb").read(); out = raw
    try:
        import io
        from PIL import Image
        im = Image.open(path).convert("RGBA"); cols = im.getcolors(256)
        if cols:
            pal = {c: i for i, (n, c) in enumerate(cols)}
            pi = Image.new("P", im.size); pi.putdata([pal[c] for c in im.getdata()])
            pi.putpalette([v for n, c in cols for v in c[:3]])
            buf = io.BytesIO(); pi.save(buf, "PNG", optimize=True, transparency=bytes(c[3] for n, c in cols))
            if len(buf.getvalue()) < len(raw): out = buf.getvalue()
    except Exception as e:
        print("png pack failed", path, e)
    for old in os.listdir(CACHE):
        if old.startswith(os.path.basename(path) + "."): os.remove(os.path.join(CACHE, old))
    tmp = key + f".tmp{os.getpid()}"; open(tmp, "wb").write(out); os.replace(tmp, key); return out   # atomic: agents build concurrently
bundle = {}
for fn in sorted(os.listdir(ASSETS)):
    name, ext = os.path.splitext(fn)
    path = os.path.join(ASSETS, fn)
    if ext == ".png":
        bundle.setdefault(name, {})["png"] = "data:image/png;base64," + base64.b64encode(packed_png(path)).decode()
    elif ext == ".json" and not name.endswith("_meta"):
        d = json.load(open(path))
        bundle.setdefault(name, {})["json"] = {"frames": [{"frame": f["frame"], "duration": f["duration"]} for f in d["frames"]],
                                               "meta": {"frameTags": d["meta"].get("frameTags", [])}}
    elif ext == ".json":
        bundle[name] = json.load(open(path))
bundle = {k: v for k, v in bundle.items() if k.endswith("_meta") or ("png" in v and "json" in v)}
MAXW = 8192
def regrid(name, entry):
    """Wide horizontal strips break some browsers (Safari/mobile texture limits): repack frames into a grid, rewrite frame x/y. Lossless, cached."""
    fr = entry["json"]["frames"]
    if not fr: return
    W = max(f["frame"]["x"] + f["frame"]["w"] for f in fr); Hh = max(f["frame"]["y"] + f["frame"]["h"] for f in fr)
    if W <= MAXW: return
    fw = max(f["frame"]["w"] for f in fr); fh = max(f["frame"]["h"] for f in fr)
    cols = max(1, MAXW // fw)
    layout = [(i % cols * fw, i // cols * fh) for i in range(len(fr))]
    src = os.path.join(ASSETS, name + ".png"); st = os.stat(src)
    key = os.path.join(CACHE, f"{name}.png.{int(st.st_mtime)}.{st.st_size}.grid{cols}")
    if not os.path.exists(key):
        import io
        from PIL import Image
        im = Image.open(io.BytesIO(packed_png(src))).convert("RGBA")
        out = Image.new("RGBA", (cols * fw, ((len(fr) + cols - 1) // cols) * fh), (0, 0, 0, 0))
        for f, (x, y) in zip(fr, layout):
            q = f["frame"]; out.paste(im.crop((q["x"], q["y"], q["x"] + q["w"], q["y"] + q["h"])), (x, y))
        cols_ = out.getcolors(256); buf = io.BytesIO()
        if cols_:
            pal = {c: i for i, (n, c) in enumerate(cols_)}
            pi = Image.new("P", out.size); pi.putdata([pal[c] for c in out.getdata()]); pi.putpalette([v for n, c in cols_ for v in c[:3]])
            pi.save(buf, "PNG", optimize=True, transparency=bytes(c[3] for n, c in cols_))
        else: out.save(buf, "PNG", optimize=True)
        for old in os.listdir(CACHE):
            if old.startswith(name + ".png.") and ".grid" in old: os.remove(os.path.join(CACHE, old))
        tmp = key + f".tmp{os.getpid()}"; open(tmp, "wb").write(buf.getvalue()); os.replace(tmp, key)
    entry["png"] = "data:image/png;base64," + base64.b64encode(open(key, "rb").read()).decode()
    for f, (x, y) in zip(fr, layout): f["frame"] = {**f["frame"], "x": x, "y": y}
for _n, _e in bundle.items():
    if not _n.endswith("_meta") and "png" in _e: regrid(_n, _e)
src_dir = os.path.join(HERE, "src")
game = "\n".join(open(os.path.join(src_dir, f)).read() for f in sorted(os.listdir(src_dir)) if f.endswith(".js"))
shell = open(os.path.join(HERE, "shell.html")).read()
os.makedirs(os.path.join(HERE, "dist"), exist_ok=True)
out = os.environ.get("BUILD_OUT") or os.path.join(HERE, "dist", "index.html")   # agents: BUILD_OUT=web/dist/<name>.html
with open(out, "w") as fh:
    fh.write(shell)
    fh.write("\n<script>const ASSETS = " + json.dumps(bundle, separators=(",", ":")) + ";</script>\n")
    fh.write("<script>\n(() => {\n" + game + "\n})();\n</script>\n")
print("wrote", out, f"{os.path.getsize(out) / 1024:.0f} KB;", len(bundle), "assets")

# publish build (SPLIT=1): page + asset chunks fetched at startup, so the page stays under the artifact's 16 MB file limit
if os.environ.get("SPLIT"):
    pub = os.path.join(HERE, "dist", "pub"); os.makedirs(pub, exist_ok=True)
    for old in os.listdir(pub): os.remove(os.path.join(pub, old))
    chunks, cur, size = [], {}, 0
    for k, v in bundle.items():
        n = len(json.dumps(v, separators=(",", ":")))
        if cur and size + n > 9_000_000: chunks.append(cur); cur, size = {}, 0
        cur[k] = v; size += n
    if cur: chunks.append(cur)
    names = []
    for i, c in enumerate(chunks):
        fn = f"assets{i}.json"; names.append(fn)
        open(os.path.join(pub, fn), "w").write(json.dumps(c, separators=(",", ":")))
    loader = ("<script>let ASSETS = null;</script>\n<script>window.__startGame = () => {\n" + game + "\n};</script>\n"
              "<script>(() => { const SZ = " + json.dumps({fn: os.path.getsize(os.path.join(pub, fn)) for fn in names}) + ", got = {}, tot = {}; const upd = () => { const g = Object.values(got).reduce((a, b) => a + b, 0), t = Object.values(tot).reduce((a, b) => a + b, 0) || 1; window.__loadProgress && window.__loadProgress(0.9 * g / t, 'Kindling the ashes… ' + Math.round(100 * g / t) + '%'); };\n"
              "const get = async u => { const r = await fetch(u); if (!r.ok) throw new Error(u + ' ' + r.status); tot[u] = SZ[u] || 5e6; got[u] = 0;"
              " if (!r.body || !r.body.getReader) { const j = await r.json(); got[u] = tot[u]; upd(); return j; }"
              " const rd = r.body.getReader(), parts = []; for (;;) { const { done, value } = await rd.read(); if (done) break; parts.push(value); got[u] += value.length; if (got[u] > tot[u]) tot[u] = got[u]; upd(); }"
              " return JSON.parse(new TextDecoder().decode(await new Blob(parts).arrayBuffer())); };\n"
              "window.__getAll = () => Promise.all(" + json.dumps(names) + ".map(get)); })();\n"
              "window.__getAll()"
              ".then(parts => { ASSETS = Object.assign({}, ...parts); window.__startGame(); })"
              ".catch(e => { document.body.insertAdjacentHTML('beforeend', '<p style=\"color:#e6c77a;font:16px serif;text-align:center\">Could not load the game assets: ' + e.message + '</p>'); });</script>\n")
    open(os.path.join(pub, "index.html"), "w").write(shell + "\n" + loader)
    print("split build:", ", ".join(f"{fn} {os.path.getsize(os.path.join(pub, fn)) / 1e6:.1f} MB" for fn in names + ["index.html"]))
