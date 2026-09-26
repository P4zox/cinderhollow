await boot(); G.grantTechniques(); const o = [];
const pos = () => [G.room, Math.round(G.P.x/16*10)/10, Math.round(G.P.y/16*10)/10, G.P.state, Math.round(G.P.hp)].join(' ');
// D3 -> DU1 through the east wall
G.tp('D3', 44, 10); G.step(20); o.push('d3 ' + pos());
for (let i = 0; i < 40 && G.room === 'D3'; i++) G.step(3, ['right']);
G.step(10); o.push('enter ' + pos()); await snap('00_du1_entry');
for (const [id, x, y] of [['DU1', 4, 10], ['DU1', 44, 10], ['DU2', 4, 10], ['DU2', 30, 16], ['DU3', 5, 16], ['DU3', 22, 12], ['DU3', 58, 14], ['DU4', 3, 14], ['DU4', 10, 35],
  ['DU5', 66, 11], ['DU5', 36, 8], ['DU6', 36, 11], ['DU7', 30, 17], ['DU7', 3, 17], ['DU8', 8, 14]]) {
  G.tp(id, x, y); G.step(30); o.push(id + ' ' + pos() + ' en=' + G.enemies.filter(e=>e.alive).length + (G.boss ? ' boss=' + G.boss.kind + ':' + G.boss.state : ''));
  await snap('r_' + id + '_' + x);
}
return o;
