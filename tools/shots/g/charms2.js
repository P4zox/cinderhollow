// agent G (Expansion 2): charm effects
await boot();
const X = window.__gear3;
const CH = ['c_antler','c_moss','c_gill','c_pearl','c_bloodvial','c_countess','c_crown','c_court','c_scarab','c_sun','c_star','c_orrery','c_hack','c_neon','c_lastflame'];
const log = [];
const setup = (eq) => { G.give({ charms: CH, charmsEq: eq, charmSlots: 6 }); G.tp('R2', 5, 10); G.step(2); G.enemies.forEach((e, i) => { e.x = 128 + i * 24; e.y = 176; e.hp = e.maxHp = 5000; e.aggro = false; e.cool = 5; e.state = 'idle'; }); G.P.fp = 999; G.P.hp = G.D.maxHp; G.P.face = 1; };
// bloodvial + antler: heavy attack heals and roots
setup(['c_bloodvial', 'c_antler']); G.P.hp = 100; G.step(1, [], ['heavy']); G.step(40);
log.push('bloodvial hp 100->' + (G.P.hp | 0) + ' root ' + G.enemies.map(e => (e.gStun || 0).toFixed(1)).join(','));
// moss
setup(['c_moss']); G.enemies.forEach(e => e.x = 600); G.P.hp = 100; G.step(360); log.push('moss 6s hp 100->' + (G.P.hp | 0));
// pearl
setup(['c_pearl']); G.enemies.forEach(e => e.x = 600); G.P.fp = 10; G.P.hp = 100; G.step(1, [], ['heal']); G.step(60); log.push('pearl fp 10->' + (G.P.fp | 0) + ' hp ' + (G.P.hp | 0));
// star orbit
setup(['c_star']); for (let i = 0; i < 6; i++) { G.step(20); if (i == 2) await snap('star'); } log.push('star dmg ' + G.enemies.map(e => 5000 - e.hp).join(','));
// sun: cast ash bolt
G.give({ spellsOwned: ['ash_bolt'], spellsEq: ['ash_bolt'], spell: 'ash_bolt' });
setup(['c_sun']); G.step(1, [], ['cast']); G.step(30); await snap('sun'); G.step(30); log.push('sun dmg ' + G.enemies.map(e => 5000 - e.hp).join(','));
// orrery: art cost
G.give({ arts: ['reap'], art: 'reap' }); setup(['c_orrery']); G.P.fp = 100; G.step(1, [], ['art']); G.step(3); log.push('orrery fp 100->' + G.P.fp + ' count ' + G.P.artCount + ' state ' + G.P.state);
// last flame
setup(['c_lastflame']); G.P.hp = 5; const s = G.enemies.find(e => e.type === 'hollow_soldier'); s.x = G.P.x + 26; s.aggro = true; s.cool = 0; s.face = -1;
for (let i = 0; i < 120; i++) G.step(1); log.push('lastflame hp ' + (G.P.hp | 0) + ' state ' + G.P.state + ' used ' + X.S.lastFlame);
// scarab + neon: roll through the soldier's attack (try a few timings)
for (const off of [34, 38, 42, 46]) {
  setup(['c_scarab', 'c_neon']); const s2 = G.enemies.find(e => e.type === 'hollow_soldier'); s2.x = G.P.x + 26; s2.aggro = true; s2.cool = 0; s2.face = -1;
  let n = -1; const hp0 = G.P.hp;
  for (let i = 0; i < 90; i++) { if (n < 0 && s2.state === 'attack') n = 0; if (n >= 0) n++; if (n === off) G.step(1, ['right'], ['roll']); else G.step(1); }
  log.push('scarab/neon off ' + off + ' php ' + (hp0 - G.P.hp) + ' soldier stun ' + (s2.gStun || 0).toFixed(2) + ' hp ' + s2.hp);
}
// court + crown: kill two weak enemies
setup(['c_court', 'c_crown']); G.enemies.forEach(e => { e.hp = 5; }); const l0 = G.D.light; G.step(1, [], ['attack']); G.step(30); G.step(1, [], ['attack']); G.step(30);
log.push('court light ' + l0.toFixed(1) + '->' + G.D.light.toFixed(1) + ' stacks ' + X.S.court.length + ' alive ' + G.enemies.filter(e => e.alive).length);
await snap('court');
return log;
