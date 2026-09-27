await boot(); G.SAVE.items.talon = 1; G.tp('R11', 19, 5); G.step(400); const out = [];
for (const [r, x, y] of [['R11', 19, 5], ['K11', 11, 16]]) {
  G.tp(r, x, y); G.step(30); G.step(1, [], ['interact']); G.step(150);
  const S = window.__sys; out.push(r + ' seated: ' + !!(S && S.SYS.vista) + ' vistas ' + JSON.stringify(Object.keys(S.x3().vistas || {})) + ' lore ' + JSON.stringify(Object.keys(S.x3().lore || {})));
  await snap('vista_' + r);
  G.step(1, [], ['jump']); G.step(60);
}
return out;
