await boot(); stubOn(); const o = [];
G.SAVE.skills = []; G.SAVE.shards = 3; G.st.open(0); G.step(30); await snap('a_early');
G.st.zoom(1); G.step(40); await snap('b_early_zoom');
G.SAVE.skills = ['keen_edge','fourth_strike','blade_1','charged_arts','quickstep','iron_flask','steadfast']; G.SAVE.shards = 30; G.st.open(0); G.step(40); await snap('c_mid');
G.st.input('right'); G.step(20); G.st.input('confirm'); G.step(10); await snap('d_armed');
G.st.input('confirm'); G.step(12); await snap('e_learned');
G.st.page(1); G.step(30); await snap('f_arsenal');
o.push(G.st.pts); return o;
