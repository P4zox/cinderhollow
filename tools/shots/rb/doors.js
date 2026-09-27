await boot(); G.SETTINGS.god = true; G.SAVE.seenAreas = { mire: 1, archives: 1, hoarfrost: 1 };
G.give({ items: { talon: 1, hook: 1, emberdash: 1 } });
const S = window.__sys, out = [];
const pairs = [['M2', 'rb_m7'], ['M7', 'up'], ['M4', 'rb_m9'], ['M9', 'sc'], ['A5', 'rb_a10'], ['A10', 'down'], ['A2', 'rb_a9'], ['A9', 'sc'],
  ['A10', 'hl'], ['A15', 'end'], ['HF6', 'rb_hf10'], ['HF10', 'in'], ['HF2', 'rb_hf9'], ['HF9', 'sc'], ['HF11', 'tr'], ['HF15', 'end']];
const ROOMS = window.__sys.roomObj && null;
for (const [r, id] of pairs) {
  G.tp(r, 1, 1); G.step(2);
  const def = S.roomObj.def, d = def.spawns.find(s => s.t === 'sys' && s.kind === 'door' && s.id === id);
  G.tp(r, d.x, d.y); G.step(30);
  G.step(1, [], ['interact']); G.step(90);
  const P = G.P; out.push(`${r}:${id} -> ${G.room} (want ${d.to}) at ${(P.x / 16).toFixed(1)},${(P.y / 16).toFixed(1)} ${G.room === d.to ? 'OK' : 'FAIL'}`);
}
return out;
