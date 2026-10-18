// Shading phase 1: debug views of the lighting buffers (LX.dbg 2 = baked AO, 3 = summed light, 0 = final). window.__dbgD / __dbgSpots override.
await boot(); G.SETTINGS.god = 1; const E = G.sk.ev;
const out = [];
for (const [n, r, x, y] of (window.__dbgSpots || [['cat', 'C10', 26, 10], ['ram', 'R5', 70, 12]])) {
  G.tp(r, x, y); for (let i = 0; i < 200; i++) { G.step(1); G.enemies.length = 0; if (G.state !== 'play') G.step(1, [], ['pause']); }
  for (const d of (window.__dbgD || [0, 2, 3, 7])) { E(`LX.dbg = ${d}`); E(`vctx.fillStyle = '#050407'; vctx.fillRect(0, 0, view.width, view.height); renderWorld(); presentWorld();`); await snap(`${n}_dbg${d}`); }
  E('LX.dbg = 0');
}
return out;
