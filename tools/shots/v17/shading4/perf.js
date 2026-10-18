// Shading phase 4: frame cost (phase-2/3 method). Per room and setting: renderWorld (CPU) and presentWorld (GPU lighting + reflection
// + post, read back so it really finishes), averaged over 240 frames of the knight running.   SHOT_HTML=<build> node ../../shot.js perf.js <out>
await boot(); G.SETTINGS.god = 1;
const E = G.sk.ev, p4 = !!G.lx4, o = [];
const R = [['C10', 26, 10], ['CF5', 45, 14], ['K7', 14, 7], ['DB15', 9, 10], ['SP8', 68, 17], ['R5', 70, 12], ['SF11', 101, 28]];
const SETS = p4 ? [['new off', { refl: 0, lpart: 0, dhaze: 0, rays: 0 }], ['refl', { refl: 1, lpart: 0, dhaze: 0, rays: 0 }], ['lpart', { refl: 0, lpart: 1, dhaze: 0, rays: 0 }],
  ['shafts', { refl: 0, lpart: 0, dhaze: 0, rays: 1 }], ['haze', { refl: 0, lpart: 0, dhaze: 1, rays: 0 }], ['all on (default)', { refl: 1, lpart: 1, dhaze: 1, rays: 1 }]]
  : [['phase 3 (default)', {}], ['phase 3, shafts off', { rays: 0 }]];
for (const [r, x, y] of R) {
  G.tp(r, x, y);
  for (let i = 0; i < 120; i++) G.step(1);
  for (let i = 0; i < 5 && G.state !== 'play'; i++) G.step(1, [], ['pause']);
  for (const [n, s] of SETS) {
    Object.assign(G.SETTINGS, s); G.GFX.sync = true; G.step(20);
    E(`window.__rwT = 0; { const f = renderWorld; renderWorld = function () { const t = performance.now(); f(); window.__rwT += performance.now() - t; }; window.__rwF = f; }`);
    G.GFX.pt = 0; G.GFX.pn = 0; const t1 = performance.now();
    for (let i = 0; i < 240; i++) { G.step(1, i % 60 < 30 ? ['right'] : ['left']); G.P.hp = 99999; }
    const whole = (performance.now() - t1) / 240, rw = E('window.__rwT') / G.GFX.pn;
    E('renderWorld = window.__rwF');
    o.push(`${r} ${n}: renderWorld ${rw.toFixed(2)} ms, presentWorld ${(G.GFX.pt / G.GFX.pn).toFixed(2)} ms, whole step ${whole.toFixed(2)} ms, lights ${G.lx.LX.n}` + (p4 ? `, refl rects ${E('LX4.rn')}, beams ${E('LX4.beams')}, lit particles ${E('LX4.pn')}` : ''));
  }
  G.GFX.sync = false;
}
return o;
