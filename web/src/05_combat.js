// ------------------------------------------------------------------ fx, particles, projectiles, props
let fx = [], particles = [], ghosts = [], popups = [], hazards = [], toasts = [];
let hitstop = 0, shake = 0, slowmo = 0, flashScreen = 0, time = 0;
const FX_NATIVE_LEFT = new Set(['boss_slash', 'arc_down', 'arc_up', 'arc_wide', 'thrust', 'light_spear']);
const FX_BOTTOM = new Set(['shockwave', 'heal', 'dust', 'pillar', 'ground_crack', 'spin', 'flame_ring', 'levelup', 'death_ash', 'root_spike']);
function fxSheet(name) { return sheet('fx_' + name, { native: FX_NATIVE_LEFT.has(name) ? -1 : 1 }); }
const fxOr = (...names) => names.find(n => n && fxSheet(n).ok);
function spawnFx(name, x, y, face = 1, follow = null, extra = {}) {
  if (!name) return null;
  const s = fxSheet(name); if (!s.ok) return null;
  const e = { name, s, anim: new Anim(s, Object.keys(s.tags)[0], !!extra.loop, extra.speed || 1), x, y, face, follow,
              center: !FX_BOTTOM.has(name) && !extra.bottom, bottom: FX_BOTTOM.has(name) || extra.bottom, ...extra };
  fx.push(e); return e;
}
function updateFx(dt) {
  for (const f of fx) { f.anim.update(dt); if (f.follow) { f.x = f.follow.x; f.y = f.follow.y; } if (f.life !== undefined && (f.life -= dt) <= 0) f.kill = true; }
  fx = fx.filter(f => !f.anim.done && !f.kill);
}
function drawFx(f) {
  drawSprite(f.s, f.anim.frame, f.x, f.y, f.face, { center: f.center, bottom: f.bottom, pivot: f.pivot, rot: f.rot, alpha: f.alpha,
    flash: f.tint ? 0.55 : 0, flashColor: f.tint, blend: f.add ? 'lighter' : undefined });
}
function popup(x, y, v, color = '#f1e6c8') { popups.push({ x: x + rand(-4, 4), y, v: String(Math.round(v)), color, life: 0.9 }); }
function toast(msg, dur = 2.6) { if (toasts.length && toasts[toasts.length - 1].msg === msg) { toasts[toasts.length - 1].life = dur; return; } toasts.push({ msg, life: dur, t: 0 }); if (toasts.length > 3) toasts.shift(); }
function gainCinders(n, x, y) {
  n = Math.round(n * (charmOn('c_greed') ? 1.25 : 1) * NGP.cinders);
  SAVE.cinders += n;
  for (let i = 0; i < Math.min(18, 3 + n / 20); i++) particles.push({ x: x + rand(-8, 8), y: y + rand(-10, 4), vx: rand(-60, 60), vy: -rand(40, 110), life: 1.6, kind: 'cinder', home: 0.35 + rand(0, 0.3) });
  cinderFlash = 1.2; cinderGain += n;
}
let cinderFlash = 0, cinderGain = 0;

function ambientParticles(dt) {
  const kind = AREAS[room.def.biome].amb;
  let n = 0; for (const p of particles) if (p.amb) n++;
  while (n++ < 34) {
    const p = { x: cam.x + rand(-20, W + 20), y: cam.y + rand(-10, H + 10), amb: true, life: rand(4, 9), sway: rand(0, 6.28) };
    if (kind === 'ash') Object.assign(p, { vx: rand(4, 14), vy: rand(4, 12), kind: 'ash' });
    else if (kind === 'dust') Object.assign(p, { vx: rand(-3, 3), vy: rand(-3, 3), kind: 'dust' });
    else if (kind === 'spore') Object.assign(p, { vx: rand(-3, 3), vy: -rand(2, 8), kind: 'spore' });
    else if (kind === 'petal') Object.assign(p, { vx: rand(4, 14), vy: rand(6, 14), kind: 'petal', pet: true });
    else Object.assign(p, { vx: rand(-3, 3), vy: -rand(3, 10), kind: 'mote' });
    particles.push(p);
  }
}
function updateParticles(dt) {
  for (const p of particles) {
    p.life -= dt; p.sway = (p.sway || 0) + dt * 2;
    if (p.kind === 'cinder') {
      p.home -= dt;
      if (p.home <= 0) { const dx = P.x - p.x, dy = P.y - 16 - p.y, d = Math.hypot(dx, dy) || 1; p.vx = lerp(p.vx, dx / d * 260, Math.min(1, dt * 8)); p.vy = lerp(p.vy, dy / d * 260, Math.min(1, dt * 8)); if (d < 8) { p.life = 0; if (Math.random() < 0.3) sfx.cinders(); } }
      else { p.vy += 300 * dt; p.vx *= Math.pow(0.1, dt); }
      p.x += p.vx * dt; p.y += p.vy * dt; continue;
    }
    if (p.g) p.vy += p.g * dt;
    p.x += ((p.vx || 0) + (p.amb ? Math.sin(p.sway) * 5 : 0)) * dt; p.y += (p.vy || 0) * dt;
    if (p.kind === 'rock' && p.g && solidAtPx(p.x, p.y)) { p.vy *= -0.3; p.vx *= 0.6; p.y -= 1; }
    if (p.amb && (p.x < cam.x - 40 || p.x > cam.x + W + 40 || p.y < cam.y - 40 || p.y > cam.y + H + 40)) p.life = 0;
  }
  particles = particles.filter(p => p.life > 0);
  if (particles.length > 700) particles.splice(0, particles.length - 700);
}
const PCOL = { spark: '255,240,200', gold: '255,205,110', fire: '255,120,50', ember: '255,150,70', rock: '90,84,100', ash: '150,140,150',
  dust: '160,150,120', mote: '255,225,150', spore: '150,210,90', petal: '255,244,220', teal: '120,235,205', ink: '120,80,200', blood: '200,30,45', cinder: '255,215,120', blood: '170,20,30', frost: '180,220,255', root: '255,190,80' };
function drawParticles() {
  for (const p of particles) {
    const a = p.amb ? Math.min(1, p.life / 2) * (p.kind === 'mote' ? 0.7 : 0.45) : Math.min(1, p.life * 2.5);
    g.fillStyle = `rgba(${PCOL[p.kind] || PCOL.gold},${a})`;
    const s = p.kind === 'rock' || p.kind === 'cinder' || (p.pet && Math.sin(p.sway * 2) > 0) ? 2 : 1;
    g.fillRect(Math.round(p.x), Math.round(p.y), s, s);
    if (p.kind === 'cinder' || p.kind === 'fire' || p.kind === 'mote') addLight(p.x, p.y, p.kind === 'mote' ? 10 : 14, '255,190,90', 0.35);
  }
}

// ---- projectiles
function updateProjectiles(dt) {
  for (const pr of projectiles) {
    if (pr.delay > 0) { pr.delay -= dt; if (pr.delay <= 0 && pr.onStart) pr.onStart(); continue; }
    pr.t += dt; pr.life -= dt;
    if (pr.homing && pr.life > 0.3) {
      const a = Math.atan2(P.y - 16 - pr.y, P.x - pr.x), cur = Math.atan2(pr.vy, pr.vx);
      let d = a - cur; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI;
      const na = cur + clamp(d, -pr.homing * dt, pr.homing * dt), sp = Math.hypot(pr.vx, pr.vy);
      pr.vx = Math.cos(na) * sp; pr.vy = Math.sin(na) * sp;
    }
    if (pr.seek && pr.t > 0.15) {
      let best = null, bd = 1e9;
      for (const t of targets()) { if (t.prop) continue; const d = Math.hypot(t.x - pr.x, t.y - 16 - pr.y); if (d < bd && d < 220) { bd = d; best = t; } }
      if (best) { const hb = best.hurtbox(); if (hb) { const a = Math.atan2((hb.y0 + hb.y1) / 2 - pr.y, (hb.x0 + hb.x1) / 2 - pr.x), cur = Math.atan2(pr.vy, pr.vx); let d = a - cur; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI; const na = cur + clamp(d, -pr.seek * dt, pr.seek * dt), sp = Math.max(170, Math.hypot(pr.vx, pr.vy) + 200 * dt); pr.vx = Math.cos(na) * sp; pr.vy = Math.sin(na) * sp; } }
    }
    if (pr.tick) { pr.tickT = (pr.tickT || 0) - dt; if (pr.tickT <= 0) { pr.tickT = pr.tick; pr.hits = new Set(); } if (Math.random() < 0.5) particles.push({ x: pr.x + rand(-24, 24), y: pr.y - rand(0, 30), vx: 0, vy: -rand(5, 20), life: 0.7, kind: 'spore' }); }
    if (pr.g) pr.vy += pr.g * dt;
    pr.x += pr.vx * dt; pr.y += pr.vy * dt;
    const L = pr.kind === 'fireball' || pr.kind === 'ashbolt' ? ['255,160,70', 40] : pr.kind === 'sunspear' || pr.kind === 'lightorb' || pr.kind === 'sovlance' ? ['255,220,140', 46] : pr.kind === 'lance' || pr.kind === 'moonwave' ? ['160,210,255', 44] : pr.kind === 'shard' ? ['200,160,255', 22] : pr.kind === 'rotglob' ? ['150,210,90', 26] : null;
    if (L) addLight(pr.x, pr.y, L[1], L[0], 0.9);
    if (pr.kind === 'ashbolt' || pr.kind === 'fireball') if (Math.random() < 0.7) particles.push({ x: pr.x - sign(pr.vx) * 6, y: pr.y + rand(-2, 2), vx: -pr.vx * 0.1, vy: rand(-15, 5), life: 0.35, kind: pr.kind === 'fireball' ? 'fire' : 'gold' });
    if (pr.kind === 'sunspear') if (Math.random() < 0.6) particles.push({ x: pr.x - sign(pr.vx) * 10, y: pr.y + rand(-1, 1), vx: 0, vy: rand(-8, 8), life: 0.3, kind: 'gold' });
    if (!pr.static && solidAtPx(pr.x, pr.y)) { impact(pr); continue; }
    if (pr.static) pr.vx *= Math.pow(0.1, dt);
    const r = pr.kind === 'mist' || pr.kind === 'emist' ? rect(pr.x - pr.r, pr.y - 34, pr.x + pr.r, pr.y) : rect(pr.x - pr.r, pr.y - pr.r, pr.x + pr.r, pr.y + pr.r);
    if (pr.owner === 'player') {
      for (const t of targets()) {
        if (pr.hits.has(t)) continue;
        const hb = hbOf(t); if (!hb || !overlap(r, hb)) continue;
        if (pr.win && (pr.t < pr.win[0] || pr.t > pr.win[1])) continue;
        pr.hits.add(t);
        const hb2 = t.hurtbox();
        t.hit({ dmg: outgoing(pr.dmg, 1, pr.kind === 'crescent' || pr.kind === 'moonwave' ? 'melee' : 'spell'), poise: pr.poise || (pr.kind === 'crescent' ? 30 : pr.kind === 'mist' ? 0 : 22), dir: sign(pr.vx), kind: 'spell', x: pr.kind === 'mist' ? (hb2.x0 + hb2.x1) / 2 : pr.x, y: pr.kind === 'mist' ? (hb2.y0 + hb2.y1) / 2 : pr.y, big: !['ashbolt', 'mist', 'shard'].includes(pr.kind), quiet: pr.kind === 'mist' });
        if (!pr.pierce) { impact(pr); break; }
      }
      hitBreakablesProjectile(pr);
    } else if (overlap(r, playerHurtbox())) {
      if (pr.tick) { hurtPlayer(pr.dmg, sign(pr.vx) || 1, pr.id + '_' + Math.floor(pr.t / pr.tick), { rot: pr.rot }); }
      else if (hurtPlayer(pr.dmg, sign(pr.vx), pr.id, { rot: pr.rot })) impact(pr);
    }
  }
  projectiles = projectiles.filter(p => p.life > 0);
}
function hitBreakablesProjectile(pr) {}
function impact(pr) {
  pr.life = 0;
  if (pr.kind === 'ashbolt') spawnFx(fxOr('ashbolt_hit', 'hit'), pr.x, pr.y);
  else if (pr.kind === 'fireball') { spawnFx(fxOr('ashbolt_hit', 'hit'), pr.x, pr.y, 1, null, { tint: '#ff7030' }); for (let i = 0; i < 8; i++) particles.push({ x: pr.x, y: pr.y, vx: rand(-60, 60), vy: rand(-80, 20), g: 200, life: 0.5, kind: 'fire' }); }
  else if (pr.kind === 'sunspear') spawnFx(fxOr('spear_impact', 'hit'), pr.x, pr.y);
  else if (pr.kind === 'rotglob') { spawnFx(fxOr('rot_hit', 'hit'), pr.x, pr.y); for (let i = 0; i < 8; i++) particles.push({ x: pr.x, y: pr.y, vx: rand(-50, 50), vy: rand(-70, 10), g: 250, life: 0.5, kind: 'spore' }); }
  else if (pr.kind === 'lightorb' || pr.kind === 'sovlance') spawnFx(fxOr('spear_impact', 'hit'), pr.x, pr.y);
  else if (pr.kind === 'inkbolt') { spawnFx('hit', pr.x, pr.y, 1, null, { tint: '#7a50d0' }); for (let i = 0; i < 6; i++) particles.push({ x: pr.x, y: pr.y, vx: rand(-50, 50), vy: rand(-60, 10), g: 200, life: 0.5, kind: 'ink' }); }
  else if (pr.kind === 'shard' || pr.kind === 'lance') spawnFx('hit', pr.x, pr.y);
  else if (pr.kind === 'arrow') { for (let i = 0; i < 4; i++) particles.push({ x: pr.x, y: pr.y, vx: rand(-40, 40), vy: -rand(10, 60), g: 300, life: 0.4, kind: 'spark' }); }
}
function drawProjectiles() {
  for (const pr of projectiles) {
    if (pr.delay > 0) continue;
    if (pr.fxName) {
      const s = fxSheet(pr.fxName); if (!s.ok) continue;
      const t = s.tag(Object.keys(s.tags)[0]); let ms = pr.t * 1000, f = t.from;
      while (f < t.to && ms >= s.frames[f].ms) { ms -= s.frames[f].ms; f++; }
      drawSprite(s, f, pr.x, pr.y, pr.face || 1, { bottom: true });
      addLight(pr.x, pr.y - 30, 50, pr.kind === 'ppillar' ? '255,240,200' : '255,200,110', 0.8);
      continue;
    }
    if (pr.kind === 'sunspear') { const s = fxSheet('light_spear'); if (s.ok) { drawRotated(s, s.tag(Object.keys(s.tags)[0]).from + Math.floor(pr.t * 16) % 4, pr.x, pr.y, pr.vx > 0 ? 0 : Math.PI); continue; } }
    if (pr.kind === 'mist' || pr.kind === 'emist') { const ms = fxSheet('rotmist'); if (ms.ok) { const t = ms.tag('rotmist'), n = t.to - t.from + 1; drawSprite(ms, t.from + Math.min(n - 1, Math.floor(pr.t * 8)) % n, pr.x, pr.y, 1, { bottom: true, alpha: Math.min(1, pr.life * 2) * 0.85 }); } else { g.fillStyle = 'rgba(120,180,60,0.35)'; g.fillRect(pr.x - pr.r, pr.y - 30, pr.r * 2, 30); } continue; }
    const PS = { arrow: 'proj_arrow', fireball: 'proj_fireball', rotglob: 'proj_rotglob', lightorb: 'proj_lightorb', inkbolt: 'proj_inkbolt' };
    const s = PS[pr.kind] ? sheet(PS[pr.kind]) : fxSheet(pr.sh ? pr.sh.replace('fx_', '') : pr.kind);
    if (s && s.ok) {
      const t = s.tag(Object.keys(s.tags)[0]), n = t.to - t.from + 1;
      if (pr.kind === 'arrow' || pr.kind === 'lance' || pr.kind === 'sovlance' || pr.kind === 'shard') drawRotated(s, t.from + Math.floor(pr.t * 10) % n, pr.x, pr.y, Math.atan2(pr.vy, pr.vx));
      else drawSprite(s, t.from + Math.floor(pr.t * 14) % n, pr.x, pr.y, sign(pr.vx), { center: true });
    } else { g.fillStyle = pr.owner === 'player' ? '#ffd77a' : '#ff7040'; g.fillRect(Math.round(pr.x) - 2, Math.round(pr.y) - 2, 4, 4); }
  }
}

// ---- hazards (ground waves, root spikes, delayed pillars)
function updateHazards(dt) {
  for (const h of hazards) {
    if (h.delay > 0) { h.delay -= dt; if (h.delay <= 0 && h.onStart) h.onStart(h); continue; }
    h.life -= dt; h.t = (h.t || 0) + dt;
    if (h.update) h.update(h, dt);
    else {
      h.x += (h.vx || 0) * dt;
      if (h.wave && Math.random() < 0.6) particles.push({ x: h.x + rand(-4, 4), y: h.y - rand(0, 6), vx: 0, vy: -rand(20, 60), life: 0.5, kind: h.color || 'gold' });
      if (h.wave && (solidAtPx(h.x + sign(h.vx) * 6, h.y - 4) || !solidAtPx(h.x, h.y + 2))) h.life = 0;
    }
    if (h.active === undefined || h.active(h)) {
      const r = rect(h.x - h.w / 2, h.y - h.h, h.x + h.w / 2, h.y);
      if (overlap(r, playerHurtbox())) hurtPlayer(h.dmg, h.dir || (P.x < h.x ? -1 : 1), h.tick ? h.id + '_' + Math.floor(h.t / h.tick) : h.id, { rot: h.rot });
      if (h.pool && Math.random() < 0.3) particles.push({ x: h.x + rand(-h.w / 2, h.w / 2), y: h.y - 2, vx: 0, vy: -rand(5, 18), life: 0.6, kind: 'spore' });
    }
  }
  hazards = hazards.filter(h => h.life > 0);
}
let hazardId = 1e6;

// ---- props: shrine, urn, lantern, chest, item, lever, gate, fog, remnant
function makeProp(type, x, y, extra = {}) {
  const shName = { shrine: 'prop_shrine', urn: 'prop_urn', lantern: 'prop_lantern', chest: 'prop_chest', item: 'prop_item', lever: 'prop_lever',
                   gate: 'prop_gate', fog: 'prop_fog', remnant: 'prop_remnant', anvil: 'prop_anvil', bell: 'prop_bell', throne: 'prop_throne', grave: 'prop_grave',
                   lectern: 'prop_lectern', candelabra: 'prop_candelabra', shelfcage: 'prop_shelfcage' }[type];
  const sh = sheet(shName);
  const p = { type, x, y, face: 1, sh, ...extra };
  const firstTag = { shrine: extra.lit ? 'lit' : 'unlit', urn: 'idle', lantern: 'loop', chest: extra.open ? 'open' : 'closed', item: 'loop', lever: extra.on ? 'on' : 'off',
                     gate: extra.open ? 'open' : 'closed', fog: 'loop', remnant: 'loop', anvil: 'loop', bell: 'idle', throne: 'idle', grave: 'idle', lectern: 'loop', candelabra: 'loop', shelfcage: 'idle' }[type];
  p.anim = new Anim(sh, firstTag || Object.keys(sh.tags)[0], ['lit', 'loop'].includes(firstTag));
  if (extra.open && type === 'chest') p.anim.i = p.anim.n - 1;
  return p;
}
function propHurtbox(p) {
  if (p.hurtbox) return p.hurtbox();   // custom props (region files): hurtbox() + onHit(info)
  if (p.type === 'urn' && !p.broken) return rect(p.x - 6, p.y - 20, p.x + 6, p.y);
  if (p.type === 'lever' && !p.on) return rect(p.x - 7, p.y - 22, p.x + 7, p.y);
  if (p.type === 'chest' && !p.open) return rect(p.x - 12, p.y - 18, p.x + 12, p.y);
  return null;
}
function propTarget(p) {
  return { x: p.x, y: p.y, prop: p, hurtbox: () => propHurtbox(p), hit: info => hitProp(p, info) };
}
function hitProp(p, info) {
  if (p.onHit) return p.onHit(info);
  if (p.type === 'urn' && !p.broken) {
    p.broken = true; p.anim.set('break', false); sfx.urn();
    for (let i = 0; i < 8; i++) particles.push({ x: p.x, y: p.y - 10, vx: rand(-70, 70), vy: -rand(40, 120), g: 420, life: 0.8, kind: 'rock' });
    if (Math.random() < 0.7) gainCinders(irand(4, 14), p.x, p.y - 10);
  } else if (p.type === 'lever' && !p.on) pullLever(p);
  else if (p.type === 'chest' && !p.open) openChest(p);
}
function pullLever(p) {
  p.on = true; p.anim.set('pull', false); SAVE.flags[p.key] = 1; sfx.gate(); shake = 4;
  for (const q of props) if (q.type === 'gate' && !q.open) { q.open = true; q.anim.set('opening', false); SAVE.flags[q.key] = 1; }
  toast('Somewhere, a gate grinds open'); saveGame();
}
function openChest(p) {
  p.open = true; p.anim.set('open', false); SAVE.flags[p.key] = 1; sfx.gate();
  setTimeout(() => grantItem(p.item, p.x, p.y - 20), 350);
}
function grantItem(id, x, y) {
  const it = ITEMS[id]; if (!it) return;
  sfx.pickup();
  if (id === 'shard') SAVE.shards++;
  else if (id === 'seed' || id === 'rotseed') { SAVE.flaskBase++; if (P) P.flasksR++; }
  else if (id === 'gold') gainCinders(600, x, y);
  else if (id === 'herb') SAVE.flaskPot++;
  else if (id === 'slot') SAVE.spellSlots++;
  else if (id === 'charmslot') SAVE.charmSlots++;
  else if (id === 'emberstone' || id === 'tear') SAVE.inv[id] = (SAVE.inv[id] || 0) + 1;
  else if (it.weapon) { if (SAVE.weapons[it.weapon] === undefined) SAVE.weapons[it.weapon] = 0; const art = WEAPONS[it.weapon].art; if (!SAVE.arts.includes(art)) SAVE.arts.push(art); }
  else if (it.art) { if (!SAVE.arts.includes(it.art)) SAVE.arts.push(it.art); }
  else if (it.spell) { if (!SAVE.spellsOwned.includes(it.spell)) SAVE.spellsOwned.push(it.spell); autoEquipSpell(it.spell); }
  else if (it.charm) { if (!SAVE.charms.includes(id)) SAVE.charms.push(id); if (SAVE.charmsEq.length < SAVE.charmSlots) { SAVE.charmsEq.push(id); refreshDerived(); } }
  else SAVE.items[id] = 1;
  if (x !== undefined) for (let i = 0; i < 16; i++) particles.push({ x, y, vx: rand(-60, 60), vy: -rand(20, 100), g: 60, life: rand(0.6, 1.2), kind: 'gold' });
  const hint = it.weapon ? ' Equip it from the menu (Esc).' : it.charm ? ' Charms are worn from the menu (Esc).' : it.spell ? ' Equip spells from the menu (Esc).' : '';
  banner(it.name, it.desc + hint, it.icon);
  saveGame();
}
function autoEquipSpell(id) { if (!SAVE.spellsEq.includes(id) && SAVE.spellsEq.length < SAVE.spellSlots) SAVE.spellsEq.push(id); if (!SAVE.spell) SAVE.spell = id; }
function makeNpc(id, x, y) {
  const sh = sheet(NPC_INFO[id].sheet);
  return { type: 'npc', id, x, y, face: -1, sh, anim: new Anim(sh, 'idle', true) };
}
function interactNearby() {
  for (const p of props) {
    if (Math.abs(p.x - P.x) > (p.type === 'shrine' || p.type === 'npc' ? 22 : 16) || Math.abs(p.y - P.y) > 24) continue;
    if (p.interact) { p.interact(); return true; }   // custom props
    if (p.type === 'npc') { startDialogue(npcScript(p.id), p); return true; }
    if (p.type === 'grave') { readGrave(p.lore); return true; }
    if (p.type === 'bell') { ringBell(p); return true; }
    if (p.type === 'shrine') { useShrine(p); return true; }
    if (p.type === 'chest' && !p.open) { openChest(p); return true; }
    if (p.type === 'lever' && !p.on) { pullLever(p); return true; }
  }
  return false;
}
function nearbyPrompt() {
  if (!free() || !P.ground) return null;
  for (const p of props) {
    if (Math.abs(p.x - P.x) > (p.type === 'shrine' || p.type === 'npc' ? 22 : 16) || Math.abs(p.y - P.y) > 24) continue;
    if (p.prompt) { const t = p.prompt(); if (t) return t; continue; }
    if (p.type === 'npc') return 'Talk';
    if (p.type === 'grave') return 'Read';
    if (p.type === 'bell' && !SAVE.flags['bell:rung']) return 'Ring';
    if (p.type === 'shrine') return p.lit ? 'Rest' : 'Kindle the shrine';
    if (p.type === 'chest' && !p.open) return 'Open';
    if (p.type === 'lever' && !p.on) return 'Pull';
  }
  return null;
}
function updateProps(dt) {
  for (const p of props) {
    p.anim.update(dt);
    if (p.update) { p.update(dt); continue; }
    if (p.type === 'shrine') {
      if (p.anim.tag === 'kindle' && p.anim.done) p.anim.set('lit', true);
      if (p.lit) { addLight(p.x, p.y - 30, 90, '255,200,110', 1); if (Math.random() < 0.3) particles.push({ x: p.x + rand(-6, 6), y: p.y - 34, vx: rand(-4, 4), vy: -rand(10, 30), life: rand(0.6, 1.4), kind: 'gold' }); }
      else addLight(p.x, p.y - 20, 30, '255,190,110', 0.4);
    }
    if (p.type === 'lantern') addLight(p.x, p.y + 20, 70 + Math.sin(time * 9 + p.x) * 3, '255,180,100', 0.9);
    if (p.type === 'candle') addLight(p.x, p.y - 6, 36 + Math.sin(time * 11 + p.x) * 2, '255,190,110', 0.7);
    if (p.type === 'item') {
      addLight(p.x, p.y - 8, 40, '255,220,140', 0.9);
      if (Math.random() < 0.2) particles.push({ x: p.x + rand(-4, 4), y: p.y - 8, vx: 0, vy: -rand(10, 25), life: 0.8, kind: 'gold' });
      if (Math.abs(P.x - p.x) < 12 && Math.abs(P.y - p.y) < 20) { p.taken = true; SAVE.flags[p.key] = 1; grantItem(p.item, p.x, p.y - 8); }
    }
    if (p.type === 'remnant') {
      addLight(p.x, p.y - 12, 50, '255,120,80', 0.9);
      if (Math.random() < 0.3) particles.push({ x: p.x + rand(-5, 5), y: p.y - rand(4, 20), vx: 0, vy: -rand(8, 20), life: 0.8, kind: 'ember' });
      if (Math.abs(P.x - p.x) < 14 && Math.abs(P.y - p.y) < 24 && P.state !== 'dead') {
        p.taken = true; SAVE.cinders += SAVE.remnant.amount; cinderGain += SAVE.remnant.amount; cinderFlash = 1.5;
        toast(`Recovered ${SAVE.remnant.amount} cinders`); SAVE.remnant = null; sfx.pickup(); saveGame();
        for (let i = 0; i < 20; i++) particles.push({ x: p.x, y: p.y - 10, vx: rand(-80, 80), vy: -rand(20, 120), life: 1.4, kind: 'cinder', home: 0.2 });
      }
    }
    if (p.type === 'fog') { if (p.on()) addLight(p.x, p.y - 40, 50, '255,210,130', 0.6); }
    if (p.type === 'anvil') { addLight(p.x, p.y - 10, 50, '255,150,70', 0.9); if (Math.random() < 0.15) particles.push({ x: p.x + rand(-6, 6), y: p.y - 14, vx: rand(-40, 40), vy: -rand(30, 80), g: 300, life: 0.5, kind: 'fire' }); }
    if (p.type === 'npc' && p.id === 'ashwright') { addLight(p.x + 8, p.y - 8, 56, '255,150,70', 0.9); if (Math.random() < 0.08) particles.push({ x: p.x + 10 + rand(-4, 4), y: p.y - 12, vx: rand(-40, 40), vy: -rand(30, 80), g: 300, life: 0.5, kind: 'fire' }); }
    if (p.type === 'npc' && p.id === 'venn') addLight(p.x + 6, p.y - 16, 40, '255,200,120', 0.7);
    if (p.type === 'lectern') addLight(p.x, p.y - 20, 46, '200,170,255', 0.8);
    if (p.type === 'candelabra') addLight(p.x, p.y - 26, 64, '255,190,110', 0.9);
    if (p.type === 'throne') addLight(p.x, p.y - 40, 80, '255,240,210', 0.8);
  }
  props = props.filter(p => !p.taken);
}
function drawProp(p) {
  if (p.draw) return p.draw();
  if (p.type === 'fog' && !p.on()) return;
  if (p.type === 'candle') return;
  if (p.type === 'gate' && p.open && p.anim.done) { drawSprite(p.sh, p.sh.first('open'), p.x, p.y, 1, { bottom: true }); return; }
  if (!p.sh.ok) { g.fillStyle = '#c9a050'; g.fillRect(Math.round(p.x) - 4, Math.round(p.y) - 12, 8, 12); return; }
  if (p.type === 'npc') { drawSprite(p.sh, p.anim.frame, p.x, p.y, p.face, { bottom: true }); return; }
  if (p.type === 'veil' || p.type === 'updraft') { drawTallProp(p); return; }
  if (p.type === 'hookpoint') { if (p.sh.ok) drawSprite(p.sh, p.anim.frame, p.x, p.y, 1, { bottom: true }); else { g.fillStyle = '#ffd77a'; g.fillRect(Math.round(p.x) - 3, Math.round(p.y) - 11, 6, 6); } addLight(p.x, p.y - 8, 26, '255,210,120', SAVE.items.hook ? 0.9 : 0.4); return; }
  const bob = p.type === 'item' ? Math.round(Math.sin(time * 3) * 2) : 0;
  drawSprite(p.sh, p.anim.frame, p.x, p.y + bob, p.face, { bottom: true, alpha: p.type === 'fog' ? 0.85 : 1, pivot: p.type === 'lantern' || p.type === 'shelfcage' ? [Math.floor(p.sh.fw / 2), 0] : undefined });
  if (p.type === 'shrine' && !p.lit && !p.sh.ok) return;
}

function ringBell(p) {
  if (SAVE.flags['bell:rung']) { toast('The bell hums softly.'); return; }
  if (!SAVE.items.bell) { toast('A great bell, silent. Its tongue is missing — something small and golden would fit.', 3.5); sfx.deny(); return; }
  SAVE.flags['bell:rung'] = 1; p.anim.set(p.sh.has('ring') ? 'ring' : 'idle', false);
  [196, 247, 294].forEach((f, i) => tone(f, 3.5, 0.18, 'sine', 1, i * 0.05)); tone(98, 4, 0.2, 'triangle');
  shake = 6; flashScreen = 0.4;
  for (const q of props) if (q.type === 'gate' && !q.open) { q.open = true; q.anim.set('opening', false); }
  toast('The Ashen Bell tolls. The way to the Crown opens.', 4); saveGame();
}
