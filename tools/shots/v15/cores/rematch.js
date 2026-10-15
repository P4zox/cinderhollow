// v15 cores: Rekindle on every boss that can be rekindled (31: Venn is excluded by design).
// Per boss: the first kill in its own room (the Core drops) -> the effigy rises -> E, confirm -> the boss is back with
// rematch set and the arena sealed -> a save made mid-fight still holds the boss flag -> kill it -> flags, Cores, items and
// the ending untouched, Mastery +150 and 10% of its cinders -> the effigy rises again. Then: death in a rematch (nothing
// lost), two rematches in a row, Sovereign / First Ember never replay their ending.
// Run: SHOT_HTML=web/dist/v15_cores.html node tools/shots/shot.js tools/shots/v15/cores/rematch.js <out>
// window.__crOnly = ['hound', ...] limits the bosses.
await boot();
const R = [], T = (name, pass, detail = '') => R.push(`${pass ? 'OK ' : 'BAD'} ${name}${detail ? '  [' + detail + ']' : ''}`);
const C = G.cores, E = C.ev, sleep = ms => new Promise(r => setTimeout(r, ms));
const step = (n = 1, tap = []) => G.step(n, [], tap);
E(`SETTINGS.god = 1; for (const k of Object.keys(BOSS_INFO)) for (const f of ['cut:', 'cutp2:', 'cutp3:']) SAVE.flags[f + k] = 1; SAVE.flags.true_epilogue = 1;`);
const KINDS = window.__crOnly || E(`trnBosses().map(b => b.kind).filter(k => !CR_NO_REMATCH.has(k))`);
const home = k => E(`(() => { const b = trnBosses().find(b => b.kind === '${k}'); const st = TRN_PSTART['${k}'] || trnStartNear(ROOM_BY[b.room], b.hx, b.hy); return [b.room, st[0], st[1]]; })()`);
const unstick = () => { for (let i = 0; i < 60 && G.state === 'cine'; i++) { step(1, ['pause']); step(5); } for (let i = 0; i < 40 && G.state === 'cut'; i++) step(15); if (G.state === 'dialog') E('dialog = null; state = "play"'); if (G.state === 'cut') E('cut = null; state = "play"'); };
// killBoss: a quarter of its health a blow, one body at a time (phases are crossed the way a player crosses them), never
// during an intro or a transformation (a boss one-shot there stands back up)
async function killBoss() {
  E('window.__woke = undefined; window.__big = 0');
  for (let i = 0; i < 300; i++) {
    const s = E(`(() => { if (!boss) return 'none'; if (!boss.alive) return 'dead'; if (!boss.active && !boss.cutting) boss.activate();
      if (['intro', 'dormant', 'summon', 'rise', 'transform'].includes(boss.state) || boss.cutting || state === 'cut') return 'alive'; if (!boss.active) return 'alive'; if (window.__woke === undefined) window.__woke = 0; if (window.__woke++ < 10) return 'alive';
      if (window.__woke > 120) window.__big = 1; for (const t of targets()) if (crBossy(t) && t.alive !== false) t.hit({ dmg: window.__big ? 99999 : Math.max(60, (t.maxHp || boss.maxHp || 2000) * 0.25), poise: 0, dir: 1, kind: 'heavy', x: t.x, y: t.y - 20, melee: true, big: true }); return 'alive'; })()`);
    if (s !== 'alive') return s;
    step(20); unstick();
  }
  return 'timeout';
}
const sum = [], WALK = {};
async function rekindleHere(k) {
  for (let i = 0; i < 20 && !E(`props.some(p => p.type === 'cr_effigy' && p.kind === '${k}')`); i++) step(30);
  const pos = E(`(() => { const p = props.find(p => p.type === 'cr_effigy' && p.kind === '${k}'); return p ? [p.x, p.y] : null; })()`);
  if (!pos) return 'no effigy';
  // walk up to it (held arrow keys, as a player would); only if the walk can't get there, stand on it
  let walked = false;
  for (let i = 0; i < 700; i++) { const d = E('P.x') - pos[0]; if (Math.abs(d) < 6 && Math.abs(E('P.y') - pos[1]) < 20 && E('P.ground')) { walked = true; break; } G.step(1, [d < 0 ? 'right' : 'left']); }
  WALK[k] = walked;
  if (!walked) E(`P.x = ${pos[0]} + 4; P.y = ${pos[1]}; P.vx = 0; P.vy = 0; setP('idle', 'idle', true); P.ground = true;`);
  step(6);
  const pr = E('nearbyPrompt()');
  if (!/^Rekindle /.test(pr || '')) return 'no prompt: ' + pr;
  step(1, ['interact']);
  for (let i = 0; i < 6 && !E('!!(dialog && dialog.steps[dialog.i] && dialog.steps[dialog.i].choice)'); i++) step(1, ['confirm']);
  step(1, ['confirm']); step(2);
  if (!E(`boss && boss.kind === '${k}' && boss.rematch && REM.on && REM.on.kind === '${k}'`)) return `no boss (${E('boss && boss.kind')})`;
  const foes = E(`enemies.filter(e => typeof e.key === 'string' && e.key.startsWith(room.id + ':')).length`);
  return foes ? `${foes} room foes still there` : 'ok';
}
let shots = 0;
for (const k of KINDS) {
  const row = { k };
  try {
    E(`delete SAVE.flags['boss:${k}']; if (SAVE.cores) delete SAVE.cores['${k}']; SAVE.mastery = {}; SETTINGS.god = 1; REM.on = null`);
    const [rm, tx, ty] = home(k);
    G.tp(rm, tx, ty); step(20); unstick();
    const first = await killBoss(); step(30); unstick();
    row.first = first;
    const core = E(`!!(SAVE.cores && SAVE.cores['${k}'])`);
    T(`${k}: first kill -> its Core`, first === 'dead' && core && E(`!!SAVE.flags['boss:${k}']`), `${first}, core ${core}`);
    await sleep(2600 + E(`(BOSS_INFO['${k}'].reward || []).length`) * 2400 + 1400); step(320); unstick();   // the boss's own reward grants are real-time timers
    const rk = await rekindleHere(k);
    T(`${k}: the effigy rekindles the fight`, rk === 'ok', rk);
    if (rk !== 'ok') { sum.push(`${k}: ${rk}`); continue; }
    const flags0 = E('JSON.stringify(SAVE.flags)'), cores0 = E('JSON.stringify(SAVE.cores)'), items0 = E('JSON.stringify([SAVE.items, SAVE.inv, SAVE.spellsOwned, SAVE.charms, SAVE.shards])');
    E('dialogAfterEnding = false');
    const cin0 = E('SAVE.cinders'), xp0 = E('masteryXP(wtype())'), ending0 = E('SAVE.ending || null'), wins0 = E('REM.wins');
    step(30); unstick();
    E('if (boss && !boss.active && !boss.cutting) boss.activate()'); step(20); unstick();
    const fog = E(`props.filter(p => p.type === 'fog' && p.on && p.on()).length`), dyn = E('room.dyn.filter(d => d.on && d.on()).length');
    E('saveGame()');
    const saved = E(`JSON.parse(localStorage.getItem(SAVE_KEY)).flags['boss:${k}'] === 1`);
    T(`${k}: a save made mid-rematch still holds the boss flag`, saved);
    if (shots < 8 && ['hound', 'twins', 'executioners', 'sentinels', 'coven', 'omen', 'sovereign', 'champion'].includes(k)) { shots++; await snap(`rematch_${k}`); }
    const res = await killBoss(); step(30); unstick();
    await sleep(50); step(330); unstick();
    const flags1 = E('JSON.stringify(SAVE.flags)'), cores1 = E('JSON.stringify(SAVE.cores)'), items1 = E('JSON.stringify([SAVE.items, SAVE.inv, SAVE.spellsOwned, SAVE.charms, SAVE.shards])');
    const dc = E('SAVE.cinders') - cin0, want = E(`Math.round(BOSS_INFO['${k}'].cinders * CR_REMATCH_CINDERS)`), dxp = E('masteryXP(wtype())') - xp0;
    const ok = res === 'dead' && flags0 === flags1 && cores0 === cores1 && items0 === items1 && dxp >= 150 && dxp < 200 && dc >= want * 0.5 && dc <= want * 1.6 && E('SAVE.ending || null') === ending0 && E('REM.wins') === wins0 + 1 && G.state === 'play' && !E('dialogAfterEnding') && !E('dialog');
    T(`${k}: rematch kill -> Mastery +150, ${want} cinders; no Core, items, flags or ending`, ok,
      `${res}, flags ${flags0 === flags1 ? '=' : 'CHANGED'}, cores ${cores0 === cores1 ? '=' : 'CHANGED'}, items ${items0 === items1 ? '=' : 'CHANGED'}, xp +${dxp}, cinders +${dc}, fog ${fog}, walls ${dyn}, state ${G.state}`);
    if (flags0 !== flags1) { const a = JSON.parse(flags0), b = JSON.parse(flags1); sum.push(`${k} flag diff: ${Object.keys({ ...a, ...b }).filter(q => a[q] !== b[q]).join(',')}`); }
    const eff = E(`props.some(p => p.type === 'cr_effigy' && p.kind === '${k}')`);
    T(`${k}: the effigy returns after the rematch`, eff);
    row.fog = fog; row.walls = dyn; sum.push(`${k}: first ${first}, rematch ${res}, fog ${fog}, walls ${dyn}, walked up ${WALK[k]}, room foes cleared ${E('REM.on ? REM.on.cleared : "-"')}`);
  } catch (e) { T(`${k}: no exceptions`, false, String(e).slice(0, 200)); unstick(); }
}
// ---- death in a rematch: nothing lost, back at the shrine, the boss stays defeated
{ await sleep(9000); const k = 'hound'; E(`SETTINGS.god = 1; SAVE.flags['boss:${k}'] = 1; SAVE.cinders = 1234; SAVE.remnant = null; REM.on = null`);
  const [rm, tx, ty] = home(k); G.tp(rm, tx, ty); step(80);
  const rk = await rekindleHere(k);
  E('if (boss && !boss.active) boss.activate()'); step(30);
  const d0 = E('SAVE.deaths');
  E('SETTINGS.god = 0; P.inv = 0; P.lastHit = null; hurtPlayer(1e6, 1, "crtest", {})');
  const waitDeath = async () => { let seen = false; for (let i = 0; i < 80; i++) { step(10); await sleep(5); if (G.state === 'dead') seen = true; if (seen && G.state === 'play' && E('fadePhase') === 0) break; } step(30); return seen; };
  const died = await waitDeath();
  T('death in a rematch: cinders kept, no remnant, the boss stays down, the rematch ends', rk === 'ok' && died && E('SAVE.cinders') === 1234 && E('SAVE.remnant') === null && E(`SAVE.flags['boss:${k}']`) === 1 && E('REM.on') === null && E('SAVE.deaths') === d0 + 1,
    `${rk}, cinders ${E('SAVE.cinders')}, remnant ${JSON.stringify(E('SAVE.remnant'))}, room ${G.room}, deaths ${d0}->${E('SAVE.deaths')}`);
  // a normal death (no rematch) still leaves the cinders where you fell: the wrapper only steps in during a rekindled fight
  { const [rm2, tx2, ty2] = home('hound'); G.tp(rm2, tx2, ty2); step(20); }   // die away from the shrine (respawning on your own remnant picks it straight up)
  E('SETTINGS.god = 1; SAVE.cinders = 500; SAVE.remnant = null; REM.on = null; state = "dead"; finishDeath()'); for (let i = 0; i < 20; i++) { step(10); await sleep(5); }
  T('a normal death still leaves a remnant', E('SAVE.cinders') === 0 && E('SAVE.remnant && SAVE.remnant.amount') === 500, `${E('SAVE.cinders')} ${JSON.stringify(E('SAVE.remnant'))}`);
  E('SETTINGS.god = 1'); }
// ---- again and again: three rematches in a row on the Twins
{ const k = 'twins'; E(`SAVE.flags['boss:${k}'] = 1; SAVE.mastery = {}`); const [rm, tx, ty] = home(k); G.tp(rm, tx, ty); step(80);
  let n = 0; for (let i = 0; i < 3; i++) { if (await rekindleHere(k) !== 'ok') break; if (await killBoss() !== 'dead') break; step(330); n++; }
  T('three rematches in a row on the Twins', n === 3, `${n}`); }
// ---- the story: the Ashwright's Core list, the map's boss marks and the Sovereign's ending
T('after it all every rekindled boss still counts as defeated', KINDS.every(k => E(`SAVE.flags['boss:${k}'] === 1`)));
T('no ending was chosen by any of it', !E('SAVE.ending'));
T('the effigy was reached on foot (held arrows + E + confirm) in most arenas, incl. the Librarian and the Ice Warden', WALK.librarian !== false && WALK.ice_warden !== false && Object.values(WALK).filter(Boolean).length >= Object.keys(WALK).length - 4, Object.entries(WALK).filter(([k, v]) => !v).map(([k]) => k).join(',') || 'all walked');
return { R, sum };
