await boot(); G.grantTechniques(); const o = [];
const B = () => G.boss;
const bs = () => B() ? `${B().state}/${B().atk||''}/${B().anim.tag}:${B().anim.i} x${Math.round(B().x)} y${Math.round(B().y)} hp${B().hp} ph${B().phase}` : 'none';
G.tp('DU6', 37, 11); G.step(10);
for (let i = 0; i < 40 && G.room === 'DU6'; i++) { G.step(2, ['left']); if (G.state === 'cut') break; }
o.push('trigger ' + G.state + ' ' + bs());
for (let i = 0; i < 10 && G.state === 'cut'; i++) { G.step(30); if (i === 1) await snap('s_cut'); }
o.push('after cut ' + G.state + ' ' + bs());
const seen = {}; let hits = 0, last = G.P.hp;
for (let ph = 1; ph <= 2; ph++) {
  if (ph === 2) { B().hp = Math.round(B().maxHp * 0.49); for (let i = 0; i < 40; i++) { G.step(15); if (G.state !== 'cut' && B().phase === 2) break; } o.push('p2 ' + bs()); }
  for (let i = 0; i < 1800; i++) {
    G.step(1); if (G.P.hp < last) hits++; G.P.hp = G.D.maxHp; last = G.P.hp;
    const b = B(), k = b.state === 'attack' ? b.atk : ['under', 'rising', 'charge', 'crash'].includes(b.state) ? b.state : null;
    if (k) { seen[ph + k] = (seen[ph + k] || 0) + 1; if (seen[ph + k] === 12) await snap(`s${ph}_${k}`); }
    if (b.x < b.L - 1 || b.x > b.R + 1 || Math.abs(b.y - b.floor) > 0.5) o.push('OOB ' + bs());
  }
}
o.push('moves ' + JSON.stringify(seen) + ' hits ' + hits + ' swarm=' + G.enemies.filter(e => e.alive && e.type === 'du_scarab').length);
B().hp = 5; B().hit({ dmg: 50, poise: 0, dir: 1, kind: 'light', x: B().x, y: B().y - 30 });
for (let i = 0; i < 10; i++) { G.step(30); if (i === 1) await snap('s_death'); }
o.push('dead ' + bs() + ' flag=' + G.SAVE.flags['boss:scarab'] + ' fogs=' + G.props.filter(p => p.type === 'fog' && p.on()).length);
return o;
