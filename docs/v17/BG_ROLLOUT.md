# BG rollout (owner approved the pilot look, 2026-10-16): three agents, one shared ComfyUI

Read first: docs/v17/BG_AUDIT.md (defects per biome) and docs/v17/bg_pilot.md (the method as built: art/bgv2lib.py,
art/gen_bg_catacombs_v2.py / gen_bg_cathedral_v2.py as templates, settings, lessons: pixel-art LoRA 0.6, guide with
real values, roll-and-repaint seams, palette lock to the old ramps extended upward, reject seeds with figures, keep
512x216 / tags / frame counts / alpha contract). Branch `bg-overhaul`. Do not commit, push or publish; the lead commits.

| agent | biomes (in order) | also owns |
|---|---|---|
| A | crown, archives, deep, spire (keep spire's 10 frames + lightning tags) | GFX_SUN / grade entries for its biomes |
| B | hoarfrost, mire, necropolis (remove the opaque dark band atop mid), dunes (tone down saturation, replace the blocky Anubis; update GFX_SUN if the painted sun moves) | same |
| C | threshold, ember, hermit; neohallow far-layer seam; the pilot's weak spots (catacombs skull rows reading as jars, cathedral rose-window dither + olive smudges + plain mid arcade); the per-biome `veil` key (01_data.js) for any biome where it fixes the wall-to-sky staircase or box edges (A and B tell C which of theirs need it) | 03_world.js / 01_data.js |

Shared ComfyUI: one server on :8188 for all three (it queues). Start it only if `curl -s localhost:8188/system_stats`
fails; never stop it (the lead stops it at the end). Use distinct filename prefixes per biome. Owner taste: dark
mythology, sleek, painterly pixel art matching the ramparts quality bar; never cartoony; never a different style;
backdrops must not compete with the player/enemies. Iterate until each clearly beats its original; if one doesn't,
keep the old one and say so.

Per biome deliver: art/gen_bg_<biome>_v2.py, art/bg_src/<biome>/ (big raw renders gitignored as in the pilot), new
assets + aseprite, in-game before/after of 2 rooms (shaders on) in tools/shots/v17/bgroll/<biome>/, and a section in
docs/v17/bg_rollout_<agent>.md. Report at the end with a montage tools/shots/v17/bgroll/<agent>_before_after.png.
