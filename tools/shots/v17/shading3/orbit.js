// Shading phase 3: one lamp moved around the knight, a shield warden, a rot hulk and the Hearthkeeper (a still) in a dark catacomb:
// cast shadows, contact pools and glints on their own.  sh orbit.sh <html> <outdir> [settings-json]   (TUNE / NTUNE / DBG / ALT as in shoot.sh)
await boot(); G.SETTINGS.god = 1;
const E = G.sk.ev;
E('window.requestAnimationFrame = () => 0');
Object.assign(G.SETTINGS, window.__shSet || {});
if (window.__shTune && G.lx) Object.assign(G.lx.LX_TUNE, window.__shTune);
if (window.__shNTune && G.lxn) Object.assign(G.lxn.LXN_TUNE, window.__shNTune);
const R = window.__orbRoom || ['C10', 26, 10];
E('time = 100'); G.tp(R[0], R[1], R[2]);
for (let i = 0; i < 120; i++) { G.step(1); G.enemies.length = 0; if (G.state !== 'play') G.step(1, [], ['pause']); }
E(`(() => { P.face = 1; enemies.length = 0;
  const a = makeEnemy('shield_warden', P.x + 46, P.y, 'orb_a'), b = makeEnemy('rot_hulk', P.x - 70, P.y, 'orb_b');
  for (const e of [a, b]) { e.update = () => {}; enemies.push(e); } a.face = -1; b.face = 1;
  HOOKS.renderMid = HOOKS.renderMid || [];
  window.__orbHk = () => { const s = sheet('hearthkeeper_p1_8'); if (s.ok) { const o = typeof LXO !== 'undefined'; if (o) LXO.occ = LXO.on && SETTINGS.csh >= 2; drawSprite(s, 0, P.x + 150, P.y, -1); if (o) LXO.occ = false; } };
  HOOKS.renderMid.push(window.__orbHk);
})()`);
for (let i = 0; i < 60; i++) E('renderWorld()');
await new Promise(r => setTimeout(r, 400));
for (let i = 0; i < 60; i++) E('renderWorld()');
const LAMPS = window.__orbLamps || [['none', null], ['left', [-40, -22]], ['right', [40, -22]], ['above', [0, -60]], ['low_left', [-30, -6]], ['hk_left', [110, -50]], ['hk_right', [200, -50]]];
const out = [];
const shot = async (n, d) => {
  E(`lights = []; ${d ? `lights.push({ x: P.x + ${d[0]}, y: P.y + ${d[1]}, r: 110, color: '255,170,90', k: 1.3, o: {} });` : ''} vctx.fillStyle = '#050407'; vctx.fillRect(0, 0, view.width, view.height); renderWorld(); presentWorld();`);
  await snap((window.__shPrefix || '') + n);
};
for (const [n, d] of LAMPS) {
  await shot('orb_' + n, d); out.push(n);
  for (const [an, alt] of Object.entries(window.__shAlt || {})) { const keep = {}; for (const k in alt) keep[k] = G.SETTINGS[k]; Object.assign(G.SETTINGS, alt); E('renderWorld()'); await shot('orb_' + n + '_' + an, d); Object.assign(G.SETTINGS, keep); }
  for (const dg of (window.__shDbg || [])) { E(`window.__game.lx.LX.dbg = ${dg}`); await shot('orb_' + n + '_dbg' + dg, d); E('window.__game.lx.LX.dbg = 0'); }
}
return out;
