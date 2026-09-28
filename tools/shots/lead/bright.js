await boot(); G.grantTechniques(); G.SAVE.flags['boss:sovereign'] = 1;
for (const [r, x, y] of [['X5', 40, 10], ['X3', 20, 10], ['DU10', 20, 20], ['SF2', 20, 10], ['LF1', 40, 12], ['R1', 20, 10]]) { try { G.tp(r, x, y); } catch (e) { continue; } G.step(40); await snap('br_' + r); }
return 'ok';
