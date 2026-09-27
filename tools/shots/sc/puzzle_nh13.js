// NH13 Firewall: throw terminals A and C (every barrier open at once), then open the vault chest
await boot(); G.grantTechniques();
G.tp('NH13', 34, 16); G.step(30); G.xs.clean();
const K = id => G.xs.KIT.byId[id], out = [];
const st = () => `levers ${['A','B','C','D'].map(i => K(i).active ? 1 : 0).join('')} gates ${['G1','G2','G3','G4'].map(i => K(i).on ? 'o' : 'x').join('')}`;
out.push('start ' + st());
K('B').interact(); G.step(20); out.push('B ' + st());
K('D').interact(); G.step(20); out.push('B+D ' + st());
K('B').interact(); G.step(20); K('D').interact(); G.step(20); out.push('reset ' + st());
for (let i = 0; i < 6; i++) { K('A').interact(); G.step(20); }   // fruitless flipping: the hint toast
out.push('hint ' + G.xs.XS.fireHint);
K('A').interact(); G.step(20); K('C').interact(); G.step(40); out.push('A+C ' + st());
await snap('p13_a');
G.tp('NH13', 5, 16); G.step(20);
for (let i = 0; i < 200 && G.P.x / 16 > 3.6; i++) G.step(1, ['left']);
G.step(1, [], ['interact']); G.step(200); await new Promise(r => setTimeout(r, 700)); G.step(2);
out.push('chest ' + !!G.SAVE.flags['chest:NH13:0'] + ' inv ' + JSON.stringify(G.SAVE.inv));
return out;
