// Starfall wing, walked without teleporting: SF7 -> SF10 -> SF16 -> SF10 -> SF13 -> SF14 -> SF17 -> SF14 -> SF11 -> SF18 ->
// SF11 -> SF12 -> SF15 -> SF12 -> SF11 -> (the pool) SF9 -> SF6 -> SF7 -> SF10 -> SF13 -> SF14 -> SF11, then back down:
// SF11 -> SF14 -> SF13 -> SF10 -> SF7
G.tp('SF7', 40, 16); G.step(30); log('start');
const met = (id, x, y) => { waitSolid(id, 0.35, 600, 0.9); return leap(x, y, { jumps: 1 }); };
const climbWing = () => {   // SF7 -> SF10 -> (SF16 and back) -> SF13 -> SF14 -> (SF17 and back) -> SF11
  wander(1, 'SF10');
  hopTo(18, 21, 8); leap(24, 5); leap(27, 4); walkTo(35.5); hopTo(35.5, 42, 9);
  exitTo(1, 'SF16'); walkTo(20); exitTo(-1, 'SF10');
  hopTo(44, 46, 7); leap(49, 4); leap(51, 2); leap(51, 20, { jumps: 1 }); expect('SF13');
  met('m0', 46, 19); leap(42, 16); met('m1', 38, 14); met('m2', 34, 12); leap(30, 11); met('m3', 25, 9); met('m4', 21, 8); leap(17, 8);
  met('m5', 13, 7); leap(5, 6); leap(7, 3); leap(7, 0); leap(6, 26, { jumps: 1 }); expect('SF14');
  leap(12, 23); leap(20, 20); leap(28, 17); leap(36, 14); leap(43, 16); exitTo(1, 'SF17'); walkTo(9); exitTo(-1, 'SF14');
  leap(36, 14); leap(28, 11); leap(19, 8); leap(10, 6); leap(4, 4); exitTo(-1, 'SF11');
};
climbWing();
// the Expanse: up the east shelves to the high road, up into the Moonstep Spire and back, west to the canyon
hopTo(116, 114, 21); leap(106, 18); leap(98, 15); leap(88, 14); leap(77, 11); leap(80, 6); leap(83, 2); leap(82, 44, { jumps: 1 });
until(() => G.room === 'SF18', ['jump'], 60); until(() => G.P.ground, [], 120); expect('SF18');
walkTo(31.5); dropThrough(); dropThrough(); until(() => G.room === 'SF11' && G.P.ground, [], 200); expect('SF11');
walkTo(80); walkTo(76.5); leap(68, 9); leap(59, 6); leap(49, 7); leap(41, 3); leap(33, 6); leap(25, 9); leap(17, 11); leap(8, 14); exitTo(-1, 'SF12');
walkTo(36); walkTo(24); walkTo(16); wander(-1, 'SF15'); walkTo(30); wander(1, 'SF12');
walkTo(19); leap(22, 13); leap(32, 10); leap(41, 7); exitTo(1, 'SF11');
// the low road east to the starlight pool: it drains into the Last Light, which opens onto the Crater Rim (the loop back)
walkTo(13); walkTo(17); until(() => G.P.ground, [], 60); hopTo(18, 24, 23); wander(1, 'SF9');
until(() => G.P.ground, [], 200); wander(-1, 'SF6'); wander(1, 'SF7');
climbWing();
// and back down the wing
wander(1, 'SF14'); walkTo(4); leap(10, 6, { jumps: 0 }); for (let i = 0; i < 90 && !(G.P.ground && py() > 20); i++) G.step(1, ['right']); walkTo(11); leap(6, 26, { jumps: 0 });
dropThrough(); until(() => G.room === 'SF13' && G.P.ground, [], 200);
for (let k = 0; k < 3 && py() < 7; k++) { dropThrough(); until(() => G.P.ground, [], 120); }
met('m5', 13, 7); leap(17, 8); met('m4', 21, 8); met('m3', 25, 9); leap(30, 11); met('m2', 34, 12); met('m1', 38, 14); leap(42, 16); met('m0', 46, 19); leap(51, 20);
for (let k = 0; k < 6 && !(G.room === 'SF10' && py() > 11); k++) { dropThrough(); until(() => G.P.ground, [], 120); }
walkTo(46); hopTo(45, 42, 9); leap(34, 8); leap(31, 5); leap(27, 4); leap(24, 5); leap(21, 8); walkTo(15); wander(-1, 'SF7');
return { log: LOG.filter(l => !/landed|airTo ok/.test(l)), rooms: ROOMLOG };
