await boot(); G.SETTINGS.god = true; const out = [], K = () => G.KIT;
G.tp('T1', 45, 96); G.step(3);
{ const r = K().byId.rise1; G.step(80);
  out.push('rise state ' + r.st + ' row ' + (r.sy / 16).toFixed(1));
  // teleport to the top platform (goal) mid-rise
  const P = G.P; P.x = 54 * 16 + 8; P.y = 82 * 16; P.vy = 0; G.step(40); await snap('rising_mid');
  out.push('after goal ' + r.st + ' done=' + r.done); G.step(200); out.push('drained row ' + (r.sy / 16).toFixed(1)); }
// persistence: switch S1 + persistent gate, lever L1
G.tp('T1', 56, 56); G.step(3);
K().byId.S1.interact(); K().byId.L1.interact(); G.step(120);
G.tp('T1', 10, 16); G.step(5); G.tp('T1', 56, 56); G.step(5);
out.push('reentry S1=' + K().byId.S1.active + ' g4.k=' + K().byId.g4.k.toFixed(2) + ' L1=' + K().byId.L1.active + ' g2.k=' + K().byId.g2.k.toFixed(2));
// kitForce like a KS gauntlet
G.kitForce('g2', false); G.step(90); const k1 = K().byId.g2.k; G.kitForce('g2', null); G.step(90);
out.push('force close ' + k1.toFixed(2) + ' release ' + K().byId.g2.k.toFixed(2));
// kitReset (trial): movers back home
G.tp('T1', 4, 16); const m = K().byId.mA; G.step(100); const x1 = m.d.x0; G.kitReset('T1'); out.push('reset mover ' + x1 + ' -> ' + m.d.x0);
return out;
