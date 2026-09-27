await boot(); for (const [r, x, y] of [['R2', 24, 10], ['C1', 12, 24], ['K1', 38, 10], ['R1', 9, 10]]) { G.tp(r, x, y); G.step(200); await snap('anchor_' + r); } return 'ok';
