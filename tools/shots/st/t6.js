await boot(); const o = [];
const settle = (n = 30) => { for (let i = 0; i < n; i++) G.step(1); };
const S = G.SAVE; S.skills = ['keen_edge','fourth_strike','quickstep','riposte_mastery','deflect']; S.shards = 8;
G.st.open(0); settle(); G.st.sel('measured_cut'); settle(); await snap('q_fork_mid');
G.st.zoom(1); settle(); await snap('q_fork_close');
G.st.sel('evasive_strike'); settle(); await snap('q_fork_sealed');
G.st.zoom(-1); G.st.zoom(-1); settle(); await snap('q_fork_over');
return o;
