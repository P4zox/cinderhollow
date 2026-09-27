await boot(); G.grantTechniques(); G.SAVE.items.talon = 1; G.SAVE.seenAreas = { deep: 1, spire: 1 }; const log = [];
const eq = id => { G.SAVE.charms = [id]; G.SAVE.charmsEq = [id]; G.SAVE.charmSlots = 3; };
// Slagwalker's Sole: walk into D2's lava river twice
G.SETTINGS.god = 0; eq('c_x3_slag'); G.tp('D2', 8, 10); G.step(30); const hp0 = G.P.hp;
for (let i = 0; i < 90 && G.P.hp === hp0; i++) G.step(1, ['right']);
log.push('slag: hp ' + hp0 + ' -> ' + G.P.hp + ' vy ' + Math.round(G.P.vy) + ' (bounced if hp unchanged)');
G.step(60); G.P.x = 12 * 16; G.P.y = 12 * 16; for (let i = 0; i < 60; i++) G.step(1); log.push('second touch within 10 s: hp ' + G.P.hp);
G.SETTINGS.god = 1;
// Stormglass Feather: glide speed
for (const on of [false, true]) { eq(on ? 'c_x3_storm' : 'c_heel'); G.tp('SP2', 20, 3); G.step(10); G.step(1, ['right', 'jump'], ['jump']); let vx = 0; for (let i = 0; i < 60; i++) { G.step(1, ['right', 'jump']); if (G.P.state === 'glide') vx = Math.max(vx, G.P.vx); } log.push('glide vx ' + (on ? 'storm ' : 'plain ') + Math.round(vx)); }
// Sovereign's Sigil: slam stamina
for (const on of [false, true]) { eq(on ? 'c_x3_crown' : 'c_heel'); G.tp('D9', 12, 37); G.step(30); G.P.st = 50; G.step(1, ['jump'], ['jump']); G.step(10, ['jump']); const s0 = G.P.st; G.step(1, ['down'], ['heavy']); G.step(1); log.push('slam stamina ' + (on ? 'crown ' : 'plain ') + (s0 - G.P.st).toFixed(1)); G.step(60); }
return log;
