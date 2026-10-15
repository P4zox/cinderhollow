// v15 cores flow: the first-kill drop (single and multi-body bosses), the Ashwright's Enchant screen driven by real inputs,
// the inventory category, the save/load round trip and New Game+.
// Run: SHOT_HTML=web/dist/v15_cores.html node tools/shots/shot.js tools/shots/v15/cores/flow.js <out>
await boot();
const R = [], T = (name, pass, detail = '') => R.push(`${pass ? 'OK ' : 'BAD'} ${name}${detail ? '  [' + detail + ']' : ''}`);
const C = G.cores, E = C.ev, sleep = ms => new Promise(r => setTimeout(r, ms));
const step = (n = 1, tap = []) => G.step(n, [], tap);
E(`SETTINGS.god = 1; SAVE.cinders = 5000; for (const k of Object.keys(BOSS_INFO)) for (const f of ['cut:', 'cutp2:', 'cutp3:']) SAVE.flags[f + k] = 1;`);
const home = k => E(`(() => { const b = trnBosses().find(b => b.kind === '${k}'); const st = TRN_PSTART['${k}'] || trnStartNear(ROOM_BY[b.room], b.hx, b.hy); return [b.room, st[0], st[1]]; })()`);
async function killBoss(k) {
  E('window.__woke = undefined');
  for (let i = 0; i < 400; i++) {
    const s = E(`(() => { if (!boss) return 'none'; if (!boss.alive) return 'dead'; if (!boss.active && !boss.cutting) boss.activate();
      if (['intro', 'dormant', 'summon', 'rise', 'transform'].includes(boss.state) || boss.cutting || state === 'cut') return 'alive'; if (!boss.active) return 'alive'; if (window.__woke === undefined) window.__woke = 0; if (window.__woke++ < 30) return 'alive';
      if (boss.pendingPhase && boss.enterPhase2 && boss.phase < 2) {}
      for (const t of targets()) if (crBossy(t) && t.alive !== false) t.hit({ dmg: Math.max(60, (t.maxHp || boss.maxHp || 2000) * 0.25), poise: 0, dir: 1, kind: 'heavy', x: t.x, y: t.y - 20, melee: true, big: true }); return 'alive'; })()`);
    if (s !== 'alive') return s;
    step(8);
    for (let j = 0; j < 40 && G.state === 'cut'; j++) step(15); if (G.state === 'dialog') E('dialog = null; state = "play"');
  }
  return 'timeout';
}
// ---------------------------------------------------------------- 1) drops: Gravetusk (single), the Twins and the Sentinels (multi-body)
for (const k of ['hound', 'twins', 'sentinels']) {
  const [rm, tx, ty] = home(k);
  G.tp(rm, tx, ty); step(30);
  const had = E(`!!(SAVE.cores && SAVE.cores['${k}'])`), em0 = E('SAVE.inv.emberstone || 0'), c0 = E('SAVE.cinders');
  const res = await killBoss(k);
  step(60); await sleep(200);
  const got = E(`!!SAVE.cores['${k}']`), flag = E(`!!SAVE.flags['boss:${k}']`);
  T(`${k}: first kill drops its Core (${res})`, !had && got && flag, `core ${got}, flag ${flag}`);
  T(`${k}: the boss's own cinders still pay out`, E('SAVE.cinders') > c0, `${c0} -> ${E('SAVE.cinders')}`);
  if (k === 'hound') { await sleep(2600 + E('BOSS_INFO.hound.reward.length') * 2400 + 900); step(2); T('hound: the reward caches still convert (Emberstones)', E('SAVE.inv.emberstone || 0') > em0, `${em0} -> ${E('SAVE.inv.emberstone || 0')}`);
    T('hound: the Core banner shows', E('bannerMsg && bannerMsg.title') === E("CORES.hound.name"), String(E('bannerMsg && bannerMsg.title'))); }
  // a second kill of the same boss never duplicates it (forced through rewards())
  E(`(() => { const n = Object.keys(SAVE.cores).length; BossBase.prototype.rewards.call({ kind: '${k}', x: P.x, y: P.y }); window.__crN = [n, Object.keys(SAVE.cores).length]; })()`);
  const nn = E('window.__crN'); T(`${k}: a repeat kill gives no second Core`, nn[0] === nn[1], nn.join(' -> '));
  T(`${k}: the effigy rises once the fight is over`, (step(300), E(`props.some(p => p.type === 'cr_effigy' && p.kind === '${k}')`)));
}
// a save written DURING the rematch rebuild (an enter hook that saves) still holds the boss flag
{ const [rm, tx, ty] = home('hound'); G.tp(rm, tx, ty); step(80);
  const r = E(`(() => { window.__crSaved = null; const h = () => { saveGame(); window.__crSaved = JSON.parse(localStorage.getItem(SAVE_KEY)).flags['boss:hound']; }; HOOKS.enter.push(h);
    let ok; try { ok = crRekindle('hound'); } finally { HOOKS.enter.splice(HOOKS.enter.indexOf(h), 1); }
    return [ok, window.__crSaved, SAVE.flags['boss:hound'], !!(boss && boss.rematch)]; })()`);
  T('a save made while the arena is rebuilt still holds the boss flag', r[0] === true && r[1] === 1 && r[2] === 1 && r[3], JSON.stringify(r));
  E('REM.on = null'); G.tp('C2', 10, 10); step(10); }

// ---------------------------------------------------------------- 2) the Ashwright: talk, pick "Enchant a weapon", set the Core, leave
G.tp('C2', 10, 10); step(20);
E(`(() => { const a = props.find(p => p.type === 'npc' && p.id === 'ashwright'); P.x = a.x - 12; P.y = a.y; P.face = 1; P.vx = 0; setP('idle', 'idle', true); })()`); step(4);
step(1, ['interact']);
T('talking to the Ashwright opens a dialogue', G.state === 'dialog', G.state);
for (let i = 0; i < 12 && !E('!!(dialog && dialog.steps[dialog.i] && dialog.steps[dialog.i].choice)'); i++) { step(1, ['confirm']); step(1, ['confirm']); }
const labels = E('dialog && dialog.steps[dialog.i].choice ? dialog.steps[dialog.i].choice.map(c => c[0]) : []');
const ei = labels.indexOf('Enchant a weapon');
T('the Ashwright offers "Enchant a weapon" (right after Temper)', ei === labels.findIndex(l => /^Temper/.test(l)) + 1, labels.join(' | '));
for (let i = 0; i < ei; i++) step(1, ['down']);
step(1, ['confirm']);
T('it opens the Enchant screen', G.state === 'menu' && E('menu && menu.screen') === 'enchant', `${G.state} ${E('menu && menu.screen')}`);
await snap('enchant_menu');
const ty = E('wtype()'), cin0 = E('SAVE.cinders');
// the list: hound, twins, sentinels (journey order); pick the Twins' core (row 2 when nothing is set: hound, twins, sentinels)
const rows = E('crRows().map(r => r.core || ("-" + r.remove))');
step(1, ['down']); step(1, ['confirm']);
T('Enter sets the chosen Core in the weapon in hand', E(`SAVE.enchants['${ty}']`) === rows[1], `${E(`SAVE.enchants['${ty}']`)} (rows ${rows.join(',')})`);
T(`setting costs ${E('CR_COST')} cinders`, cin0 - E('SAVE.cinders') === E('CR_COST'), `${cin0} -> ${E('SAVE.cinders')}`);
step(30); await snap('enchant_set');
T('the screen now offers "Remove" first', E('crRows()[0].remove') === rows[1]);
// remove (free) and set the hound core instead
const cin1 = E('SAVE.cinders');
E('menu.sel = 0'); step(1, ['confirm']);
T('Remove returns the Core for free', !E(`SAVE.enchants['${ty}']`) && E('SAVE.cinders') === cin1 && E(`!!SAVE.cores['${rows[1]}']`));
E('menu.sel = 0'); step(1, ['confirm']);
T('the hound Core goes in', E(`SAVE.enchants['${ty}']`) === 'hound');
// a Core sits in one weapon at a time: moving it to another type takes it from the first
E(`(() => { crSocket('twins', 'katana'); crSocket('twins', 'spear'); })()`);
T('one Core, one weapon: setting it elsewhere moves it', E(`SAVE.enchants.katana === undefined && SAVE.enchants.spear === 'twins'`));
step(1, ['back']);
for (let i = 0; i < 6 && G.state !== 'play'; i++) step(2, ['confirm']);
T('leaving returns to the world', G.state === 'play', G.state);
// ---------------------------------------------------------------- 3) the inventory: Boss Cores
E(`openPauseMenu(); menu.tab = 1; menu.cat = INV_CATS.findIndex(c => c.k === 'core'); menu.bar = false; menu.isel = 0`);
step(1); await snap('inventory_cores');
const inv = E(`catEntries(INV_CATS.find(c => c.k === 'core')).map(e => e.name + (e.where ? ' @' + e.where : ''))`);
T('the inventory lists the Cores with where they sit', inv.length === 3 && inv.some(s => s.includes('@' + ty)), inv.join(' | '));
E('menu.isel = 1'); step(1); await snap('inventory_core2');
E('closeMenu()'); step(2);
// ---------------------------------------------------------------- 4) save / load round trip, and New Game+
E('saveGame()');
const back = E(`(() => { const s = loadGame(); return { cores: s.cores, enchants: s.enchants }; })()`);
T('save/load keeps Cores and enchants', JSON.stringify(back.cores) === JSON.stringify(E('SAVE.cores')) && JSON.stringify(back.enchants) === JSON.stringify(E('SAVE.enchants')), JSON.stringify(back));
E('continueGame()'); step(10);
T('continue: the journey still has them', E(`SAVE.cores.hound === 1 && SAVE.enchants['${ty}'] === 'hound'`));
const pre = E('JSON.stringify([SAVE.cores, SAVE.enchants])');
E('startNGPlus()'); step(10);
T('New Game+ keeps every Core and enchant (bosses are back)', E('JSON.stringify([SAVE.cores, SAVE.enchants])') === pre && !E(`SAVE.flags['boss:hound']`), E('JSON.stringify([SAVE.cores, SAVE.enchants])'));
// the NG+ first kill doesn't duplicate (still one hound core)
{ const [rm, tx, ty2] = home('hound'); E(`for (const f of ['cut:', 'cutp2:', 'cutp3:']) SAVE.flags[f + 'hound'] = 1; SETTINGS.god = 1`); G.tp(rm, tx, ty2); step(20); await killBoss('hound'); step(30);
  T('New Game+ kill: no second hound Core', E('Object.keys(SAVE.cores).length') === 3 && E('SAVE.cores.hound') === 1); }
return R;
