// WM test prelude (prepended by run.sh): deterministic clock, a fake target that records every hit, helpers
await boot(); G.grantTechniques();
const E = G.mv.ev;
E(`(() => {
  if (window.__wm) return;
  const W = window.__wm = { ms: 0, log: [] };
  performance.now = () => W.ms;
  W.frame = (n = 1) => { for (let i = 0; i < n; i++) { if (W.follow) { const d = enemies.find(e => e.wmDummy); if (d) d.x = P.x + W.follow; } W.ms += 1000 / 60; update(1 / 60); if (state !== 'play' && state !== 'dead') { try { state = 'play'; } catch (e) {} } } };
  W.down = a => press(a); W.up = a => release(a);
  W.tap = (a, n = 1) => { press(a); W.frame(n); release(a); };
  W.dummy = (dx = 30, o = {}) => {
    enemies = enemies.filter(e => !e.wmDummy);
    const d = { wmDummy: true, type: 'wm_dummy', key: 'wm_dummy', alive: true, x: P.x + P.face * dx, y: P.y, w: 16, h: 40, ground: true, cfg: { ...(o.cfg || {}) }, face: -1, state: 'idle', hp: 1e9, vx: 0, vy: 0,
      boss: !!o.boss, half: o.half || 8, tall: o.tall || 40,
      update() {}, draw() {},
      hurtbox() { return rect(this.x - this.half, this.y - this.tall, this.x + this.half, this.y); },
      hit(info) { const el = info.fire && D.W.fire && info.kind === 'heavy' ? 1 + D.W.fire : 1; W.log.push({ st: P.state, dmg: info.dmg / el, raw: info.dmg, poise: info.poise, kind: info.kind, melee: !!info.melee, t: W.ms, mvT: P.mvT, lv: P.mvLv, light: D.light }); },
    };
    if (o.breakStance) d.breakStance = o.breakStance;
    enemies.push(d); return d;
  };
  W.reset = (type, rank = 1) => {
    wmEquip(type, { quiet: true }); MV.rank = rank; SAVE.stats.str = 11; SAVE.skills = []; SAVE.charmsEq = []; refreshDerived(false);
    P.hp = D.maxHp; P.st = D.maxSt; P.fp = D.maxFp; P.demon = false; P.arch = false; P.gauge = 0; P.sheathed = false; P.mom = 0; P.crack = 0; P.pdT = 0; P.exhT = 0; P.whCd = 0;
    P.state = 'idle'; P.anim.set('idle', true); P.vx = 0; P.vy = 0; P.mvChain = null; P.mvQ = null; P.mvQ2 = null; P.dg = null; P.dgEnd = null; P.spPower = 0; P.moonlit = false; P.counterBonus = 0; P.gcT = 0; P.guardKind = null; P.airLock = false; P.airN = 0; P.smashLock = false; P.smashN = 0; P.face = 1;
    clearBuffer(); held.clear(); W.log = []; W.follow = 0; hitstop = 0; slowmo = 0;
  };
})()`);
const W = () => window.__wm;
const rnd = { s: 7 }; Math.random = () => 0.5;   // rand(a, b) -> the midpoint: damage rolls are exact
// a wide flat floor with nothing else in it (the Training Grounds' first chamber)
const arena = () => { if (G.room !== 'TR1') { G.trn.start(); W().frame(10); } E("P.x = 120; P.y = 304; P.vx = 0; P.vy = 0; P.ground = true; enemies = enemies.filter(e => e.wmDummy); projectiles.length = 0"); W().frame(2); };
