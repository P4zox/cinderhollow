await boot(); G.grantTechniques(); const o = [];
const B = () => G.boss;
const bs = () => B() ? `${B().state}/${B().atk||''}/${B().anim.tag}:${B().anim.i} x${Math.round(B().x)} y${Math.round(B().y)} hp${B().hp} ph${B().phase}` : 'none';
G.tp('DU8', 20, 14); G.step(10);
o.push('start ' + G.state + ' ' + bs());
// the intro cutscene
for (let i = 0; i < 12; i++) { G.step(30); if (i % 3 === 0) await snap('cut_' + i); if (G.state !== 'cut') break; }
for (let i = 0; i < 60 && G.state === 'cut'; i++) G.step(30);
o.push('after cut ' + G.state + ' ' + bs() + ' flag=' + G.SAVE.flags['cut:pharaoh']);
// phase 1: stand and watch, count hits
const seen = {}; let hits = 0, lastHp = G.P.hp;
for (let i = 0; i < 1500; i++) {
  G.step(1);
  if (G.P.hp < lastHp) hits++;
  G.P.hp = G.D.maxHp; lastHp = G.P.hp;
  const b = B(); if (b && b.state === 'attack') { const k = b.atk; if (!seen[k]) { seen[k] = 0; } seen[k]++; if (seen[k] === 25) await snap('p1_' + k); }
  if (b && (b.x < b.L - 1 || b.x > b.R + 1 || Math.abs(b.y - b.floor) > 0.5)) o.push('OUT OF BOUNDS ' + bs());
  if (i % 300 === 0) o.push('p1 t' + i + ' ' + bs());
}
o.push('p1 attacks ' + JSON.stringify(seen) + ' hits=' + hits);
// phase 2
B().hp = Math.round(B().maxHp * 0.49); G.step(5);
for (let i = 0; i < 40 && G.state === 'cut'; i++) { G.step(15); if (i === 1) await snap('p2_cut'); }
o.push('p2 ' + G.state + ' ' + bs() + ' storm=' + JSON.stringify(G.du.DU.storm && { k: G.du.DU.storm.k, boss: G.du.DU.storm.boss }));
const seen2 = {}; hits = 0; lastHp = G.P.hp;
for (let i = 0; i < 2400; i++) {
  G.step(1);
  if (G.P.hp < lastHp) hits++;
  G.P.hp = G.D.maxHp; lastHp = G.P.hp;
  const b = B(); const k = b.state === 'attack' ? b.atk : b.state === 'buried' ? 'buried' : null;
  if (k) { seen2[k] = (seen2[k] || 0) + 1; if (seen2[k] === 20) await snap('p2_' + k); }
  if (b && (b.x < b.L - 1 || b.x > b.R + 1 || Math.abs(b.y - b.floor) > 0.5)) o.push('OUT OF BOUNDS ' + bs());
  if (i % 400 === 0) o.push('p2 t' + i + ' ' + bs() + ' zones=' + G.du.DU.zones.length);
}
o.push('p2 attacks ' + JSON.stringify(seen2) + ' hits=' + hits);
await snap('p2_late');
// kill it
B().hp = 5; B().hit({ dmg: 50, poise: 0, dir: 1, kind: 'light', x: B().x, y: B().y - 50 });
for (let i = 0; i < 20; i++) { G.step(30); if (i === 2) await snap('death'); }
o.push('dead ' + bs() + ' flag=' + G.SAVE.flags['boss:pharaoh'] + ' fogOn=' + G.props.filter(p => p.type === 'fog' && p.on()).length + ' storm=' + (G.du.DU.storm && G.du.DU.storm.k.toFixed(2)));
await snap('after');
return o;
