// SA: frame cost in the grand rooms and vistas (dynamic lighting + shadows on)
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.items.tidebreath = 1; G.giveArmory();
const o = [];
for (const [r, x, y] of [['TV9', 56, 10], ['TV9', 90, 27], ['DB10', 51, 12], ['DB10', 60, 28], ['CM9', 52, 14], ['CM12', 20, 10], ['TV14', 12, 13], ['DB15', 20, 15], ['CM16', 9, 21]]) {
  G.tp(r, x, y); G.step(60); for (let i = 0; i < 5 && G.state !== 'play'; i++) G.step(1, [], ['pause']);
  G.SETTINGS.light = 2; G.GFX.sync = true; G.step(5); G.GFX.pt = 0; G.GFX.pn = 0; const t0 = performance.now();
  for (let i = 0; i < 240; i++) { G.step(1, i % 60 < 30 ? ['right'] : ['left']); G.P.hp = 99999; }
  o.push(`${r}@${x},${y}: present ${(G.GFX.pt / G.GFX.pn).toFixed(2)} ms, whole step ${((performance.now() - t0) / 240).toFixed(2)} ms, lights ${G.lx.LX.n}, props ${G.props.length}`);
}
G.GFX.sync = false; return o;
