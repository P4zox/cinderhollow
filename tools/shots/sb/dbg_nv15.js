G.SAVE.items.emberdash = 1; G.tp('NV15', 51, 12); for (let i = 0; i < 6; i++) { G.step(20); settle(); }
const P = () => G.P; const out = []; const hist = {};
for (let t = 0; t < 200; t++) {
  const seq = TR.chunks(-1, {});
  TR.start(); const a0 = S.SYS.trial.attempts; let minx = 9999, why = '';
  for (let i = 0; i < seq.length; i++) { G.step(1, seq[i][0], seq[i][1]); if (S.SYS.trial.attempts !== a0) { why = S.SYS.trial.why; break; } minx = Math.min(minx, P().x); }
  const k = Math.floor(minx / 32) * 2 + ':' + why; hist[k] = (hist[k] || 0) + 1;
}
return hist;
