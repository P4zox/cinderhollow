"""AA's art review sheets (weapon arts x the weapons that use them), without rebuilding the sheets.

  python3 art/player_aa_preview.py rows out.png tag:kind,kind ...     # like player_preview rows, wrapped to <= COLS frames per line
  python3 art/player_aa_preview.py all  out_dir                        # every art x every weapon that owns it (one sheet per art)
Env: SC (scale, default 4), COLS (frames per line, default 6), BG=dark for an in-game-ish backdrop.
"""
import os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_player as G

W, H = G.W, G.H
_FN = dict(G.ANIMS)
_CACHE = {}
# weapon -> (class prefix, art) : mirrors WEAPONS[id].art / WEAPON_CLASS (web/src/01b_gear.js, 04_player.js)
OWN = {"longsword": ("sw", "crescent"), "dagger": ("dg", "bloodstep"), "greatsword": ("gs", "warcry"), "spear": ("sp", "warcry"),
       "katana": ("kt", "moonwave"), "maul": ("gs", "cinderblade"), "oathbrand": ("sw", "cinderblade"), "kalden": ("sw", "moonwave"),
       "gravetusk": ("gs", "stormleap"), "omen": ("sw", "backstep_slash"), "rotmaw": ("gs", "warcry"), "scepter": ("sp", "moonwave"),
       "frostbrand": ("sw", "moonwave"), "pagecutter": ("dg", "ink_mark"), "colossus_hammer": ("gs", "magma_quake"),
       "glacier_maul": ("gs", "stormleap"), "bell_hammer": ("gs", "tolling_blow"), "forge_cleaver": ("gs", "cinderblade"),
       "stormfang": ("sp", "thunder_lunge"), "stormvein": ("kt", "bloodstep"), "quarterstaff": ("st", "whirlwind"),
       "windstaff": ("st", "gale_vault"), "inkquill": ("st", "ink_mark"), "lantern_staff": ("st", "cinderblade"),
       "knight_shield": ("sh", "aegis"), "twinborne": ("sh", "frost_aegis"), "overseer_bulwark": ("sh", "shield_charge"),
       "twinfangs": ("tw", "twin_tempest"), "first_ember": ("sw", "echo"), "antler_scythe": ("sc", "harvest_moon"),
       "briar_scythe": ("sc", "reap"), "thornwood_staff": ("st", "whirlwind"), "choir_harpoon": ("sp", "tidal_surge"),
       "tidecleaver": ("gs", "tidal_surge"), "barnacle_fang": ("dg", "bloodstep"), "sanguine_rapier": ("sw", "blood_frenzy"),
       "carving_knife": ("dg", "backstep_slash"), "crimson_scythe": ("sc", "reap"), "vael_greatsword": ("gs", "moonwave"),
       "headsman_chain": ("wh", "chain_drag"), "gravechain": ("wh", "lash"), "pharaoh_khopesh": ("sw", "solar_flare"),
       "sun_sceptre": ("st", "solar_flare"), "scarab_spear": ("sp", "warcry"), "starblade": ("kt", "starfall"),
       "meteor_maul": ("gs", "stormleap"), "orrery_whip": ("wh", "lash"), "saint_lance": ("sp", "overclock"),
       "plasma_katana": ("kt", "overclock"), "last_kindling": ("sc", "pale_pyre")}


def tag_for(kind):
    pre, art = OWN[kind]
    t = f"art_{art}__{pre}"
    return t if t in _FN else f"art_{art}"


def frames(tag):
    if tag not in _CACHE:
        _CACHE[tag] = list(_FN[tag]())
    return _CACHE[tag]


def render(tag, kind):
    out = []
    for cels, ms in frames(tag):
        body = G.compose(G.imgs(cels, None))
        w = G.imgs(cels, kind).get("Sword") if kind else None
        out.append((G.over(body, w), ms))
    return out


def sheet(rows, out):
    sc, cols = int(os.environ.get("SC", "4")), int(os.environ.get("COLS", "6"))
    bg = (24, 22, 30, 255) if os.environ.get("BG") == "dark" else (58, 58, 66, 255)
    lines = []
    for tag, kind in rows:
        fr = render(tag, kind)
        act = G.ACTIVE.get(tag, (0, -1))
        for k in range(0, len(fr), cols):
            lines.append((tag, kind, k, fr[k:k + cols], act))
    lw = 40
    img = Image.new("RGBA", (lw + cols * (W + 1), len(lines) * (H + 1)), (92, 92, 100, 255))
    for ry, (tag, kind, k0, fr, act) in enumerate(lines):
        for i, (im, ms) in enumerate(fr):
            cell = Image.new("RGBA", (W, H), bg)
            cell.alpha_composite(im)
            d = ImageDraw.Draw(cell)
            if act[0] <= k0 + i <= act[1]:
                d.line([(0, H - 1), (7, H - 1)], fill=(255, 196, 90, 255))
            img.alpha_composite(cell, (lw + i * (W + 1), ry * (H + 1)))
    img = img.resize((img.width * sc, img.height * sc), Image.NEAREST)
    d = ImageDraw.Draw(img)
    for ry, (tag, kind, k0, fr, act) in enumerate(lines):
        y = ry * (H + 1) * sc
        if k0 == 0:
            d.text((4, y + 4), tag[4:], fill=(255, 255, 255, 255))
            d.text((4, y + 18), kind[:15], fill=(200, 200, 210, 255))
        for i, (_, ms) in enumerate(fr):
            d.text(((lw + i * (W + 1)) * sc + 3, y + 3), f"{k0 + i}:{ms}", fill=(255, 220, 150, 255))
    img.save(out)
    print(out, img.size)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "rows":
        rows = []
        for spec in sys.argv[3:]:
            tag, kinds = spec.split(":")
            rows += [(tag, k) for k in kinds.split(",")]
        sheet(rows, sys.argv[2])
    elif mode == "all":
        od = sys.argv[2]
        os.makedirs(od, exist_ok=True)
        by = {}
        for kind, (pre, art) in OWN.items():
            by.setdefault(art, []).append((tag_for(kind), kind))
        for art, rows in sorted(by.items()):
            sheet(sorted(rows), os.path.join(od, f"art_{art}.png"))
