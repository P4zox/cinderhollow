await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.seenAreas={catacombs:1};
G.tp('T1', 36, 29); G.step(200); await snap('k_swing');
G.tp('T1', 70, 36); G.step(60); await snap('k_pend');
return 'ok';
