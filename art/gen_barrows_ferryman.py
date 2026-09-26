#!/usr/bin/env python3
"""Mini-boss generator -- THE FERRYMAN of the Drowned Barrows.

    python3 art/gen_barrows_ferryman.py              full build (Aseprite): ferryman + fx_db_wave/wisp/hook + meta + previews
    python3 art/gen_barrows_ferryman.py --preview    previews + meta only (no Aseprite)
    python3 art/gen_barrows_ferryman.py --only sweep,slam --preview    quick iteration (writes *_wip previews)

Outputs
    art/ferryman.aseprite, assets/ferryman.png/.json     192x128, faces RIGHT, hem on the bottom row, anchor [96,128]
    assets/ferryman_meta.json                             hurtbox / attacks / spawn / telegraph / notes
    fx_db_wave (48x32, 4 loop, pivot bottom), fx_db_wisp (12x12, 4 loop), fx_db_hook (16x16, 2)
    art/previews/ferryman.png (3x, one row per tag), ferryman_closeup.png, ferryman_hitbox.png, fx_db_ferryman.png

A tall, gaunt hooded ferryman of the dead (~86px) gliding on black water: tattered black-teal robes whose hem
dissolves into dripping water, a deep cowl with two cold teal eye-points and a pale jaw, gaunt bone hands and a
long black oar-staff (broad blade below, iron boat-hook above) from which hangs a teal hook-lantern.
Drawing lives in art/barrows_ferryman_draw.py, FX in art/barrows_ferryman_fx.py.
"""
import json, math, os, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import enemy_kit as K  # noqa: E402
import barrows_ferryman_draw as D  # noqa: E402
from barrows_ferryman_draw import P_, W, H, AX, FLOOR, LAYERS  # noqa: E402

BUILD = "--preview" not in sys.argv
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None


# =========================================================================== animations
def S(g, a, u, **kw):
    d = dict(g=g, a=a, u=u)
    d.update(kw)
    return d


def S_tip(tip, a):
    """Loose staff (no hand) given its blade tip and angle."""
    dv = K.dirv(a)
    T = (tip[0] - dv[0] * D.SL, tip[1] - dv[1] * D.SL)
    return S(T, a, 0.0)


IDLE_ST = S((114.0, 64.0), 80.0, 46.0)


def a_idle():
    fr = []
    for i in range(6):
        ph = i * math.pi / 3
        b = 0.5 - 0.5 * math.cos(ph)                   # breath 0..1..0
        fr.append((170, P_(P=(94.0, 79.0 + 0.5 * b), lean=5.0 - 0.6 * b, htilt=1.0 * b,
                           st=S((114.0, 64.0 + 0.6 * b), 80.0, 46.0),
                           hb=(92.0, 89.5 + 0.4 * b), lsw=5.0 * math.sin(ph + 0.4), wind=0.6 * math.sin(ph),
                           fphase=0.5 * math.sin(ph))))
    return fr


def a_stride():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        bob = 0.8 * math.cos(2 * ph)
        fr.append((110, P_(P=(95.0, 79.5 + bob), lean=9.0 + 0.6 * math.sin(ph), htilt=-2.0, trail=7.0 + 1.2 * math.sin(ph),
                           hemx=-1.5, st=S((116.0, 66.0 + bob * 0.8), 75.0 + 1.5 * math.sin(ph), 48.0),
                           hb=(94.0 + 2.0 * math.sin(ph), 90.0 + bob), lsw=-12.0 + 6.0 * math.sin(ph + 1.0),
                           wind=2.0, wake=1.0, fphase=ph)))
    return fr


def a_sweep():
    U, UB = 40.0, 30.0
    fr = [
        (120, P_(P=(94.0, 80.0), lean=3.0, st=S((110.0, 68.0), 100.0, U), hb_on=UB + 4, lsw=4)),
        (120, P_(P=(93.0, 81.0), lean=0.0, st=S((101.0, 76.0), 125.0, U), hb_on=UB, lsw=12, trail=-2, wind=-1)),
        (130, P_(P=(91.0, 82.0), lean=-4.0, htilt=-3, st=S((91.0, 82.0), 150.0, U), hb_on=UB, lsw=18, trail=-4, wind=-2)),
        (140, P_(P=(90.0, 82.5), lean=-6.0, htilt=-4, st=S((85.0, 86.0), 162.0, U), hb_on=UB, lsw=14, trail=-5, wind=-3)),
        (330, P_(P=(89.5, 83.0), lean=-7.0, htilt=-5, st=S((83.0, 88.0), 168.0, U), hb_on=UB, lsw=10, trail=-6, wind=-3,
                 glint="blade", eye=2)),
    ]
    k5 = S((100.0, 92.0), 26.0, U)
    k6 = S((122.0, 97.0), 16.0, U)
    k7 = S((124.0, 87.0), -12.0, U)
    fr += [
        (60, P_(P=(97.0, 84.0), lean=10.0, st=k5, hb_on=UB, lsw=-20, trail=6, wind=4,
                sweep=[S((90.0, 95.0), 80.0, U), k5], spray=1)),
        (60, P_(P=(101.0, 86.0), lean=18.0, htilt=4, st=k6, hb_on=UB, lsw=-30, trail=9, wind=6, hemx=2,
                sweep=[S((100.0, 92.0), 50.0, U), k5, k6], spray=2)),
        (80, P_(P=(100.0, 84.0), lean=12.0, htilt=2, st=k7, hb_on=UB, lsw=-26, trail=8, wind=5, hemx=2,
                sweep=[S((123.0, 93.0), 4.0, U), k7])),
        (130, P_(P=(98.0, 81.0), lean=8.0, st=S((120.0, 76.0), -24.0, U), hb_on=UB, lsw=-10, trail=5, wind=2, hemx=1)),
        (140, P_(P=(96.0, 80.0), lean=6.0, st=S((118.0, 72.0), 28.0, U + 2), hb_on=UB + 2, lsw=10, trail=3, wind=-1)),
        (140, P_(P=(95.0, 79.5), lean=5.0, st=S((116.0, 67.0), 60.0, U + 4), lsw=14, trail=2, wind=-1)),
        (160, P_(P=(94.0, 79.0), lean=5.0, st=S((114.5, 64.5), 77.0, 45.0), lsw=6, trail=2)),
    ]
    return fr


def a_slam():
    U, UB = 46.0, 36.0
    k5 = S((95.0, 35.0), 204.0, U)
    k6 = S((110.0, 46.0), -35.0, U)
    k7 = S((124.0, 90.0), 41.0, U + 1)
    fr = [
        (130, P_(P=(94.0, 79.0), lean=6.0, st=S((112.0, 66.0), 72.0, U), hb_on=UB, lsw=4)),
        (120, P_(P=(93.0, 79.0), lean=2.0, st=S((106.0, 58.0), 118.0, U), hb_on=UB, lsw=16, wind=-1)),
        (120, P_(P=(92.0, 78.0), lean=-2.0, htilt=-4, st=S((100.0, 48.0), 160.0, U), hb_on=UB, lsw=22, wind=-2, trail=-2)),
        (130, P_(P=(92.0, 77.5), lean=-5.0, htilt=-6, st=S((97.0, 39.0), 190.0, U), hb_on=UB, lsw=12, wind=-2, trail=-3)),
        (130, P_(P=(92.0, 77.0), lean=-7.0, htilt=-7, st=S((96.0, 36.0), 200.0, U), hb_on=UB, lsw=6, wind=-3, trail=-4)),
        (340, P_(P=(91.5, 77.0), lean=-8.0, htilt=-8, st=k5, hb_on=UB, lsw=4, wind=-3, trail=-4, glint="blade", eye=2)),
        (60, P_(P=(96.0, 80.0), lean=6.0, htilt=2, st=k6, hb_on=UB, lsw=-24, wind=3, trail=3,
                sweep=[S((95.0, 35.0), 204.0, U), S((100.0, 38.0), 250.0, U), k6])),
        (90, P_(P=(100.0, 85.0), lean=16.0, htilt=6, st=k7, hb_on=UB + 1, lsw=-34, wind=5, trail=7, hemx=2,
                sweep=[S((116.0, 60.0), -8.0, U), S((121.0, 78.0), 20.0, U), k7], splash=1)),
        (140, P_(P=(100.0, 85.5), lean=16.0, htilt=6, st=S((124.0, 90.0), 41.0, U + 1), hb_on=UB + 1, lsw=-10,
                 trail=6, hemx=2, splash=2)),
        (150, P_(P=(99.0, 83.0), lean=12.0, htilt=3, st=S((121.0, 84.0), 50.0, U), hb_on=UB, lsw=12, trail=4,
                 hemx=1, splash=3)),
        (140, P_(P=(96.0, 80.5), lean=8.0, st=S((116.0, 72.0), 68.0, U), lsw=10, trail=3)),
        (160, P_(P=(94.0, 79.0), lean=5.0, st=S((114.5, 65.0), 78.0, U), lsw=4, trail=2)),
    ]
    for _, p in fr:
        p["splash_at"] = (167.0, 127.0)
    return fr


def a_hook():
    U, UB = 40.0, 52.0
    brace = dict(P=(90.0, 81.0), lean=-9.0, htilt=-4, trail=-3, hemx=-1)
    fr = [
        (120, P_(P=(94.0, 79.0), lean=5.0, st=S((113.0, 66.0), 100.0, U), lsw=-6)),
        (120, P_(P=(94.0, 79.5), lean=6.0, st=S((113.0, 68.0), 125.0, U), hb_on=UB, lsw=-14)),
        (130, P_(P=(95.0, 80.0), lean=7.0, st=S((115.0, 70.0), 145.0, U), hb_on=UB, lsw=-8)),
        (130, P_(P=(96.0, 80.0), lean=8.0, st=S((118.0, 68.0), 150.0, U), hb_on=UB, lsw=4)),
        (330, P_(P=(96.0, 80.5), lean=6.0, st=S((119.0, 67.0), 153.0, U), hb_on=UB, lsw=2, lvl=2, glint="lantern",
                 eye=2)),
        (80, P_(P=(99.0, 81.0), lean=14.0, htilt=3, st=S((126.0, 66.0), 160.0, U), hb_on=UB, lant=None, trail=5,
                wind=4, hemx=1, hook_flare=1)),
    ]
    for k in range(4):
        j = (0.0, 0.6, -0.4, 0.3)[k]
        fr.append(((120, 110, 110, 140)[k], P_(**brace, st=S((104.0 + j, 74.0), 140.0 + j * 2, U), hb_on=UB,
                                               lant=None, wind=-2 + j)))
    fr += [
        (130, P_(P=(92.0, 80.0), lean=0.0, st=S((110.0, 70.0), 120.0, U), hb_on=UB, lsw=-26, lvl=1.0)),
        (160, P_(P=(94.0, 79.0), lean=5.0, st=S((113.5, 65.0), 90.0, 45.0), lsw=-10)),
    ]
    return fr


def a_flare():
    lv = (1.0, 1.25, 1.6, 2.0, 2.4, 2.8)
    raise_ = [((114.0, 63.0), 82.0, 46.0), ((111.0, 55.0), 86.0, 41.0), ((108.0, 46.0), 88.0, 36.0),
              ((106.0, 42.0), 90.0, 32.0), ((105.0, 40.0), 90.0, 30.0), ((105.0, 39.5), 90.0, 29.0)]
    fr = []
    for k, (g, a, u) in enumerate(raise_):
        fr.append(((130, 130, 140, 160, 150, 170)[k],
                   P_(P=(94.0, 79.0 - 0.4 * k), lean=5.0 - k * 1.4, htilt=-k * 2.0, st=S(g, a, u), hb_on=u + 12 + k,
                      lsw=(4, -3, 2, -1, 1, 0)[k], lvl=lv[k], glint="lantern" if k == 3 else None,
                      eye=2 if k >= 3 else 1, wind=-0.5 * k)))
    fr += [
        (90, P_(P=(94.0, 77.0), lean=-3.0, htilt=-12, st=S((105.0, 39.5), 90.0, 29.0), hb_on=47.0, lsw=0, lvl=3,
                burst=1, eye=2, wind=-3)),
        (110, P_(P=(94.0, 77.5), lean=-2.0, htilt=-10, st=S((105.0, 40.0), 90.0, 30.0), hb_on=48.0, lsw=0, lvl=2,
                 burst=2, eye=2, wind=-2)),
        (140, P_(P=(94.0, 78.5), lean=2.0, htilt=-4, st=S((108.0, 48.0), 87.0, 37.0), hb_on=55.0, lsw=4, lvl=1.3,
                 burst=3)),
        (170, P_(P=(94.0, 79.0), lean=5.0, st=S((113.0, 62.0), 82.0, 45.0), lsw=5)),
    ]
    return fr


def a_vault():
    fr = [
        (120, P_(P=(95.0, 80.0), lean=8.0, st=S((116.0, 66.0), 72.0, 44.0), hb_on=36.0, lsw=-6)),
        (260, P_(P=(94.0, 88.0), lean=14.0, htilt=8, squash=0.12, st=S((114.0, 70.0), 75.0, 40.0), hb_on=31.0, lsw=-10,
                 glint="blade", eye=2, trail=2)),
        (110, P_(P=(93.0, 92.0), lean=17.0, htilt=10, squash=0.2, st=S((112.0, 74.0), 78.0, 40.0), hb_on=31.0, lsw=-14, trail=3)),
        # airborne (drawn in place; the engine flies him in an arc)
        (90, P_(P=(96.0, 76.0), lean=-8.0, htilt=-6, st=S((110.0, 66.0), 100.0, 40.0), hb_on=31.0, lsw=20, air=True,
                hemy=114.0, trail=-2, wind=-4)),
        (100, P_(P=(96.0, 75.0), lean=4.0, st=S((112.0, 64.0), 150.0, 40.0), hb_on=30.0, lsw=10, air=True, hemy=112.0,
                 trail=4, wind=2)),
        (110, P_(P=(95.0, 75.0), lean=-2.0, htilt=-4, st=S((99.0, 40.0), 196.0, 44.0), hb_on=34.0, lsw=4, air=True,
                 hemy=112.0, trail=2, wind=1)),
        (100, P_(P=(95.0, 76.0), lean=-4.0, htilt=-6, st=S((97.0, 37.0), 204.0, 44.0), hb_on=34.0, lsw=0, air=True,
                 hemy=113.0, trail=0, wind=-1, eye=2)),
        (60, P_(P=(96.0, 78.0), lean=6.0, htilt=2, st=S((108.0, 44.0), -40.0, 44.0), hb_on=34.0, lsw=-20, air=True,
                hemy=116.0, trail=3, wind=3, sweep=[S((97.0, 37.0), 204.0, 44.0), S((102.0, 38.0), 250.0, 44.0),
                                                     S((108.0, 44.0), -40.0, 44.0)])),
        (100, P_(P=(96.0, 88.0), lean=15.0, htilt=6, squash=0.15, st=S((106.0, 68.0), 88.0, 47.0), hb_on=37.0, lsw=-30, trail=4,
                 wind=4, sweep=[S((108.0, 44.0), -40.0, 44.0), S((108.0, 58.0), 40.0, 46.0),
                                S((106.0, 68.0), 88.0, 47.0)], splash=1)),
        (200, P_(P=(95.0, 82.0), lean=9.0, htilt=3, st=S((110.0, 66.0), 84.0, 47.0), hb_on=37.0, lsw=10, trail=2,
                 splash=2)),
    ]
    for _, p in fr:
        p["splash_at"] = (106.0, 127.0)
    return fr


def a_stagger():
    return [
        (100, P_(P=(91.0, 80.0), lean=-13.0, htilt=-16, hood_back=1.5, jaw=1.0, st=S((106.0, 68.0), 104.0, 46.0),
                 hb=(78.0, 84.0), lsw=34, eye=2, trail=-5, wind=-5)),
        (120, P_(P=(90.0, 80.5), lean=-10.0, htilt=-12, hood_back=1.0, jaw=1.0, st=S((105.0, 70.0), 100.0, 46.0),
                 hb=(80.0, 88.0), lsw=-22, trail=-4, wind=-3)),
        (200, P_(P=(92.0, 82.0), lean=10.0, htilt=12, st=S((108.0, 72.0), 90.0, 46.0), hb=(95.0, 92.0), lsw=18,
                 eye=3, trail=1, wind=2)),
        (240, P_(P=(92.0, 82.5), lean=11.0, htilt=13, st=S((108.0, 72.5), 90.0, 46.0), hb=(95.0, 92.5), lsw=-8,
                 eye=3, trail=1)),
    ]


def a_death():
    tip = (124.0, 125.0)
    fall = [80.0, 74.0, 62.0, 44.0, 24.0, 8.0, 1.0, 3.0, 1.5]            # staff angle for frames 3..11
    fr = [
        (140, P_(P=(92.0, 80.0), lean=-9.0, htilt=-10, st=S((110.0, 67.0), 88.0, 46.0), hb=(84.0, 88.0), lsw=20,
                 lvl=0.5, eye=2, trail=-3, wind=-3)),
        (160, P_(P=(94.0, 81.0), lean=9.0, htilt=10, st=S((112.0, 70.0), 84.0, 46.0), hb=(96.0, 91.0), lsw=-12,
                 lvl=0.5, eye=3, trail=2, wind=2)),
        (180, P_(P=(94.0, 82.0), lean=6.0, htilt=14, st=S((112.0, 72.0), 82.0, 46.0), hb=(95.0, 92.0), lsw=6,
                 lvl=0.5, eye=3, trail=1)),
    ]
    melt = [0.1, 0.28, 0.45, 0.62, 0.8]
    for k, m in enumerate(melt):
        fr.append(((170, 150, 140, 130, 130)[k],
                   P_(P=(94.0 + k * 0.5, 86.0 + k * 8.0), lean=10.0 + k * 5.0, htilt=12 + k * 4, melt=m, sback=True,
                      st=S_tip(tip, fall[k]), hf=(108.0 - k, 92.0 + k * 7), hb=(97.0, 95.0 + k * 7),
                      lant="hook", lvl=0, lsw=-10 - k * 6, eye=0, puddle=26 + k * 6, hemy=D.HEM_Y + k * 1.2)))
    for k, (hh, pw) in enumerate(((7.0, 50), (4.5, 60), (3.0, 66), (3.0, 66))):
        fr.append(((150, 160, 200, 1000)[k],
                   P_(P=(94.0, 110.0), heap=hh, puddle=pw, st=S_tip(tip, fall[5 + k]),
                      lant="lying" if k else "hook", lvl=0, lsw=-40 if not k else 0, sback=True)))
    return fr


TAGDEFS = [("idle", a_idle), ("stride", a_stride), ("sweep", a_sweep), ("slam", a_slam), ("hook", a_hook),
           ("flare", a_flare), ("vault", a_vault), ("stagger", a_stagger), ("death", a_death)]
COUNTS = dict(idle=6, stride=8, sweep=12, slam=12, hook=12, flare=10, vault=10, stagger=4, death=12)
LOOPS = ("idle", "stride")
# =========================================================================== render
def render_all(only=None):
    frames, infos, tags, flats = [], {}, [], []
    for tag, fn in TAGDEFS:
        fr = fn()
        assert len(fr) == COUNTS[tag], (tag, len(fr))
        if only and tag not in only:
            continue
        drv = [p["P"][0] + math.sin(math.radians(p["lean"])) * D.SP for _, p in fr]
        sway = K.spring(drv, loop=tag in LOOPS, extra=[p.get("wind", 0.0) for _, p in fr])
        a = len(frames)
        infos[tag] = []
        for k, (ms, p) in enumerate(fr):
            Ls, info = D.draw(p, a + k, sway[k])
            for side, r in info["reach"]:
                if r > 0.8:
                    print(f"  WARN {tag}[{k}] {side} hand out of reach by {r:.1f}px")
            imgs = {}
            for n in LAYERS:
                v = Ls.get(n)
                if v is None:
                    continue
                imgs[n] = K.render_layer(v) if isinstance(v, K.Layer) else v.image()
            frames.append({"ms": ms, "cels": imgs})
            flats.append(K.flatten(imgs, LAYERS))
            infos[tag].append(info)
        tags.append((tag, a, len(frames) - 1))
        print("rendered", tag, len(fr))
    return frames, infos, tags, flats


# =========================================================================== previews
BG = (86, 88, 98, 255)
CELL = (70, 73, 84, 255)
DARK = (14, 17, 20, 255)


def preview_rows(tags, flats, path, scale=3):
    cols = max(b - a + 1 for _, a, b in tags)
    pad, lab = 2, 10
    sheet = Image.new("RGBA", (cols * (W + pad) * scale, len(tags) * (H + pad + lab) * scale), BG)
    d = ImageDraw.Draw(sheet)
    for r, (t, a, b) in enumerate(tags):
        y0 = r * (H + pad + lab) * scale
        d.text((4, y0 + 4), f"{t} ({b - a + 1})", fill=(235, 235, 240, 255))
        for i in range(a, b + 1):
            fr = Image.new("RGBA", (W, H), CELL)
            fr.alpha_composite(flats[i])
            d2 = ImageDraw.Draw(fr)
            sheet.alpha_composite(fr.resize((W * scale, H * scale), Image.NEAREST),
                                  ((i - a) * (W + pad) * scale, y0 + lab * scale))
    sheet.save(path)


def closeup(tags, flats, path, picks, scale=5):
    """Key frames at 5x, 3 per row; the first on a dark background with the player for scale."""
    start = {t: a for t, a, _ in tags}
    pl = Image.open(os.path.join(asebuild.ASSETS, "player.png")).crop((0, 0, 64, 40))
    picks = [(t, k) for t, k in picks if t in start]
    cols = 3
    rows = (len(picks) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * (W + 2) * scale, rows * (H + 2) * scale), BG)
    for j, (t, k) in enumerate(picks):
        fr = Image.new("RGBA", (W, H), DARK if j == 0 else CELL)
        if j == 0:
            fr.alpha_composite(pl, (160 - 28, H - 40))
        fr.alpha_composite(flats[start[t] + k])
        sheet.alpha_composite(fr.resize((W * scale, H * scale), Image.NEAREST),
                              ((j % cols) * (W + 2) * scale, (j // cols) * (H + 2) * scale))
    sheet.save(path)


def onex(tags, flats, path):
    """1x strip of every frame on the dark background (silhouette check) + 2x upscale for viewing."""
    n = len(flats)
    sheet = Image.new("RGBA", (n * W, H), DARK)
    for i, f in enumerate(flats):
        sheet.alpha_composite(f, (i * W, 0))
    sheet.save(path)


# =========================================================================== meta
def bbox(pts):
    pts = [p for p in pts if K.inb(*p)]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1]


def union_rect(rs):
    x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs)
    x1 = max(r[0] + r[2] for r in rs); y1 = max(r[1] + r[3] for r in rs)
    return [x0, y0, x1 - x0, y1 - y0]


def window(infos, tag, a, b, xmin=None, xmax=None, extra=None):
    rs = {}
    for k in range(a, b + 1):
        pts = infos[tag][k]["hit"]
        if xmin is not None:
            pts = {q for q in pts if q[0] >= xmin}
        if xmax is not None:
            pts = {q for q in pts if q[0] <= xmax}
        r = bbox(pts)
        if extra:
            r = union_rect([r, extra])
        r[3] = H - r[1]                        # always reach the floor (a 10x26 player standing on it)
        rs[str(k)] = r
    return {"active": [a, b], "hit": union_rect(list(rs.values())), "rects": rs}


def pt(q):
    return [int(round(q[0])), int(round(q[1]))]


def build_meta(infos, tags):
    i0 = infos["idle"][0]
    body = i0["robe"] | i0["torso"] | i0["mantle"] | i0["head"]
    bx = bbox(body)
    hurt = [bx[0] + 3, bx[1] + 2, bx[2] - 6, H - (bx[1] + 2)]
    sw, sl, hk, fl, vt = infos["sweep"], infos["slam"], infos["hook"], infos["flare"], infos["vault"]
    meta = {
        "native": 1,
        "frame": [W, H],
        "anchor": [AX, H],
        "hurtbox": hurt,
        "attacks": {
            "sweep": window(infos, "sweep", 5, 7, xmin=AX + 4, extra=[AX + 10, 101, 10, 27]),
            "slam": window(infos, "slam", 6, 7, xmin=AX + 8),
            "vault": window(infos, "vault", 8, 8, xmin=AX - 44, xmax=AX + 44, extra=[AX - 40, 100, 81, 28]),
        },
        "spawn": {
            "slam": {"frame": 7, "at": [int(round(sl[7]["tip"][0])), H - 1]},
            "hook": {"frame": 5, "at": pt(hk[5]["top"])},
            "flare": {"frame": 6, "at": pt(fl[6]["lantern"])},
        },
        "telegraph": {
            "sweep": {"frame": 4, "at": pt(sw[4]["glint"])},
            "slam": {"frame": 5, "at": pt(sl[5]["glint"])},
            "hook": {"frame": 4, "at": pt(hk[4]["glint"])},
            "flare": {"frame": 3, "at": pt(fl[3]["glint"])},
            "vault": {"frame": 1, "at": pt(vt[1]["glint"])},
        },
        "fx": {"wave": "fx_db_wave", "wisp": "fx_db_wisp", "hook": "fx_db_hook"},
        "notes": "faces right, anchor = hem centre on the water (x=96, bottom row); no feet: the robe hem liquefies into "
                 "black water that always touches the bottom row, so he glides (stride is a loop drawn in place). "
                 "hurtbox = robe+cowl, not the oar. "
                 "sweep: 0-3 draws the oar back low behind him, 4 held windup (blade glint = telegraph.at), active 5-7 "
                 "the blade sweeps low in front from the waterline up to chest height, reach ~90px (rects per frame), "
                 "8-11 recover. slam: 0-4 raises the oar overhead (blade behind), 5 held (glint), 6 swings over, 7 "
                 "blade crashes into the water -> spawn.slam = impact on the floor: spawn fx_db_wave there travelling "
                 "forward (pivot bottom-centre), 8-11 recover. hook: 0-3 lifts the hook-lantern end forward, 4 held "
                 "(lantern flares = telegraph), frame 5 the hook-lantern leaves the staff: spawn the chained hook "
                 "projectile (fx_db_hook, faces right) at spawn.hook = the bare staff tip and draw the chain from that "
                 "point; 6-9 he braces back pulling (staff tip stays near spawn.hook +-2px), 10-11 lantern back on the "
                 "hook. flare: 0-5 raises the lantern overhead, glow growing (3 = telegraph), frame 6 burst -> spawn "
                 "homing fx_db_wisp at spawn.flare (the lantern), 7-9 recover. vault: 0-2 plants the oar and crouches "
                 "(1 = telegraph, blade glint), 3-7 airborne pose drawn in place (move him in an arc; the hem lifts off "
                 "the water in these frames), 8 lands with the blade striking down at his feet (active, hit covers "
                 "+-40px around the anchor), 9 recover. 'hit' = union of per-frame 'rects' over the inclusive active "
                 "range; every rect reaches the floor. stagger (4) holds its last frame; death (12): the lantern "
                 "gutters (0-2) and goes out (3), the robe sinks and collapses empty into a spreading black puddle "
                 "while the oar topples behind him (3-10); final frame held 1000ms.",
    }
    return meta


def hitbox_preview(tags, flats, meta, path, scale=3):
    start = {t: (a, b) for t, a, b in tags}
    A = meta["attacks"]
    rows = [("sweep", [A["sweep"]]), ("slam", [A["slam"]]), ("vault", [A["vault"]]), ("hook", []), ("flare", []),
            ("idle", [])]
    pad, lab = 2, 12
    cols = max(start[t][1] - start[t][0] + 1 for t, _ in rows)
    sheet = Image.new("RGBA", (cols * (W + pad) * scale, len(rows) * (H + pad + lab) * scale), BG)
    dd = ImageDraw.Draw(sheet)
    ax, ay = meta["anchor"]
    for r, (t, wins) in enumerate(rows):
        a, b = start[t]
        y0 = r * (H + pad + lab) * scale
        sp, tg = meta["spawn"].get(t), meta["telegraph"].get(t)
        txt = t + "  " + "  ".join(f"active {w['active']} hit {w['hit']}" for w in wins)
        if sp:
            txt += f"  spawn f{sp['frame']} {sp['at']}"
        if tg:
            txt += f"  telegraph f{tg['frame']} {tg['at']}"
        dd.text((4, y0 + 4), txt, fill=(235, 235, 240, 255))
        for i in range(a, b + 1):
            k = i - a
            fr = Image.new("RGBA", (W, H), CELL)
            fr.alpha_composite(flats[i])
            big = fr.resize((W * scale, H * scale), Image.NEAREST)
            d = ImageDraw.Draw(big)

            def rect(rc, col, wdt=1):
                x, y, w, h = rc
                d.rectangle([x * scale, y * scale, (x + w) * scale - 1, (y + h) * scale - 1], outline=col, width=wdt)

            def cross(q, col):
                x, y = q
                d.line([((x - 4) * scale, y * scale), ((x + 4) * scale, y * scale)], fill=col, width=2)
                d.line([(x * scale, (y - 4) * scale), (x * scale, (y + 4) * scale)], fill=col, width=2)
            rect(meta["hurtbox"], (60, 230, 90, 255))
            for w in wins:
                if w["active"][0] <= k <= w["active"][1]:
                    rect(w["hit"], (255, 170, 60, 255), 1)
                    rc = w["rects"][str(k)]
                    rect(rc, (255, 50, 50, 255), 2)
                    rect([min(W - 10, rc[0] + rc[2] - 6), H - 26, 10, 26], (90, 150, 255, 255))
            if sp and sp["frame"] == k:
                cross(sp["at"], (255, 60, 255, 255))
            if tg and tg["frame"] == k:
                cross(tg["at"], (60, 240, 255, 255))
            d.line([(ax * scale - 5, ay * scale - 2), (ax * scale + 5, ay * scale - 2)], fill=(255, 255, 0, 255), width=2)
            d.line([(ax * scale, ay * scale - 8), (ax * scale, ay * scale - 1)], fill=(255, 255, 0, 255), width=2)
            sheet.alpha_composite(big, (k * (W + pad) * scale, y0 + lab * scale))
    sheet.save(path)


def fx_preview(sheets, path, s=6):
    """Each FX sheet as a row: frames on the dark background, then on mid-grey."""
    rows = []
    for name, (w, h, layers, frames) in sheets.items():
        rows.append((name, w, h, layers, frames))
    width = max(len(f) * 2 * (w + 2) for _, w, h, _, f in rows) * s
    height = sum((h + 6) for _, w, h, _, _ in rows) * s
    sheet = Image.new("RGBA", (width, height), BG)
    d = ImageDraw.Draw(sheet)
    y = 0
    for name, w, h, layers, frames in rows:
        d.text((4, y * s + 2), name, fill=(235, 235, 240, 255))
        for j, bgc in enumerate((DARK, CELL)):
            for i, f in enumerate(frames):
                fr = Image.new("RGBA", (w, h), bgc)
                for n in layers:
                    if n in f["cels"]:
                        fr.alpha_composite(f["cels"][n])
                x = (j * len(frames) + i) * (w + 2)
                sheet.alpha_composite(fr.resize((w * s, h * s), Image.NEAREST), (x * s, (y + 4) * s))
        y += h + 6
    sheet.save(path)


# =========================================================================== main
def main():
    frames, infos, tags, flats = render_all(ONLY)
    pv = os.path.join(ART, "previews")
    os.makedirs(pv, exist_ok=True)
    sfx = "_wip" if ONLY or "--wip" in sys.argv else ""
    preview_rows(tags, flats, os.path.join(pv, f"ferryman{sfx}.png"))
    closeup(tags, flats, os.path.join(pv, f"ferryman_closeup{sfx}.png"),
            [("idle", 0), ("stride", 2), ("sweep", 4), ("sweep", 6), ("slam", 7), ("hook", 4), ("flare", 6),
             ("vault", 5), ("death", 11)])
    if ONLY:
        return
    meta = build_meta(infos, tags)
    hitbox_preview(tags, flats, meta, os.path.join(pv, f"ferryman_hitbox{sfx}.png"))
    for t, dct in meta["attacks"].items():
        print("attack", t, dct["active"], dct["hit"])
    print("hurtbox", meta["hurtbox"])
    print("spawn", meta["spawn"])
    print("telegraph", meta["telegraph"])
    import barrows_ferryman_fx as FXM
    wave, wisp, hook = FXM.fx_db_wave(), FXM.fx_db_wisp(), FXM.fx_db_hook()
    fx_preview({"fx_db_wave": (48, 32, FXM.LAYERS_WAVE, wave), "fx_db_wisp": (12, 12, FXM.LAYERS_WISP, wisp),
                "fx_db_hook": (16, 16, FXM.LAYERS_HOOK, hook)}, os.path.join(pv, f"fx_db_ferryman{sfx}.png"))
    if "--wip" in sys.argv:
        return
    with open(os.path.join(asebuild.ASSETS, "ferryman_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    if BUILD:
        asebuild.build("ferryman", W, H, LAYERS, frames, tags)
        asebuild.build("fx_db_wave", 48, 32, FXM.LAYERS_WAVE, wave, [("fx_db_wave", 0, 3)])
        asebuild.build("fx_db_wisp", 12, 12, FXM.LAYERS_WISP, wisp, [("fx_db_wisp", 0, 3)])
        asebuild.build("fx_db_hook", 16, 16, FXM.LAYERS_HOOK, hook, [("fx_db_hook", 0, 1)])


if __name__ == "__main__":
    main()
