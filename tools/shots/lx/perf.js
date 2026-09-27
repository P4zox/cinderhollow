// LX: frame time of presentWorld (performance.now() around it, 300 frames) per lighting mode; sync = gl.finish() inside the probe
await boot(); G.SETTINGS.god = 1; G.giveArmory();
const o = [], R = [['C2', 24, 10], ['SP7', 26, 15], ['NH2', 28, 10]];
for (const [r, x, y] of R) {
  G.tp(r, x, y); G.step(60); for (let i = 0; i < 5 && G.state !== 'play'; i++) G.step(1, [], ['pause']);
  for (const sync of [false, true]) for (const m of [0, 1, 2]) {
    G.SETTINGS.light = m; G.GFX.sync = sync; G.step(5);
    G.GFX.pt = 0; G.GFX.pn = 0; const t0 = performance.now();
    for (let i = 0; i < 300; i++) { G.step(1, i % 40 < 20 ? ['right'] : ['left']); G.P.hp = 99999; }
    o.push(`${r} ${['classic', 'dynamic', 'dyn+shadows'][m]}${sync ? ' (gl.finish)' : ''}: presentWorld ${(G.GFX.pt / G.GFX.pn).toFixed(3)} ms avg over ${G.GFX.pn}, whole step ${((performance.now() - t0) / 300).toFixed(2)} ms, lights ${G.lx.LX.n}`);
  }
}
G.GFX.sync = false;
return o;
