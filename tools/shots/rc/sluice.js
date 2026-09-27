await boot(); G.SETTINGS.god = 1; G.SAVE.seenAreas = { deep: 1 };
const X = G.xrc;
G.tp('D13', 22, 19); G.step(200); await snap('sl_a');
G.tp('D13', 30, 4); G.step(60); X.pour(2); G.step(40); await snap('sl_pour'); G.step(200);
G.tp('D13', 14, 19); G.step(30); await snap('sl_b');
return ['ok'];
