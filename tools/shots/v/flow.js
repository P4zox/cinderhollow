// refusal flow: X5 after the Sovereign -> choice -> refuse -> betrayal cutscene -> fight starts
await boot();
G.give({ flags: { ...G.SAVE.flags, 'boss:omen': 1, 'boss:sovereign': 1, 'cut:sovereign': 1 } });
G.tp('X5', 36, 10);
G.step(30);
const npc = G.props.find(p => p.vnEnd);
const log = [];
log.push({ npc: !!npc, nx: npc && npc.x, px: G.P.x });
G.P.x = npc.x - 16;
G.vn.vnOfferEnding(npc);
await snap('f00_dialog');
// advance the three lines
for (let i = 0; i < 3; i++) { G.step(2, [], ['interact']); G.step(2, [], ['interact']); }
await snap('f01_choice');
log.push({ state: G.state });
G.step(2, [], ['down']); G.step(2, [], ['down']);
await snap('f02_refuse_sel');
G.step(2, [], ['interact']);
for (let i = 0; i < 2; i++) { G.step(2, [], ['interact']); G.step(2, [], ['interact']); }
await snap('f03_confirm');
G.step(2, [], ['interact']);    // "The flame is mine."
for (let i = 0; i < 4; i++) { G.step(2, [], ['interact']); G.step(2, [], ['interact']); }
log.push({ state: G.state, boss: G.boss && G.boss.kind, flags: G.SAVE.flags.venn_betrayed });
for (let i = 0; i < 14; i++) { G.step(20); if (i % 3 === 0) await snap('f1' + i.toString(16) + '_cut'); }
for (let i = 0; i < 40 && G.state === 'cut'; i++) G.step(20);
log.push({ state: G.state, boss: G.step(1).boss, fog: G.props.filter(p => p.type === 'fog').map(p => p.on()) });
G.step(30);
await snap('f20_fight');
return log;
