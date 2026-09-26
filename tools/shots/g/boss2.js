// agent G (Expansion 2): new spells/arts vs a boss (Morvain, K4)
await boot();
const SP = ['soul_chains','sunbeam','comet','sandstorm','null_field','blood_lance'];
G.give({ spellsOwned: SP, spellsEq: SP, spellSlots: 6, arts: ['chain_drag','harvest_moon','solar_flare','starfall'] });
G.SAVE.flags['cut:omen'] = 1; delete G.SAVE.flags['boss:omen'];
G.tp('K4', 6, 10); for (let i = 0; i < 5; i++) G.step(5, ['right']);
for (let i = 0; i < 200; i++) { G.P.inv = 9; G.step(5); G.P.hp = 99999; if (G.boss && G.boss.active && G.boss.state !== 'intro' && G.boss.state !== 'dormant') break; }
const log = [];
const run = async (fn, name, n = 100) => { const b = G.boss; G.P.x = b.x - 70; G.P.face = 1; G.P.fp = 999; G.P.hp = 99999; const h0 = b.hp; fn(); for (let i = 0; i < n; i++) { G.step(1); G.P.hp = 99999; G.P.inv = 0.2; if (i % 25 === 20) await snap(name + '_' + i); } log.push(name + ' dmg ' + (h0 - b.hp) + ' stance ' + Math.round(b.stance || 0) + ' state ' + b.state + ' slow ' + (b._slowT || 0).toFixed(1) + ' bx ' + Math.round(b.x) + ' px ' + Math.round(G.P.x)); };
for (const sp of SP) await run(() => { G.SAVE.spell = sp; G.step(1, [], ['cast']); }, sp);
for (const a of ['chain_drag', 'harvest_moon', 'solar_flare', 'starfall']) await run(() => { G.SAVE.art = a; G.step(1, [], ['art']); }, a);
return log;
