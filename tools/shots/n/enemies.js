// Enemies: each type engages, lands hits, the ringer's toll stuns, the noble parries, all can be killed.
await boot(); G.give({ stats: { vig: 60, str: 30, dex: 30 } }); window.__nvLog = [];
const out = [];
const one = async (room, tx, ty, type, n = 700) => {
  G.tp(room, tx, ty); G.step(5);
  const keep = G.enemies.filter(e => e.type === type).sort((a, b) => Math.abs(a.x - G.P.x) - Math.abs(b.x - G.P.x))[0];
  for (const e of G.enemies) if (e !== keep) { e.hp = 0; e.state = 'dead'; e.gone = true; }
  if (!keep) return `${type}: none`;
  const states = {}; let stunned = 0, parries = 0;
  for (let i = 0; i < n; i++) {
    const d = keep.x < G.P.x ? 'left' : 'right', far = Math.abs(keep.x - G.P.x) > 40;
    G.step(1, far && i > 250 ? [d] : [], !far && i > 250 && i % 12 === 0 ? ['attack'] : []);
    G.P.hp = 9999;
    states[keep.state + (keep.state === 'attack' ? ':' + keep.atk : '')] = 1;
    if (G.NVR.stunT > 0) stunned++;
    if (keep.state === 'parry') parries++;
    if (i === 180) await snap(`en_${type}`);
    if (!keep.alive) break;
  }
  for (let i = 0; i < 200 && keep.alive; i++) { keep.hit({ dmg: 60, poise: 5, dir: 1, kind: 'heavy', x: keep.x, y: keep.y - 10, melee: true }); G.step(3); G.P.hp = 9999; }
  for (let i = 0; i < 60; i++) G.step(2);
  const hits = window.__nvLog.splice(0).filter(h => h[1].startsWith(type) || h[1].includes('undefined') || true).length;
  return `${type}: states ${Object.keys(states).join(',')} | hits on player ${hits} | stun frames ${stunned} | parries ${parries} | dead ${!keep.alive}`;
};
out.push(await one('NV4', 14, 16, 'nv_noble'));
out.push(await one('NV4', 62, 16, 'nv_ringer'));
out.push(await one('NV2', 22, 10, 'nv_hound'));
G.tp('NV4', 14, 16); G.step(5); const nb = G.enemies.find(e => e.type === 'nv_noble'); let pr = 0;
for (let k = 0; k < 40; k++) { nb.state = 'idle'; nb.aggro = true; nb.face = G.P.x < nb.x ? -1 : 1; nb.hp = nb.maxHp; const hp = nb.hp; nb.hit({ dmg: 10, poise: 1, dir: -nb.face, kind: 'light', x: nb.x, y: nb.y - 20, melee: true }); if (nb.hp === hp) pr++; G.step(1); }
out.push(`noble parried ${pr}/40 frontal light blows`);
return out;
