await boot(); const o = [];
const pos = () => [G.room, Math.round(G.P.x/16*10)/10, Math.round(G.P.y/16*10)/10, G.P.state, Math.round(G.P.hp)].join(' ');
const T1 = [15*16+2, 17*16-2], T2 = [31*16+2, 33*16-2];
async function glide(dir, label) {
  // run + jump off the ledge, glide, hover in each thermal until high, then continue
  G.step(1, [dir === 1 ? 'right' : 'left'], ['jump']);
  const key = dir === 1 ? 'right' : 'left';
  let stage = 0, n = 0;
  const ths = dir === 1 ? [T1, T2] : [T2, T1];
  for (let i = 0; i < 900; i++) {
    const th = ths[stage];
    const inT = th && G.P.x > th[0] && G.P.x < th[1];
    if (inT && G.P.y > 70) { G.step(1, ['jump']); }
    else { if (inT) stage++; G.step(1, [key, 'jump']); }
    if (G.P.ground && i > 30) break;
    if (G.room !== 'DU1') break;
    if (i % 60 === 0) o.push(label + ' t' + i + ' ' + pos());
    if (i === 120 || i === 300) await snap(label + '_' + i);
  }
  o.push(label + ' end ' + pos());
}
// 1) without the Gale Cloak: best jump + double jump + air dash falls short
G.give({ items: { wings: 1, talon: 1 } });
G.tp('DU1', 7, 10); G.step(10);
G.step(1, ['right']); for (let i=0;i<10;i++) G.step(1,['right']);
G.step(1, ['right'], ['jump']); for (let i=0;i<22;i++) G.step(1,['right','jump']);
G.step(1, ['right'], ['jump']); for (let i=0;i<20;i++) G.step(1,['right','jump']);
G.step(1, ['right'], ['roll']); for (let i=0;i<120;i++) G.step(1,['right']);
o.push('nogale ' + pos() + ' safe=' + JSON.stringify(G.du.DU.safe));
await snap('g0_nogale');
G.step(60); o.push('nogale after ' + pos());
// 2) with the Gale Cloak: west -> east
G.grantTechniques(); G.P.hp = G.D.maxHp;
G.tp('DU1', 7, 10); G.step(10);
for (let i=0;i<8;i++) G.step(1,['right']);
await glide(1, 'east');
await snap('g1_east');
for (let i = 0; i < 60 && G.room === 'DU1'; i++) G.step(2, ['right']);
o.push('walk east ' + pos());
// 3) back: east ledge -> west
G.tp('DU1', 40, 10); G.step(10); G.P.face = -1;
for (let i=0;i<4;i++) G.step(1,['left']);
await glide(-1, 'west');
for (let i = 0; i < 60 && G.room === 'DU1'; i++) G.step(2, ['left']);
o.push('walk west ' + pos());
return o;
