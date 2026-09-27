// SF15 The Lens Array: solve by turning the lenses (strikes), check the three bars and the reliquary chest
await boot(); G.grantTechniques();
G.tp('SF15', 30, 21); G.step(30); G.xs.clean();
const K = id => G.xs.KIT.byId[id], out = [];
const turn = (id, n) => { for (let i = 0; i < n; i++) { K(id).interact(); G.step(20); } };
const st = () => `rot L1=${K('L1').rot} L2=${K('L2').rot} L3=${K('L3').rot} L4=${K('L4').rot} s=${['s1','s2','s3'].map(i => K(i).active ? 1 : 0).join('')} gates=${['b1','b2','b3'].map(i => G.xs.KIT.byId[i].on ? 'o' : 'x').join('')}`;
out.push('start ' + st());
turn('L1', 1); out.push('after L1x1 ' + st());
await snap('p15_a');
turn('L1', 2); turn('L3', 3); out.push('after S2 route ' + st());
await snap('p15_b');
turn('L1', 1); turn('L2', 3); turn('L4', 3); out.push('after S3 route ' + st());
G.step(60); await snap('p15_c');
// walk into the reliquary and open the chest
G.tp('SF15', 9, 21); G.step(20);
for (let i = 0; i < 200 && G.P.x / 16 > 2.6; i++) G.step(1, ['left']);
G.step(1, [], ['interact']); G.step(120); await new Promise(r => setTimeout(r, 700)); G.step(2);
out.push('chest opened ' + !!G.SAVE.flags['chest:SF15:0'] + ' emberstones ' + (G.SAVE.inv.emberstone || 0));
// persistence: leave and come back
G.tp('SF12', 20, 17); G.step(10); G.tp('SF15', 30, 21); G.step(10); out.push('after re-entry ' + st());
return out;
