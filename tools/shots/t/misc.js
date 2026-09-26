await boot(); G.give({ items: { talon: 1 } });
G.tp('C2', 3, 10); G.enemies.length = 0; G.step(90); await snap('m_c2');
G.tp('TV1', 2, 5); G.step(2); await snap('m_tv1');
G.tp('TV7', 26, 9); G.step(40); await snap('m_tv7_closed');
G.step(2, [], ['interact']); G.step(30); await snap('m_tv7_open');
G.tp('TV2', 5, 4); G.step(30, ['up']); await snap('m_tv2_shaft');
G.tp('TV5', 18, 9); G.step(40); await snap('m_tv5_top');
return G.step(1).p;
