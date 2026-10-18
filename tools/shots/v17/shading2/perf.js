// Shading phase 2: frame cost. Per room and setting: renderWorld (CPU: the scene + the normal mirror) and presentWorld
// (GPU lighting + post, read back so it really finishes) averaged over 240 frames of the knight running, plus the
// normal-cache work (first visit) and the room-layer bake. SHOT_HTML=<build> node ../../shot.js perf.js <out>
await boot(); G.SETTINGS.god = 1;
const E = G.sk.ev, has = !!G.lxn, o = [];
const R = [['C10', 26, 10], ['R5', 70, 12], ['X11', 20, 19], ['CF5', 45, 14], ['SF11', 101, 28]];
const SETS = has ? [['surf off', { surf: 0, rim: 0 }], ['surf on', { surf: 1, rim: 1 }]] : [['phase 1', {}]];
for (const [r, x, y] of R) {
  const t0 = performance.now(); G.tp(r, x, y); const tEnter = performance.now() - t0;
  let bake = 0, gen0 = has ? G.lxn.LXN.gen : 0, f = 0;
  if (has) { G.SETTINGS.surf = 1; const tb = performance.now(); for (; f < 200 && G.lxn.LXN.q.length + (f < 2 ? 1 : 0); f++) E('renderWorld()'); bake = performance.now() - tb; }
  G.step(60); for (let i = 0; i < 5 && G.state !== 'play'; i++) G.step(1, [], ['pause']);
  for (const [n, s] of SETS) {
    Object.assign(G.SETTINGS, s); G.GFX.sync = true; G.step(20);
    let rw = 0; const _rw = E('renderWorld'); E(`window.__rwT = 0; { const f = renderWorld; renderWorld = function () { const t = performance.now(); f(); window.__rwT += performance.now() - t; }; window.__rwF = f; }`);
    G.GFX.pt = 0; G.GFX.pn = 0; const t1 = performance.now();
    for (let i = 0; i < 240; i++) { G.step(1, i % 60 < 30 ? ['right'] : ['left']); G.P.hp = 99999; }
    const whole = (performance.now() - t1) / 240; rw = E('window.__rwT') / G.GFX.pn;
    E('renderWorld = window.__rwF');
    o.push(`${r} ${n}: renderWorld ${rw.toFixed(2)} ms, presentWorld ${(G.GFX.pt / G.GFX.pn).toFixed(2)} ms, whole step ${whole.toFixed(2)} ms, lights ${G.lx.LX.n}, foes ${G.enemies.length}`);
  }
  if (has) o.push(`${r} enter ${tEnter.toFixed(0)} ms; normal caches: ${G.lxn.LXN.gen - gen0} frames + room layers in ${f} frames, ${bake.toFixed(0)} ms total (budget/frame ${G.lxn.LXN.budget} ms, ×3 while fading); cached px ${(G.lxn.LXN.px / 1e6).toFixed(1)} M`);
  G.GFX.sync = false;
}
return o;
