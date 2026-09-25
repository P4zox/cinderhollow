"""Aseprite build helper for big Tempest Spire sheets: same as asebuild.build() but exports the sheet as a GRID
(--sheet-type rows, N columns) so a 288x176 x 124-frame boss stays under 4096 px in both directions.
The engine reads frame rects from the json, so a grid sheet works everywhere a strip does."""
import os, shutil, subprocess, tempfile
import asebuild

ASEPRITE, ART, ASSETS = asebuild.ASEPRITE, asebuild.ART, asebuild.ASSETS


def build_grid(name, w, h, layers, frames, tags, columns=14):
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
        subprocess.run([ASEPRITE, "-b", "--script-param", f"dir={tmp}", "--script-param", f"out={src}", "--script",
                        os.path.join(ART, "build_sprite.lua")], check=True)
        subprocess.run([ASEPRITE, "-b", src, "--sheet", os.path.join(ASSETS, f"{name}.png"), "--sheet-type", "rows",
                        "--sheet-columns", str(columns), "--data", os.path.join(ASSETS, f"{name}.json"),
                        "--format", "json-array", "--list-tags"], check=True, stdout=subprocess.DEVNULL)
        return src
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
