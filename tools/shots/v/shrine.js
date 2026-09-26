// the Crown Shrine (X4) right before her: rest there, walk east into X5, refuse, die, respawn at X4, walk back in
await boot();
G.give({ flags: { ...G.SAVE.flags, 'boss:omen': 1, 'boss:sovereign': 1, 'cut:sovereign': 1, 'cut:venn': 1 } });
const log = [];
G.tp('X4', 12, 10); G.step(10);
G.step(2, [], ['interact']); G.step(60); await new Promise(r => setTimeout(r, 1500)); G.step(10);
for (let i = 0; i < 30 && (G.state !== 'play' || G.P.state === 'rest'); i++) { G.step(5, [], ['pause']); await new Promise(r => setTimeout(r, 100)); }
G.step(40);
log.push({ rested: G.SAVE.shrine, lit: G.SAVE.shrines.includes('X4') });
for (let i = 0; i < 200 && G.room === 'X4'; i++) G.step(4, ['right']);
log.push({ walkedInto: G.room, px: Math.round(G.P.x), st: G.state, ps: G.P.state });
await snap('sh0_entered');
const npc = G.props.find(p => p.vnEnd); if (!npc) return log;
G.P.x = npc.x - 20; G.vn.vnOfferEnding(npc);
const adv = n => { for (let i = 0; i < n; i++) { G.step(2, [], ['interact']); G.step(2, [], ['interact']); } };
adv(3); G.step(2, [], ['down']); G.step(2, [], ['down']); G.step(2, [], ['interact']); adv(2); G.step(2, [], ['interact']); adv(4);
for (let i = 0; i < 80 && G.state !== 'play'; i++) G.step(10, [], ['pause']);
G.P.hp = 1; G.boss.cool = 0;
for (let i = 0; i < 600 && G.state === 'play'; i++) { G.P.x = G.boss.x - 40; G.step(1); }
for (let i = 0; i < 200 && !(G.state === 'play' && G.room === 'X4'); i++) G.step(10);
log.push({ respawn: G.room, state: G.state, ps: G.P.state, px: Math.round(G.P.x), menu: G.state });
G.step(60); await new Promise(r => setTimeout(r, 800)); for (let i = 0; i < 20 && (G.state !== 'play' || G.P.state === 'rest'); i++) { G.step(5, [], ['pause']); await new Promise(r => setTimeout(r, 100)); }
log.push({ ready: G.state, ps: G.P.state });
await snap('sh1_respawn');
for (let i = 0; i < 200 && G.room === 'X4'; i++) G.step(4, ['right']);
for (let i = 0; i < 40; i++) G.step(4, ['right']);
log.push({ back: G.room, boss: G.boss && G.boss.kind, active: G.boss && G.boss.active, fog: G.props.filter(p => p.type === 'fog').map(p => p.on()), hp: G.boss && G.boss.hp });
await snap('sh2_back');
return log;
