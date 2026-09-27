await boot(); G.SETTINGS.god = 1; G.SAVE.seenAreas = { crown: 1 };
G.tp('X9', 3, 16); G.step(200); await snap('petal_a'); G.tp('X9', 30, 3); G.P.y = 8 * 16; G.step(2); await snap('petal_b'); return ['ok'];
