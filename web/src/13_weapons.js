// ------------------------------------------------------------------ v8 expansion weapons (agent W), cut down in the weapon revamp (agent WS)
// Three of the nine weapons live here (types in 74_arsenal9.js, moves in 75_moves.js), plus the status buildup on foes
// (frost, burn) and the small effect system other weapon code uses (WFX).
registerGear({ weapons: {
  quarterstaff: { name: 'Pilgrim’s Quarterstaff', base: 42, sc: { str: 'D', dex: 'C', fth: '-' }, speed: 1.2, reach: 1.25, stam: 0.8, poise: 1.0, art: 'whirlwind',
    desc: 'Ash wood shod in iron at both ends. Fast and patient: it strikes with either end, and vaults you over whatever stands in your way.' },
  knight_shield: { name: 'Knight’s Sword and Shield', base: 42, sc: { str: 'C', dex: 'D', fth: '-' }, speed: 1.05, reach: 0.95, stam: 0.95, poise: 1.1, guard: 1.0, art: 'aegis',
    desc: 'The oldest answer to fear: a blade in one hand, a wall in the other. Hold block to raise the shield; tap it to turn a blow aside.' },
  twinfangs: { name: 'Twinfangs', base: 42, sc: { str: 'D', dex: 'A', fth: '-' }, speed: 1.3, reach: 0.9, stam: 0.8, poise: 0.7, bleed: 14, art: 'twin_tempest',
    desc: 'The Hollow Champion fought a hundred duels in the ramparts’ pit and never once used one blade where two would do.' },
} });

// ------------------------------------------------------------------ WFX: small world effects owned by weapons
// { t, life, update(dt) -> false to die early, draw() }, cleared on room change.
let WFX = [];
function wfx(e) { e.t = 0; WFX.push(e); return e; }
HOOKS.enter.push(() => { WFX = []; });
HOOKS.update.push(dt => {
  for (const e of WFX) { e.t += dt; if ((e.update && e.update(dt) === false) || (e.life !== undefined && e.t >= e.life)) e.dead = true; }
  WFX = WFX.filter(e => !e.dead);
});
HOOKS.render.push(() => drawGlow(() => { for (const e of WFX) if (e.draw) e.draw(); }));   // weapon fx emit light (41_light.js)
// play a wpn_fx_* strip at (x, y) (bottom-anchored unless center), frame chosen by time t
function wfxSheet(name) { return sheet('wpn_fx_' + name); }
function wfxDraw(name, t, x, y, face = 1, opt = {}) {
  const s = wfxSheet(name); if (!s.ok) return false;
  const tg = s.tag(Object.keys(s.tags)[0]); let ms = t * 1000, f = tg.from;
  if (opt.loop) { let tot = 0; for (let i = tg.from; i <= tg.to; i++) tot += s.frames[i].ms; ms %= tot; }
  while (f < tg.to && ms >= s.frames[f].ms) { ms -= s.frames[f].ms; f++; }
  drawSprite(s, f, x, y, face, { bottom: !opt.center, center: !!opt.center, alpha: opt.alpha, rot: opt.rot, pivot: opt.pivot });
  return true;
}
function wfxDur(name) { const s = wfxSheet(name); if (!s.ok) return 0.4; const tg = s.tag(Object.keys(s.tags)[0]); let n = 0; for (let i = tg.from; i <= tg.to; i++) n += s.frames[i].ms; return n / 1000; }
// damage every target in a rect (once per call); returns the list hit
function wStrike(r, dmg, opt = {}) {
  const out = [];
  for (const t of targets()) {
    if (opt.skip && opt.skip.has(t)) continue;
    const hb = hbOf(t); if (!hb || !overlap(r, hb)) continue;
    if (opt.skip) opt.skip.add(t);
    const x = clamp((r.x0 + r.x1) / 2, hb.x0 + 2, hb.x1 - 2), y = clamp((r.y0 + r.y1) / 2, hb.y0, hb.y1);
    t.hit({ dmg: dmg * rand(0.93, 1.07), poise: opt.poise || 0, dir: opt.dir || (t.x > P.x ? 1 : -1), kind: opt.kind || 'spell', x, y, big: !!opt.big, fire: !!opt.fire, quiet: !!opt.quiet });
    out.push(t);
    if (opt.frost) wAddFrost(t, opt.frost);
    if (opt.burn) wAddBurn(t, opt.burn[0], opt.burn[1]);
  }
  return out;
}
function wFloorBelow(x, y) {   // px y of the floor surface under (x, y), or null
  let fy = Math.floor(y / TILE) * TILE;
  for (let k = 0; k < 6 && !solidAtPx(x, fy + 1); k++) fy += TILE;
  return solidAtPx(x, fy + 1) ? fy : null;
}

// ------------------------------------------------------------------ status buildup on foes (enemies, bosses, boss parts)
// frost: a meter fills with each frost hit; full -> burst (~8% max HP, capped on bosses) + a brief slow and stance damage
// burn: damage over time from fire weapons (and Cinder Blade)
const wIsBoss = t => !!t.boss;
function wMaxHp(t) { return t.maxHp || (boss && boss.maxHp) || 300; }
function wAddFrost(t, n) {
  if (!t || t.prop || !t.alive && t.alive !== undefined) return;
  if ((t._frostCd || 0) > 0) return;
  t._frost = (t._frost || 0) + n * (wIsBoss(t) ? 0.7 : 1); t._frostShow = 2.5;
  if (t._frost >= 100) wFrostBurst(t);
}
function wFrostBurst(t) {
  t._frost = 0; t._frostCd = 2.5;
  const hb = t.hurtbox && t.hurtbox(); const x = hb ? (hb.x0 + hb.x1) / 2 : t.x, y = hb ? (hb.y0 + hb.y1) / 2 : t.y - 14;
  const d = wIsBoss(t) ? Math.min(wMaxHp(t) * 0.08, 150 + D.light * 1.2) : wMaxHp(t) * 0.08 + 14;
  t.hit({ dmg: d, poise: wIsBoss(t) ? 70 : 45, dir: t.x > P.x ? 1 : -1, kind: 'frost', x, y, big: true });
  t._slowT = wIsBoss(t) ? 1.6 : 3.0; wSlowWrap(t);
  shake = Math.max(shake, 4); tone(1480, 0.35, 0.07, 'triangle', 0.5); tone(2200, 0.25, 0.05, 'sine', 0.6); noise(0.25, 5000, 2, 0.2, 'highpass');
  const e = wfx({ life: wfxDur('frost') || 0.5, x, y, draw() { if (!wfxDraw('frost', this.t, this.x, this.y, 1, { center: true })) { g.fillStyle = 'rgba(190,230,255,0.6)'; g.fillRect(this.x - 8, this.y - 8, 16, 16); } addLight(this.x, this.y, 50, '170,220,255', 0.9); } });
  for (let i = 0; i < 18; i++) particles.push({ x, y, vx: rand(-110, 110), vy: rand(-120, 40), g: 260, life: rand(0.4, 0.9), kind: 'frost' });
  return e;
}
function wAddBurn(t, secs, dps) {
  if (!t || t.prop) return;
  t._burnT = Math.max(t._burnT || 0, secs); t._burnDps = Math.max(t._burnT > 0 ? (t._burnDps || 0) * 0.5 : 0, dps);
}
// public status API (other agents may route their own frost/burn through here so every source shares one meter)
const WSTATUS = { frost: wAddFrost, burn: wAddBurn, burst: wFrostBurst };
// slowing a foe: wrap its update so time passes slower for it while _slowT > 0 (works for any enemy/boss class)
function wSlowWrap(t) {
  if (t._slowWrapped || typeof t.update !== 'function') return;
  const o = t.update; t._slowWrapped = true;
  t.update = function (dt, ...a) { return o.call(this, this._slowT > 0 ? dt * 0.55 : dt, ...a); };
}
HOOKS.update.push(dt => {
  for (const t of targets()) {
    if (t.prop) continue;
    if (t._frostCd > 0) t._frostCd -= dt;
    if (t._frost > 0) { t._frost = Math.max(0, t._frost - 5 * dt); t._frostShow -= dt; }
    if (t._slowT > 0) { t._slowT -= dt; if (Math.random() < 0.3) { const hb = t.hurtbox && t.hurtbox(); if (hb) particles.push({ x: rand(hb.x0, hb.x1), y: rand(hb.y0, hb.y1), vx: 0, vy: rand(5, 20), life: 0.6, kind: 'frost' }); } }
    if (t._burnT > 0) {
      t._burnT -= dt; t._burnTick = (t._burnTick || 0) + dt;
      const hb = t.hurtbox && t.hurtbox();
      if (hb && Math.random() < 0.45) particles.push({ x: rand(hb.x0, hb.x1), y: rand(hb.y0 + (hb.y1 - hb.y0) * 0.3, hb.y1), vx: rand(-8, 8), vy: -rand(20, 60), life: rand(0.3, 0.6), kind: 'fire' });
      if (hb) addLight((hb.x0 + hb.x1) / 2, (hb.y0 + hb.y1) / 2, 30, '255,140,60', 0.5);
      if (t._burnTick >= 0.5) {
        t._burnTick -= 0.5;
        const d = Math.max(1, Math.round(t._burnDps * 0.5)), x = hb ? (hb.x0 + hb.x1) / 2 : t.x, y = hb ? hb.y0 + 6 : t.y - 20;
        if (wIsBoss(t) && typeof t.commonUpdate === 'function') {   // bosses: burn like rot does (never the killing blow)
          t.hp = Math.max(1, t.hp - d); t.dmgShown = (t.dmgT > 0 ? t.dmgShown : 0) + d; t.dmgT = Math.max(t.dmgT || 0, 1.0); popup(x, y, d, '#ff9a4a');
        } else t.hit({ dmg: d, poise: 0, dir: 0, kind: 'burn', x, y, quiet: true, fire: true });
      }
    }
  }
});
// frost meters above chilled foes, a pale frost sheen on slowed ones
HOOKS.render.push(() => {
  for (const t of targets()) {
    if (t.prop) continue;
    const hb = t.hurtbox && t.hurtbox(); if (!hb) continue;
    if (t._frost > 1 && t._frostShow > 0) {
      const w = 16, x = Math.round((hb.x0 + hb.x1) / 2 - w / 2), y = Math.round(hb.y0 - 6), f = Math.min(1, t._frost / 100);
      g.fillStyle = 'rgba(10,16,30,0.75)'; g.fillRect(x - 1, y - 1, w + 2, 4);
      g.fillStyle = '#6aa8e8'; g.fillRect(x, y, Math.round(w * f), 2);
      g.fillStyle = '#e6f6ff'; g.fillRect(x, y, Math.round(w * f), 1);
    }
    if (t._slowT > 0 && t.sh && t.anim && t.sh.ok) drawSprite(t.sh, t.anim.frame, t.x, t.y, t.face, { flash: 0.55, flashColor: '#a8dcff', alpha: 0.45 * Math.min(1, t._slowT) });
  }
});
// every melee hit: frost from frost weapons, burn from fire weapons / a burning blade
HOOKS.strike.push((t, info, A) => {
  if (!t || t.prop || !D) return;
  const W = D.W, heavy = !!info.heavy;
  if (W.frost) wAddFrost(t, W.frost * (heavy ? 1.7 : 1) * (P.charged ? 1.4 : 1));
  if (W.fire || P.fireT > 0) wAddBurn(t, heavy ? 4 : 2.5, D.light * (heavy ? 0.24 : 0.14) * (1 + (W.fire || 0)));
});

// ------------------------------------------------------------------ procedural lightning (chain lightning, sky bolts)
function wBoltPath(x0, y0, x1, y1, jag = 6) {
  const n = Math.max(3, Math.round(Math.hypot(x1 - x0, y1 - y0) / 8)), pts = [[x0, y0]];
  for (let i = 1; i < n; i++) { const k = i / n; pts.push([x0 + (x1 - x0) * k + rand(-jag, jag) * 0.5, y0 + (y1 - y0) * k + rand(-jag, jag)]); }
  pts.push([x1, y1]); return pts;
}
function wDrawBolt(pts, a = 1, w = 1) {
  g.save(); g.globalAlpha = a; g.lineCap = 'round';
  for (const [col, lw] of [['rgba(90,140,230,0.55)', 3 * w], ['#aad6ff', 1.6 * w], ['#f4fbff', 0.8 * w]]) {
    g.strokeStyle = col; g.lineWidth = lw; g.beginPath(); g.moveTo(pts[0][0], pts[0][1]);
    for (const p of pts.slice(1)) g.lineTo(p[0], p[1]); g.stroke();
  }
  g.restore();
  for (const p of pts) addLight(p[0], p[1], 22, '170,210,255', 0.5 * a);
}
function wZap(x0, y0, x1, y1, life = 0.18) {
  wfx({ life, pts: wBoltPath(x0, y0, x1, y1), k: 0, update() { if ((this.k += 1) % 3 === 0) this.pts = wBoltPath(x0, y0, x1, y1); }, draw() { wDrawBolt(this.pts, 1 - this.t / this.life); } });
}

// debug handles for headless tests (tools/shots): window.__game.w
if (typeof window !== 'undefined' && window.__game) window.__game.w = {
  hurt: (dmg, dir, opt) => hurtPlayer(dmg, dir, 'dbg' + Math.random(), opt || {}), Enemy, spawn(type, tx, ty) { const e = new Enemy(type, tx * TILE + 8, (ty + 1) * TILE, 'dbg' + enemyId); enemies.push(e); return e; },
  spawnBoss(kind, tx, ty) { SAVE.flags['cut:' + kind] = 1; const cx = tx * TILE + 8, fy = (ty + 1) * TILE; boss = kind === 'hound' ? new Hound(cx, fy) : kind === 'omen' ? new Omen(cx, fy) : BOSS_SPAWN[kind](cx, fy, {}); return boss; },
  projCount: () => projectiles.filter(p => p.owner === 'player').length,
  get WFX() { return WFX; }, addFrost: wAddFrost, addBurn: wAddBurn, wcls, moveset, ATK, get targets() { return targets(); },
};
