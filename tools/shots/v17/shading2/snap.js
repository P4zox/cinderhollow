// Shading phase 2: world-only captures (no HUD). Like ../shading/snap.js, plus foes kept in frame and debug views.
//   sh shoot.sh <html> <outdir> [settings-json] [names…]   (TUNE / NTUNE env: LX_TUNE / LXN_TUNE overrides)
// window.__shSet: SETTINGS overrides; __shOnly: names to keep; __shDbg: also save LX.dbg views (e.g. [8] normals);
// __shAlt: { suffix: settings } also saves the same frame under those settings (e.g. { surfoff: { surf: 0, rim: 0 } })
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); Object.assign(G.SAVE.items, { talon: 1, slam: 1, wings: 1, hook: 1, dash: 1, emberdash: 1 });
const E = G.sk.ev;
E('window.requestAnimationFrame = () => 0');   // stop the page's own loop: only this script advances the game (same frame across settings)
E(`(() => { let seed = 1; window.__shSeed = (n) => { seed = n; }; Math.random = () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; })()`);
Object.assign(G.SETTINGS, window.__shSet || {});
if (window.__shTune && G.lx) Object.assign(G.lx.LX_TUNE, window.__shTune);
if (window.__shNTune && G.lxn) Object.assign(G.lxn.LXN_TUNE, window.__shNTune);
const PRE = window.__shPrefix || '', ONLY = window.__shOnly, DBG = window.__shDbg || [];
// [name, room, tx, ty, kind, face]   kind: '' stand, 'foes' keep the room's foes (pulled next to the knight), 'seat' bench vista, 'dark' lights-out
const SPOTS = window.__shSpots || [
  ['p_cat_lamp', 'C10', 26, 10, 'foes'], ['p_cat_torch', 'C10', 40, 10, '', -1], ['p_ramparts', 'R5', 70, 12, 'foes'], ['p_X11', 'X11', 20, 19], ['p_X11_seat', 'X11', 20, 19, 'seat'],
  ['p_hermit', 'H3', 6, 10], ['p_hermit2', 'H3', 20, 10], ['p_C8', 'C8', 31, 30, 'foes'], ['p_forge', 'CF5', 45, 14, 'foes'], ['p_deep', 'D11', 29, 35, 'foes'],
];
const world = async (n) => { E(`vctx.fillStyle = '#050407'; vctx.fillRect(0, 0, view.width, view.height); renderWorld(); presentWorld();`); await snap(PRE + n); };
const out = [];
for (const [n, r, x, y, kind, face] of SPOTS) {
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
    G.step(2); await world(n);
    for (const [an, alt] of Object.entries(window.__shAlt || {})) {   // the same frame under other settings (toggle montages)
      const keep = {}; for (const k in alt) keep[k] = G.SETTINGS[k]; Object.assign(G.SETTINGS, alt); E('renderWorld(); renderWorld()'); await world(n + '_' + an); Object.assign(G.SETTINGS, keep);
    }
    for (const d of DBG) { E(`window.__game.lx.LX.dbg = ${d}`); await world(n + '_dbg' + d); E('window.__game.lx.LX.dbg = 0'); }
    if (kind === 'seat' && window.__sys) { window.__sys.stand(); for (let i = 0; i < 60; i++) G.step(1); }
    E('darkT = 0');
    out.push(`${n} ok room=${G.room} foes=${G.enemies.length} lxn=${G.lxn ? G.lxn.LXN.gen + '/' + G.lxn.LXN.q.length : '-'}`);
  } catch (e) { out.push(`${n} ERR ${e.message}`); }
}
return out;
