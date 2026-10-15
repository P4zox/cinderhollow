// v15 Scythe: every move from real inputs, the rank gates, souls (harvest / cap / fade / scatter / Reap levels), the
// hook step, mashing, turning, step distances. Run: SHOT_HTML=web/dist/v15_scythe.html sh tools/shots/wm/run.sh <this> <out>
const out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
arena();
const go = (r = 1, souls = 0) => { W().reset('scythe', r); E(`P.x = 160; P.y = 304; P.vx = 0; P.vy = 0; P.ground = true; P.face = 1; P.scySouls = ${souls}; P.scyFade = 0; P.mvInv = 0`); W().frame(2); W().log = []; };
const seq = () => W().log.map(l => l.st);
const uniq = a => a.filter((x, i) => x !== a[i - 1]);
const dm = st => W().log.filter(l => l.st === st).map(l => +(l.dmg / l.light).toFixed(2));
const states = n => { const s = []; for (let i = 0; i < n; i++) { W().frame(1); const st = E('P.state'); if (s[s.length - 1] !== st) s.push(st); } return s; };
const tapJ = (n = 1, gap = 10) => { for (let i = 0; i < n; i++) { W().tap('attack', 2); W().frame(gap); } };
ok(E("WTYPE_INFO.scythe.prefix") === 'scy_' && E("pHas('scy_1')"), 'type info prefix scy_, scy_ tags in the sheet');
// every move plays its own tag
const missing = E("Object.values(MV.defs).filter(d => d.type === 'scythe').filter(d => mvResolve(ATK[d.id]).tag !== d.tags[0]).map(d => d.id)");
ok(missing.length === 0, 'every scythe move plays its own new tag' + (missing.length ? ': missing ' + missing.join(' ') : ` (${E("Object.values(MV.defs).filter(d => d.type === 'scythe').length")} moves)`));
ok(E("['scy_plunge','scy_charge'].every(t => pHas(t))"), 'scy_plunge (plunge fall) and scy_charge (hold loop) tags exist');

// ---- J chain + mashing stops at the finisher
go(); W().dummy(36); tapJ(8, 6); W().frame(120);
ok(uniq(seq()).join() === 'scy_1,scy_2,scy_3,scy_4', 'mash J x8: J J J J then stops at the harvest moon: ' + uniq(seq()).join(' ') + ' ' + W().log.map(l => (l.dmg / l.light).toFixed(2)).join('/'));
ok(dm('scy_3').length === 2 && dm('scy_4')[0] === 1.7, 'turning harvest 2 hits, harvest moon 1.7');
// behind: the low reap cuts 12 px behind, the turning harvest well behind
go(); W().dummy(-10); tapJ(1); W().frame(40); ok(seq().includes('scy_1'), 'low reap hits a foe just behind (10 px)');
go(); W().dummy(-30); tapJ(3, 14); W().frame(60); ok(seq().includes('scy_3'), 'turning harvest hits a foe 30 px behind');
// turning between chain steps
go(); W().dummy(36); W().tap('attack', 2); W().frame(4); W().down('left'); W().tap('attack', 2); W().frame(30); const f2 = E('P.face'); W().up('left'); W().frame(30);
ok(f2 === -1, 'holding back turns you round between chain steps (face ' + f2 + ')');

// ---- J K hook pull, J J K spiral, J J (pause) J pendulum
go(); W().dummy(40); W().tap('attack', 2); W().frame(6); W().tap('heavy', 2); const hx0 = E('enemies.find(e => e.wmDummy).x'); W().frame(60);
const hx1 = E('enemies.find(e => e.wmDummy).x');
ok(seq().includes('scy_hook') && hx0 - hx1 >= 12, `J K hook pull drags a small foe in (${hx0.toFixed(0)} -> ${hx1.toFixed(0)}, P.x ${E('P.x').toFixed(0)})`);
go(); W().dummy(36); W().tap('attack', 2); W().frame(6); W().tap('attack', 2); W().frame(6); W().tap('heavy', 2); W().frame(80);
ok(dm('scy_spiral').length === 3, 'J J K scything spiral: 3 hits ' + dm('scy_spiral').join('/'));
for (const r of [1, 2]) {
  go(r); W().dummy(36); W().tap('attack', 2); W().frame(6); W().tap('attack', 2);
  for (let i = 0; i < 60 && E("P.state") !== 'idle'; i++) W().frame(1);
  W().frame(14); W().tap('attack', 2); W().frame(60);
  const s = uniq(seq());
  ok(r === 1 ? !s.includes('scy_pend') : s.includes('scy_pend') && dm('scy_pend').length === 2, `J J (pause) J at rank ${r}: ${s.join(' ')}`);
}
go(2); W().dummy(36); W().tap('attack', 2); W().frame(6); W().tap('attack', 2); for (let i = 0; i < 60 && E("P.state") !== 'idle'; i++) W().frame(1); W().frame(14); W().tap('attack', 2); W().frame(10); W().tap('attack', 2); W().frame(80);
ok(uniq(seq()).slice(-2).join() === 'scy_pend,scy_4', 'pendulum -> J: harvest moon');

// ---- K, K K, hold K (no souls: charge), early release
go(); W().dummy(36); W().tap('heavy', 2); W().frame(60); ok(dm('scy_heavy').join() === '1.3', 'K: wide crescent 1.3');
go(); W().dummy(-30); W().tap('heavy', 2); W().frame(60); ok(dm('scy_heavy').length === 1, 'the wide crescent cuts behind (30 px)');
go(); W().dummy(36); W().tap('heavy', 2); W().frame(8); W().tap('heavy', 2); W().frame(100); ok(dm('scy_twin').length === 2, 'K K: twin crescent 2 hits ' + dm('scy_twin').join('/'));
go(); W().dummy(36); W().down('heavy'); W().frame(50); const ch = E('P.state'); W().up('heavy'); W().frame(70);
ok(ch === 'scy_charge' && dm('scy_charged').join() === '2', `hold K 0.85 s, no souls: ${ch} -> charged crescent ${dm('scy_charged')}`);
go(); W().dummy(36); W().down('heavy'); W().frame(20); W().up('heavy'); W().frame(70);
ok(dm('scy_heavy').length === 1 && !dm('scy_charged').length, 'hold K released before the gleam: the plain crescent');
go(); W().dummy(36); W().down('heavy'); let stMin = 1e9; for (let i = 0; i < 50; i++) { W().frame(1); stMin = Math.min(stMin, E('P.st')); } W().up('heavy'); for (let i = 0; i < 30; i++) { W().frame(1); stMin = Math.min(stMin, E('P.st')); }
ok(Math.abs(E('D.maxSt') - stMin - 20) < 1.5, `charged crescent costs ${(E('D.maxSt') - stMin).toFixed(1)} stamina in all (16 + 4)`);
go(1, 3); W().dummy(36); W().down('heavy'); stMin = 1e9; for (let i = 0; i < 40; i++) { W().frame(1); stMin = Math.min(stMin, E('P.st')); if (i === 16) W().up('heavy'); }
ok(Math.abs(E('D.maxSt') - stMin - 18) < 1.5, `the Reap costs ${(E('D.maxSt') - stMin).toFixed(1)} stamina in all (16 + 2)`);

// ---- souls
go(); W().dummy(14); tapJ(1); W().frame(40); ok(E('P.scySouls') === 0, 'a hit right up close (haft) harvests nothing');
go(); W().dummy(38); tapJ(1); W().frame(40); ok(E('P.scySouls') === 1, 'a far-edge hit harvests a soul');
go(); W().dummy(38); E('window.__wm.follow = 38'); tapJ(4, 14); W().frame(60); W().frame(30); tapJ(4, 14); W().frame(80); ok(E('P.scySouls') === 3, 'souls cap at 3 (' + E('MV.scyHarvests') + ' harvests counted)');
go(1, 1); E('P.scyFade = 14.9'); W().frame(10); ok(E('P.scySouls') === 0, 'souls fade after 15 s without a harvest');
go(1, 2); E("P.inv = 0; P.iframes = 0; hurtPlayer(10, 1, 'scytest')"); W().frame(4);
const afterHurt = E('P.scySouls'); ok(afterHurt === 1, 'a blow that lands scatters a soul (2 -> ' + afterHurt + ')');
for (const [r, n, want, p] of [[1, 1, 1.6, 50], [1, 2, 2.4, 70], [1, 3, 3.2, 90], [4, 2, 3.2, 90]]) {
  go(r, n); W().dummy(36); W().down('heavy'); W().frame(16); W().up('heavy'); W().frame(80);
  const d = dm('scy_reap'), pz = W().log.filter(l => l.st === 'scy_reap').map(l => l.poise);
  ok(d[0] === want && E('P.scySouls') === 0, `rank ${r}, ${n} soul(s): hold K = Reap ${d.join('/')} (want ${want}), poise ${pz.map(x => x.toFixed(0)).join('/')}, souls spent`);
}
for (const [js, want, name] of [[1, 'scy_hook', 'J'], [2, 'scy_spiral', 'J J']]) {
  go(1, 2); W().dummy(36); E('window.__wm.follow = 36'); for (let i = 0; i < js; i++) { W().tap('attack', 2); W().frame(6); }
  W().down('heavy'); W().frame(40); W().up('heavy'); W().frame(80); const s = uniq(seq());
  ok(s.includes('scy_reap') && !W().log.some(l => l.st === want), `${name} + hold K with souls: the Reap (${s.join(' ')}) -- a tap stays the ${want}`);
}
go(); W().dummy(-30); E('P.scySouls = 3'); W().down('heavy'); W().frame(16); W().up('heavy'); W().frame(80); ok(dm('scy_reap').length === 1, 'the Reap cuts behind too');
for (const r of [4, 5]) { go(r, 3); E('P.hp = D.maxHp * 0.5'); const h0 = E('P.hp'); W().dummy(36); W().down('heavy'); W().frame(16); W().up('heavy'); W().frame(80); const g = E('P.hp') - h0; ok(r === 5 ? Math.abs(g - E('D.maxHp') * 0.06) < 2 : g === 0, `rank ${r}: a connecting Reap heals ${g.toFixed(1)} (V: 2% x 3 souls = ${(E('D.maxHp') * 0.06).toFixed(1)})`); }

// ---- up J, L -> J, L -> K
go(); W().dummy(30); W().down('up'); W().tap('attack', 2); W().up('up'); W().frame(50); ok(dm('scy_up').join() === '1', 'up J: rising harvest 1.0');
go(); W().dummy(110); W().tap('roll', 2); W().frame(14); W().tap('attack', 2); W().frame(50); ok(dm('scy_rollj').join() === '1', 'L -> J: ghost slash 1.0');
go(); W().dummy(110); W().tap('roll', 2); W().frame(14); W().tap('heavy', 2); W().frame(60); ok(dm('scy_rollk').join() === '1.1', 'L -> K: leg sweep 1.1 (rank I, as C4)');

// ---- I: hook step (small foe; boss gated to III), I -> J backstab (II)
go(); W().dummy(30); W().tap('parry', 2); W().frame(40);
const dx = E('enemies.find(e => e.wmDummy).x'); ok(E('P.x') > dx + 8 && E('P.face') === -1, `I: hook step lands behind the foe (${E('P.x').toFixed(0)} vs foe ${dx.toFixed(0)}) facing it (${E('P.face')})`);
go(); W().dummy(30, { boss: true }); W().tap('parry', 2); W().frame(40); ok(E('P.x') < E('enemies.find(e => e.wmDummy).x') && E('P.face') === 1, 'rank I: no hook round a boss (a short step instead)');
go(3); W().dummy(30, { boss: true }); W().tap('parry', 2); W().frame(40); ok(E('P.x') > E('enemies.find(e => e.wmDummy).x') && E('P.face') === -1, 'rank III: the hook step swings round a boss');
for (const r of [1, 2]) { go(r); W().dummy(30); W().tap('parry', 2); W().frame(6); W().tap('attack', 2); W().frame(60); const s = uniq(seq()); ok(r === 1 ? !s.includes('scy_backstab') : dm('scy_backstab').join() === '1.6', `rank ${r} I -> J: ${s.join(' ') || 'nothing'}`); }
go(); W().dummy(300); W().tap('parry', 2); const x0 = E('P.x'); W().frame(40); ok(Math.abs(E('P.x') - x0 - 26) < 4 && E('P.face') === 1, `I with nothing to hook: a short step (${(E('P.x') - x0).toFixed(0)} px)`);
go(); W().dummy(30); W().tap('parry', 2); let inv = 0; for (let i = 0; i < 20; i++) { W().frame(1); if (E('mvIframes()')) inv++; } ok(inv >= 12, `hook step is invulnerable through the swing (${inv} of 20 frames)`);

// ---- air: J, J J (crescent dive), down J, K (grave plunge)
go(); W().dummy(26); W().tap('jump', 2); W().frame(8); W().tap('attack', 2); W().frame(6); W().tap('attack', 2); W().frame(60);
ok(uniq(seq()).join() === 'scy_air,scy_dive' && E('P.ground'), 'air J J: air arc, crescent dive to the floor: ' + uniq(seq()).join(' '));
go(); W().tap('jump', 2); W().frame(18); W().dummy(0); W().down('down'); W().tap('attack', 2); W().frame(30); W().up('down'); W().frame(40); ok(seq().includes('scy_down'), 'air down J: grave pogo');
go(); W().tap('jump', 2); W().frame(10); W().tap('heavy', 2); const ps = states(50); W().frame(30);
ok(E("P.anim") && ps.includes('plunge'), 'air K: the grave plunge');
go(); W().tap('jump', 2); W().frame(10); W().tap('heavy', 2); let tags = new Set(); for (let i = 0; i < 50; i++) { W().frame(1); tags.add(E('P.anim.tag')); } ok(tags.has('scy_plunge'), 'grave plunge falls on its own tag: ' + [...tags].join(' '));

// ---- step distances: no move travels more than ~36 px with forward held (the hook step is the deliberate exception)
const far = [];
const travel = (name, pre, btn, hold) => {
  go(); if (pre) { W().tap('roll', 2); W().frame(14); }
  W().down('right'); if (hold) W().down('heavy'); else W().tap(btn, 2);
  let x0 = null, id = null;
  for (let i = 0; i < 120; i++) { const s = E('P.state'); if (x0 === null && ATKS(s)) { x0 = E('P.x') - E('P.vx') / 60; id = s; } if (hold && i === 30) W().up('heavy'); if (x0 !== null && s !== id && !ATKS(s)) break; if (x0 !== null && s !== id) { id = s; } W().frame(1); }
  W().up('right'); W().up('heavy'); const d = Math.abs(E('P.x') - x0); far.push(name + ' ' + d.toFixed(0)); return d;
};
const ATKS = s => E(`!!(ATK['${s}'] && ATK['${s}'].mv)`);
const tr = [travel('J', false, 'attack'), travel('K', false, 'heavy'), travel('L->J', true, 'attack'), travel('L->K', true, 'heavy'), travel('hold K', false, null, true)];
ok(tr.every(d => d <= 38), 'no move travels more than ~36 px with forward held');
out.push('INFO travel with forward held: ' + far.join(', '));
// ---- a real boss (Gravetusk, C5): the hook step at III swings round it, a Reap lands on it
{
  W().reset('scythe', 3); E('enemies = enemies.filter(e => !e.wmDummy)');
  delete G.SAVE.flags['boss:hound']; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'hound'] = 1;
  G.tp('C5', 6, 10); const b = G.boss;
  for (let i = 0; i < 200 && !b.active; i++) { W().down('right'); W().frame(4); W().up('right'); G.P.hp = 99999; }
  W().reset('scythe', 3); E('enemies = enemies.filter(e => !e.wmDummy)');
  const bx = b.x, by0 = b.y; b.update = function (dt) { this.x = bx; this.y = by0; this.commonUpdate(dt); }; b.hp = 1e7; b.state = 'idle';
  const hb = E('hbOf(boss)'); G.P.x = hb.x0 - 30; G.P.face = 1; G.P.vx = 0; W().frame(2);
  W().tap('parry', 2); W().frame(40);
  ok(G.P.x > hb.x1 && G.P.face === -1, `rank III vs Gravetusk: hook step from ${Math.round(hb.x0 - 30)} lands at ${Math.round(G.P.x)} past its far edge ${Math.round(hb.x1)}, facing it`);
  let got = 0; const oh = b.hit; b.hit = function (info) { if (G.P.state === 'scy_reap') got += info.dmg / G.D.light; return oh.call(this, info); };
  E('P.scySouls = 3; P.st = D.maxSt'); W().down('heavy'); W().frame(16); W().up('heavy'); W().frame(80); b.hit = oh;
  ok(Math.abs(got - 3.2) < 0.3, `a 3-soul Reap on Gravetusk lands ${got.toFixed(2)} (x AR)`);
}
out.push(fail.length ? `${fail.length} FAILED` : 'ALL OK');
return out;
