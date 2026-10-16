// v17 FOES: the Hollow Smith, Quench Wraith, Bellows Hulk and Cinder Mite fight on their own (seeded random), every
// attack and special state is seen, then each dies. The Hulk: stance -> core flare -> stagger -> FATALITY (K).
// SHOT_HTML=$PWD/web/dist/v17_foes.html sh tools/shots/wm/run.sh tools/shots/v17/foes/beasts.js tools/shots/v17/foes/out_beasts
E(`(() => { let s = 4242; Math.random = () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; })()`);
G.tp('CF9', 6, 9); W().frame(30); const FY = E('P.y');
E(`(() => {
  if (window.__cfHook) return; window.__cfHook = true; window.__cfLog = [];
  const o = hurtPlayer; hurtPlayer = function (d, dir, id, opt = {}) { const r = o(d, dir, id, opt); const e = opt.src || window.__e; if (r) window.__cfLog.push({ atk: e && (e.atk || e.state), st: e && e.state, fx: !opt.src, dmg: Math.round(d) }); return r; };
  killPlayer = function (dir) { P.hp = D.maxHp; return false; };
})()`);
const shots = [], res = {};
const shot = async (name) => { E('hitstop = 0; areaCard = null; bannerMsg = null; regionCard = null; toasts.length = 0; render()'); await snap(name); shots.push(name); };
const place = d => E(`projectiles.length = 0; P.x = clamp(__e.x - ${d}, 30, room.pw - 30); P.y = ${FY}; P.vx = 0; P.vy = 0; if (P.state !== 'rest') { P.state = 'idle'; P.anim.set('idle', true); } P.face = 1; P.hp = D.maxHp; P.inv = 0`);
for (const type of ['cf_smith', 'cf_wraith', 'cf_hulk', 'cf_mite']) {
  E(`enemies = []; window.__cfLog = []; window.__e = makeEnemy('${type}', 300, ${FY}, 'bt_${type}'); enemies.push(__e); __e.aggro = true; 1`);
  W().frame(2); await new Promise(r => setTimeout(r, 300));
  const seen = {}, shotAt = {};
  const dists = type === 'cf_wraith' ? [60, 30, 100, 60, 20, 110] : type === 'cf_mite' ? [50, 30, 60, 40] : [130, 30, 100, 40, 140, 25];
  if (type === 'cf_wraith') { place(150); for (let f = 0; f < 40; f++) W().frame(1); await shot('bt_wraith_still'); place(60); }
  for (let f = 0; f < 3000; f++) {
    if (f % 220 === 0 && !E('__e.state === "hold" || __e.state === "throw" || __e.state === "cling" || __e.state === "attack"')) place(dists[(f / 220) % dists.length]);
    W().frame(1); E('P.st = D.maxSt; if (P.hp < D.maxHp * 0.3) P.hp = D.maxHp');
    const st = E('__e.state'), k = st === 'attack' ? E('__e.atk') : st;
    if (!seen[k]) seen[k] = 0; seen[k]++;
    const kf = st === 'attack' ? E(`(metaWindows(__e.sh, __e.atk)[0] || { active: [((__e.sh.meta.spawn || {})[__e.atk] || [3])[0]] }).active[0]`) : -1;
    if (!shotAt[k] && ((st === 'attack' && E('__e.anim.i') === kf) || (['hold', 'throw', 'vent', 'cling', 'rising', 'sinking'].includes(st) && seen[k] === 6))) { shotAt[k] = 1; await shot(`bt_${type.slice(3)}_${k}`); }
    const need = { cf_smith: ['hammer', 'grab', 'toss', 'hold', 'throw'], cf_wraith: ['rising', 'hiss', 'lunge', 'claw', 'sinking'], cf_hulk: ['slam', 'sweep', 'blast', 'vent'], cf_mite: ['leap', 'cling'] }[type];
    if (need.every(n => seen[n] >= (n === 'cling' ? 45 : 8))) break;
  }
  const log = E('__cfLog'); const hitBy = {}; for (const l of log) hitBy[l.atk] = (hitBy[l.atk] || 0) + 1;
  res[type] = { seen: Object.keys(seen), hitBy };
  if (type === 'cf_mite') res[type].clingBurns = E('CFF.burns || 0');
  if (type === 'cf_hulk') {
    // stance -> the core flares -> stagger -> fatality
    E(`__e.state = 'idle'; __e.setA('idle', 'idle'); __e.stance = 0; __e.vent = 0; __e.cool = 99; __e.x = 300; __e.hp = __e.maxHp`); place(26);
    let hits = 0, flared = false;
    for (let k = 0; k < 40 && E('__e.state') !== 'stagger'; k++) {
      E(`__e.hit({ dmg: 10, poise: 28, dir: 1, kind: 'light', x: __e.x - 8, y: __e.y - 30 })`); hits++;
      for (let f = 0; f < 8; f++) { W().frame(1); E('__e.cool = 99'); }
      if (!flared && E('__e.stance / __e.cfg.stance') > 0.62) { flared = true; W().frame(4); await shot('bt_hulk_core_flare'); }
    }
    const staggered = E('__e.state'); W().frame(10); await shot('bt_hulk_stagger');
    const hp0 = E('__e.hp'), critable = E('__e.critable()');
    E(`P.x = __e.x - 22; P.face = 1; P.state = 'idle'; P.anim.set('idle', true)`); W().frame(1);
    W().tap('heavy', 2);
    let fat = false; for (let f = 0; f < 400; f++) { W().frame(1); if (E('!!FAT.on')) { fat = true; if (f === 30) await shot('bt_hulk_fatality'); } else if (fat) break; }
    res.hulk_fatality = { hitsToStagger: hits, staggered, critable, fat, last: E('FAT.last && { type: FAT.last.type, name: FAT.last.name, exec: FAT.last.exec, dealt: Math.round(FAT.last.dealt || 0) }'), hp0, hp1: E('__e.hp'), state: E('__e.state') };
    // the vent: stance damage x1.8
    E(`__e.hp = __e.maxHp; __e.state = 'vent'; __e.anim.set('vent', true); __e.vent = 1.5; __e.stance = 0`);
    E(`__e.hit({ dmg: 1, poise: 20, dir: 1, kind: 'light', x: __e.x - 8, y: __e.y - 30 })`); res.hulk_vent_stance = E('Math.round(__e.stance)');
  }
  E(`if (__e.alive) __e.hit({ dmg: 99999, poise: 0, dir: 1, kind: 'light', x: __e.x, y: __e.y - 10 })`);
  let gone = false; for (let f = 0; f < 300 && !gone; f++) { W().frame(1); if (f === 20) await shot(`bt_${type.slice(3)}_death`); gone = E('!!__e.gone'); }
  res[type].gone = gone; res[type].killed = E(`killed.has('bt_${type}')`);
}
// a clutch from the spawn kind
E(`enemies = []; SPAWNS.cf_swarm({ n: 4 }, { cx: P.x + 60, fy: ${FY}, key: 'swarmtest' }); 1`);
res.swarm = E(`enemies.map(e => e.type + ':' + Math.round(e.x))`);
return { res, shots };
