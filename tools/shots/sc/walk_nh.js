// NEO-HALLOW, walked without teleporting: NH4 -(grate)-> NH8 -> NH17 -> NH8 -> NH11 -> NH16 -> NH11 -> NH12 -> NH15 -> NH12 ->
// (grate) NH6, then back: NH6 -> NH12 -> NH11 -> NH8 -> NH10 -> NH9 -> NH13 -> NH9 -> NH10 -> NH8 -> NH14 -> NH8 -(grate)-> NH4
G.tp('NH4', 15, 24); G.step(20); log('start');
dropThrough(); until(() => G.room === 'NH8' && G.P.ground, [], 200);
walkTo(45.5); until(() => G.P.ground, [], 100);
for (let i = 0; i < 6 && G.room === 'NH8'; i++) { G.step(1, ['right'], ['attack']); G.step(14, ['right']); }
wander(1, 'NH17'); walkTo(9); wander(-1, 'NH8');
walkTo(31); walkTo(29); until(() => G.P.ground, [], 100); walkTo(25.5); until(() => G.P.ground, [], 100);
walkTo(38); walkTo(43); until(() => G.P.ground, [], 200); walkTo(45); until(() => G.P.ground, [], 100); walkTo(46); until(() => G.P.ground, [], 100);
if (py() < 42) { dropThrough(); until(() => G.P.ground, [], 100); }
wander(1, 'NH11');
hopTo(4, 8, 12, { jumps: 0 }); walkTo(8.5, 0.3); until(() => py() < 12.9, [], 900); log('riding east');
until(() => px() > 55 || py() > 13.5, [], 900); leap(66, 14, { jumps: 1 }); walkTo(90); wander(1, 'NH16'); walkTo(4); wander(-1, 'NH11');
walkTo(70); leap(67, 11); leap(72, 8); leap(67, 5); leap(70, 2); leap(71, 38, { jumps: 2 }); until(() => G.room === 'NH12' && G.P.ground, ['jump'], 90);
const bb = (id, x, y) => { waitSolid(id, 0.15, 600, 1.4); return leap(x, y, { jumps: 1 }); };
walkTo(20); bb('bb0', 12, 32); leap(5, 29); walkTo(6); bb('bb1', 13, 26); leap(3, 24); wander(-1, 'NH15'); walkTo(8); wander(1, 'NH12');
walkTo(4); bb('bb2', 10, 21); leap(18, 18); walkTo(20.7, 0.1); bb('bb3', 25, 15); leap(16, 12); walkTo(13.5, 0.2); bb('bb4', 9, 9); leap(16, 6); leap(7, 3);
walkTo(4.5, 0.1); leap(2, 1, { jumps: 0 }); leap(2, -1, { jumps: 0 }); G.step(1, ['jump'], ['jump']); G.step(30, ['jump']); until(() => G.P.ground, [], 120); expect('NH6');
// back down: the Vestibule's grate -> the billboards -> the highway (ride west) -> the Megablock
walkTo(14.6, 0.2); for (let k = 0; k < 6 && !(G.room === 'NH12' && py() > 3.5); k++) { dropThrough(); until(() => G.P.ground, [], 120); }
walkTo(11.5); until(() => G.P.ground && py() > 37, ['right'], 600); walkTo(7.5, 0.3);
for (let k = 0; k < 4 && G.room === 'NH12'; k++) { dropThrough(); until(() => G.P.ground, [], 120); }
for (let i = 0; i < 600 && !(G.P.ground && py() > 14.5); i++) { if (G.P.ground && i % 40 === 39) dropThrough(); else G.step(1, ['right']); }
log('station ' + px().toFixed(1)); hopTo(64.5, 58, 12, { jumps: 0 }); walkTo(56.8, 0.3);
until(() => py() < 12.9, [], 1500); until(() => py() < 8.6, [], 300); log('riding west');
until(() => px() < 17 || py() > 9, [], 1200); until(() => G.P.ground && px() < 16, [], 400); wander(-1, 'NH8');   // step off the car, west through the portal mouth
// down the Megablock to the ground floor, west through the tunnels and alleys to the Firewall
walkTo(35); until(() => G.P.ground, [], 60);
for (let i = 0; i < 2000 && !(G.P.ground && py() > 60.5); i++) { const x = px(); G.step(1, [x > 25 ? 'left' : 'right']); if (G.P.ground && py() < 60 && i % 200 === 199) dropThrough(); }
log('ground floor ' + px().toFixed(1)); hopTo(28.6, 22, 57, { jumps: 1 }); leap(17, 54, { jumps: 1 }); walkTo(15.5, 0.2); dropThrough(); until(() => G.P.ground && py() > 60, [], 120);
wander(-1, 'NH10'); wander(-1, 'NH9'); go(1); wander(-1, 'NH13'); walkTo(20); wander(1, 'NH9'); go(46); wander(1, 'NH10'); wander(1, 'NH8');
// up the west side to the mezzanine and the Lockdown
walkTo(15.5, 0.2); leap(22, 57, { jumps: 1 }); leap(17, 54); leap(12, 51); leap(6, 48); leap(12, 45); leap(19, 42); leap(14, 39); wander(-1, 'NH14'); walkTo(20); wander(1, 'NH8');
// up the rest of the block to the roof and the grate into the Server Cathedral
walkTo(13, 0.2); leap(15, 36); leap(20, 33); go(25); leap(30, 33); walkTo(37); leap(40, 30); leap(34, 27); leap(29, 24); go(9); leap(5, 21); leap(12, 18); leap(18, 15);
go(21); leap(26, 15); walkTo(28); leap(28, 12); leap(34, 9); walkTo(33); leap(27, 6); leap(33, 3);
walkTo(35.5, 0.2); chimney(34, 37, 0, 600, () => G.room === 'NH4' && py() < 25.2); for (let i = 0; i < 90 && !(G.room === 'NH4' && G.P.ground); i++) G.step(1, G.P.vy < 0 ? ['jump'] : []);
expect('NH4'); log('back in the Server Cathedral');
until(() => G.P.ground, [], 120); expect('NH4');
return { log: LOG.filter(l => !/landed|airTo ok/.test(l)), rooms: ROOMLOG };
