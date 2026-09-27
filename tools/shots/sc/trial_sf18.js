// SF18 The Moonstep Trial: a full scripted clear (needs talon, wings, moonstep)
await boot(); G.grantTechniques(); Object.assign(G.SAVE.items, { moonstep: 1, wings: 1, talon: 1 });
G.tp('SF18', 36, 44); G.step(30); G.step(1, [], ['interact']); G.step(5); log('sigil');
walkTo(25.5);
leap(18, 41); leap(11, 38); leap(4, 35); leap(11, 28, { jumps: 2 });
walkTo(12.8);
for (const [id, x, y] of [['tm0', 17, 26], ['tm1', 22, 24], ['tm2', 27, 25], ['tm3', 32, 23]]) { waitSolid(id, 0.05, 600, 0.9); leap(x, y, { jumps: 1 }); }
leap(39, 21, { jumps: 2 });
walkTo(37.6);
leap(21, 15, { jumps: 2, margin: 20, dash: true, dashAt: 40, dashT: 60 });
walkTo(15.2);
chimney(13, 17, 4);
for (let i = 0; i < 90 && !(G.P.ground && py() < 4.2); i++) G.step(1, [px() < 17.4 ? 'right' : px() > 17.7 ? 'left' : 'down', ...(G.P.vy < 0 ? ['jump'] : [])], (G.P.vy > 0 && G.P.y > 3.5 * 16 && G.P.airJumps > 0 && i % 10 == 0) ? ['jump'] : []);
log('on wall top'); walkTo(17.6, 0.2);
hopDash(1, 5);
walkTo(28.5);
for (let i = 0; i < 30; i++) G.step(1);
await snap('trial_sf18');
for (let i = 0; i < 260; i++) G.step(1);
const R = S().result, rec = window.__sys.x3().trials['SF18:moon'];
return [...LOG, 'RESULT ' + JSON.stringify(R && { t: +R.time.toFixed(2), par: R.par, gold: R.gold, attempts: R.attempts }), 'rec ' + JSON.stringify(rec), 'charm ' + G.SAVE.charms.includes('c_x3_moon')];
