await boot();
const out = [];
G.SAVE.flags['cut:saint0'] = 1; G.SAVE.flags['cutp3:saint0'] = 1; G.SAVE.flags['cutp2:saint0'] = 1;
G.tp('NH7', 10, 10); G.step(20);
const B = G.boss; B.activate(); G.step(10); G.nhGod(true);
out.push(['activated (intro seen)', B.state, B.active]);
const bad = [];
for (const ph of [1, 2, 3]) {
  if (ph === 3) G.nhEnterCyber(B);
  for (const px of [3 * 16 + 10, 38 * 16 + 4]) {
    for (const m of ['orbs', 'volley', 'limbo', 'grid', 'gaze', 'burn', 'spiral', 'dive', 'delete', 'lighthouse', 'rain']) {
      B.phase = ph; B.state = 'idle'; B.cool = 99; B.cancelMove(); B.cds = {}; G.P.x = px; G.P.y = 11 * 16; G.P.vx = 0;
      B.startMove(m);
      for (let k = 0; k < 420 && B.state === 'attack'; k++) { G.step(1); G.P.x = px; if (B.x < B.L - 0.5 || B.x > B.R + 0.5 || B.y < 40 || B.y > B.floor - 23.5) bad.push([ph, m, Math.round(B.x), Math.round(B.y)]); }
    }
  }
}
out.push(['clamp/bounds violations', bad.length, bad.slice(0, 5), 'L..R', B.L, B.R]);
// the eye never gets stuck in a state
out.push(['state after sweep', B.state]);
// deleted floor never softlocks
G.nhExitCyber(); B.phase = 2; B.state = 'idle'; B.cool = 99; B.cancelMove();
G.P.x = 20 * 16 + 8; G.P.y = 176; G.nhDeleteFloor(B);
let maxY = 0; for (let k = 0; k < 420; k++) { G.step(1, k % 60 < 30 ? [] : ['left']); maxY = Math.max(maxY, G.P.y); }
for (let k = 0; k < 400; k++) G.step(1, ['right']);
out.push(['deletion: max y', Math.round(maxY), 'all restored', G.NHR.dels.every(d => d.st === 'solid'), 'player y', Math.round(G.P.y)]);
// player death mid-fight -> Vestibule shrine, arena normal, boss full
G.nhGod(false); G.nhEnterCyber(B); B.phase = 3; G.P.hp = 1; B.state = 'idle'; B.cool = 0;
G.SAVE.shrines.push('NH6'); G.SAVE.shrine = 'NH6';
for (let k = 0; k < 1500 && G.state !== 'dead'; k++) { G.step(1); G.P.hp = Math.min(G.P.hp, 1); }
for (let k = 0; k < 400 && G.room !== 'NH6'; k++) G.step(2);
out.push(['respawn', G.state, G.room]);
for (let k = 0; k < 200 && G.room !== 'NH7'; k++) G.step(3, ['right']);
const B2 = G.boss;
out.push(['back in', G.room, G.nhRoom().def.biome, B2.hp === B2.maxHp, B2.phase, 'fog', G.NHR.fogs.length]);
// kill: rewards, banner, fog lifts, exit cyber
G.nhGod(true); B2.activate(); G.step(30); B2.phase = 3; G.nhEnterCyber(B2);
B2.hp = 1; B2.hit({ dmg: 99, poise: 0, dir: 1, x: B2.x, y: B2.y, crit: true });
for (let k = 0; k < 200; k++) G.step(2);
out.push(['dead', B2.state, G.SAVE.flags['boss:saint0'], G.nhRoom().def.biome, 'fog on', G.NHR.fogs.map(f => f.on()).join(','), 'items', ['w:saint_lance', 'sp:null_field', 'c_neon'].map(i => i.startsWith('w:') ? G.SAVE.weapons[i.slice(2)] !== undefined : i.startsWith('sp:') ? G.SAVE.spellsOwned.includes(i.slice(3)) : G.SAVE.charms.includes(i)).join(',')]);
// walk out the way you came
for (let k = 0; k < 300 && G.room === 'NH7'; k++) G.step(3, ['left']);
out.push(['exit', G.room]);
return out;
