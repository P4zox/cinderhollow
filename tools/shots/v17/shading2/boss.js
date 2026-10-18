// Shading phase 2: the Hearthkeeper in its arena (CF8), deterministic stills at fixed frames (no flash-triggered picks),
// so the before and after builds show the same moment.  SHOT_HTML=<build> sh ../boss/run.sh boss.js <out> '{"arena":1}'
Object.assign(G.SETTINGS, window.__shSet || {}, ARGS.set || {});
if (ARGS.tune && G.lx) Object.assign(G.lx.LX_TUNE, ARGS.tune);
if (ARGS.ntune && G.lxn) Object.assign(G.lxn.LXN_TUNE, ARGS.ntune);
const world = async (n) => { E('renderWorld(); renderWorld()'); E(`vctx.fillStyle = '#050407'; vctx.fillRect(0, 0, view.width, view.height); renderWorld(); presentWorld();`); await snap(n); };
E('window.requestAnimationFrame = () => 0');   // stop the page's own loop: only this script advances the game (deterministic)
const out = { summon: E('window.__hk.summon()') };
out.wake = E('window.__hk.wake()');
E('boss.stanceMax = boss.stanceBase = 9999');
const at = { 90: 'hk_a', 170: 'hk_b', 260: 'hk_c', 330: 'hk_d' };
for (let f = 0; f <= 330; f++) {
  if (f % 40 === 0) E('window.__hk.front(40)');
  if (f % 9 === 0) E('press("attack")'); else if (f % 9 === 2) E('release("attack")');
  E('window.__hk.play(1); P.hp = D.maxHp');
  if (at[f]) { await world(at[f]); for (const dg of ARGS.dbg || []) { E(`window.__game.lx.LX.dbg = ${dg}`); await world(at[f] + '_dbg' + dg); E('window.__game.lx.LX.dbg = 0'); } out[at[f]] = E('[boss.phase, boss.atk || boss.state, Math.round(boss.x), Math.round(P.x)].join(" ")'); }
}
E('boss.phase = 3; hkDark(true); boss.applySpeed && boss.applySpeed()');
for (let i = 0; i < 120; i++) E('window.__hk.play(1); P.hp = D.maxHp');
E('window.__hk.front(34)'); await world('hk_p3');
out.p3 = E('[boss.phase, boss.atk || boss.state, Math.round(boss.x), Math.round(P.x)].join(" ")');
out.lights = E('lights.map(L => [Math.round(L.x - cam.x), Math.round(L.y - cam.y), Math.round(L.r), L.k.toFixed(2), L.color].join(" ")).slice(0, 30)');
out.errs = E('window.__hk.errs.slice(0, 5)');
return out;
