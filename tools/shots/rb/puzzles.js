await boot(); G.SETTINGS.god = true; G.SAVE.seenAreas = { mire: 1, archives: 1, hoarfrost: 1 };
G.give({ items: { talon: 1, hook: 1, emberdash: 1 } });
const S = window.__sys, RB = window.__rb, log = [];
const K = () => RB.kit;
const lvl = () => { const o = K().byId.lvl; return o ? (o.sy / 16).toFixed(1) : '-'; };
// ---------------- M12 Valve House
G.tp('M12', 4, 5); G.step(60);
log.push(`M12 start: water ${lvl()} gate ${K().byId.gT.on} vHigh ${K().byId.vHigh.active}`);
await snap('p_m12_0');
G.step(1, [], ['interact']); G.step(360);
log.push(`M12 after the high valve: water ${lvl()} gate ${K().byId.gT.on}`);
await snap('p_m12_1');
G.tp('M12', 11, 22); G.step(30); G.step(1, [], ['interact']); G.step(360);
log.push(`M12 after the low valve: water ${lvl()} gate ${K().byId.gT.on} player y ${(G.P.y / 16).toFixed(1)} state ${G.P.state}`);
await snap('p_m12_2');
// float up to the shelf / the pillar: the chest is reachable floating
G.tp('M12', 20, 6); G.step(90); log.push(`M12 floating at ${(G.P.x / 16).toFixed(1)},${(G.P.y / 16).toFixed(1)} ${G.P.state}`);
// ---------------- A13 Cipher Wall: three wrong tries (hint), then the right order
G.tp('A13', 20, 14); G.step(60);
const strike = id => { const o = K().byId[id]; o.strike({ kind: 'light' }); G.step(20); };
for (let k = 0; k < 3; k++) { strike('g1'); G.step(40); }
G.step(100);
log.push(`A13 wrongs ${RB.XRB.wrongs} hint shown ${RB.XRB.hints.map(h => h.shown)}`);
for (const id of ['g5', 'g2', 'g7', 'g0']) strike(id);
G.step(120);
log.push(`A13 seq ${K().byId.cipher.active} gate ${K().byId.gc.on} flag ${G.SAVE.flags['x3:A13:cipher']}`);
await snap('p_a13');
// ---------------- A12 Index Room: a wrong book, then 3 9 14
G.tp('A12', 14, 11); G.step(60);
RB.pull(5); G.step(90);
log.push('A12 wrong state ' + RB.XRB.books.resetT);
log.push(`A12 after wrong: out ${RB.XRB.books.books.filter(b => b.out).map(b => b.n)} wrongs ${RB.XRB.wrongs}`);
RB.pull(3); G.step(10); RB.pull(9); G.step(10); RB.pull(14); G.step(90);
log.push(`A12 solved ${RB.XRB.books.solved} gate ${K().byId.gi.on} flag ${G.SAVE.flags['x3:A12:index']}`);
await snap('p_a12');
G.tp('A12', 14, 11); G.step(30); log.push(`A12 re-entry: solved ${RB.XRB.books.solved} gate ${K().byId.gi.on}`);
// ---------------- HF13 Brazier Locks: the right order (b2, b1, then b3 on the middle lock)
G.tp('HF13', 12, 6); G.step(60);
const lock = () => RB.XRB.freeze.map(L => L.s.id + (L.frozen ? ':ice' : ':water')).join(' ');
log.push(`HF13 start ${lock()} P ${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)}`);
const walkTo = (tx) => { for (let i = 0; i < 240 && Math.abs(G.P.x / 16 - tx) > 0.4; i++) G.step(1, [G.P.x / 16 < tx ? 'right' : 'left']); G.step(10); };
walkTo(20.5); G.step(1, [], ['interact']); G.step(60);
log.push(`HF13 lit b2: ${lock()} b2 ${K().byId.b2.active}`);
walkTo(6.5); G.step(1, [], ['interact']); G.step(120);
log.push(`HF13 lit b1: ${lock()} P ${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)}`);
await snap('p_hf13_1');
walkTo(20.5); G.step(1, [], ["interact"]); G.step(90); await new Promise(r => setTimeout(r, 600));   // the reliquary
log.push(`HF13 chest: emberstones ${G.SAVE.inv.emberstone || 0} P ${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)} ${G.P.state}`);
walkTo(6.5); G.step(1, [], ['interact']); G.step(150);
log.push(`HF13 lit b3: ${lock()} P ${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)}`);
await snap('p_hf13_2');
return log;
