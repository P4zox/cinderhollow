await boot(); const o = [];
const S = G.SAVE; S.skills = G.st.SKILLS.filter(s => s.br === 'blade' || s.br === 'veil').filter(s => !/f1b|f2a/.test(s.slot)).map(s => s.id); S.shards = 40;
G.st.open(0); for (let i = 0; i < 20; i++) G.step(1);
for (const zi of [0, 1, 2]) { G.st.ST.zi = zi; for (let i = 0; i < 20; i++) G.step(1); const t0 = performance.now(); for (let i = 0; i < 60; i++) G.step(1); o.push(`zoom ${zi}: ${((performance.now() - t0) / 60).toFixed(2)} ms/frame (update+render)`); }
G.st.ST.summary = true; { const t0 = performance.now(); for (let i = 0; i < 60; i++) G.step(1); o.push(`summary: ${((performance.now() - t0) / 60).toFixed(2)} ms/frame`); }
return o;
