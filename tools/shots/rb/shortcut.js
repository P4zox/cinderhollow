await boot(); G.SETTINGS.god = true; G.SAVE.seenAreas = { mire: 1, archives: 1, hoarfrost: 1 }; G.give({ items: { talon: 1, hook: 1, emberdash: 1 } });
const RB = window.__rb, sim = RB.sim, log = [];
for (const [r, from] of [['M9', 'M4'], ['A9', 'A2'], ['HF9', 'HF2']]) {
  G.tp(r, 8, r === 'HF9' ? 12 : 10); G.step(20);
  const gate0 = RB.kit.byId.scg.on; G.P.x = 7 * 16 + 8; G.step(1, [], ['interact']); G.step(60);
  const gate1 = RB.kit.byId.scg.on;
  G.tp(from, 1, 1); G.step(5); G.tp(r, 8, r === 'HF9' ? 12 : 10); G.step(20);
  log.push(`${r}: gate ${gate0} -> ${gate1}; after re-entry ${RB.kit.byId.scg.on}; walk to door: ` + (() => { for (let i = 0; i < 120; i++) sim(1, ['left']); return (G.P.x / 16).toFixed(1); })());
}
// the false bookcase: strike it and the Annex opens
G.tp('A8', 60, 32); G.step(20); G.P.face = 1;
for (let i = 0; i < 12; i++) { G.step(1, ['right'], ['attack']); G.step(20); }
G.step(10); await snap('sc_falseshelf');
log.push('false shelf broken: ' + [30, 31, 32].map(y => !!G.SAVE.flags[`brk:A8:63,${y}`]).join(','));
for (let i = 0; i < 90; i++) sim(1, ['right']); G.step(1); log.push('walked into ' + G.room);
return log;
