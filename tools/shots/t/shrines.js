await boot();
const out = {};
for (const [r, x, y] of [['TV3', 20, 10], ['TV7', 20, 9]]) {
  G.tp(r, x - 1, y); G.enemies.length = 0; G.step(10);
  const sh = G.props.find(p => p.type === 'shrine');
  out[r] = sh ? sh.name : 'none';
  G.step(2, [], ['interact']); for (let i = 0; i < 120; i++) { G.step(1); if (G.state !== 'play') G.step(1, [], ['pause']); }
  out[r + '_lit'] = G.SAVE.shrines.includes(r);
  await snap('shrine_' + r);
}
return out;
