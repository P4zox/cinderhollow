// Shading phase 1: world-only captures (no HUD) of every region, bench vistas (seated), dark rooms, lava/neon, classic path.
//   SHOT_HTML=$PWD/web/dist/shading.html node tools/shots/shot.js tools/shots/v17/shading/snap.js <outdir>
// window.__shSet: SETTINGS overrides; window.__shOnly: list of shot names to keep; window.__shPrefix: file name prefix.
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); Object.assign(G.SAVE.items, { talon: 1, slam: 1, wings: 1, hook: 1, dash: 1, emberdash: 1 });
const E = G.sk.ev;
// deterministic: seeded Math.random (re-seeded per shot), so lightning, sparks and flicker match between builds
E(`(() => { let seed = 1; window.__shSeed = (n) => { seed = n; }; Math.random = () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; })()`);
Object.assign(G.SETTINGS, window.__shSet || {});
if (window.__shTune && G.lx) Object.assign(G.lx.LX_TUNE, window.__shTune);   // live look knobs (no rebuild): LX_TUNE / GFX_TONE
if (window.__shTone && G.GFX_TONE) Object.assign(G.GFX_TONE, window.__shTone);
const PRE = window.__shPrefix || '', ONLY = window.__shOnly;
// [name, room, tx, ty, kind]   kind: '' stand, 'seat' bench vista, 'dark' darkT lights-out
const SPOTS = window.__shSpots || [
  ['r_ramparts', 'R5', 70, 12], ['r_catacombs', 'C8', 31, 30], ['r_cathedral', 'K7', 43, 28], ['r_mire', 'M14', 15, 8], ['r_crown', 'X7', 41, 44],
  ['r_archives', 'A8', 28, 27], ['r_hoarfrost', 'HF14', 35, 20], ['r_spire', 'SP8', 68, 17], ['r_deep', 'D11', 29, 35], ['r_hermit', 'H3', 6, 10],
  ['r_ember', 'E5', 38, 27], ['r_thornveil', 'TV9', 31, 27], ['r_barrows', 'DB15', 11, 10], ['r_crimson', 'CM9', 42, 26], ['r_necropolis', 'NV10', 20, 55],
  ['r_dunes', 'DU10', 47, 22], ['r_starfall', 'SF11', 101, 28], ['r_neohallow', 'NH8', 2, 39], ['r_lastfield', 'LF1', 56, 16], ['r_forge', 'CF5', 45, 14],
  ['r_threshold', 'CT2', 46, 31], ['r_training', 'TR2', 28, 18],
  ['d_catacombs', 'C10', 26, 10], ['d_crimson', 'CM1', 22, 8], ['d_hermit', 'H2', 24, 8], ['d_lightsout', 'C10', 26, 10, 'dark'],
  ['h_deep', 'D17', 8, 11], ['h_ember', 'E4', 28, 10], ['h_forge_hearth', 'CF8', 35, 17], ['h_neon', 'NH17', 8, 9], ['h_flue', 'CF3', 14, 26],
  ['v_R11', 'R11', 19, 5, 'seat'], ['v_K11', 'K11', 11, 16, 'seat'], ['v_HF14', 'HF14', 14, 14, 'seat'], ['v_SP15', 'SP15', 11, 6, 'seat'], ['v_DU15', 'DU15', 31, 12, 'seat'],
  ['v_LF1', 'LF1', 66, 15, 'seat'], ['v_X11', 'X11', 20, 19, 'seat'], ['s_LF1', 'LF1', 66, 15], ['s_X11', 'X11', 20, 19], ['s_crown_snow', 'X10', 24, 11], ['s_dunes_sand', 'DU1', 37, 5],
  ['s_threshold_nofill', 'CT2', 46, 31, 'nofill'], ['s_threshold_read', 'CT2', 46, 31, 'read'],   // nofill first: 'read' marks the page read for good
];
const world = async (n) => { E(`vctx.fillStyle = '#050407'; vctx.fillRect(0, 0, view.width, view.height); renderWorld(); presentWorld();`); await snap(PRE + n); };
const out = [JSON.stringify({ shaders: G.SETTINGS.shaders, light: G.SETTINGS.light, lband: G.SETTINGS.lband, rim: G.SETTINGS.rim, bloom: G.SETTINGS.bloom, rays: G.SETTINGS.rays, bright: G.SETTINGS.bright, mood: G.SETTINGS.mood, grade: G.SETTINGS.grade })];
for (const [n, r, x, y, kind] of SPOTS) {
  if (ONLY && !ONLY.includes(n)) continue;
  try {
    E('darkT = 0; time = 100'); window.__shSeed(1234 + n.length * 7);
    G.tp(r, x, y);
    for (let i = 0; i < 200; i++) { G.step(1); G.enemies.length = 0; if (G.state === 'cut' || G.state === 'cine' || G.state === 'dialog') G.step(1, [], ['pause']); }
    if (G.xs && G.xs.clean) G.xs.clean();
    if (kind === 'seat') {
      const b = window.__sys && window.__sys.prop('sys_bench');
      if (b) { window.__sys.x3().vistas[b.key] = 1; b.interact(); if (window.__sys.SYS.vista) window.__sys.SYS.vista.lore = null; }
      for (let i = 0; i < 170; i++) { G.step(1); G.enemies.length = 0; }
    }
    if (kind === 'dark') { E('darkT = 6'); }
    if (kind === 'read' && window.__sys) { for (const p of G.props) if (p.page) window.__sys.x3().lore[p.page] = 1; }   // lore pages read: no 'unread' glow
    const pl0 = G.lx && G.lx.LX_TUNE.player; if (kind === 'nofill' && G.lx) G.lx.LX_TUNE.player = 0;   // the knight's fill off (diagnostic)
    G.step(2); await world(n);
    if (kind === 'nofill' && G.lx) G.lx.LX_TUNE.player = pl0;
    if (kind === 'seat' && window.__sys) { window.__sys.stand(); for (let i = 0; i < 60; i++) G.step(1); }
    E('darkT = 0');
    out.push(`${n} ok room=${G.room} state=${G.state}`);
  } catch (e) { out.push(`${n} ERR ${e.message}`); }
}
return out;
