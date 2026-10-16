// v17 FOES: the Unforged with each of the 14 weapon types. For every type: each of its three moves is started with the
// player standing in that move's range (it must fire and land), then a free fight (its own choices, seeded random),
// then it dies. Snapshots: the first active frame of every move + the death heap.
// SHOT_HTML=$PWD/web/dist/v17_foes.html sh tools/shots/wm/run.sh tools/shots/v17/foes/uf.js tools/shots/v17/foes/out_uf
let seed = 12345; Math.random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
E(`(() => { let s = 777; Math.random = () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; })()`);
G.tp('CF9', 6, 9); W().frame(30); const FY = E('P.y');
E(`(() => {
  if (window.__cfHook) return; window.__cfHook = true; window.__cfLog = [];
  const o = hurtPlayer; hurtPlayer = function (d, dir, id, opt = {}) { const r = o(d, dir, id, opt); const e = opt.src || window.__e; if (r) window.__cfLog.push({ atk: e && e.atk, st: e && e.state, fx: !opt.src, dmg: Math.round(d) }); return r; };
  killPlayer = function (dir) { P.hp = D.maxHp; return false; };
})()`);
const types = E('CFF_TYPES');
const res = {}, shots = [];
const shot = async (name) => { E('hitstop = 0; areaCard = null; bannerMsg = null; regionCard = null; toasts.length = 0; render()'); await snap(name); shots.push(name); };
const reset = (d) => E(`projectiles.length = 0; hazards.length = 0; P.x = clamp(__e.x - ${d}, 30, room.pw - 30); P.y = ${FY}; P.vx = 0; P.vy = 0; P.state = 'idle'; P.anim.set('idle', true); P.face = 1; P.hp = D.maxHp; P.inv = 0; P.lastHit = undefined; __e.face = -1`);
for (const t of types) {
  E(`CFF.force = '${t}'; enemies = []; window.__cfLog = []; window.__e = makeEnemy('cf_unforged', 300, ${FY}, 'uf_test_${t}'); enemies.push(__e); __e.aggro = true; __e.announced = true; 1`);
  W().frame(2); await new Promise(r => setTimeout(r, 400));   // the big sheet decodes (on room entry warmSheets does this)
  const forced = {};
  for (const a of ['atk1', 'atk2', 'atk3']) {
    const rg = E(`UF_KITS['${t}'].${a}.range`);
    const d = Math.round(Math.min(rg[1] - 8, Math.max(rg[0] + 10, (rg[0] + rg[1]) / 2 - 10)));
    E(`__e.x = 300; __e.y = ${FY}; __e.vx = 0; __e.setA('idle', 'idle'); __e.state = 'idle'; __e.cool = 99; __e.combo = null`); reset(d);
    E(`window.__cfLog = []; __e.facePlayer(); __e.begin('${a}')`);
    const kf = E(`(metaWindows(__e.sh, '${a}')[0] || { active: [((__e.sh.meta.spawn || {})['${a}'] || [99])[0]] }).active[0]`);
    let snapped = false, frames = 0;
    for (let f = 0; f < 600; f++) {
      W().frame(1); frames++;
      E('P.hp = D.maxHp; P.st = D.maxSt; if (P.state === "rest" && !(__e.pulled)) {}');
      const s = E('[__e.state, __e.atk, __e.anim.i]');
      if (!snapped && s[0] === 'attack' && s[1] === a && s[2] === kf) { snapped = true; await shot(`uf_${t}_${a}`); }
      if (s[0] !== 'attack' || s[1] !== a) break;
    }
    if (E(`__e.combo`)) { for (let f = 0; f < 400; f++) { W().frame(1); E('P.hp = D.maxHp'); const s = E('[__e.state, __e.atk]'); if (f > 2 && s[0] !== 'attack') break; } }
    const log = E('__cfLog');
    forced[a] = { hits: log.length, dmg: log.map(l => l.dmg), dist: d, frames, snapped };
  }
  // free fight: its own choices
  E(`__e.x = 300; __e.cool = 0.3; __e.combo = null; window.__cfLog = []`); reset(60);
  const used = {};
  for (let f = 0; f < 1500; f++) {
    if (f % 200 === 0) reset([30, 70, 110, 50, 140, 40, 90, 60][(f / 200) % 8]);
    W().frame(1); E('P.hp = D.maxHp; P.st = D.maxSt');
    if (E('__e.state === "attack" && __e.anim.i === 0 && __e.anim.changed')) { const a = E('__e.atk'); used[a] = (used[a] || 0) + 1; }
  }
  const free = { used, hits: E('__cfLog.length') };
  E(`__e.hit({ dmg: 99999, poise: 0, dir: 1, kind: 'light', x: __e.x, y: __e.y - 20 })`);
  let gone = false; for (let f = 0; f < 300 && !gone; f++) { W().frame(1); if (f === 40) { E('P.x = __e.x - 60'); W().frame(1); await shot(`uf_${t}_death`); }; gone = E('!!__e.gone'); }
  res[t] = { forced, free, gone, killed: E(`killed.has('uf_test_${t}')`) };
}
// the roll: no forced type -> one of the 14 per encounter, never the type in the player's hand
E(`CFF.force = null`);
const rolls = {}; const mine = E('wtype()');
for (let k = 0; k < 140; k++) { const t = E(`makeEnemy('cf_unforged', 300, ${FY}, 'roll' + ${k}).wt`); rolls[t] = (rolls[t] || 0) + 1; }
// a placed spawn may fix the type: {"t":"enemy","type":"cf_unforged","w":"katana"}
const fixed = E(`(() => { const d = ROOM_BY['CF9']; const i = d.spawns.findIndex(s => s.type === 'cf_unforged'); if (i < 0) return 'no spawn'; const o = d.spawns[i].w; d.spawns[i].w = 'bell'; const t = makeEnemy('cf_unforged', 300, ${FY}, 'CF9:sp' + i).wt; if (o === undefined) delete d.spawns[i].w; else d.spawns[i].w = o; return t; })()`);
return { res, n: shots.length, roll: { mine, rolls, kinds: Object.keys(rolls).length, fixed } };
