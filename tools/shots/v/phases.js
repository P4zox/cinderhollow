// full fight skeleton: refusal -> p1 -> p2 scene -> p3 scene -> death -> the last flame -> ending cinematic -> NG+
await boot();
G.give({ flags: { ...G.SAVE.flags, 'boss:omen': 1, 'boss:sovereign': 1, 'cut:sovereign': 1 } });
G.tp('X5', 36, 10); G.step(20);
const npc = G.props.find(p => p.vnEnd);
G.P.x = npc.x - 20;
const log = [];
G.vn.vnOfferEnding(npc);
const adv = n => { for (let i = 0; i < n; i++) { G.step(2, [], ['interact']); G.step(2, [], ['interact']); } };
adv(3); G.step(2, [], ['down']); G.step(2, [], ['down']); G.step(2, [], ['interact']);
adv(2); G.step(2, [], ['interact']); adv(4);
for (let i = 0; i < 80 && G.state !== 'play'; i++) G.step(10, [], ['pause']);
const b = G.boss;
log.push({ after_refuse: G.state, kind: b.kind, active: b.active, ph: b.phase });
const hit = (dmg) => b.hit({ dmg, poise: 0, x: b.x, y: b.y - 30, dir: 1, melee: true, kind: 'light' });
G.P.x = b.x - 120; G.step(5);
hit(2200); G.step(1); log.push({ biome0: G.vn.biome() });
log.push({ hp_after_big_hit: b.hp, pending: b.pendingPhase });
for (let i = 0; i < 200 && G.state !== 'cut'; i++) { G.vn.hold(); if (b.state === 'attack') b.anim.done = true; G.step(1); }
await snap('p00_p2scene');
for (let i = 0; i < 14; i++) { G.step(10); if (i === 5) await snap('p01_p2scene'); }
for (let i = 0; i < 100 && G.state === 'cut'; i++) G.step(10);
log.push({ phase: b.phase, state: G.state, biome: G.vn.biome(), amb: G.vn.amb() });
await snap('p02_p2');
hit(2500); G.step(1);
for (let i = 0; i < 300 && G.state !== 'cut'; i++) { G.vn.hold(); if (b.state === 'attack') b.anim.done = true; G.step(1); }
for (let i = 0; i < 6; i++) G.step(10);
await snap('p03_p3scene');
for (let i = 0; i < 100 && G.state === 'cut'; i++) G.step(10);
log.push({ phase: b.phase, state: G.state, hp: b.hp, name: b.name, biome: G.vn.biome() });
G.step(40); await snap('p04_p3');
hit(5000); G.step(1);
log.push({ dead: !b.alive, endT: G.vn.VN.endT });
for (let i = 0; i < 8; i++) { G.step(20); if (i % 2) await snap('p1' + i + '_death'); }
const trace = []; for (let i = 0; i < 60 && G.state === 'play'; i++) { G.step(10); trace.push(G.room + ':' + G.vn.biome() + ':' + G.P.s + ':' + Math.round(G.P.hp)); } log.push(trace.join(' '));
log.push({ state: G.state, items: Object.keys(G.SAVE.weapons), charms: G.SAVE.charms });
for (let i = 0; i < 6; i++) { G.step(20); await snap('p2' + i + '_finale'); }
for (let i = 0; i < 100 && G.state === 'cut'; i++) G.step(10);
log.push({ state: G.state, ending: G.SAVE.ending, endings: G.SAVE.endings });
for (let s = 0; s < 3; s++) { G.step(90); await snap('p3' + s + '_cine'); G.step(2, [], ['interact']); }
for (let i = 0; i < 20 && G.state === 'cine'; i++) G.step(30, [], ['interact']);
G.step(200);
await snap('p40_endscreen');
log.push({ state: G.state });
G.step(2, [], ['interact']);
G.step(30);
log.push({ afterNG: G.state, ngp: G.SAVE.ngp, endings: G.SAVE.endings, betrayed: !!G.SAVE.flags.venn_betrayed, weapons: Object.keys(G.SAVE.weapons).includes('last_kindling'), room: G.room });
return log;
