// Colossus: how many leg hits (and seconds of mashing) each weapon needs for the 1st and 2nd topple
await new Promise(r => setTimeout(r, 300));
const T = G.trn, E = G.sk.ev, out = [];
const errs = []; window.addEventListener('error', e => errs.push(e.message));
T.start(); G.step(10);
for (const w of ['longsword', 'dagger', 'twinfangs', 'greatsword', 'katana']) {
  E(`SAVE.weapon = '${w}'; SAVE.weapons['${w}'] = 3`); G.give({}); E('refreshDerived(false)');
  T.summon('colossus'); G.step(5); const B = G.boss; B.active = true; B.state = 'idle';
  const leg = B.parts.find(p => p.name === 'knee_n');
  const res = [];
  for (const topple of [1, 2]) {
    let hits = 0; const t0 = B.topples;
    while (B.topples === t0 && hits < 200) {
      const A = E(`ATK[moveset().combo[${hits % 3}]]`) || { poise: 12, mult: 1 };
      const po = A.poise * (G.D.W.poise || 1);
      B.chipT = -9; B.state = 'idle';
      leg.hit({ dmg: G.D.light, poise: po, dir: 1, kind: 'light', x: B.x, y: B.floor - 20, melee: true });
      hits++;
    }
    res.push(`topple ${topple}: ${hits} hits`);
    B.state = 'idle'; B.t = 0;
  }
  out.push(`${w.padEnd(11)} ${res.join(', ')}  (meter now ${Math.round(B.toppleMax())})`);
  T.clear(); G.step(3);
}
out.push('errors ' + JSON.stringify(errs));
return out;
