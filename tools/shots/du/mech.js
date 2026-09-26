await boot(); G.grantTechniques(); const o = [];
const pos = () => [G.room, Math.round(G.P.x/16*10)/10, Math.round(G.P.y/16*10)/10, G.P.state, Math.round(G.P.hp), 'sand=' + Math.round(G.P.duSand ?? -1)].join(' ');
// quicksand pit DU2 (cols 29-33, rows 17-18): stand in it, sink, then jump out
for (const e of []) {}
G.tp('DU2', 31, 16); for (const e of G.enemies) { e.hp = 0; e.state = 'dead'; }
G.step(20); o.push('in pit ' + pos());
G.step(90); o.push('after 1.5s ' + pos()); await snap('qs_sink');
G.step(1, [], ['jump']); for (let i = 0; i < 12; i++) G.step(1, ['jump', 'right']); for (let i = 0; i < 40; i++) G.step(1, ['right']);
o.push('jumped ' + pos());
// idle in the pit for 6 s: damage ticks but never a permanent trap
G.P.hp = G.D.maxHp; G.tp('DU2', 31, 16); G.step(360); o.push('6s idle ' + pos());
G.step(1, [], ['jump']); for (let i = 0; i < 12; i++) G.step(1, ['jump', 'left']); for (let i = 0; i < 40; i++) G.step(1, ['left']); o.push('escaped ' + pos());
// DU3 basin: slide down the dune into the quicksand, jump out the other side
G.P.hp = G.D.maxHp; G.tp('DU3', 22, 12); G.step(5);
for (let i = 0; i < 40; i++) G.step(1, ['right']); o.push('slide ' + pos() + ' vx=' + Math.round(G.P.vx)); await snap('slide');
// the storm
G.tp('DU3', 5, 16); G.du.storm(true); G.step(60); o.push('storm push x ' + pos()); await snap('storm');
// altars in DU5: stand under one for 4 s
G.P.hp = G.D.maxHp; G.tp('DU5', 16, 11); for (const e of G.enemies) { e.hp = 0; e.state = 'dead'; } const h0 = G.P.hp; G.step(240); o.push('altar dmg ' + (h0 - G.P.hp));
for (let i = 0; i < 200; i++) { G.step(1); const a = G.du.DU.altars[0]; if (a.st === 'fire') { await snap('altar'); break; } }
// enemies: let each fight a god-mode player
for (const [room, x, y, type] of [['DU2', 27, 16, 'du_priest'], ['DU3', 10, 16, 'du_scarab'], ['DU3', 54, 14, 'du_jackal']]) {
  G.tp(room, x, y); let hits = 0, last = G.P.hp, st = {};
  for (let i = 0; i < 600; i++) { G.step(1); if (G.P.hp < last) hits++; G.P.hp = G.D.maxHp; last = G.P.hp;
    for (const e of G.enemies) if (e.type === type && e.alive) { st[e.state + ':' + e.anim.tag] = 1; if (e.state === 'attack' && !st['snap' + e.atk]) { st['snap' + e.atk] = 1; await snap('en_' + type + '_' + e.atk); } } }
  const e = G.enemies.find(e => e.type === type && e.alive);
  o.push(type + ' hits=' + hits + ' states=' + Object.keys(st).filter(k => !k.startsWith('snap')).join(','));
  if (e) { e.face = -1; e.state = 'idle'; e.hit({ dmg: 9999, poise: 0, dir: 1, kind: 'light', x: e.x, y: e.y - 10 }); G.step(8); await snap('en_' + type + '_death'); G.step(60); o.push(type + ' dead=' + !e.alive); }
}
return o;
