// NH16 The Glitch Run: a full scripted clear (needs talon, emberdash)
await boot(); G.grantTechniques(); Object.assign(G.SAVE.items, { talon: 1 });
G.tp('NH16', 4, 20); G.step(30); G.step(1, [], ['interact']); G.step(5); log('sigil');
walkTo(6.8);
const hop = (id, x, y, cur, flight = 0.55, o = {}) => { waitTakeoff(id, flight, cur); return leap(x, y, { jumps: 0, ...o }); };
hop('p0', 9, 18, null); hop('p1', 13, 17, 'p0'); hop('p2', 17, 16, 'p1');
waitTakeoff('p3', 0.5, 'p2'); hopDash(1, 3);
waitTakeoff('p3', 0.0, null, 0, 0.05); leap(28, 14, { jumps: 0 });
hop('p4', 32, 12, null, 0.6); hop('p5', 35, 9, 'p4'); leap(38, 8, { jumps: 0 });
waitTakeoff('p6', 0.55, null); leap(45, 8, { jumps: 0, dash: true, dashT: 3, dashAt: 20, holdT: 6 });
hop('p7', 49, 6, 'p6', 0.5, { holdT: 9 }); hop('p8', 53, 6, 'p7', 0.45, { holdT: 6 }); leap(59, 5, { jumps: 0, holdT: 8 }); walkTo(60.5);
for (let i = 0; i < 30; i++) G.step(1);
await snap('trial_nh16');

for (let i = 0; i < 260; i++) G.step(1);
const rec = window.__sys.x3().trials['NH16:glitch'];
return [...LOG, 'rec ' + JSON.stringify(rec), 'charm ' + G.SAVE.charms.includes('c_x3_glitch')];
