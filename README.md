# Cinderhollow

A hard 2D side-scrolling soulslike (Elden Ring × Hollow Knight) that runs in the browser. Pixel art is generated in Python and built through Aseprite.

**Play:** open `web/dist/index.html` in Chrome, Edge or Firefox. It's a single self-contained file that also works offline. When GitHub Pages is enabled, the game is served at `https://<your-username>.github.io/cinderhollow/`.

## Content
- 61 rooms across 11 regions: Ashen Ramparts, Rootbound Catacombs, Sunken Cathedral, Weeping Mire, Pale Crown, Ashen Archives, Hoarfrost Aqueduct, Tempest Spire, Burning Deep, and two secret areas.
- 20 bosses and mini-bosses, with intro cutscenes and multi-phase fights.
- 29 weapons in 8 movesets: sword, dagger, greatsword, spear, katana, staff, sword & shield, and twin blades.
- 18 weapon arts, 16 spells and 25 charms.
- Level-ups, a skill tree, a forge, shrines with map travel, New Game+, and three endings.

## Controls
| Key | Action |
|---|---|
| A D / ← → | Move (W / S aim up / down) |
| Space | Jump (hold to jump higher) · ↓ + Space drops through thin floors |
| J / left click | Attack |
| K / right click | Heavy attack (hold to charge) · in the air: plunging attack |
| L / Shift | Roll · air dash |
| I | Parry, then J to riposte · with a shield: hold to block |
| O | Weapon art (hold to charge) |
| U / Q | Cast spell / switch spell |
| F / R | Crimson flask / azure flask |
| H / C | Root Hook |
| S + K in the air | Cinder Slam |
| E | Talk · interact · rest |
| Tab / M | Map |
| Esc | Menu (the Settings tab has test options: god mode, infinite stamina, armory) |

## Building from source
Requirements: Python 3 with Pillow. To regenerate art you also need [Aseprite](https://www.aseprite.org/) (the CLI path is set in `art/asebuild.py`).

```bash
python3 web/build_web.py            # -> web/dist/index.html (validates rooms, bundles code + assets)
SPLIT=1 python3 web/build_web.py    # also writes web/dist/pub/ (page + asset chunks; this is what GitHub Pages serves)
python3 art/gen_<thing>.py          # regenerate a sprite sheet: art/*.aseprite + assets/*.png/json
```

## Project layout
| Path | Contents |
|---|---|
| `web/src/*.js` | Game engine and content. Files are concatenated in name order into one script. |
| `tools/rooms.py`, `tools/regions/*.py` | Room definitions and the level validator; generates `web/src/02_rooms.js` |
| `art/` | Art generators and Aseprite sources |
| `assets/` | Exported sprite sheets and creature metadata |
| `docs/` | Art specs, the expansion plan and the build contract |
| `tools/shots/` | Headless test harness (`npm i`, then `node shot.js <test.js>`; uses your installed Chrome) |
