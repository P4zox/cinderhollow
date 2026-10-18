// Shading phase 2: one lamp moved around the knight, a shield warden, a rot hulk and the Hearthkeeper (drawn as a still)
// in a dark catacomb, so the wrap / shade / rim reads on its own.  sh orbit.sh <html> <outdir> [settings-json]
await boot(); G.SETTINGS.god = 1;
const E = G.sk.ev;
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
  window.__orbHk = () => { const s = sheet('hearthkeeper_p1_8'); if (s.ok) drawSprite(s, 0, P.x + 150, P.y, -1); };
  HOOKS.renderMid.push(window.__orbHk);
})()`);
for (let i = 0; i < 60; i++) E('renderWorld()');   // warm the normal caches (and let the boss sheet load)
await new Promise(r => setTimeout(r, 400));
for (let i = 0; i < 60; i++) E('renderWorld()');
const LAMPS = [['none', null], ['left', [-40, -22]], ['right', [40, -22]], ['above', [0, -60]], ['hk_left', [110, -50]], ['hk_right', [200, -50]]];
const out = [];
for (const [n, d] of LAMPS) {
  E(`lights = []; ${d ? `lights.push({ x: P.x + ${d[0]}, y: P.y + ${d[1]}, r: 110, color: '255,170,90', k: 1.3, o: {} });` : ''} vctx.fillStyle = '#050407'; vctx.fillRect(0, 0, view.width, view.height); renderWorld(); presentWorld();`);
  await snap((window.__shPrefix || '') + 'orb_' + n); out.push(n);
  for (const dg of (window.__shDbg || [])) { E(`window.__game.lx.LX.dbg = ${dg}; vctx.fillStyle = '#050407'; vctx.fillRect(0, 0, view.width, view.height); renderWorld(); presentWorld(); window.__game.lx.LX.dbg = 0`); await snap('orb_' + n + '_dbg' + dg); }
}
return out;
