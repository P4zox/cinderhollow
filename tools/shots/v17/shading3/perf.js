// Shading phase 3: frame cost (phase-2 method). Per room and setting: renderWorld (CPU: scene, normal mirror, silhouettes, pools)
// and presentWorld (GPU lighting + post, read back so it really finishes), averaged over 240 frames of the knight running.
//   SHOT_HTML=<build> node ../../shot.js perf.js <out>
await boot(); G.SETTINGS.god = 1;
const E = G.sk.ev, p3 = !!(G.lxn && G.lxn.LXO), o = [];
const R = [['C10', 26, 10], ['R5', 70, 12], ['CF5', 45, 14], ['SF11', 101, 28], ['SP8', 68, 17], ['SP8*', 68, 17]];   // SP8*: a lightning flash held on
const SETS = p3 ? [['p2-equiv', { csh: 0, mat: 0, eyead: 0 }], ['contact', { csh: 1, mat: 0 }], ['shadows', { csh: 2, mat: 0 }], ['all on', { csh: 2, mat: 1, eyead: 1 }]] : [['phase 2', {}]];
for (const [r, x, y] of R) {
  G.tp(r.replace('*', ''), x, y);
  for (let i = 0; i < 120; i++) G.step(1);
  for (let i = 0; i < 5 && G.state !== 'play'; i++) G.step(1, [], ['pause']);
  for (const [n, s] of SETS) {
    Object.assign(G.SETTINGS, s); G.GFX.sync = true; G.step(20);
    E(`window.__rwT = 0; { const f = renderWorld; renderWorld = function () { const t = performance.now(); f(); window.__rwT += performance.now() - t; }; window.__rwF = f; }`);
    G.GFX.pt = 0; G.GFX.pn = 0; const t1 = performance.now();
    for (let i = 0; i < 240; i++) { if (r.endsWith('*')) E('SPR.flash = 0.8'); G.step(1, i % 60 < 30 ? ['right'] : ['left']); G.P.hp = 99999; }
    const whole = (performance.now() - t1) / 240, rw = E('window.__rwT') / G.GFX.pn;
    E('renderWorld = window.__rwF');
    o.push(`${r} ${n}: renderWorld ${rw.toFixed(2)} ms, presentWorld ${(G.GFX.pt / G.GFX.pn).toFixed(2)} ms, whole step ${whole.toFixed(2)} ms, lights ${G.lx.LX.n}, foes ${G.enemies.length}`);
  }
  G.GFX.sync = false;
}
if (p3) {   // the eye-adaptation meter (one 48×27 readback on room entry) and the pre-warm queue
  const t = []; for (let i = 0; i < 20; i++) { const t0 = performance.now(); E('gfxMeter(LX.tOut)'); t.push(performance.now() - t0); }
  t.sort((a, b) => a - b); o.push(`meter: median ${t[10].toFixed(2)} ms, max ${t[19].toFixed(2)} ms`);
}
return o;
