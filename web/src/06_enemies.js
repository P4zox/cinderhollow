// ------------------------------------------------------------------ enemies (generic, driven by art meta)
let enemyId = 1;
const ATTACK_TAGS = { hollow_soldier: ['attack'], shield_warden: ['bash'], rot_crawler: ['lunge'], gloom_wisp: ['dive'], hollow_archer: ['shoot'],
                      ember_acolyte: ['cast'], grave_knight: ['combo', 'slam'], rot_hulk: ['smash'], bog_spitter: ['spit'], mire_witch: ['cast'],
                      gilded_sentinel: ['sweep', 'thrust'], root_spawn: ['burst'], sun_seraph: ['dive'],
                      grimoire: ['dive'], ink_hound: ['pounce'], lantern_monk: ['swing'] };
function metaWindows(sh, tag) {
  const a = sh.meta && sh.meta.attacks && sh.meta.attacks[tag];
  if (!a) return [];
  if (a.windows) return a.windows;
  return [{ active: a.active, hit: a.hit }];
}
// later regions are tougher (play order: Archives → Hoarfrost → Spire → Deep); scales HP, damage and cinders per biome
const BIOME_TIER = { spire: { hp: 1.4, dmg: 1.25, cin: 1.3 }, deep: { hp: 1.6, dmg: 1.4, cin: 1.5 }, ember: { hp: 1.8, dmg: 1.5, cin: 1.6 } };
function tierCfg(cfg) {
  const T = typeof room !== 'undefined' && room && BIOME_TIER[room.def.biome]; if (!T) return cfg;
  const c = { ...cfg, hp: Math.round(cfg.hp * T.hp), cinders: Math.round((cfg.cinders || 0) * T.cin) };
  if (cfg.dmg) c.dmg = Object.fromEntries(Object.entries(cfg.dmg).map(([k, v]) => [k, typeof v === 'number' ? Math.round(v * T.dmg) : v]));
  if (cfg.contact) c.contact = Math.round(cfg.contact * T.dmg);
  return c;
}
class Enemy {
  constructor(type, x, y, key) {
    this.type = type; this.cfg = tierCfg(ENEMY[type]); this.key = key; this.id = enemyId++;
    this.sh = sheet(type);
    const hb = this.sh.meta && this.sh.meta.hurtbox;
    this.w = hb ? Math.min(hb[2], 22) : 14; this.h = hb ? Math.min(hb[3], 44) : 26;
    this.x = x; this.y = y; this.home = x; this.vx = 0; this.vy = 0; this.ground = true;
    this.face = P && P.x < x ? -1 : 1;
    this.hp = Math.round(this.cfg.hp * NGP.hp); this.maxHp = this.hp; this.poise = 0; this.stance = 0; this.bleed = 0;
    this.state = 'idle'; this.anim = new Anim(this.sh, this.sh.has('idle') ? 'idle' : (this.sh.has('fly') ? 'fly' : Object.keys(this.sh.tags)[0] || 'idle'));
    this.cool = rand(0.5, 1.2); this.aggro = false; this.lostT = 0; this.flash = 0; this.hitIds = new Set(); this.atkId = 0; this.t = 0;
    this.patrolDir = Math.random() < 0.5 ? -1 : 1; this.patrolT = rand(1, 3); this.blinkCool = 0;
    if (this.cfg.flying) { this.hy = y - 24; this.y = this.hy; }
    this.dmgShown = 0; this.dmgT = 0;
    // melee range = how far the art's hitboxes actually reach (plus the lunge)
    this.atkRange = this.cfg.range;
    if (!this.cfg.ranged && !this.cfg.flying && this.type !== 'rot_crawler' && !this.cfg.leap && this.sh.meta && this.sh.meta.attacks) {
      let reach = 0;
      for (const [tag, a] of Object.entries(this.sh.meta.attacks)) for (const w of (a.windows || [a])) if (w.hit) reach = Math.max(reach, w.hit[0] + w.hit[2] - this.sh.ax + ((this.cfg.lunge && this.cfg.lunge[tag]) || 0) * 0.12);
      if (reach > 0) this.atkRange = Math.min(this.cfg.range, reach + 2);
    }
  }
  get alive() { return this.state !== 'dead'; }
  hurtbox() {
    if (!this.alive) return null;
    if (this.sh.ok && this.sh.meta && this.sh.meta.hurtbox) return metaRect(this.sh, this, this.sh.meta.hurtbox);
    return rect(this.x - this.w / 2, this.y - this.h, this.x + this.w / 2, this.y);
  }
  critable() { return this.alive && (this.state === 'stagger' || this.state === 'parried') && !this.critDone; }
  onCritStart() { this.critDone = true; this.t = Math.max(this.t, 0.9); }
  onParried() {
    if (!this.alive) return;
    this.state = 'parried'; this.t = 1.6; this.critDone = false; this.anim.set(this.sh.has('hurt') ? 'hurt' : 'idle', false); this.vx = -this.face * 40;
  }
  setA(st, tag, loop = true, speed = 1) { this.state = st; if (this.sh.has(tag)) this.anim.set(tag, loop, speed); else this.anim.set(Object.keys(this.sh.tags)[0], loop, speed); }
  hit(info) {
    if (!this.alive) return;
    const c = this.cfg;
    // shield warden blocks light frontal attacks
    if (c.guard && !info.crit && info.kind !== 'heavy' && ['idle', 'walk', 'guard'].includes(this.state) && info.dir === -this.face && info.kind !== 'spell') {
      sfx.block(); spawnFx(fxOr('parry_spark', 'hit'), info.x, info.y, info.dir);
      this.stance += info.poise * 0.6; P.vx = -P.face * 90; P.st -= 8; hitstop = 0.05;
      const d = Math.round(info.dmg * 0.08); this.hp -= d; popup(info.x, info.y - 8, d, '#9a9aa8');
      if (this.stance >= c.stance) this.breakStance();
      return;
    }
    let dmg = Math.round(info.dmg);
    if (this.state === 'stagger' && !info.crit) dmg = Math.round(dmg * 1.3);
    this.hp -= dmg; this.flash = 1; this.dmgShown = this.dmgT > 0 ? this.dmgShown + dmg : dmg; this.dmgT = 1.5;
    if (!info.quiet || Math.random() < 0.5) popup(info.x, info.y - 10, dmg, info.crit ? '#ffcf6a' : '#f1e6c8');
    if (!info.quiet) { hitstop = Math.max(hitstop, info.big ? 0.09 : 0.05); shake = Math.max(shake, info.big ? 3.5 : 1.8);
    (info.big ? sfx.bigHit : sfx.hit)();
    spawnFx(info.big ? fxOr('parry_spark', 'hit') : 'hit', info.x, info.y, info.dir); }
    for (let i = 0; i < (info.big ? 9 : 5); i++) particles.push({ x: info.x, y: info.y, vx: info.dir * rand(20, 100), vy: -rand(20, 90), g: 280, life: rand(0.3, 0.6), kind: info.fire ? 'fire' : 'spark' });
    if (info.rotDot) this.rotT = 4;
    if (info.bleed) {
      this.bleed += info.bleed;
      if (this.bleed >= 100) { this.bleed = 0; const bd = Math.round(this.maxHp * 0.15 + 20); this.hp -= bd; popup(this.x, this.y - this.h - 8, bd, '#ff3040'); sfx.bleed(); spawnFx(fxOr('bleed', 'blood'), this.x, this.y - this.h / 2, info.dir); }
    }
    if (this.hp <= 0) return this.die(info);
    if (info.crit) { this.stance = 0; if (this.state === 'parried' || this.state === 'stagger') { this.t = 0.5; } return; }
    this.aggro = true;
    this.poise += info.poise; this.stance += info.poise;
    if (this.stance >= c.stance) return this.breakStance();
    const attacking = this.state === 'attack';
    if (this.poise >= c.poise && !(c.elite && attacking)) {
      this.poise = 0; this.state = 'hurt'; this.anim.set(this.sh.has('hurt') ? 'hurt' : 'idle', false);
      this.vx = info.dir * (c.elite ? 30 : 110); if (!c.flying) this.vy = c.elite ? 0 : -60;
      if (c.flying) { this.vx = info.dir * 140; this.vy = -30; }
    }
  }
  breakStance() {
    this.stance = 0; this.poise = 0; this.state = 'stagger'; this.t = 1.8; this.critDone = false;
    this.anim.set(this.sh.has('hurt') ? 'hurt' : 'idle', false); sfx.glint();
    spawnFx(fxOr('parry_flash', 'parry_spark'), this.x, this.y - this.h * 0.6, this.face, null, { alpha: 0.7 });
  }
  die(info) {
    this.state = 'dead'; this.anim.set(this.sh.has('death') ? 'death' : 'hurt', false);
    this.vx = (info ? info.dir : 0) * 60; killed.add(this.key);
    gainCinders(this.cfg.cinders, this.x, this.y - this.h / 2);
    if (has('soul_siphon')) { P.fp = Math.min(D.maxFp, P.fp + 8); P.hp = Math.min(D.maxHp, P.hp + Math.round(D.maxHp * 0.03)); }
    if (this.cfg.elite) { slowmo = 0.5; shake = 8; sfx.roar(); }
  }
  dist() { return P.x - this.x; }
  canSee() {
    const dx = this.dist(), dy = P.y - this.y;
    if (Math.abs(dx) > this.cfg.aggro * (charmOn('c_veil') ? 0.65 : 1) || Math.abs(dy) > (this.cfg.flying ? 140 : 70)) return false;
    return lineOfSight(this.x, this.y - this.h * 0.7, P.x, P.y - 16);
  }
  facePlayer() { this.face = P.x < this.x ? -1 : 1; }
  startAttack(tag) {
    this.facePlayer(); this.atk = tag; this.hitIds = new Set(); this.atkId = ++hazardId; this.spawned = false;
    this.setA('attack', tag, false);
    const wins = metaWindows(this.sh, tag); this.firstActive = wins.length ? wins[0].active[0] : 2;
  }
  update(dt) {
    const c = this.cfg;
    this.flash = Math.max(0, this.flash - dt * 5); this.poise = Math.max(0, this.poise - dt * 12); this.stance = Math.max(0, this.stance - dt * 6);
    this.bleed = Math.max(0, this.bleed - dt * 6); this.dmgT -= dt;
    if (this.rotT > 0 && this.alive) {
      this.rotT -= dt; this.hp -= this.maxHp * 0.025 * dt; this.rotAcc = (this.rotAcc || 0) + this.maxHp * 0.025 * dt;
      if (Math.random() < 0.3) particles.push({ x: this.x + rand(-6, 6), y: this.y - rand(4, this.h), vx: 0, vy: -rand(5, 18), life: 0.5, kind: 'spore' });
      if (this.rotAcc >= 5) { popup(this.x, this.y - this.h - 4, this.rotAcc, '#9ae05a'); this.rotAcc = 0; }
      if (this.hp <= 0) { this.die({ dir: 0 }); return; }
    }
    this.anim.update(dt);
    if (this.state === 'dead') {
      this.vx *= Math.pow(0.02, dt);
      if (!c.flying) { this.vy = Math.min(this.vy + 800 * dt, 400); moveBody(this, dt); } else { this.vy += 300 * dt; this.y += this.vy * dt; }
      if (this.anim.done && !this.gone) { this.gone = true; spawnFx(fxOr('death_ash', 'dust'), this.x, this.y + (c.flying ? 8 : 0), this.face); for (let i = 0; i < 14; i++) particles.push({ x: this.x + rand(-8, 8), y: this.y - rand(0, this.h), vx: rand(-20, 20), vy: -rand(20, 60), life: rand(0.6, 1.3), kind: 'ash' }); }
      return;
    }
    if (c.flying) return this.updateFlying(dt);
    const dx = this.dist(), adx = Math.abs(dx);
    if (!this.aggro && this.canSee()) { this.aggro = true; this.cool = Math.max(this.cool, 0.4); }
    if (this.aggro && (adx > c.aggro * 1.9 || Math.abs(P.y - this.y) > 160 || P.state === 'dead')) { this.lostT += dt; if (this.lostT > 2.5) { this.aggro = false; this.lostT = 0; } } else this.lostT = 0;
    this.cool -= dt; this.blinkCool -= dt;
    switch (this.state) {
      case 'idle': case 'walk': case 'guard': {
        if (!this.aggro) { this.patrol(dt); break; }
        this.facePlayer();
        const dy = P.y - this.y;
        if (c.ranged) {
          if (c.blink && adx < 64 && this.blinkCool <= 0) { this.setA('blink', 'blink', false); this.blinkCool = 4; break; }
          if (this.cool <= 0 && adx < c.range && Math.abs(dy) < 90 && this.canSee()) { this.startAttack(ATTACK_TAGS[this.type][0]); break; }
          const want = adx < 72 ? -sign(dx) : adx > c.range * 0.8 ? sign(dx) : 0;
          this.walk(want, dt, 0.8);
          break;
        }
        if (this.cool <= 0 && adx < this.atkRange && Math.abs(dy) < 36) {
          const tags = ATTACK_TAGS[this.type];
          this.startAttack(tags.length > 1 ? (adx < 40 && Math.random() < 0.5 ? tags[1] : tags[Math.random() < 0.6 ? 0 : 1]) : tags[0]);
          break;
        }
        if (c.guard && adx < 90) { this.walk(adx > this.atkRange * 0.8 ? sign(dx) : 0, dt, 0.6, 'guard'); break; }
        this.walk(adx > this.atkRange * 0.8 ? sign(dx) : 0, dt, 1);
        break;
      }
      case 'attack': this.updateAttack(dt); break;
      case 'blink': {
        this.vx = 0; this.gravity(dt);
        if (this.anim.done) {
          const nx = this.findBlinkSpot();
          if (nx !== null) { spawnFx(fxOr('death_ash', 'dust'), this.x, this.y, 1, null, { speed: 2 }); this.x = nx; }
          for (let i = 0; i < 12; i++) particles.push({ x: this.x + rand(-6, 6), y: this.y - rand(0, 30), vx: rand(-20, 20), vy: -rand(20, 60), life: 0.8, kind: 'fire' });
          this.setA('idle', 'idle'); this.cool = 0.5;
        }
        break;
      }
      case 'hurt':
        this.vx *= Math.pow(0.02, dt); this.gravity(dt);
        if (this.anim.done) { this.setA('idle', 'idle'); this.cool = Math.max(this.cool, 0.25); }
        break;
      case 'stagger': case 'parried':
        this.vx *= Math.pow(0.02, dt); this.gravity(dt); this.t -= dt;
        if (this.anim.i === this.anim.n - 1 || this.anim.done) this.anim.hold();
        if (Math.random() < 0.3) particles.push({ x: this.x + rand(-6, 6), y: this.y - this.h - 4, vx: 0, vy: -rand(10, 20), life: 0.4, kind: 'gold' });
        if (this.t <= 0) { this.setA('idle', 'idle'); this.cool = 0.3; }
        break;
    }
    // thorns hurt foes too (knock them in!)
    this.spikeCd = (this.spikeCd || 0) - dt;
    if (this.spikeCd <= 0 && spikeHit(this)) { this.spikeCd = 0.6; this.hit({ dmg: this.maxHp * 0.34 + 10, poise: 0, dir: -this.face, kind: 'env', x: this.x, y: this.y - 6 }); if (!this.alive) return; }
    // contact damage for crawlers
    if (c.contact && this.state !== 'hurt' && overlap(this.hurtbox(), playerHurtbox())) hurtPlayer(c.contact, sign(P.x - this.x), 'c' + this.id + Math.floor(time * 2));
  }
  gravity(dt) { this.vy = Math.min(this.vy + 800 * dt, 400); moveBody(this, dt); this.clampRoom(); }
  clampRoom() { this.x = clamp(this.x, 8, room.pw - 8); }
  walk(dir, dt, spd = 1, tag = 'walk') {
    const c = this.cfg;
    if (dir && !ledgeAhead(this, dir)) dir = 0;
    if (dir && wallAt(this, dir)) dir = 0;
    this.vx = approach(this.vx, dir * c.speed * spd, 400 * dt);
    const want = tag === 'guard' ? 'guard' : dir ? 'walk' : 'idle';
    const t = want === 'guard' ? (this.sh.has('guard') ? 'guard' : 'idle') : want === 'walk' ? (this.sh.has('walk') ? 'walk' : this.sh.has('run') ? 'run' : 'crawl') : 'idle';
    if (this.state !== want || this.anim.tag !== t) this.setA(want, t);
    this.gravity(dt);
  }
  patrol(dt) {
    this.patrolT -= dt;
    if (this.patrolT <= 0) { this.patrolT = rand(1.5, 3.5); this.patrolDir = Math.random() < 0.35 ? 0 : (this.x > this.home ? -1 : 1); }
    let d = this.patrolDir;
    if (d && (!ledgeAhead(this, d) || wallAt(this, d) || Math.abs(this.x + d * 10 - this.home) > 60)) { this.patrolDir = 0; d = 0; }
    if (d) this.face = d;
    this.walk(d, dt, 0.45);
  }
  findBlinkSpot() {
    for (let k = 0; k < 12; k++) {
      const nx = P.x + (Math.random() < 0.5 ? -1 : 1) * rand(90, 150);
      if (nx < 16 || nx > room.pw - 16) continue;
      const b = { x: nx, y: this.y, w: this.w, h: this.h };
      if (solidAtPx(nx, this.y - 8) || solidAtPx(nx, this.y - this.h + 2)) continue;
      if (!groundBelow(b, 2)) continue;
      return nx;
    }
    return null;
  }
  updateAttack(dt) {
    const an = this.anim, tag = this.atk, c = this.cfg, wins = metaWindows(this.sh, tag);
    if (an.i < this.firstActive - 1) this.facePlayer();
    if (an.changed && an.i === Math.max(0, this.firstActive - 1)) {   // telegraph glint just before the strike
      const tele = this.sh.meta && this.sh.meta.telegraph && this.sh.meta.telegraph[tag];
      if (c.elite || tele) { const p = tele ? metaPoint(this.sh, this, tele.at) : { x: this.x + this.face * 8, y: this.y - this.h * 0.8 }; spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); }
    }
    let lunging = false;
    wins.forEach((w, wi) => {
      if (an.i >= w.active[0] && an.i <= w.active[1]) {
        lunging = true;
        if (an.changed && an.i === w.active[0]) { sfx.swing(); if (c.lunge && c.lunge[tag]) this.vx = this.face * c.lunge[tag]; if (this.type === 'rot_crawler') { this.vx = this.face * 190; this.vy = -140; } if (c.leap) { this.vx = this.face * c.leap[0]; this.vy = c.leap[1]; } }
        if (!this.hitIds.has(wi) && w.hit) {
          const r = metaRect(this.sh, this, w.hit);
          if (overlap(r, playerHurtbox())) {
            const dmg = (c.dmg[tag] || 25) * (wi > 0 ? 1.1 : 1);
            if (hurtPlayer(dmg, this.face, this.atkId * 10 + wi, { parryable: this.type !== 'rot_crawler' && !c.suicide, src: this, rot: c.rot })) this.hitIds.add(wi);
            else if (this.state === 'parried') return;
          }
        }
        if (c.suicide && an.changed && an.i === w.active[0]) {
          sfx.boom(); shake = 5; spawnFx(fxOr('holy_burst', 'parry_flash'), this.x, this.y - 10, 1);
          for (let i = 0; i < 16; i++) particles.push({ x: this.x, y: this.y - 8, vx: rand(-100, 100), vy: -rand(20, 120), g: 300, life: 0.6, kind: 'gold' });
          hazards.push({ x: this.x, y: this.y, w: 44, h: 32, dmg: c.dmg.burst * NGP.dmg, id: ++hazardId, life: 0.12 });
        }
        if (this.type === 'rot_hulk' && an.changed && an.i === w.active[0]) {
          shake = 6; sfx.boom(); const q = metaRect(this.sh, this, w.hit), px = this.face > 0 ? q.x1 - 8 : q.x0 + 8;
          spawnFx(fxOr('rot_hit', 'dust'), px, this.y - 6, this.face);
          hazards.push({ x: px, y: this.y, w: 44, h: 8, dmg: 5, rot: 22, tick: 0.5, id: ++hazardId, life: 4, pool: true });
        }
        if (this.type === 'grave_knight' && tag === 'slam' && an.changed && an.i === w.active[0]) {
          shake = 7; sfx.boom();
          const fx0 = metaRect(this.sh, this, w.hit), cx = this.face > 0 ? fx0.x1 - 6 : fx0.x0 + 6;
          spawnFx('shockwave', cx, this.y, 1); spawnFx('ground_crack', cx, this.y, 1);
          for (const d of [-1, 1]) hazards.push({ x: cx, y: this.y, vx: d * 150, w: 12, h: 12, dmg: 30, id: ++hazardId, life: 0.9, wave: true, dir: d });
        }
      }
    });
    if (this.state !== 'attack') return;
    // projectiles
    const sp = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn[tag];
    const spawnFrame = sp ? sp.frame : (tag === 'shoot' ? 6 : 6);
    if (!this.spawned && an.i >= spawnFrame && (c.ranged)) {
      this.spawned = true;
      const at = sp ? metaPoint(this.sh, this, sp.at) : { x: this.x + this.face * 12, y: this.y - this.h * 0.6 };
      if (c.ranged === 'arrow') {
        let ang = Math.atan2(P.y - 14 - at.y, P.x - at.x); const base = this.face > 0 ? 0 : Math.PI;
        let d = ang - base; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI; ang = base + clamp(d, -0.5, 0.5);
        projectiles.push({ owner: 'enemy', kind: 'arrow', x: at.x, y: at.y, vx: Math.cos(ang) * 230, vy: Math.sin(ang) * 230, g: 60, dmg: c.dmg.arrow, life: 2.5, r: 3, t: 0, id: ++hazardId });
        sfx.shoot();
      } else if (c.ranged === 'rotglob') {
        const T = 0.75, dx = clamp(P.x - at.x, -200, 200);
        projectiles.push({ owner: 'enemy', kind: 'rotglob', x: at.x, y: at.y, vx: dx / T, vy: -170, g: 420, dmg: c.dmg.rotglob * NGP.dmg, rot: c.rot, life: 3, r: 5, t: 0, id: ++hazardId });
        sfx.shoot();
      } else if (c.ranged === 'mist') {
        projectiles.push({ owner: 'enemy', kind: 'emist', x: P.x + rand(-10, 10), y: P.y, vx: 0, vy: 0, dmg: c.dmg.mist * NGP.dmg, rot: c.rot, life: 3.6, r: 24, t: 0, tick: 0.5, static: true, id: ++hazardId });
        sfx.fire();
      } else {
        projectiles.push({ owner: 'enemy', kind: 'fireball', x: at.x, y: at.y, vx: this.face * 120, vy: -10, homing: 1.3, dmg: c.dmg.fireball, life: 3.2, r: 5, t: 0, id: ++hazardId });
        sfx.fire();
      }
    }
    if (!lunging) this.vx *= Math.pow(0.004, dt);
    this.gravity(dt);
    if (an.done && c.suicide) { this.hp = 0; this.state = 'dead'; this.anim.set(this.sh.has('death') ? 'death' : 'hurt', false); killed.add(this.key); gainCinders(c.cinders, this.x, this.y - 8); this.anim.done = true; return; }
    if (an.done) { this.setA('idle', 'idle'); this.cool = rand(...c.cool); }
  }
  updateFlying(dt) {
    const c = this.cfg, dx = this.dist(), adx = Math.abs(dx);
    this.cool -= dt; this.t += dt;
    if (!this.aggro && this.canSee()) this.aggro = true;
    const clampFly = () => { this.x = clamp(this.x, 10, room.pw - 10); this.y = clamp(this.y, 20, room.ph - 10); };
    switch (this.state) {
      case 'idle': case 'walk': {
        if (this.anim.tag !== 'fly' && this.sh.has('fly')) this.anim.set('fly', true);
        let tx = this.home, ty = this.hy + Math.sin(this.t * 2) * 8;
        if (this.aggro) { this.facePlayer(); tx = P.x - this.face * 56; ty = P.y - 56 + Math.sin(this.t * 2.4) * 10; }
        this.vx = approach(this.vx, clamp((tx - this.x) * 1.8, -c.speed, c.speed), 200 * dt);
        this.vy = approach(this.vy, clamp((ty - this.y) * 1.8, -c.speed, c.speed), 200 * dt);
        this.x += this.vx * dt; this.y += this.vy * dt; clampFly();
        if (this.aggro && c.ranged && this.cool <= 0 && adx < c.range && Math.random() < 0.6 && lineOfSight(this.x, this.y, P.x, P.y - 14)) {
          this.startAttack('cast'); this.vx *= 0.3; this.vy *= 0.3; break;
        }
        if (this.aggro && this.cool <= 0 && this.sh.has('dive') && adx < (c.ranged ? 110 : c.range + 30) && lineOfSight(this.x, this.y, P.x, P.y - 14)) {
          this.startAttack('dive'); const a = Math.atan2(P.y - 14 - this.y, P.x - this.x); this.diveV = { x: Math.cos(a), y: Math.sin(a) };
          this.vx = -this.diveV.x * 40; this.vy = -this.diveV.y * 40;   // wind back
        }
        break;
      }
      case 'attack': {
        if (this.atk === 'cast') {
          this.vx *= Math.pow(0.05, dt); this.vy *= Math.pow(0.05, dt); this.x += this.vx * dt; this.y += this.vy * dt; clampFly(); this.facePlayer();
          const sp = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn.cast;
          if (!this.spawned && this.anim.i >= (sp ? sp.frame : 6)) {
            this.spawned = true; const at = sp ? metaPoint(this.sh, this, sp.at) : { x: this.x, y: this.y };
            if (c.ranged === 'inkbolt') { const a = Math.atan2(P.y - 14 - at.y, P.x - at.x); projectiles.push({ owner: 'enemy', kind: 'inkbolt', x: at.x, y: at.y, vx: Math.cos(a) * 170, vy: Math.sin(a) * 170, homing: 1.4, dmg: c.dmg.inkbolt * NGP.dmg, life: 2.6, r: 4, t: 0, id: ++hazardId }); }
            else for (let k = -1; k <= 1; k++) { const a = Math.atan2(P.y - 14 - at.y, P.x - at.x) + k * 0.28; projectiles.push({ owner: 'enemy', kind: 'lightorb', x: at.x, y: at.y, vx: Math.cos(a) * 150, vy: Math.sin(a) * 150, dmg: c.dmg.lightorb * NGP.dmg, life: 2.5, r: 4, t: 0, id: ++hazardId }); }
            sfx.glint();
          }
          if (this.anim.done) { this.setA('idle', this.sh.has('fly') ? 'fly' : 'idle'); this.cool = rand(...c.cool); }
          break;
        }
        const an = this.anim, w = metaWindows(this.sh, 'dive')[0] || { active: [2, 4] };
        if (an.i >= w.active[0] && an.i <= w.active[1]) {
          if (an.changed && an.i === w.active[0]) sfx.swing();
          this.vx = this.diveV.x * 210; this.vy = this.diveV.y * 210;
          if (!this.hitIds.has(0) && overlap(this.hurtbox(), playerHurtbox()) && hurtPlayer(c.dmg.dive * NGP.dmg, sign(this.vx), this.atkId, { parryable: true, src: this })) this.hitIds.add(0);
        } else { this.vx *= Math.pow(0.05, dt); this.vy *= Math.pow(0.05, dt); }
        this.x += this.vx * dt; this.y += this.vy * dt; clampFly();
        if (solidAtPx(this.x, this.y)) { this.x -= this.vx * dt; this.y -= this.vy * dt; this.vx = 0; this.vy = 0; }
        if (an.done) { this.setA('idle', this.sh.has('fly') ? 'fly' : 'idle'); this.cool = rand(...c.cool); }
        break;
      }
      case 'hurt':
        this.vx *= Math.pow(0.05, dt); this.vy *= Math.pow(0.05, dt); this.x += this.vx * dt; this.y += this.vy * dt; clampFly();
        if (this.anim.done) { this.setA('idle', 'fly'); this.cool = Math.max(this.cool, 0.6); }
        break;
      case 'stagger': case 'parried':
        this.t -= dt * 2; this.vy = 30; this.y += this.vy * dt; clampFly();
        if (this.anim.done) this.anim.hold();
        if (this.t <= 0 || this.t > 100) { this.setA('idle', 'fly'); this.cool = 0.6; this.t = 0; }
        break;
    }
    addLight(this.x, this.y, 26, '160,200,255', 0.5);
  }
  draw() {
    const opt = this.flash > 0 ? { flash: this.flash * 0.7 } : this.state === 'stagger' || this.state === 'parried' ? { flash: 0.18 + 0.12 * Math.sin(time * 20), flashColor: '#ffd070' } : {};
    if (this.state === 'dead' && this.anim.done) { opt.alpha = 0; return; }
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
    if (!this.sh.ok) { g.fillStyle = '#8a3040'; g.fillRect(Math.round(this.x - this.w / 2), Math.round(this.y - this.h), this.w, this.h); }
    if (this.critable()) { g.fillStyle = '#ffd070'; const y = Math.round(this.y - this.h - 10 + Math.sin(time * 8) * 1.5); g.fillRect(Math.round(this.x) - 1, y, 3, 3); g.fillRect(Math.round(this.x), y - 1, 1, 5); g.fillRect(Math.round(this.x) - 2, y + 1, 5, 1); }
    if (this.hp < this.maxHp && this.alive && this.dmgT > -4) {
      const w = this.cfg.elite ? 40 : 20, x = Math.round(this.x - w / 2), y = Math.round(this.y - this.h - (this.cfg.flying ? 0 : 6) - 4);
      g.fillStyle = 'rgba(10,6,8,0.8)'; g.fillRect(x - 1, y - 1, w + 2, 4);
      g.fillStyle = '#8a1a1a'; g.fillRect(x, y, Math.max(0, w * this.hp / this.maxHp), 2);
      if (this.bleed > 0) { g.fillStyle = '#d02040'; g.fillRect(x, y + 2, w * this.bleed / 100, 1); }
    }
  }
}
