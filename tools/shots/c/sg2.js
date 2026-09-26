await boot();
G.give({ items: { emberdash: 1 } });
G.SAVE.flags['cut:sanguine'] = 1;
G.tp('CM7', 6, 14); G.step(30, ['right']);
const B = G.boss, P = G.P, log = [];
for (let i = 0; i < 60 && !B.active; i++) G.step(5);
G.step(60);
B.hp = Math.floor(B.maxHp * 0.5) - 5; B.state = 'idle'; B.cool = 0.1;
for (let i = 0; i < 400 && B.phase !== 2; i++) G.step(1);
log.push({ phase: B.phase, state: G.state, st: B.state });
for (let i = 0; i < 40; i++) { G.step(10); if (G.state === 'cut') continue; if (i % 4 === 0) await snap('p2_a' + String(i).padStart(2, '0')); }
log.push({ after: B.state, flood: window.__cm.CM.flood && window.__cm.CM.flood.k, sheet: B.sh.name });
// forced aerial tests with edge positions: pin the player at each wall
const res = {};
for (const [name, px] of [['left', 40], ['right', 660], ['mid', 340]]) {
  P.x = px; P.y = 240; P.hp = G.D.maxHp; B.state = 'idle'; B.alt = 0; B.cool = 99; B.skyCd = 0;
  window.__cm.force('fly'); let minX = 1e9, maxX = -1e9, maxAlt = 0, hp0 = P.hp;
  for (let k = 0; k < 420; k++) { G.step(1); minX = Math.min(minX, B.x); maxX = Math.max(maxX, B.x); maxAlt = Math.max(maxAlt, B.alt); P.x = px; if (k % 70 === 20 && name === 'mid') await snap('p2_fly_' + String(k).padStart(3, '0')); }
  res[name] = { minX: Math.round(minX), maxX: Math.round(maxX), maxAlt: Math.round(maxAlt), L: B.L, R: B.R, dmg: Math.round(hp0 - P.hp), st: B.state };
}
log.push(res);
// batport / lunge at the edges
const e2 = {};
for (const [name, px, bx] of [['L', 40, 200], ['R', 660, 500]]) {
  for (const m of ['batport', 'lunge', 'dance']) { P.x = px; B.x = bx; B.alt = 0; B.state = 'idle'; B.cool = 99; window.__cm.force(m); let mn = 1e9, mx = -1e9; for (let k = 0; k < 200; k++) { G.step(1); P.x = px; mn = Math.min(mn, B.x); mx = Math.max(mx, B.x); } e2[name + m] = [Math.round(mn), Math.round(mx)]; }
}
log.push(e2);
// tide
window.__cm.CM.waves = []; B.state = 'idle'; B.cool = 99; B.tideT = 0; P.hp = G.D.maxHp;
for (let k = 0; k < 150; k++) { G.step(1); if (k % 30 === 10) await snap('p2_tide_' + String(k).padStart(3, '0')); }
log.push({ tideDmg: Math.round(G.D.maxHp - P.hp) });
// death
B.hp = 1; B.state = 'idle'; P.x = B.x - 40; G.P.face = 1;
for (let k = 0; k < 20 && B.alive; k++) { G.step(2, [], ['attack']); G.step(20); }
log.push({ alive: B.alive, flag: G.SAVE.flags['boss:sanguine'] });
G.step(400);
await snap('p2_dead');
log.push({ weapons: Object.keys(G.SAVE.weapons), charms: G.SAVE.charms, spells: G.SAVE.spellsOwned, fog: G.props.filter(p => p.type === 'fog').map(p => p.on()) });
return log;
