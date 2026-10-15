// v15 cores visuals: the enchanted move's slash light, tip ribbon and sparks take the Core's colour; ordinary blows don't;
// an idle enchanted blade breathes a faint ember; proc effects (omen line, storm arc, bell ring, dusk sigil) draw.
// Run: SHOT_HTML=web/dist/v15_cores.html sh tools/shots/wm/run.sh tools/shots/v15/cores/visuals.js <out>
const R = [], T = (name, pass, detail = '') => R.push(`${pass ? 'OK ' : 'BAD'} ${name}${detail ? '  [' + detail + ']' : ''}`);
const C = G.cores, fr = n => W().frame(n), tap = a => { W().down(a); fr(1); W().up(a); };
const setup = (kind, type = 'longsword') => {
  W().reset(type, 5); arena(); W().reset(type, 5);
  E('D.maxSt = 1e6; P.st = 1e6');
  C.ev(`SAVE.cores = {}; for (const k of Object.keys(CORES)) SAVE.cores[k] = 1; SAVE.enchants = {}; ${kind ? `SAVE.enchants['${type}'] = '${kind}';` : ''} CR.cd = {}; CR.vfx = []; CR.bell = 0; CR.star = 0; CR.twin = 0`);
  W().dummy(26, { boss: true }); W().follow = 26;
};
// render() is what draws: G.step(0) renders a frame without advancing
const show = async name => { G.step(0); await snap(name); };
// 1) the finisher: tinted fx + ribbon colour; light hits stay plain
for (const [kind, col] of [['overseer', '#ff9038'], ['ice_warden', '#a8dcff'], ['sanguine', '#c0182c'], ['astrel', '#eef4ff']]) {
  setup(kind);
  tap('attack'); fr(12); tap('attack'); fr(14); tap('attack');
  let lightTint = false; for (let i = 0; i < 20; i++) { fr(1); if (E('fx.some(f => f.tint)')) lightTint = true; }
  tap('attack');
  let seen = { fx: [], trail: [], el: null }, shot = false;
  for (let i = 0; i < 40; i++) {
    fr(1);
    const s = E(`(() => ({ st: P.state, fx: fx.filter(f => f.tint).map(f => f.name + ':' + f.tint), trail: [...new Set(FEEL.trail.map(t => t.col))], el: feelElement(false).glow }))()`);
    if (s.st === 'attack4') { seen.fx.push(...s.fx); seen.trail.push(...s.trail); seen.el = seen.el || s.el; }
    if (!shot && s.st === 'attack4' && s.fx.length) { shot = true; await show(`finisher_${kind}`); }
  }
  T(`${kind}: the finisher's slash light is tinted ${col}`, seen.fx.some(f => f.endsWith(col)), [...new Set(seen.fx)].join(' '));
  T(`${kind}: the tip ribbon takes the colour`, seen.trail.includes(col), [...new Set(seen.trail)].join(' '));
  T(`${kind}: the light blows before it stay plain`, !lightTint);
}
// 2) plain weapon: nothing tinted
{ setup(null); for (const k of 'JJJJ') { tap('attack'); fr(14); } let any = false; for (let i = 0; i < 30; i++) { fr(1); if (E('fx.some(f => f.tint)')) any = true; } T('no Core: nothing is tinted', !any); }
// 3) idle glow: embers rise from the blade (feel sparks in the Core's rgb) and a faint light sits on it
{ setup('first_ember'); E("enemies = enemies.filter(e => !e.wmDummy)"); fr(90);
  const n = E(`FEEL.sparks.filter(s => s.col === CORES.first_ember.rgb).length`);
  T('idle: the enchanted blade sheds embers of its colour', n > 0, `${n} sparks`); await show('idle_glow_first_ember');
  setup('cindervane'); E("enemies = enemies.filter(e => !e.wmDummy)"); fr(90); await show('idle_glow_cindervane'); }
// 4) the proc effects (polled every frame; the first frame a kind shows is snapped)
const seenV = {};
const pf = async (n, want) => { for (let i = 0; i < n; i++) { fr(1); const ks = E('CR.vfx.map(v => v.k)'); for (const k of ks) if (!seenV[k]) { seenV[k] = true; if (want && want.includes(k)) await show('proc_' + k); } } };
const combo = async (want, tail = 40) => { for (const k of 'JJJ') { tap('attack'); await pf(14, want); } tap('attack'); await pf(tail, want); };
{ setup('omen'); await combo(['line', 'pillar'], 90); T('Omen Line draws its line, then the pillar', seenV.line && seenV.pillar); }
{ setup('cindervane'); W().follow = 0; E(`(() => { const d = enemies.find(e => e.wmDummy); const e2 = { ...d, wmDummy: false, key: 'd2', x: d.x + 40, hit(i) { W2.push(i.dmg); }, hurtbox() { return rect(this.x - 8, this.y - 40, this.x + 8, this.y); } }; window.W2 = []; enemies.push(e2); })()`);
  await combo(['arc'], 100); T('Stormcall arcs to the second foe', seenV.arc && E('W2.length') > 0, `second foe hit ${E('W2.length')}x`); }
{ setup('bellringer'); for (let c = 0; c < 3; c++) await combo(['ring'], 100); T('Toll rings on the third move', seenV.ring); }
{ setup('pharaoh'); await combo(['sigil'], 100); T('Dusk Count hangs its sigil', seenV.sigil); }
{ setup('astrel'); for (let c = 0; c < 3; c++) await combo(['star'], 100); T('Starfall drops its star', seenV.star); }
// 5) the effigy in a boss room (the real world, not the chamber)
{ G.trn.exit && G.trn.exit(); fr(5); }
return R;
