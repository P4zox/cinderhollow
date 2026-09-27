// LX: worst case — 60 shadowed lights of r=90 on screen (48 used), 300 frames, per mode, with gl.finish in the probe
await boot(); G.SETTINGS.god = 1;
G.tp('C2', 24, 10); G.step(60);
for (let i = 0; i < 60; i++) { const x = G.P.x - 180 + (i % 12) * 32, y = G.P.y - 150 + Math.floor(i / 12) * 36; G.props.push({ type: 'lxtest', x, y, anim: { update() {} }, update() { G.lx.addLight(x, y, 90, i % 2 ? '255,180,100' : '120,160,255', 0.5, { flicker: true }); }, draw() {} }); }
const o = [];
for (const m of [0, 1, 2]) { G.SETTINGS.light = m; G.GFX.sync = true; G.step(5); G.GFX.pt = 0; G.GFX.pn = 0;
  for (let i = 0; i < 300; i++) G.step(1);
  o.push(`${['classic', 'dynamic', 'dyn+shadows'][m]}: presentWorld ${(G.GFX.pt / G.GFX.pn).toFixed(3)} ms (gl.finish), lights used ${G.lx.LX.n}/${G.lx.LX.NL}`); await snap('perf48_' + m); }
G.GFX.sync = false; return o;
