// sit on every SC vista bench (camera eases out, lore page), snapshot
await boot(); G.SETTINGS.god = 1; const out = [];
for (const [r, x, y] of [['SF16', 5, 10], ['SF17', 8, 11], ['NH15', 8, 12], ['E6', 10, 10], ['H3', 21, 10]]) {
  G.tp(r, x, y); G.step(60); G.xs.clean(); G.step(1, [], ['interact']); G.step(150);
  const S = window.__sys.SYS; out.push(`${r} seated ${!!S.vista} reader ${!!S.reader} enemies ${G.enemies.length}`);
  await snap('v_' + r);
  if (S.reader) { G.step(1, [], ['interact']); G.step(10); }
  G.step(1, [], ['jump']); G.step(30);
}
out.push('vistas logged ' + Object.keys(window.__sys.x3().vistas || {}).length);
return out;
