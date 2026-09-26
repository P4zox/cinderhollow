await boot();
G.nhGod(true);
G.tp('C6', 11, 21); for (let i = 0; i < 30; i++) { G.step(2); if (i === 29) await snap('a_c6_crack'); }
G.tp('NH1', 7, 12); G.step(120); await snap('b_nh1');
G.tp('NH1', 20, 12); G.step(30); await snap('c_nh1_east');
G.tp('NH3', 9, 10); G.step(10); const tr = G.NHR.trains[0];
for (let i = 0; i < 600 && !(tr.st === 'wait' && tr.x === tr.A); i++) G.step(2);
for (let i = 0; i < 60 && G.P.x < tr.x + 40; i++) G.step(1, ['right']);
for (let i = 0; i < 120; i++) { G.step(2); if (i === 60) await snap('d_ride'); }
G.SAVE.charmsEq = ['c_hack']; G.SAVE.charms = ['c_hack'];
G.tp('NH4', 12, 12); G.step(10);
for (let i = 0; i < 40; i++) { G.step(4); if (i === 20 || i === 39) await snap('e_hack_' + i); }
G.tp('NH6', 13, 12); G.step(30); G.step(5, [], ['interact']); G.step(90); await snap('f_lore');
for (let i = 0; i < 10; i++) G.step(10, [], ['confirm']);
G.tp('NH4', 3, 24); G.step(60); await snap('g_nh4_floor');
G.tp('NH5', 34, 12); G.SAVE.flags['boss:enforcer'] = 1; G.tp('NH5', 34, 12); G.step(60); await snap('h_nh5');
return G.state;
