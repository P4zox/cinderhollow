// Shading phase 4: world-only captures (no HUD), deterministic (the page's own loop is stopped, Math.random seeded per shot).
//   sh shoot.sh <html> <outdir> [settings-json] [names…]   env: TUNE (LX_TUNE), NTUNE (LXN_TUNE), DBG ([11,12] debug views),
//   ALT ({suffix: settings}: the same frame again under other settings), SPOTS ([[name, room, tx, ty, kind, face]])
// kind: '' stand, 'foes' keep the room's foes (pulled next to the knight), 'jump' mid-jump, 'seat' bench vista, 'dark' lights-out
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); Object.assign(G.SAVE.items, { talon: 1, slam: 1, wings: 1, hook: 1, dash: 1, emberdash: 1 });
const E = G.sk.ev;
E('window.requestAnimationFrame = () => 0');
E(`(() => { let seed = 1; window.__shSeed = (n) => { seed = n; }; Math.random = () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; })()`);
Object.assign(G.SETTINGS, window.__shSet || {});
if (window.__shTune && G.lx) Object.assign(G.lx.LX_TUNE, window.__shTune);
if (window.__shNTune && G.lxn) Object.assign(G.lxn.LXN_TUNE, window.__shNTune);
if (window.__sh4Tune && G.lx4) Object.assign(G.lx4.LX4_TUNE, window.__sh4Tune);   // phase 4 knobs (41c_atmos.js)
const PRE = window.__shPrefix || '', ONLY = window.__shOnly, DBG = window.__shDbg || [];
const SPOTS = window.__shSpots || [   // phase 4 prototypes: reflections, particles, shafts, haze
  ['rf_CF5', 'CF5', 45, 14, 'foes'], ['rf_CF5b', 'CF5', 9, 14], ['rf_CF10', 'CF10', 20, 7], ['rf_DB15', 'DB15', 9, 10, '', 1], ['rf_M14', 'M14', 14, 8, '', 1],
  ['rf_HF8', 'HF8', 25, 7], ['rf_HF13', 'HF13', 12, 6], ['rf_SP8', 'SP8', 68, 17, 'foes'], ['rf_M7', 'M7', 20, 10],
  ['sh_K7', 'K7', 14, 7], ['sh_K7b', 'K7', 40, 7], ['sh_K11', 'K11', 20, 16], ['sh_C10', 'C10', 22, 10, 'foes'], ['sh_CF5', 'CF5', 40, 14], ['sh_R5', 'R5', 70, 12],
  ['pt_C10', 'C10', 40, 10, '', -1], ['pt_C10d', 'C10', 40, 10, '', -1, "__cloud('dust', 500)"], ['pt_C10m', 'C10', 26, 10, '', 1, "__cloud('mote', 300)"],
  ['pt_HF14s', 'HF14', 35, 20, '', 1, "__cloud('petal', 300)"], ['pt_M14s', 'M14', 20, 8, '', 1, "__cloud('spore', 300)"], ['pt_K7m', 'K7', 14, 7, '', 1, "__cloud('mote', 300)"], ['pt_A8', 'A8', 28, 27], ['pt_M14', 'M14', 20, 8], ['pt_HF14', 'HF14', 35, 20], ['pt_SP8', 'SP8', 60, 17],
  ['fx_shock', 'C10', 26, 10, '', 1, "spawnFx('shockwave', P.x + 40, P.y); for (let i = 0; i < 6; i++) updateFx(1 / 60)"],
  ['fx_nova', 'C10', 26, 10, '', 1, "spawnFx(fxOr('hf_nova', 'flame_ring'), P.x + 40, P.y - 20); for (let i = 0; i < 6; i++) updateFx(1 / 60)"],
  ['fx_flame', 'C8', 31, 30, '', 1, "spawnFx(fxOr('flame_ring', 'shockwave'), P.x + 50, P.y); for (let i = 0; i < 8; i++) updateFx(1 / 60)"],
  ['fx_holy', 'CF5', 9, 14, '', 1, "spawnFx(fxOr('holy_burst', 'sov_nova'), P.x + 50, P.y - 20); for (let i = 0; i < 6; i++) updateFx(1 / 60)"],
  ['fx_slam', 'K7', 14, 7, '', 1, "spawnFx(fxOr('slam_impact', 'shockwave'), P.x + 30, P.y); for (let i = 0; i < 4; i++) updateFx(1 / 60)"],
  ['fx_parry', 'C10', 40, 10, '', -1, "spawnFx(fxOr('parry_flash', 'hit'), P.x - 14, P.y - 18); for (let i = 0; i < 2; i++) updateFx(1 / 60)"],
  ['hz_X11', 'X11', 20, 19], ['hz_LF1', 'LF1', 56, 16], ['hz_R11', 'R11', 19, 5], ['hz_DU10', 'DU10', 47, 22], ['hz_C8', 'C8', 31, 30],
];
if (window.__shPre) E(window.__shPre);
const world = async (n) => { E(`vctx.fillStyle = '#050407'; vctx.fillRect(0, 0, view.width, view.height); renderWorld(); presentWorld();`); await snap(PRE + n); };
const out = [];
E(`window.__cloud = (k, n = 260, amb = true) => { for (let i = 0; i < n; i++) particles.push({ x: cam.x + Math.random() * W, y: cam.y + Math.random() * H, vx: 0, vy: 0, amb, life: 5, sway: Math.random() * 6, kind: k }); }`);
for (const [n, r, x, y, kind, face, extra] of SPOTS) {
  if (ONLY && !ONLY.includes(n)) continue;
  try {
    E('darkT = 0; time = 100'); window.__shSeed(1234 + n.length * 7);
    G.tp(r, x, y);
    for (let i = 0; i < 200; i++) { G.step(1); if (kind !== 'foes') G.enemies.length = 0; if (G.state === 'cut' || G.state === 'cine' || G.state === 'dialog') G.step(1, [], ['pause']); }
    if (kind === 'foes') E(`(() => { let k = 0; for (const e of enemies) { if (Math.abs(e.x - P.x) > 150) { e.x = P.x + (k % 2 ? -1 : 1) * (40 + 22 * k); e.y = P.y; } k++; } })()`);
    if (face) E(`P.face = ${face}`);
    if (G.xs && G.xs.clean) G.xs.clean();
    if (kind === 'seat') {
      const b = window.__sys && window.__sys.prop('sys_bench');
      if (b) { window.__sys.x3().vistas[b.key] = 1; b.interact(); if (window.__sys.SYS.vista) window.__sys.SYS.vista.lore = null; }
      for (let i = 0; i < 170; i++) { G.step(1); G.enemies.length = 0; }
    }
    if (kind === 'dark') E('darkT = 6');
    for (let i = 0; i < 40; i++) { E('renderWorld()'); }   // let the normal caches fill (a few ms a frame)
    if (kind === 'jump') { G.step(1, [], ['jump']); G.step(9, ['jump']); }
    else G.step(2);
    if (extra) E(extra);   // phase 4: e.g. "__cloud('dust')" (a dense particle cloud), a spell
    await world(n);
    for (const [an, alt] of Object.entries(window.__shAlt || {})) {   // the same frame under other settings (toggle montages)
      const keep = {}; for (const k in alt) keep[k] = G.SETTINGS[k]; Object.assign(G.SETTINGS, alt); E('renderWorld(); renderWorld()'); await world(n + '_' + an); Object.assign(G.SETTINGS, keep);
    }
    for (const d of DBG) { E(`window.__game.lx.LX.dbg = ${d}`); await world(n + '_dbg' + d); E('window.__game.lx.LX.dbg = 0'); }
    if (kind === 'seat' && window.__sys) { window.__sys.stand(); for (let i = 0; i < 60; i++) G.step(1); }
    E('darkT = 0');
    out.push(`${n} ok room=${G.room} foes=${G.enemies.length} lxn=${G.lxn ? G.lxn.LXN.gen + '/' + G.lxn.LXN.q.length : '-'} lxo=${G.lxn && G.lxn.LXO ? G.lxn.LXO.n + '/' + G.lxn.LXO.pools : '-'}`);
  } catch (e) { out.push(`${n} ERR ${e.message}`); }
}
return out;
