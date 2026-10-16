// MOVEHELP: the combo-hint matcher on all 14 types (run with tools/shots/wm/run.sh: the WM prelude gives W(), E, arena()).
// SHOT_HTML=web/dist/movehelp.html sh tools/shots/wm/run.sh tools/shots/movehelp/hints.js tools/shots/movehelp/out
const out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
const B = { J: 'attack', K: 'heavy', I: 'parry', L: 'roll' };
const TYPES = E('MV.order');
const show = () => E('MH.show.map(c => c.parts.join(".") + "=" + c.name)');
const keys = () => E('MH.show.map(c => c.parts.join("."))');
const has = (k, name) => show().some(s => s.startsWith(k + '=') && (!name || s.includes(name)));
const go = (type, rank = 5) => { arena(); W().reset(type, rank); E("P.x = 120; P.y = 304; P.vx = 0; P.vy = 0; P.ground = true; P.face = 1; MH.show = []; MH.alpha = 0; MH.key = ''; MH.press = -9; MH.ctxT = -9"); W().frame(2); };
const until = (cond, max = 90) => { for (let i = 0; i < max; i++) { if (E(cond)) return i; W().frame(1); } return -1; };

// ---------------------------------------------------------------- 1. every combos entry is mapped (or marked "not a move")
for (const t of TYPES) {
  const r = E(`(() => { const B = mhBuild('${t}'); const bad = [];
    for (const p of B.paths) for (const n of [p.from, ...p.steps.map(s => s.node)]) if (n && !(n[0] === '@' || ATK[n] || MV_STATES[n] || ['spdive'].includes(n))) bad.push(p.e.name + ':' + n);
    for (const p of B.paths) if (p.ctx && !MH_CTX[p.ctx]) bad.push('ctx ' + p.ctx);
    return { n: B.rows.length, combos: MV.types['${t}'].combos.length, mapped: B.rows.filter(r => r.paths.length).length, none: B.rows.filter(r => r.none).map(r => r.e.name), fatal: B.rows.filter(r => r.fatal).length, unres: B.unres, bad }; })()`);
  ok(r.n === r.combos && !r.unres.length && !r.bad.length && r.mapped + r.none.length + r.fatal === r.n,
    `${t}: ${r.mapped}/${r.n} entries mapped to moves, ${r.none.length} not a move${r.none.length ? ' (' + r.none.join(', ') + ')' : ''}, fatality ${r.fatal}${r.unres.length ? ' UNRESOLVED ' + r.unres : ''}${r.bad.length ? ' BAD ' + r.bad : ''}`);
}

// ---------------------------------------------------------------- 2. the matcher, statically: every step of every path is offered at the step before
for (const t of TYPES) {
  const r = E(`(() => { const B = mhBuild('${t}'); let n = 0, hit = 0; const miss = [];
    const saved = {}; for (const k of Object.keys(MH_CTX)) saved[k] = MH_CTX[k];
    for (const p of B.paths) {
      const st = p.steps;
      for (let i = 0; i < st.length - 1; i++) {
        if (!(ATK[st[i].node] && ATK[st[i].node].mv)) continue;   // pseudo / state nodes: checked live below
        n++;
        const c = mhCands({ type: '${t}', nodes: [st[i].node], rank: 5, max: 12, noRoot: true });
        const k = st[i + 1].parts.join('.');
        if (c.some(x => x.parts.join('.') === k)) hit++; else miss.push(p.e.name + ' @' + st[i].node + ' ' + k);
      }
    }
    return { n, hit, miss }; })()`);
  ok(r.hit === r.n, `${t}: each next step offered at the step before: ${r.hit}/${r.n}${r.miss.length ? ' missing ' + r.miss.slice(0, 4).join('; ') : ''}`);
}

// ---------------------------------------------------------------- 3. rank gating: at Mastery I nothing above rank I is offered anywhere
for (const t of TYPES) {
  const r = E(`(() => { const B = mhBuild('${t}'); const bad = [], nodes = new Set();
    for (const p of B.paths) { if (p.from) nodes.add(p.from); for (const s of p.steps) nodes.add(s.node); }
    let n = 0;
    for (const nd of nodes) for (const c of mhCands({ type: '${t}', nodes: [nd], rank: 1, max: 12, noRoot: true })) { n++;
      const rk = (c.e && c.e.rank) || 1, mr = ATK[c.dest] && ATK[c.dest].mv && ATK[c.dest].mv.rank || 1;
      if (rk > 1 || mr > 1) bad.push(nd + '->' + c.name); }
    const hi = []; for (const nd of nodes) for (const c of mhCands({ type: '${t}', nodes: [nd], rank: 5, max: 12, noRoot: true })) if ((c.e && c.e.rank || 1) > 1) hi.push(c.name);
    return { n, bad, hi: [...new Set(hi)].length }; })()`);
  ok(!r.bad.length && (r.hi > 0 || t === 'bow'), `${t}: rank I offers ${r.n} hints, none above rank I${r.bad.length ? ' BAD ' + r.bad.slice(0, 3) : ''}; rank V adds ${r.hi} mastery moves`);
}

// ---------------------------------------------------------------- 4. live: every plain J/K chain of every type, pressed for real, shows its next press
for (const t of TYPES) {
  const paths = E(`mhBuild('${t}').paths.filter(p => !p.from && p.steps.length >= 2 && (!p.ctx || ['blade', 'drawn', 'swift'].includes(p.ctx)) && p.steps.every(s => /^[JK]$/.test(s.parts.join('.')) && ATK[s.node] && ATK[s.node].mv)).map(p => ({ name: p.e.name, steps: p.steps.map(s => [s.parts.join('.'), s.node]) }))`);
  let n = 0, good = 0; const miss = [];
  for (const p of paths) {
    go(t, 5); W().dummy(30);
    for (let i = 0; i < p.steps.length - 1; i++) {
      const [k, node] = p.steps[i];
      if (i === 0) W().tap(B[k], 2);
      if (until(`P.state === '${node}'`, 90) < 0) { miss.push(`${p.name}: never reached ${node} (in ${E('P.state')})`); break; }
      W().frame(2); n++;
      const want = p.steps[i + 1][0];
      if (keys().includes(want)) good++; else miss.push(`${p.name} @${node}: no ${want} in [${show().join(', ')}]`);
      W().tap(B[want], 2);
    }
  }
  ok(n > 0 && good === n, `${t}: live chains (${paths.length} paths, ${n} prefixes): the next press is shown ${good}/${n}${miss.length ? ' -- ' + miss.slice(0, 3).join(' | ') : ''}`);
}

// ---------------------------------------------------------------- 5. live specifics (contexts, dodges, air, guard)
go('longsword', 5); W().tap('attack', 2); W().frame(10); W().tap('attack', 2); until("P.state === 'attack2'"); W().frame(3);
ok(has('J', 'Light chain') && has('K', 'Horizontal slash') && has('pause.J', 'Wheel slash'), `Longsword J J: ${show().join(' / ')} (head "${E('MH.head')}")`);
go('longsword', 1); W().tap('attack', 2); W().frame(10); W().tap('attack', 2); until("P.state === 'attack2'"); W().frame(3);
ok(has('J') && has('K') && !has('pause.J'), `Longsword J J at Mastery I: no wheel slash (${show().join(' / ')})`);
go('longsword', 5); W().tap('roll', 2); W().frame(4);
ok(has('J', 'Quick slash') && has('K', 'Wheeling cut') && E('MH.head') === 'Dodge', `Longsword roll: ${show().join(' / ')}`);
go('longsword', 5); W().down('jump'); W().frame(6); W().up('jump'); W().frame(4);
ok(!E('P.ground') && has('air.J') && has('air.↓.J') && has('air.K'), `Longsword airborne: ${show().join(' / ')}`);
W().tap('attack', 2); W().frame(4); ok(has('J', 'Falling crescent'), `Longsword air J: ${show().join(' / ')}`); W().frame(90);
go('katana', 5); W().tap('parry', 2); until("P.sheathed", 60); W().frame(24);
ok(has('J', 'Draw cut') && has('K', 'Iai draw') && has('hold.K', 'Focus draw') && E('MH.head') === 'Sheathed', `Katana after I (sheathed): ${show().join(' / ')}`);
W().tap('heavy', 2); until("P.state === 'kt_iai'"); W().frame(3);
ok(has('J', 'Swallow return'), `Katana Iai: ${show().join(' / ')}`);
go('dual', 5); W().tap('parry', 2); until('P.demon', 30); W().frame(16);
ok(has('K', 'Demon flurry') && E('MH.head') === 'Demon Mode', `Dual blades after I (Demon Mode): ${show().join(' / ')}`);
W().tap('heavy', 2); until("P.state === 'tw_dflurry'"); W().frame(3);
ok(has('J', 'Bloodwheel'), `Dual Demon K: ${show().join(' / ')}`);
go('fist', 5); E("P.ftStyle = 'swift'"); W().frame(2); W().tap('parry', 2); W().frame(40);
ok(E('ftIron()') && has('J', 'Iron palm') && has('K', 'Hammer fist'), `Fist I (to Iron): ${show().join(' / ')} (head "${E('MH.head')}")`);
go('fist', 5); E("P.ftStyle = 'swift'"); W().tap('attack', 2); until("P.state === 'ft_jab'"); W().frame(2);
ok(has('J', 'Cross') && has('K', 'Rising knee') && has('I'), `Fist Swift J: ${show().join(' / ')}`);
go('saxe', 5); E('P.sxG = 100; P.sxLock = true'); W().frame(2); W().tap('parry', 2); until('P.sxAxe && P.state === "idle"', 120); W().frame(2);
ok(has('J', 'Wild swing'), `Switch axe, the morph slash's own route: ${show().join(' / ')}`); W().frame(22);
ok(E('P.sxAxe') && has('J', 'Overhead') && has('K', 'Rev thrust'), `Switch axe, I at a full gauge -> axe mode: ${show().join(' / ')} (head "${E('MH.head')}")`);
go('sns', 5); W().down('parry'); W().frame(30);
ok(['guard', 'block'].includes(E('P.state')) && has('K', 'Shield slam'), `Sword & shield holding the guard (${E('P.state')}): ${show().join(' / ')}`); W().up('parry'); W().frame(20);
go('greatsword', 5); W().tap('attack', 2); W().frame(8); W().tap('attack', 2); until("P.state === 'gs_2'"); W().frame(2);
ok(has('J') && has('K'), `Greatsword J J: ${show().join(' / ')}`);
go('scythe', 5); W().tap('attack', 2); until("P.state === 'scy_1'"); W().frame(2);
ok(has('J') && has('K', 'Hook pull'), `Scythe J: ${show().join(' / ')}`);

// ---------------------------------------------------------------- 6. the fatality on a staggered foe in range (and the riposte)
for (const t of ['longsword', 'maul', 'bow']) {
  go(t, 5); const d = W().dummy(20);
  E("(() => { const d = enemies.find(e => e.wmDummy); d.state = 'stagger'; d.critable = function () { return this.state === 'stagger'; }; })()");
  W().frame(3);
  const s = show(), nm = E(`fatDef('${t}').name`);
  ok(s[0] === 'K=Fatality: ' + nm && s.includes('J=Riposte') && E('MH.head') === 'Staggered', `${t}: staggered foe in range -> ${s.join(' / ')}`);
  E("enemies.find(e => e.wmDummy).state = 'idle'"); W().frame(30);
  ok(!E('MH.show.some(c => c.fatal)') || E('MH.alpha') < 0.5, `${t}: the stagger ends -> the fatality hint goes (alpha ${E('MH.alpha').toFixed(2)})`);
}
go('longsword', 5); W().dummy(90); E("(() => { const d = enemies.find(e => e.wmDummy); d.state = 'stagger'; d.critable = function () { return true; }; })()"); W().frame(3);
ok(!E('MH.show.some(c => c.fatal)'), 'a staggered foe out of range: no fatality hint');

// ---------------------------------------------------------------- 7. fade: in after a press, out ~1.2 s after the chain ends; nothing without a press
go('longsword', 5); W().frame(30); ok(E('MH.alpha') === 0 && !E('MH.show.length'), 'standing still: no hint');
W().tap('attack', 2); W().frame(6); const aIn = E('MH.alpha');
until("P.state === 'idle'", 90); const t0 = E('P.clk'); until('MH.alpha < 0.99', 200); const tOut = E('P.clk') - t0;
until('MH.alpha === 0', 200); const tGone = E('P.clk') - t0;
ok(aIn > 0.6 && tOut > 1.1 && tOut < 1.8 && tGone < 2.2, `fade: in ${aIn.toFixed(2)} after 6 frames, starts fading ${tOut.toFixed(2)} s after the chain ends, gone at ${tGone.toFixed(2)} s`);

// ---------------------------------------------------------------- 8. the setting, menus, bound keys
go('longsword', 5); E('SETTINGS.combohint = 0'); W().tap('attack', 2); W().frame(6);
ok(!E('MH.show.length') && E('MH.alpha') === 0, 'Combo hints Off: nothing shows');
E('SETTINGS.combohint = 1'); W().frame(60);
const row = E("SETTING_ROWS.findIndex(r => r.k === 'combohint')"), qrow = E("SETTING_ROWS.findIndex(r => r.k === 'quit')");
ok(row === qrow - 1 && E("SETTING_ROWS.findIndex(r => r.k === 'cheats')") === 9 && E(`SETTING_ROWS[${row}].label`) === 'Combo hints' && E(`SETTING_ROWS[${row}].toggle`) === true, `Settings row "Combo hints" (toggle, row ${row}) just above "Save & quit"; Cheats stays row 9`);
E(`openPauseMenu(); menu.tab = 3; menu.sel = ${row}`); E("pauseInput('right')");
ok(E('SETTINGS.combohint') === 0, 'Settings › Combo hints › → turns it Off (saving: tools/shots/movehelp/panel.js, outside the Training Grounds sandbox)');
E("pauseInput('confirm')"); ok(E('SETTINGS.combohint') === 1, 'Enter turns it back On');
ok(E('mhHidden()'), 'hidden while the menu is open'); E("menu = null; state = 'play'"); W().frame(2);
E("bindKey('attack', 0, 'KeyF'); bindKey('heavy', 0, 'KeyG')");
ok(E("mhKeyName('J')") === 'F' && E("mhKeyName('K')") === 'G' && E("mhKeyName('I')") === 'I', `rebound keys show: J -> ${E("mhKeyName('J')")}, K -> ${E("mhKeyName('K')")}`);
E('BINDINGS = defaultBindings(); saveBindings()');
ok(E("mhKeyName('J')") === 'J', 'defaults restored');

out.push(fail.length ? `${fail.length} FAILED` : 'ALL OK');
return out;
