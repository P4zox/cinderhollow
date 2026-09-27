// LX: before/after lighting shots in the §3.9 rooms. Modes: 'before' on a build without LX, else classic / dyn / dynsh.
await boot(); G.SETTINGS.god = 1; G.SAVE.seenAreas = {}; for (const k of Object.keys(G.lx ? G.lx.LX_AMB : {})) G.SAVE.seenAreas[k] = 1; G.grantTechniques(); G.SAVE.flags['sc:seal'] = 1; G.giveArmory();
const LXM = G.lx ? [['classic', 0], ['dyn', 1], ['dynsh', 2]] : [['before', -1]];
const only = (typeof ONLY !== 'undefined') ? ONLY : null;
const rooms = [['R1', 24, 10], ['C2', 24, 10], ['K1', 24, 10], ['M2', 3, 10], ['D2', 6, 10], ['A2', 24, 10], ['SP7', 26, 15], ['NV4', 48, 16], ['NH2', 28, 10],
  ['C3', 32, 10], ['HF2', 16, 7], ['DB2', 3, 9], ['CM3', 12, 9], ['TV2', 24, 10], ['DU2', 3, 10], ['SF2', 32, 9]];
const out = [];
const settle = () => { for (let i = 0; i < 8 && G.state !== 'play'; i++) G.step(1, [], ['pause']); };
const shoot = async (name) => { for (const [n, m] of LXM) { if (m >= 0) G.SETTINGS.light = m; G.step(1); await snap(name + '_' + n); } };
for (const [r, x, y] of rooms) {
  if (only && !only.includes(r)) continue;
  try { G.tp(r, x, y); G.enemies.length = 0; G.P.hp = 99999; G.step(40); settle(); for (let i = 0; i < 6; i++) { G.step(40); G.P.hp = 99999; settle(); } await shoot(r); } catch (e) { out.push(r + ': ' + e.message); }
}
// boss with spells flying: Cindervane
if (!only || only.includes('boss')) try {
  for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'cindervane'] = 1; delete G.SAVE.flags['boss:cindervane'];
  G.tp('SP7', 30, 15); const b = G.boss;
  for (let i = 0; i < 120 && b && !b.active; i++) { G.step(4, [b.x < G.P.x ? 'left' : 'right']); G.P.hp = 99999; settle(); }
  G.SAVE.spellsEq = ['ash_bolt', 'sunspear', 'emberburst']; G.SAVE.spell = 'ash_bolt';
  for (let k = 0; k < 3; k++) { G.P.fp = 999; G.P.hp = 99999; G.step(1, [], ['cast']); G.step(14); }
  G.P.fp = 999; G.step(1, [], ['cast']); G.step(10); settle();
  await shoot('boss_spells');
} catch (e) { out.push('boss: ' + e.message); }
// dark phase: the Head Librarian's snuff (darkT) in A3
if (!only || only.includes('dark')) try {
  delete G.SAVE.flags['boss:librarian']; G.SAVE.flags['cut:librarian'] = 1;
  G.tp('A3', 16, 10); const b = G.boss; out.push('lib ' + !!b);
  for (let i = 0; i < 80 && b && !b.active; i++) { G.step(4, ['right']); G.P.hp = 99999; settle(); }
  if (b) { b.moves.snuff.spawn.call(b); G.step(20); G.P.hp = 99999; settle(); await shoot('dark_librarian'); }
} catch (e) { out.push('dark: ' + e.message); }
// the Pale Sovereign
if (!only || only.includes('sov')) try {
  for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'sovereign'] = 1; delete G.SAVE.flags['boss:sovereign'];
  G.tp('X5', 10, 10); const b = G.boss;
  for (let i = 0; i < 120 && b && !b.active; i++) { G.step(4, [b.x < G.P.x ? 'left' : 'right']); G.P.hp = 99999; settle(); }
  G.step(90); G.P.hp = 99999; settle(); await shoot('sovereign');
} catch (e) { out.push('sov: ' + e.message); }
return out;
