await boot(); const E = G.sk.ev, out = [];
const base = E('({...BASE_STATS})');
for (let t = 0; t <= 13; t++) {
  const L = 5 + 6 * t, U = Math.min(5, Math.round(t / 2)), pts = L - E('levelOf(BASE_STATS)');
  const st = { ...base }; const order = ['vig', 'str', 'dex', 'end', 'vig', 'str', 'dex', 'mnd'];
  for (let i = 0; i < pts; i++) st[order[i % order.length]]++;
  G.SAVE.weapon = 'longsword'; G.SAVE.weapons.longsword = U;
  G.give({ stats: st, skills: [] });
  const d = E('({ light: Math.round(D.light), heavy: Math.round(D.heavy), hp: D.maxHp, lvl: levelOf(SAVE.stats) })');
  out.push(`t${t} L${d.lvl} +${U} light ${d.light} heavy ${d.heavy} hp ${d.hp}`);
}
// calibration point: the skill bench's no-skill build
G.SAVE.weapons.longsword = 5; G.give({ stats: { vig: 35, mnd: 25, end: 25, str: 30, dex: 30, fth: 25 }, skills: [] });
out.push('bench build: ' + JSON.stringify(E('({ light: Math.round(D.light), hp: D.maxHp, lvl: levelOf(SAVE.stats) })')));
return out;
