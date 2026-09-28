// The Hermit's Hollow, walked: H1 -> (Oswin's path) H2 -> H3 -> (the rotten boards) H4 -> H3 -> H2 -> H1
G.tp('H1', 20, 10); G.step(30); log('start');
go(3); wander(-1, 'H2'); go(31.5); leap(28, 9); leap(23, 8); leap(18, 9); leap(13, 10); go(3); wander(-1, 'H3'); go(3);
for (let i = 0; i < 8 && G.room === 'H3'; i++) { G.step(1, ['left'], ['attack']); G.step(14, ['left']); }
wander(-1, 'H4'); go(4); wander(1, 'H3'); go(28); wander(1, 'H2'); go(14.5); leap(18, 9); leap(23, 8); leap(28, 9); leap(33, 10); go(44); wander(1, 'H1');
return { log: LOG.filter(l => !/landed|airTo ok/.test(l)), rooms: ROOMLOG };
