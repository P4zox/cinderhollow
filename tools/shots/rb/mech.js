await boot(); G.SAVE.seenAreas = { mire: 1, archives: 1, hoarfrost: 1 };
G.give({ items: { talon: 1, hook: 1, emberdash: 1 } }); const S = window.__sys, RB = window.__rb, sim = RB.sim, log = [];
const pos = () => `${(G.P.x / 16).toFixed(1)},${(G.P.y / 16).toFixed(1)}`;
// ---- ink: step into the Page Storm's ink, get thrown back to safe ground (hurt)
G.tp('A11', 9, 10); G.step(30); const hp0 = G.P.hp;
for (let i = 0; i < 60; i++) sim(1, ['right']); G.step(80);
log.push(`ink: hp ${hp0} -> ${Math.round(G.P.hp)} at ${pos()} (safe ground)`);
// ---- ambush: walk along the boardwalk, the rot rises
G.tp('M8', 8, 8); G.step(20); const e0 = G.enemies.length; for (let i = 0; i < 40; i++) sim(1, ['right']); G.step(5);
log.push(`ambush: enemies ${e0} -> ${G.enemies.length} (${G.enemies.map(e => e.type).join(',')})`);
// ---- icicle footholds: stand under the channel icicles; one lands in the freezing water and becomes a foothold
G.tp('HF12', 27, 14); G.SETTINGS.god = true; G.step(5); for (let i = 0; i < 80; i++) sim(1); G.step(1);
log.push(`icicles: footholds ${RB.XRB.feet.length} ${RB.XRB.feet.map(F => (F.x / 16).toFixed(1) + '@' + (F.y0 / 16).toFixed(1)).join(' ')}`);
await snap('m_footholds');
G.SETTINGS.god = false;
// ---- Inkbound Grapple: a ring just beyond the normal reach
G.SAVE.charms.push('c_x3_ink'); G.SAVE.charmsEq = ['c_x3_ink'];
G.tp('A8', 45, 12); G.step(30); const P = G.P; P.x = 732; P.y = 218; P.vy = 0; P.face = -1; sim(1, [], ['hook']);
log.push(`ink charm: hooked ${!!G.P.hook} (dist 150 > 130)`);
G.P.hook = null; G.SAVE.charmsEq = []; G.tp('A8', 45, 12); G.step(30); G.P.hook = null; P.x = 732; P.y = 218; P.vy = 0; P.face = -1; sim(1, [], ['hook']);
log.push(`no charm: hooked ${!!G.P.hook} ${G.P.hook ? G.P.hook.h.x + "," + G.P.hook.h.y : ""} P ${G.P.x},${G.P.y}`);
// ---- Rime Heart: ember-dash through a foe
G.SAVE.charms.push('c_x3_rime'); G.SAVE.charmsEq = ['c_x3_rime'];
G.tp('HF9', 8, 12); G.step(30); const e = G.enemies.find(q => q.type === 'hf_golem'); 
if (e) { G.P.x = e.x - 40; G.P.face = 1; sim(1, ['right'], ['roll']); sim(20, ['right']); log.push(`rime: foe frost ${Math.round(e._frost || 0)} slow ${(e._slowT || 0).toFixed(1)}`); }
// ---- vistas: sit, lore page logged, stand
for (const r of ['M14', 'A14', 'HF14']) {
  G.tp(r, 1, 1); G.step(2); const b = S.roomObj.def.spawns.find(q => q.kind === 'bench'); G.tp(r, b.x, b.y); G.step(30);
  G.step(1, [], ['interact']); G.step(130); await snap('v_' + r);
  log.push(`vista ${r}: seated ${!!S.SYS.vista} logged ${!!S.x3().vistas['x3:' + r + ':bench']} lore ${b.lore} found ${!!S.x3().lore[b.lore]}`);
  G.step(1, ['left']); G.step(60);
}
// ---- lore pages: read every rb page prop
const pages = []; for (const r of ['M14', 'M12', 'A13', 'A12', 'A14', 'A16', 'HF14', 'HF13']) {
  G.tp(r, 1, 1); G.step(2); for (const q of S.roomObj.def.spawns.filter(q => q.kind === 'lore')) { G.tp(r, q.x, q.y); G.step(20); G.step(1, [], ['interact']); G.step(10); pages.push(q.page + ':' + !!S.x3().lore[q.page]); G.step(1, [], ['interact']); G.step(1, [], ['pause']); G.step(1, [], ['pause']); G.step(5); }
}
log.push('pages ' + pages.join(' '));
log.push('completion ' + JSON.stringify(S.completion && S.completion()).slice(0, 400));
return log;
