// v17 BOSS test prelude: a deterministic clock and seeded randomness (bosses need real variety), helpers for the
// Hearthkeeper in the Training Grounds chamber (or AREA's arena via ARGS.room).
await boot(); G.grantTechniques();
const E = G.sk.ev;
E(`(() => {
  if (window.__hk) return;
  let seed = ${ARGS.seed || 7}; const rng = () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  Math.random = rng;
  const T = window.__hk = { ms: 0, hits: 0, hitLog: [], errs: [] };
  performance.now = () => T.ms;
  const _h = hurtPlayer;
  hurtPlayer = function (dmg, dir, id, opt = {}) { const r = _h.call(this, dmg, dir, id, opt); if (r) { T.hits++; T.hitLog.push([boss && boss.atk, boss && boss.tag, boss && boss.anim && boss.anim.i, Math.round(dmg)]); } return r; };
  T.frame = (n = 1) => { for (let i = 0; i < n; i++) { T.ms += 1000 / 60; try { update(1 / 60); } catch (e) { T.errs.push(String(e.stack || e).split('\\n').slice(0, 3).join(' | ')); } } };
  // cutscenes run (no forced 'play'); menus/dialogs are cleared
  T.play = (n = 1) => { for (let i = 0; i < n; i++) { if (state === 'menu' || state === 'dialog') { menu = null; dialog = null; state = 'play'; } T.frame(1); } };
  T.front = (d = 60) => { const b = boss; P.x = clamp(b.x + b.face * d, TILE + 10, room.pw - TILE - 10); P.y = b.floor; P.vx = 0; P.vy = 0; P.ground = true; if (P.state !== 'idle') setP('idle', 'idle', true); P.face = P.x < b.x ? 1 : -1; P.hp = D.maxHp; P.inv = 0; };
  T.arena = () => { if (TRAINING.on) trainingExit(); delete SAVE.flags['boss:hearthkeeper']; SAVE.flags['cut:hearthkeeper'] = 1; boss = null; enterRoom('CF8', 30 * TILE + 8, 18 * TILE, { quiet: true }); for (let i = 0; i < 5; i++) T.frame(1); SETTINGS.god = 0; return !!(boss && boss.kind === 'hearthkeeper'); };
  T.summon = () => ${ARGS.arena ? 1 : 0} ? T.arena() : T.summonT();
  T.summonT = () => { if (!TRAINING.on) trainingStart(); for (let i = 0; i < 5; i++) T.frame(1); SETTINGS.god = 0; return trnSummonBoss('hearthkeeper'); };
  T.wake = () => { const b = boss; for (let i = 0; i < 600 && !b.active; i++) { P.x += b.x < P.x ? -2 : 2; T.play(1); P.hp = D.maxHp; } for (let i = 0; i < 400 && (b.rising || state === 'cut'); i++) { T.play(1); P.hp = D.maxHp; } return b.active; };
})()`);
const HKT = () => window.__hk;
