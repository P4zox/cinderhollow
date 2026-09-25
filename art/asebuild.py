"""Shared Aseprite build helper.

build(name, w, h, layers, frames, tags)
  layers: list of layer names, bottom -> top
  frames: list of dicts {"ms": int, "cels": {layer_name: PIL.Image RGBA (w x h)}}
  tags:   list of (tag_name, first_frame_index0, last_frame_index0)

Produces:
  art/<name>.aseprite                 layered, tagged source
  assets/<name>.png                   horizontal spritesheet (all layers merged)
  assets/<name>.json                  Aseprite json-array data (frames, durations, frameTags)
"""
import os, shutil, subprocess, tempfile

ASEPRITE = ("/Users/halstonchen/Library/Application Support/Steam/steamapps/common/"
            "Aseprite/Aseprite.app/Contents/MacOS/aseprite")
ART = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(ART), "assets")

def build(name, w, h, layers, frames, tags):
    tmp = tempfile.mkdtemp(prefix=f"ase_{name}_")
    try:
        with open(os.path.join(tmp, "manifest.txt"), "w") as fh:
            fh.write(f"size {w} {h}\n")
            fh.write("layers " + ",".join(layers) + "\n")
            fh.write("frames " + ",".join(str(int(f["ms"])) for f in frames) + "\n")
            for t, a, b in tags:
                fh.write(f"tag {t} {a + 1} {b + 1}\n")
        for i, f in enumerate(frames):
            for layer, img in f["cels"].items():
                assert layer in layers, layer
                assert img.size == (w, h), (layer, img.size)
                if img.getbbox():
                    img.save(os.path.join(tmp, f"{layer}_{i + 1}.png"))
        src = os.path.join(ART, f"{name}.aseprite")
        subprocess.run([ASEPRITE, "-b", "--script-param", f"dir={tmp}", "--script-param",
                        f"out={src}", "--script", os.path.join(ART, "build_sprite.lua")], check=True)
        subprocess.run([ASEPRITE, "-b", src, "--sheet", os.path.join(ASSETS, f"{name}.png"),
                        "--sheet-type", "horizontal", "--data", os.path.join(ASSETS, f"{name}.json"),
                        "--format", "json-array", "--list-tags"], check=True,
                       stdout=subprocess.DEVNULL)
        return src
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
