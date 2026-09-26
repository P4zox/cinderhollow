await boot();
G.give({ items: { wings: 1, talon: 1, hook: 1, emberdash: 1, gale: 1, slam: 1 } });
G.SAVE.shrines.push('X4');
const out = {};
G.tp('X4', 3, 10); G.step(30);
out.start = G.step(1);
// try climbing X4's west wall before the stair: should never leave X4
for (let i = 0; i < 40; i++) { G.step(6, ['left', 'jump']); G.step(3, ['right']); }
out.climbTry = G.step(1);
G.tp('X4', 5, 10); G.step(20);
// slam onto the cairn
G.step(6, [], ['jump']); G.step(10, ['jump']);
G.step(2, ['down'], ['heavy']); G.step(40);
out.afterSlam = { flag: G.SAVE.flags['sf:stair'], p: G.step(1).p };
await snap('x4_stair0');
G.step(120);
await snap('x4_stair1');
// climb the stair: platform rows 8,5,2 at cols 6..8, 2..4, 6..8
G.tp('X4', 7, 10); G.step(10);
const jumpTo = (dir, n) => { G.step(1, [], ['jump']); G.step(n, dir ? ['jump', dir] : ['jump']); G.step(20, dir ? [dir] : []); };
G.step(1, [], ['jump']); G.step(14, ['jump']); G.step(20);
out.p1 = G.step(1).p;
G.step(1, [], ['jump']); G.step(6, ['jump']); G.step(14, ['jump','left']); G.step(20);
out.p2 = G.step(1).p;
G.step(1, [], ['jump']); G.step(6, ['jump']); G.step(14, ['jump','right']); G.step(20);
out.p3 = G.step(1).p;
await snap('x4_stair2');
G.step(1, [], ['jump']); G.step(10, ['jump','left']); G.step(1, [], ['jump']); G.step(20, ['jump','left']); G.step(30, []);
out.p4 = G.step(1);
await snap('sf1_in');
return out;
