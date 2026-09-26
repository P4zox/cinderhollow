await boot();
G.tp('NH4', 32, 12); G.step(60); await snap('a_nh4_shrine');
G.tp('NH6', 9, 12); G.step(60); await snap('b_nh6_shrine');
G.tp('NH7', 8, 10); G.step(10);
for (let i = 0; i < 14; i++) { G.step(30); if (i % 2 === 1) await snap('c_intro_' + String(i).padStart(2, '0')); }
return G.state;
