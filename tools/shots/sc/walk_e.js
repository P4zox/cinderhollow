// The Ember, walked without teleporting: E1 -> E5 -> E7 -> E5 -> (the tower, the roof grate) E6 -> E5 -> E4 -> (the flue) E3 ->
// E4 -> E5 -> (the basalt shelves) E1
G.tp('E1', 18, 22); G.step(30); log('start');
wander(1, 'E5'); until(() => G.P.ground, [], 60); walkTo(6.5); until(() => G.P.ground && py() > 27, [], 300);
go(108); wander(1, 'E7'); walkTo(8); wander(-1, 'E5');
go(51);
leap(47, 24); walkTo(48.4, 0.1); leap(54, 21); walkTo(52.6, 0.1); leap(47, 18); walkTo(48.4, 0.1); leap(54, 15); walkTo(52.6, 0.1); leap(47, 12); walkTo(48.4, 0.1); leap(54, 9); walkTo(52.6, 0.1); leap(47, 6); walkTo(48.4, 0.1); leap(51, 3); for (let k = 0; k < 4 && G.room !== 'E6'; k++) { G.step(1, ['jump'], ['jump']); until(() => G.P.ground, ['jump'], 90); }
until(() => G.room === 'E6' && G.P.ground, [], 90); expect('E6'); walkTo(20); walkTo(15.5, 0.3);
for (let k = 0; k < 6 && !(G.room === 'E5' && py() > 8); k++) { dropThrough(); until(() => G.P.ground, [], 120); }
until(() => G.P.ground && py() > 26, [], 300); go(3); wander(-1, 'E4');
walkTo(40); walkTo(21.5, 0.2); log('under the flue');
chimney(19, 23, 0, 600, () => G.room === 'E3'); for (let i = 0; i < 90 && !G.P.ground; i++) G.step(1, ['right', 'jump'], i === 10 ? ['jump'] : []);
until(() => G.P.ground, [], 120); expect('E3'); walkTo(30); walkTo(37.5, 0.3); until(() => G.room === 'E4', [], 200); until(() => G.P.ground, [], 200);
wander(1, 'E5');
go(6.5); G.step(1, ['jump'], ['jump']); G.step(8, ['jump']); chimney(5, 8, 3.6); for (let i = 0; i < 60 && !(G.P.ground && py() < 5); i++) G.step(1, ['left', 'jump']); log('flue top'); wander(-1, 'E1');
return { log: LOG.filter(l => !/landed|airTo ok/.test(l)), rooms: ROOMLOG };
