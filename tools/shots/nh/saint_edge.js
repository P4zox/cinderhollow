await boot();
const out = [];
G.SAVE.flags['cut:saint0'] = 1; G.SAVE.flags['cutp3:saint0'] = 1;
G.tp('NH7', 10, 10); G.step(20);
const B = G.boss; B.activate(); G.step(10); G.nhGod(true);
const bad = [];
for (const ph of [1, 2, 3]) {
  if (ph === 3) { B.phase = 3; G.nhEnterCyber(B); }
  else B.phase = ph;
  for (const px of [3 * 16 + 12, 38 * 16 + 4]) {
    for (const m of ['thrust', 'sweep', 'wings', 'orbital', 'delete', 'firewall', 'rain', 'ring', 'blink', 'glide']) {
      G.P.x = px; G.P.y = 11 * 16; G.P.vx = 0;
      B.state = 'idle'; B.cool = 9; B.cds = {}; B.begin(m);
      for (let k = 0; k < 150; k++) { G.step(1); G.P.x = px; if (B.x < B.L - 0.5 || B.x > B.R + 0.5 || B.y > B.floor - 1) bad.push([ph, m, Math.round(B.x), Math.round(B.y)]); }
    }
  }
}
out.push(['clamp/floor violations', bad.length, bad.slice(0, 5), B.L, B.R, B.floor]);
// deleted floor: stand on a tile that gets deleted -> must bounce, never be stuck below the floor; tiles come back
G.nhGod(true);
G.P.x = 20 * 16 + 8; G.P.y = 11 * 16; B.state = 'idle'; B.cool = 99; B.q = [];
G.nhDeleteFloor(B);
let minY = 999, maxY = 0, grounded = 0;
for (let k = 0; k < 360; k++) { G.step(1, k % 60 < 30 ? [] : ['left']); maxY = Math.max(maxY, G.P.y); if (G.P.ground && G.P.y <= 11 * 16 + 0.5) grounded++; }
const dels = G.NHR.dels.filter(d => d.st !== 'solid').length;
out.push(['after deletion', 'maxY', Math.round(maxY), 'floor', 176, 'grounded frames', grounded, 'tiles not yet restored', dels, 'player', Math.round(G.P.x), Math.round(G.P.y)]);
for (let k = 0; k < 400; k++) G.step(1, ['right']);
out.push(['all restored', G.NHR.dels.every(d => d.st === 'solid'), Math.round(G.P.y)]);
// player death mid phase 3 -> room is normal again on respawn, boss full hp, fog on
G.nhGod(false); G.P.hp = 1; B.state = 'idle'; B.cool = 0;
G.SAVE.shrines.push('NH6'); G.SAVE.shrine = 'NH6';
for (let k = 0; k < 900 && G.state !== 'dead'; k++) { G.step(1); G.P.hp = Math.min(G.P.hp, 1); }
for (let k = 0; k < 400 && G.room !== 'NH6'; k++) G.step(2);
out.push(['respawn', G.state, G.room]);
for (let k = 0; k < 200 && G.room !== 'NH7'; k++) G.step(3, ['right']);
out.push(['back in', G.room, G.nhRoom().def.biome, G.boss && G.boss.hp === G.boss.maxHp, G.boss && G.boss.phase]);
return out;
