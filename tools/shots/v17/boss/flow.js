// the fight's flow: phase changes (with their scenes), tempering (the window runs out -> he re-tempers; a stance break
// cools him), a fatality on the stagger, the death -> the Core left in the ash -> taking it sets w2:open and calls
// cfFurnaceOpen; a rematch (Rekindle) never drops it again.
const out = {}; const H = window.__hk;
E(`window.__furnace = 0; if (typeof cfFurnaceOpen === 'function') { const _o = cfFurnaceOpen; cfFurnaceOpen = function () { window.__furnace++; return _o.apply(this, arguments); }; } else { window.__furnaceMissing = 1; }`);   // AREA's hook, counted
out.summon = E('window.__hk.arena()'); out.room = E('room.id'); out.wake = E('window.__hk.wake()');
E('SAVE.flags["cutp2:hearthkeeper"] = 0; SAVE.flags["cutp3:hearthkeeper"] = 0; delete SAVE.flags["w2:open"]; SAVE.cores = {}');
const st = () => E(`({ st: boss.state, tag: boss.tag, ph: boss.phase, hp: Math.round(boss.hp), max: boss.maxHp, temper: boss.temper, tWin: +boss.tWin.toFixed(1), dark: HK.darkOn, biome: room.def.biome, cut: !!cut, props: HK.props.map(p => p.kind).join(',') })`);
out.start = st();
// --- tempering: run the window out
E('boss.tWin = 0.05; boss.cool = 0; window.__hk.front(80)');
let saw = null;
for (let i = 0; i < 400; i++) { E('window.__hk.frame(1); P.hp = D.maxHp'); const s = st(); if (s.tag === 'temper' && !saw) saw = i; if (saw !== null && s.temper > 0) break; }
out.temper1 = { sawTemperAt: saw, ...st() };
E('render()'); await snap('flow_tempered_p1');
// a tempered hammer attack, then a stance break cools it
E('boss.cool = 99; boss.setS("idle","idle"); boss.begin("slam")'); for (let i = 0; i < 40; i++) E('window.__hk.frame(1); P.hp = D.maxHp');
E('render()'); await snap('flow_tempered_slam');
for (let i = 0; i < 120; i++) E('window.__hk.frame(1); P.hp = D.maxHp');
E('boss.stagger()');
out.afterStagger = st();
// --- fatality on the stagger
let ok = false;
for (let i = 0; i < 40 && !ok; i++) { E('window.__hk.frame(1)'); ok = E(`(() => { const q = boss; if (!q.critable()) return false; const side = P.x < q.x ? -1 : 1; P.y = q.floor; P.vy = 0; P.ground = true; P.x = q.x + side * (q.critRange - 10); P.face = -side; P.state = 'idle'; P.anim.set('idle', true); return critTarget() === q; })()`); }
out.critable = ok;
if (ok) {
  const hp0 = E('boss.hp'); E('clearBuffer(); held.clear(); press("heavy")'); E('window.__hk.frame(1); release("heavy")');
  out.fatStarted = E('P.state');
  let f = 0; for (; f < 400 && E('!!FAT.on'); f++) { E('window.__hk.frame(1)'); if (f === 40) { E('render()'); await snap('flow_fatality'); } }
  out.fatality = { frames: f, dealt: hp0 - E('boss.hp'), last: E('FAT.last && FAT.last.name') };
}
for (let i = 0; i < 200; i++) E('window.__hk.frame(1); P.hp = D.maxHp');
out.afterFatality = st();
// --- phase 2: push past 66%
E('boss.hit({ dmg: Math.round(boss.hp - boss.maxHp * 0.6), poise: 0, dir: 1, kind: "light", x: boss.x, y: boss.y - 40 })');
out.pending2 = E('boss.pendingPhase');
let cutSeen = false;
for (let i = 0; i < 900; i++) { E('window.__hk.play(1); P.hp = D.maxHp'); const s = st(); if (s.cut) cutSeen = true; if (s.cut && i % 40 === 20) { E('render()'); if (!out.snap2) { out.snap2 = 1; } } if (i === 60) { E('render()'); await snap('flow_p2shift'); } if (s.ph === 2 && !s.cut && s.st !== 'transform') break; }
out.phase2 = { cutSeen, ...st() };
for (let i = 0; i < 300; i++) E('window.__hk.play(1); P.hp = D.maxHp');
E('render()'); await snap('flow_p2_fight');
// --- phase 3
E('boss.stanceImmune = 0; boss.hit({ dmg: Math.round(boss.hp - boss.maxHp * 0.25), poise: 0, dir: 1, kind: "light", x: boss.x, y: boss.y - 40 })');
cutSeen = false;
for (let i = 0; i < 900; i++) { E('window.__hk.play(1); P.hp = D.maxHp'); const s = st(); if (s.cut) cutSeen = true; if (i === 90) { E('render()'); await snap('flow_p3shift'); } if (s.ph === 3 && !s.cut && s.st !== 'transform') break; }
out.phase3 = { cutSeen, ...st() };
for (let i = 0; i < 240; i++) E('window.__hk.play(1); P.hp = D.maxHp');
E('render()'); await snap('flow_p3_dark');
// --- death -> core in the ash
E('boss.stanceImmune = 0; boss.hit({ dmg: boss.hp + 10, poise: 0, dir: 1, kind: "light", x: boss.x, y: boss.y - 40 })');
let coreAt = null;
for (let i = 0; i < 700; i++) { E('window.__hk.play(1); P.hp = D.maxHp'); if (i === 60) { E('render()'); await snap('flow_death'); } if (E('props.some(p => p.type === "hk_core")')) { coreAt = i; break; } }
for (let i = 0; i < 60; i++) E('window.__hk.play(1)');
out.death = { coreAt, flag: E('SAVE.flags["boss:hearthkeeper"]'), w2: E('SAVE.flags["w2:open"]'), owned: E('!!(SAVE.cores && SAVE.cores.hearthkeeper)'), dark: E('HK.darkOn'), save: E('JSON.stringify(SAVE.hk || null)') };
E('render()'); await snap('flow_core');
// take it
E('const c = props.find(p => p.type === "hk_core"); if (c) { P.x = c.x; P.y = c.y; c.interact(); }');
for (let i = 0; i < 30; i++) E('window.__hk.play(1)');
out.furnaceMissing = E('!!window.__furnaceMissing');
out.taken = { w2: E('SAVE.flags["w2:open"]'), owned: E('!!(SAVE.cores && SAVE.cores.hearthkeeper)'), furnace: E('window.__furnace || 0'), propLeft: E('props.some(p => p.type === "hk_core")') };
// --- a rematch: no core, flag stays
E('SAVE.cores = {}'); out.effigy = E('props.some(p => p.type === "cr_effigy")');
out.rekindle = E('crRekindle("hearthkeeper")'); E('window.__hk.wake()');
E('boss.phase = 3; boss.stanceImmune = 0; boss.hit({ dmg: boss.hp + 10, poise: 0, dir: 1, kind: "light", x: boss.x, y: boss.y - 40 })');
for (let i = 0; i < 700; i++) E('window.__hk.play(1); P.hp = D.maxHp');
out.rematch = { core: E('props.some(p => p.type === "hk_core")'), w2: E('SAVE.flags["w2:open"]'), owned: E('!!SAVE.cores.hearthkeeper') };
out.errs = E('window.__hk.errs.slice(0, 8)');
return out;
