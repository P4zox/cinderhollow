# v17 brief: painted vistas for the bench rooms

Owner (2026-10-17): "improve the rooms with no enemy where you can sit, with Comfy. Make them have good views,
different than the regular region bg. Make them very very aesthetic!"

These 18 rooms are the game's rest stops: no enemies, a vista bench (`{t:'sys', kind:'bench', view:[x,y]}`); sitting
pulls the camera back (web/src/43_systems.js sysSit / sysDrawVista: zoom to ~0.4–0.55, the view rises up to 160 px into
the sky in outdoor rooms, letterbox bars, music settles). Each gets its own hand-painted view that replaces the
biome's parallax in that room only — a postcard moment, the most beautiful image in its region, clearly different
from the region's regular backdrop but unmistakably the same world.

Engine (done, commit 42c4683): `web/src/85_vistas.js` — `vistaRegister(roomId, { tint, layers: [...], fx })`. Layers are
sheets `vista_<room>_<name>` (assets/*.png/.json, tag `loop`, 1+ frames) with scroll factors fac/vfac, wrap or a single
placed painting (wrap:false, x), fps, alpha, dy; layers may be taller than 216 px (bottom-anchored; the extra height
fills the sky when the view pulls back). `fx(t, cam)` draws restrained motion over the layers (drifting cloud bands,
star twinkle, water glints, a lighthouse beam, fireflies, falling petals/snow/ash, neon flicker). Falls back to the biome
backdrop if a sheet is missing. Register from your own file `web/src/85v_<group>.js`.

| agent | rooms |
|---|---|
| V1 | R11 Watcher's Perch (ramparts), K11 The Rose Window (cathedral), M14 Fisherman's Rest (mire), A14 The Reading Nook (archives), HF14 Frostbitten Overlook (hoarfrost), SP15 Lighthouse Balcony (spire) |
| V2 | X11 The Crown Overlook (crown), TV14 Mossbed Glade (thornveil), DB15 Pearl Lagoon (barrows), CM16 Moonlit Conservatory (crimson), DU15 The Last Oasis (dunes), LF1 The Long Evening (lastfield) |
| V3 | SF16 The Stargazer's Seat + SF17 The Crater Edge (starfall — make them two different views), NH15 Neon Skyline (neohallow), E6 The Last Hearth (ember; the fire burns low after `w2:open` — the view may change too), H3 The Hermit's Garden (hermit), CT2 The Last Gate (threshold, the World 2 vista — keep the beyond mysterious) |

For each room: read its definition (web/src/02_rooms.js; region file in tools/regions/), its bench `view` focus, any
lore page on the bench (`lore:`; LORE_PAGES), its region's story, and any existing per-room sky override (LF1, X11, rooms
with `xsb_sky` — 54_sb.js, 52_rc.js, 55_sc.js; keep what is special about them and raise it). Indoor rooms (K11, A14,
E6, CM16 …) show their view through windows/openings: paint what is seen through them, and check how much shows.
Compose for BOTH the standing view (384×216, cam follows the player) and the seated, pulled-back view (take
screenshots of both: walk to the bench and interact, wait ~2 s).

Look and quality: dark mythology, sleek, painterly pixel art at the game's pixel scale and palette discipline
(quality bar: the ramparts backdrop and The Long Evening). Golden-hour skies, moonlight, aurora, starfields, light
through mist, reflections — one clear focal point, depth in 3+ planes, a calm reading space behind the bench.
Never cartoony, no figures in the art (they read as enemies), nothing that competes with the player while standing.
Mind the shaders: GFX_SUN (40_gfx.js) god rays are keyed per biome — if a painting's light source sits elsewhere,
add a per-room override or tone it (minimal surgical edit; note it).

Method: the pilot/rollout pipeline (docs/v17/bg_pilot.md, art/bgv2lib.py, art/bgv2b.py, art/bgroll_a_lib.py) — but
these are new paintings, so text2img/img2img from a painted composition guide with more freedom is fine; ComfyUI at
~/ComfyUI (run.sh, :8188, shared by three agents — start only if down, never stop; distinct filename prefixes);
generate large, downscale + palette-lock + cleanup to pixel art; separate layers by depth with clean alpha; reject
seeds with figures. Generator per room `art/gen_vista_<room>.py` reproducing the assets from saved renders
(art/bg_src/vista_<room>/, big renders gitignored as before).

Deliver: assets + .aseprite, `web/src/85v_<group>.js`, before/after (standing + seated) per room in
tools/shots/v17/vista/<room>/, a montage tools/shots/v17/vista/<agent>_before_after.png, docs/v17/vista_<agent>.md.
Look at every result yourself and iterate until it is genuinely beautiful. Do not commit, push or publish.
