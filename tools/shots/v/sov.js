// the real hand-off: the Sovereign's beast dies -> victory banner -> beginEnding -> Venn at the throne with three choices
await boot();
G.give({ flags: { ...G.SAVE.flags, 'boss:omen': 1, 'cut:sovereign': 1, 'cutp2:sovereign': 1, 'cutp3:sovereign': 1 } });
G.tp('X5', 20, 10); G.step(5);
const b = G.boss; const log = [{ kind: b && b.kind }];
G.P.x = 300; G.step(30);
try { b.phase = 2; b.startTransform(); for (let i = 0; i < 200 && G.state === 'cut'; i++) G.step(10); log.push({ ph: b.phase, st: b.state }); b.beastDie(); } catch (e) { log.push('ERR ' + e.message); }
for (let i = 0; i < 80 && G.state === 'play'; i++) G.step(10);
log.push({ state: G.state, npc: !!G.props.find(p => p.vnEnd), flag: G.SAVE.flags['boss:sovereign'] });
await new Promise(r => setTimeout(r, 900)); log.push({ opened: G.state });
for (let i = 0; i < 3; i++) { G.step(2, [], ['interact']); G.step(2, [], ['interact']); }
await snap('s_choice');
log.push({ state: G.state });
return log;
