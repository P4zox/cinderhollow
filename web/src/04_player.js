// ------------------------------------------------------------------ player
// Weapon revamp (agent WM): every melee move lives in ATK, keyed by the player state that plays it. The move tables
// themselves (9 types, docs/WEAPON_REVAMP.md Part A) are registered by 75_moves.js (engine) and 76_mech_*.js (types):
// each ATK entry carries its table row in A.mv. The fields every other system reads (active / reach / ys / mult / poise /
// cost / kind / cls / up / air / down / spin / big / counter) are kept, so parry, feel, skills and the Training Grounds
// keep working. The Longsword keeps the v3 state ids (attack1-4, heavy, attack_up, air_attack, attack_down).
const ATK = {};
// weapon id -> type id (the 9 weapons). WS's 74_arsenal9.js may add to it (Object.assign) -- never redeclare it.
const WEAPON_CLASS = { longsword: 'longsword', katana: 'katana', greatsword: 'greatsword', maul: 'maul', knight_shield: 'sns',
  twinfangs: 'dual', spear: 'spear', quarterstaff: 'staff', headsman_chain: 'whip' };
// retired weapons still in an old save / in data that hasn't been trimmed yet: their old class -> the new type
{ const OLD = { sword: 'longsword oathbrand kalden omen frostbrand sanguine_rapier pharaoh_khopesh first_ember', dagger: 'dagger pagecutter barnacle_fang carving_knife',
    great: 'gravetusk rotmaw forge_cleaver tidecleaver vael_greatsword', maul: 'colossus_hammer glacier_maul bell_hammer meteor_maul', spear: 'scepter stormfang choir_harpoon scarab_spear saint_lance',
    katana: 'stormvein starblade plasma_katana', staff: 'windstaff inkquill lantern_staff thornwood_staff sun_sceptre', shield: 'twinborne overseer_bulwark',
    twin: '', scythe: 'antler_scythe briar_scythe crimson_scythe last_kindling', whip: 'gravechain orrery_whip' };
  const TO = { sword: 'longsword', dagger: 'dual', great: 'greatsword', maul: 'maul', spear: 'spear', katana: 'katana', staff: 'staff', shield: 'sns', twin: 'dual', scythe: 'greatsword', whip: 'whip' };
  for (const [c, ids] of Object.entries(OLD)) for (const id of ids.split(' ').filter(Boolean)) if (!WEAPON_CLASS[id]) WEAPON_CLASS[id] = TO[c]; }
// MOVESETS[type] = { combo, extra, heavy, up, air, down } (rank-I light chain + its K / aerials) for older readers
// (24_secrets' arsenal, 57_skills' combo length). Filled by 75_moves.js from the move tables.
const MOVESETS = {};
const SWORD_AER = { up: 'attack_up', air: 'air_attack', down: 'attack_down' };
// the plunge impact box (used by the plunge logic, not a state of its own); dmg / poise / stamina come from the type's table
const PLUNGE_A = { active: [0, 0], mult: 1.5, poise: 70, reach: [-26, 40], ys: [-30, 0], cost: 18, fx: null, fxAt: [22, -6], lunge: 0, speed: 1, kind: 'heavy', cls: 'tech', big: true, plunge: true };
{ const pl = (typeof ASSETS !== 'undefined' && ASSETS.player_meta && ASSETS.player_meta.moves && ASSETS.player_meta.moves.plunge_land) || {};
  if (pl.hit) { PLUNGE_A.reach = [pl.hit[0], pl.hit[2]]; PLUNGE_A.ys = [pl.hit[1], pl.hit[3]]; } }
// the equipped weapon's type id (WS's 74_arsenal9.js may redefine this; its declaration then wins)
function wcls() { return WEAPON_CLASS[SAVE.weapon] || 'longsword'; }
function moveset() { return MOVESETS[typeof mvType === 'function' ? mvType() : wcls()] || MOVESETS.longsword || { combo: ['attack1'], heavy: 'heavy', extra: 'attack1', up: 'attack_up', air: 'air_attack', down: 'attack_down' }; }
// the type's up / air / down attack (d)
function aerTag(d) { const t = moveset()[d]; return t && ATK[t] ? t : SWORD_AER[d]; }
const MAXV = 122, JUMP_V = 272, GRAV_UP = 640, GRAV_DN = 860, FALL_MAX = 430;
let P = null, D = null;

function newPlayer(x, y) {
  D = derive(SAVE.stats, skillSet());
  P = { assist: true, x, y, w: 10, h: 26, vx: 0, vy: 0, ground: true, face: 1, state: 'idle', anim: new Anim(sheet('player'), 'idle'),
        hp: D.maxHp, fp: D.maxFp, st: D.maxSt, stDelay: 0, inv: 0, flash: 0, combo: 0, hitSet: new Set(), charge: 0, charged: false,
        coyote: 0, airJumps: 0, airDash: true, wallDir: 0, ctrlLock: 0, ghostT: 0, deadT: 0, healPending: 0, displayHp: D.maxHp,
        empower: 0, sw: false, drop: 0, rot: 0, rotT: 0, cryT: 0, fireT: 0, regenT: 0, artI: false, artId: null, safe: { x, y }, safeT: 0, parryWin: 0, crit: null, spellFired: false, pogoed: false, stepT: 0,
        gcT: 0, bsT: 0, backRoll: 0, twinBuff: false, sigCharge: 0, artCharged: false, artHold: false, artChargeT: 0, artCount: 0, cryBig: false };
  refillFlasks();
}
function skillSet() { return new Set(SAVE.skills); }
const has = id => SAVE.skills.includes(id);
function refreshDerived(keepRatio = true) {
  const old = D; D = derive(SAVE.stats, skillSet());
  if (P && old && keepRatio) { P.hp = Math.min(D.maxHp, P.hp + Math.max(0, D.maxHp - old.maxHp)); P.fp = Math.min(D.maxFp, P.fp + Math.max(0, D.maxFp - old.maxFp)); }
}
function flaskMax() { return SAVE.flaskBase + (has('iron_flask') ? 1 : 0); }
function refillFlasks() {
  const n = flaskMax(); SAVE.flaskBlue = clamp(SAVE.flaskBlue, 0, n);
  P.flasksR = n - SAVE.flaskBlue; P.flasksB = SAVE.flaskBlue;
}
const SH_ARMED = new Set(['guard', 'block', 'parry', 'gbreak', 'counter', 'sh_counter', 'backstep', 'art']);
function setP(st, tag, loop = false, speed = 1) {
  // sword & shield: after fighting, the shield swings back onto the back (sh_rest) instead of snapping there
  if (st === 'idle' && tag === 'idle' && P.shArmed && pHas('sh_rest') && wcls() === 'sns') { P.shArmed = false; P.state = 'idle'; P.anim.set('sh_rest', false, 1); return; }
  P.shArmed = (SH_ARMED.has(st) || (ATK[st] && ATK[st].cls === 'sns')) ? true : (st === 'idle' ? P.shArmed : false);
  P.state = st; P.anim.set(tag, loop, speed);
}
function spend(n) { P.st -= n; P.stDelay = 0.6; }
function free() { return ['idle', 'run', 'air', 'land', 'wall', 'glide'].includes(P.state); }
function inputX() { return P.ctrlLock > 0 ? 0 : (held.has('right') ? 1 : 0) - (held.has('left') ? 1 : 0); }
const pSheet = () => sheet('player');
function pHas(tag) { return pSheet().has(tag); }
function playerHurtbox() { return rect(P.x - 5, P.y - 25, P.x + 5, P.y); }
function iframes() {
  if (P.state === 'riposte' || P.state === 'rest' || P.state === 'rise' || (P.state === 'art' && P.artI)) return true;
  if (typeof mvIframes === 'function' && mvIframes()) return true;   // 75/76: dodges, vault, flash step, focus draw ...
  return false;
}
// start any move of the tables by its state id (75_moves.js does the work; kept for older callers, e.g. 31_barrows)
function startAttack(name, o) { return mvStart(name, o || {}); }
// the staff's 360-degree spin: 30% of max stamina (57_skills wraps this)
function staffSpinCost() { return D.maxSt * 0.30 * (charmOn('c_brand') ? 0.8 : 1); }
function startHeavy() { return typeof mvNeutralK === 'function' ? mvNeutralK(inputX()) : false; }
// the type's counter after a clean parry / block (75: T.counter)
function startCounter() { return typeof mvCounter === 'function' ? mvCounter() : false; }
function tryRiposte() {
  const t = critTarget();
  if (!t) return false;
  P.face = t.x > P.x ? 1 : -1; P.crit = t; P.hitSet = new Set();
  setP('riposte', pHas('riposte') ? 'riposte' : 'attack3', false, 1);
  t.onCritStart && t.onCritStart();
  return true;
}
function spellKnown(id) { return has(id) || SAVE.spellsOwned.includes(id); }
function spellCost(id) { return Math.round(SPELLS[id].fp * (has('azure_thrift') ? 0.7 : 1) * (charmOn('c_scholar') ? 0.9 : 1)); }
function startCast() {
  const id = SAVE.spell;
  if (!id || !spellKnown(id) || !SAVE.spellsEq.includes(id)) { toast(SAVE.spellsEq.length ? 'Press Q to pick a spell' : 'No spell equipped — open the menu (Esc) › Equipment'); return; }
  const cost = spellCost(id);
  if (cdLeft('spell', id) > 0) { cdDeny('spell'); return; }
  if (P.fp < cost) { sfx.deny(); toast('Not enough FP'); return; }
  cdStart('spell', id);
  P.fp -= cost; P.spellFired = false; P.castId = id;
  setP('cast', pHas('cast') ? 'cast' : 'heal', false, D.castSpeed * (id === 'emberburst' ? 0.9 : 1.1));
  sfx.charge();
}

function updatePlayer(dt) {
  const ax = inputX();
  smashTick(dt); airTick(dt);
  P.inv = Math.max(0, P.inv - dt); P.flash = Math.max(0, P.flash - dt * 6); P.ctrlLock -= dt; P.drop -= dt; P.empower -= dt; P.parryWin -= dt;
  if (P.state === 'dead') {
    P.anim.update(dt); P.vx *= Math.pow(0.01, dt); P.vy = Math.min(P.vy + GRAV_DN * dt, FALL_MAX); moveBody(P, dt);
    if (P.deadT > 0 && (P.deadT -= dt) <= 0) onPlayerDeath();
    return;
  }
  if (P.state === 'rest') { P.anim.update(dt); if (P.anim.done) P.anim.hold(); P.vx = 0; return; }
  mvTick(dt);   // 75/76: per-type timers (demon drain, perfect-dodge buff, momentum, sheathe, crack ...)
  P.coyote = P.ground ? 0.12 : P.coyote - dt;
  if (P.ground) { P.airJumps = SAVE.items.wings ? 1 : 0; P.airDash = true; }
  if (peek('interact') && free() && P.ground) { if (interactNearby()) take('interact'); }

  // ---- action starts (buffered inputs)
  const canStart = free() || (P.state === 'land' && P.anim.i >= 1);
  // airborne attacks: two per jump, then land and wait AIR_CD (swimming is exempt — see airAtkGate)
  const airIn = airAtkGate(canStart);
  if (canStart && traversalStart(ax)) { /* technique started */ }
  else if (canStart) {
    if (peek('roll') && P.st > 0 && (P.ground || P.coyote > 0 || P.airDash)) { take('roll'); mvDodgeStart(ax); }
    else if (peek('jump')) {
      if (P.ground && held.has('down') && onPlatform()) { take('jump'); P.drop = 0.25; P.y += 2; P.ground = false; setP('air', 'jump_fall'); }
      else if (P.ground || P.coyote > 0) { take('jump'); doJump(JUMP_V); }
      else if (P.state === 'wall') { take('jump'); wallJump(); }
      else if (P.airJumps > 0) { take('jump'); P.airJumps--; doJump(JUMP_V * 0.9, true); }
    }
    else if (peek('attack') && P.ground && tryRiposte()) take('attack');
    else if (mvNeutral(ax)) { /* a move from the type's table (75_moves.js) */ }
    else if (peek('art')) { take('art'); startArt(); }
    else if (peek('cast')) { take('cast'); startCast(); }
    else if (peek('heal') && P.ground) { take('heal'); if (P.flasksR > 0) { P.flasksR--; setP('heal', 'heal', false, mvHealSpeed()); P.healPending = 1; } else { sfx.deny(); toast('Your crimson flasks are empty'); } }
    else if (peek('mana') && P.ground) { take('mana'); if (P.flasksB > 0) { P.flasksB--; setP('heal', 'heal', false, mvHealSpeed()); P.healPending = 2; } else { sfx.deny(); toast('Your azure flasks are empty'); } }
  }
  if (airIn && !free() && P.mvAirFrame !== P.clk && ((airIn.a && !peek('attack')) || (airIn.h && !peek('heavy')) || (airIn.o && !peek('art')))) airAtkStart();

  // apex hang: holding jump near the top of an arc softens gravity for a smoother, floatier peak
  const grav = () => { const apex = !P.ground && P.state === 'air' && Math.abs(P.vy) < 55 && held.has('jump'); P.vy = Math.min(P.vy + (P.vy > 0 ? GRAV_DN : GRAV_UP) * (apex ? 0.55 : 1) * dt, FALL_MAX); };
  const tv = traversalUpdate(dt);
  if (tv === 'skip-physics') { P.anim.update(dt); P.stDelay -= dt; if (P.stDelay <= 0) P.st = Math.min(D.maxSt, P.st + 40 * dt); return; }
  if (!tv) switch (ATK[P.state] ? 'ATTACK' : P.state) {
    case 'idle': case 'run': case 'land': {
      const target = ax * MAXV * mvWalkMul();
      const acc = (ax ? (Math.sign(target) !== Math.sign(P.vx) && P.vx ? 2200 : 1150) : 1600) * (P.fric ?? 1);   // fric < 1 on ice
      P.vx = approach(P.vx, target, acc * dt);
      if (ax) P.face = ax;
      grav();
      if (P.state === 'land') { if (P.anim.done || ax) { const m = Math.abs(P.vx) > 5 || ax ? 'run' : 'idle'; setP(m, m, true); } }
      else {
        const want = (ax || Math.abs(P.vx) > 20) ? 'run' : 'idle', wt = mvIdleTag(want);   // 76: e.g. the katana's sheathed idle / walk
        if (P.state !== want) setP(want, wt, true);
        else if (P.anim.tag === 'sh_rest' && P.anim.done) P.anim.set(wt, true);
        else if (P.anim.tag !== wt && P.anim.tag !== 'sh_rest') P.anim.set(wt, true);
        if (want === 'run') { P.anim.speed = clamp(Math.abs(P.vx) / MAXV, 0.45, 1.15); if (P.anim.changed && P.anim.i % 4 === 1) sfx.step(); }
      }
      if (!P.ground && P.coyote <= 0) setP('air', 'jump_fall', false);
      break;
    }
    case 'air': {
      if (P.ctrlLock <= 0) P.vx = approach(P.vx, ax * MAXV, (ax && Math.sign(ax) !== Math.sign(P.vx) ? 1400 : 950) * dt);
      if (ax) P.face = ax;
      if (!held.has('jump') && P.vy < -90 && P.ctrlLock <= 0) P.vy = lerp(P.vy, -90, Math.min(1, dt * 22));   // variable jump height, eased
      grav();
      const want = P.dj ? 'double_jump' : P.vy < 0 ? 'jump_up' : 'jump_fall';
      if (P.dj && P.anim.done) P.dj = false;
      if (P.anim.tag !== want && pHas(want)) P.anim.set(want, false);
      // wall cling
      if (SAVE.items.talon && P.vy > 0 && ax && wallAt(P, ax)) { P.wallDir = ax; P.face = ax; setP('wall', pHas('wall_slide') ? 'wall_slide' : 'jump_fall', true); }
      break;
    }
    case 'wall': {
      P.vy = Math.min(P.vy + 600 * dt, has('way_wall') ? 32 : 55); P.vx = P.wallDir * 10;   // 57: Talon Grip
      if (Math.random() < 0.25) spawnFx('wall_dust', P.x + P.wallDir * 6, P.y - 8, P.face);
      if (!wallAt(P, P.wallDir) || (ax && ax !== P.wallDir) || P.ground) { P.wallDir = 0; setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); }
      break;
    }
    case 'roll': mvRollUpdate(dt, ax, grav); break;
    case 'ATTACK': mvUpdate(dt, ax, grav); break;
    case 'riposte': {
      P.vx = P.anim.i >= 2 && P.anim.i <= 3 ? P.face * 60 : P.vx * 0.8; grav();
      if (P.anim.changed && P.anim.i === 3 && P.crit) critHit(P.crit);
      if (P.anim.done) { P.crit = null; setP('idle', 'idle', true); }
      break;
    }
    case 'parry':
      P.vx = approach(P.vx, 0, 900 * dt); grav();
      if ((P.parried || P.gcT > 0) && peek('attack', 400) && P.st > 0) { take('attack', 400); if (!tryRiposte()) startCounter(); break; }   // a block inside the shield parry counts too
      if (mvParryUpdate(dt, ax)) break;   // 76: the Longsword's foresight stance (I -> K)
      if (P.shieldParry && held.has('parry') && P.anim.i >= 2) { setP('guard', 'sh_guard', true); break; }
      if (P.anim.done) setP('idle', 'idle', true);
      break;
    case 'guard': case 'block': if (!mvGuardUpdate(dt, ax, grav)) updateGuard(dt, ax, grav); break;
    case 'gbreak':
      P.vx *= Math.pow(0.02, dt); grav();
      if (P.anim.done) setP('idle', 'idle', true);
      break;
    case 'plunge': updatePlunge(dt, ax, grav); break;
    case 'spdive': updateSpDive(dt, ax, grav); break;
    case 'cast': {
      P.vx = approach(P.vx, 0, 900 * dt); grav();
      if (!P.spellFired && P.anim.i >= (pHas('cast') ? 4 : 3)) { P.spellFired = true; castSpell(P.castId); }
      if (P.anim.i >= 2 && P.anim.i <= 5) addLight(P.x + P.face * 12, P.y - 18, 40, '255,210,120', 0.9);
      if (P.anim.done) setP('idle', 'idle', true);
      break;
    }
    case 'heal':
      P.vx = approach(P.vx, mvHealWalk() * inputX() * MAXV, 900 * dt); grav();   // 76: the sword & shield drinks on the move
      if (P.anim.i === 3 && P.healPending) {
        if (P.healPending === 1) { P.hp = Math.min(D.maxHp, P.hp + Math.round((D.maxHp * 0.42 + 20) * flaskMul())); sfx.heal(); spawnFx('heal', P.x, P.y, P.face, P); }
        else { P.fp = Math.min(D.maxFp, P.fp + Math.round((D.maxFp * 0.55 + 10) * flaskMul())); sfx.mana(); spawnFx('heal', P.x, P.y, P.face, P, { tint: '#6aa8ff' }); }
        P.healPending = 0; P.rotT = 0; P.rot = 0;
      }
      if (P.anim.done) setP('idle', 'idle', true);
      break;
    case 'hurt':
      P.vx *= Math.pow(0.03, dt); grav();
      if (P.anim.done) setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground);
      break;
    case 'rise':
      P.vx = 0; grav();
      if (P.anim.done) setP('idle', 'idle', true);
      break;
    case 'art': updateArt(dt, grav); break;
    default: if (MV_STATES[P.state]) MV_STATES[P.state](dt, ax, grav);   // 76: type states (sheathe, brace, vault, grapple ...)
  }

  // ---- physics
  const wasAir = !P.ground, fallV = P.vy, preState = P.state;
  { const pv = P.pushVx || 0; P.vx += pv; moveBody(P, dt); if (P.vx) P.vx -= pv; P.pushVx = 0; }   // pushVx: wind/conveyors (set by hooks each frame)
  if (P.ground && wasAir) {
    spawnFx('dust', P.x, P.y, P.face); if (fallV > 150) sfx.land();
    P.dj = false;
    if (preState === 'slam') traversalAfterMove('slam');
    else if (P.state === 'air' || P.state === 'wall' || P.state === 'glide') setP('land', pHas('land') ? 'land' : 'idle', false);
    if (ATK[P.state] && (ATK[P.state].air || ATK[P.state].down)) { P.combo = 0; setP('land', 'land', false); }
    if (preState === 'plunge' && P.state === 'plunge' && P.anim.tag !== 'plunge_land') plungeImpact(false);
    if (preState === 'spdive' && P.state === 'spdive') { setP('land', 'land', false); shake = Math.max(shake, 3); sfx.land(); spawnFx('dust', P.x + P.face * 10, P.y, P.face); }
    mvLanded(preState);
  }
  traversalAfterMove(null);
  if (spikeHit(P)) spikeHurt();
  // remember safe ground for spike respawns
  P.safeT -= dt;
  if (P.ground && P.safeT <= 0 && !nearSpikes()) { P.safe = { x: P.x, y: P.y }; P.safeT = 0.25; if (P.entryRoom !== room) { P.entryRoom = room; P.entry = { x: P.x, y: P.y }; } }

  P.stDelay -= dt;
  if (P.stDelay <= 0 && P.state !== 'roll' && !ATK[P.state])
    P.st = Math.min(D.maxSt, P.st + (P.state === 'idle' ? 70 : 58) * dt * (P.state === 'guard' || P.state === 'block' ? 0.35 : 1) * mvRegenMul());   // 76: Demon Mode stops it
  P.gcT -= dt; P.denyT = (P.denyT || 0) - dt;
  if (P.state !== 'art') P.artCharged = false;
  // statuses: buffs, regen, rot
  P.cryT -= dt; P.fireT -= dt;
  if (P.regenT > 0) { P.regenT -= dt; P.hp = Math.min(D.maxHp, P.hp + D.maxHp * 0.35 / 4 * dt); if (Math.random() < 0.3) particles.push({ x: P.x + rand(-6, 6), y: P.y - rand(0, 24), vx: 0, vy: -rand(10, 30), life: 0.6, kind: 'gold' }); }
  if (inWater(P)) { addRot(26 * dt); if (Math.random() < 0.15) particles.push({ x: P.x + rand(-5, 5), y: P.y - 4, vx: 0, vy: -rand(8, 20), life: 0.5, kind: 'spore' }); }
  P.rot = Math.max(0, P.rot - 7 * dt);
  if (P.rotT > 0) { P.rotT -= dt; P.hp = Math.max(1, P.hp - D.maxHp * 0.018 * dt); if (Math.random() < 0.3) particles.push({ x: P.x + rand(-6, 6), y: P.y - rand(4, 24), vx: 0, vy: -rand(5, 15), life: 0.5, kind: 'spore' }); }
  if (P.fireT > 0 && Math.random() < 0.5) particles.push({ x: P.x + P.face * rand(6, 18), y: P.y - rand(10, 26), vx: 0, vy: -rand(20, 50), life: 0.4, kind: 'fire' });
  P.anim.update(dt);
  P.displayHp += (P.hp - P.displayHp) * Math.min(1, dt * (P.hp < P.displayHp ? 2.2 : 8));
}
function flaskMul() { return (1 + 0.1 * SAVE.flaskPot) * (charmOn('c_grace') ? 1.25 : 1); }
function addRot(n) {
  if (P.rotT > 0 || P.state === 'dead') return;
  P.rot += n;
  if (P.rot >= 100) { P.rot = 0; P.rotT = 9; sfx.bleed(); toast('Rotting — rest or drink a flask', 2); spawnFx(fxOr('rot_hit', 'blood'), P.x, P.y - 14, P.face); }
}
function inWater(b) { const t = tileAt(Math.floor(b.x / TILE), Math.floor((b.y - 4) / TILE)); return t === T_WATER; }
function chargeTime() { return has('charged_arts') ? 0.35 : 0.55; }
function onPlatform() {   // one-way tiles, plus one-way dynamic platforms (e.g. the Unwritten's ink platforms)
  return tileAt(Math.floor(P.x / TILE), Math.floor((P.y + 1) / TILE)) === T_PLAT ||
    room.dyn.some(d => d.oneway && d.on() && P.x >= d.x0 && P.x < d.x1 && Math.abs(P.y - d.y0) < 1.5);
}
// hazards that aren't spike tiles (region voids, ink pools, mist drops) register a test here, so no respawn spot lands inside one
const SAFE_CHECKS = [];
function unsafeAt(x, y) { for (const f of SAFE_CHECKS) if (f(x, y)) return true; return false; }
function nearSpikes() {
  if (unsafeAt(P.x, P.y)) return true;
  const tx = Math.floor(P.x / TILE), ty = Math.floor((P.y + 1) / TILE);
  for (let dx = -2; dx <= 2; dx++) { const t = tileAt(tx + dx, ty); if (t === T_SPIKE || t === T_PLAT) return true; if (tileAt(tx + dx, ty - 1) === T_SPIKE) return true; }
  return false;
}
function doJump(v, dbl = false) {
  spend(dbl ? 0 : 6); P.vy = -v; P.ground = false; P.coyote = 0;
  P.dj = dbl && pHas('double_jump');
  setP('air', P.dj ? 'double_jump' : 'jump_up', false);
  sfx.jump();
  if (dbl) { spawnFx('dust', P.x, P.y + 2, P.face); for (let i = 0; i < 8; i++) particles.push({ x: P.x + rand(-6, 6), y: P.y, vx: rand(-40, 40), vy: rand(10, 40), life: 0.4, kind: 'gold' }); }
  else spawnFx('dust', P.x, P.y, P.face);
}
function wallJump() {
  const d = P.wallDir || P.face;
  P.face = -d; P.vx = -d * 175; P.vy = -300; P.ctrlLock = 0.15; P.wallDir = 0; P.airDash = true;
  setP('air', 'jump_up', false); sfx.jump();
  spawnFx('wall_dust', P.x + d * 6, P.y - 10, -d);
}
function doRoll(ax) { return mvDodgeStart(ax); }   // every type's L (75_moves.js: roll, sidestep, hop, backhop, demon dash)

// ---- v8 techniques: parry / shield guard, backstep strike, plunging attack, spear jump thrust
function startParry() {
  spend(10); P.parried = false; P.foreQ = false; P.guardKind = null; P.guardT0 = P.clk;
  P.shieldParry = wcls() === 'sns' && pHas('sh_parry');
  setP('parry', P.shieldParry ? 'sh_parry' : pHas('parry') ? 'parry' : 'hurt', false, 1);
  P.parryWin = (has('riposte_mastery') ? 0.24 : 0.17) * (charmOn('c_thorn') ? 1.5 : 1);   // 170 ms (WEAPON_REVAMP A2 / A6)
}
// held guard (shield class): stand firm behind the shield; blocked blows drain stamina (see hurtPlayer)
function updateGuard(dt, ax, grav) {
  P.vx = approach(P.vx, 0, 900 * dt); grav();
  if (!P.ground) { setP('air', 'jump_fall'); return; }
  if (P.state === 'block' && P.anim.done) setP('guard', 'sh_guard', true);
  if (peek('attack') && P.st > 0) {
    take('attack'); if (ax) P.face = ax;
    if (tryRiposte()) return;
    if (P.gcT > 0 && startCounter()) return;
    mvStartLight(); return;
  }
  if (peek('heavy') && P.st > 0) { take('heavy'); if (ax) P.face = ax; if (!mvGuardK()) startHeavy(); return; }   // 76: shield slam (III)
  if (peek('roll') && P.st > 0) { take('roll'); doRoll(ax); return; }
  if (P.state === 'guard' && !held.has('parry')) { setP('idle', 'idle', true); return; }
  if (ax && P.state === 'guard') P.face = ax;   // turn in place behind the shield
}
function isBlocking() { return P.state === 'guard' || P.state === 'block' || (P.state === 'parry' && P.shieldParry && P.anim.i <= 3) || !!(ATK[P.state] && ATK[P.state].mv && ATK[P.state].mv.guarding); }
function startPlunge() {
  P.plg = mvPlunge(); spend(P.plg.stam * (charmOn('c_brand') ? 0.8 : 1)); P.hitSet = new Set(); P.plungeT = 0; P.charge = 0; P.charged = false; P.combo = 0;
  setP('plunge', 'plunge', false, 1); P.vy = Math.min(P.vy, -70); sfx.heavySwing();
}
function updatePlunge(dt, ax, grav) {
  const an = P.anim; P.plungeT += dt;
  if (an.tag === 'plunge') {   // heave overhead: hang for a beat
    P.vx *= Math.pow(0.05, dt); P.vy = Math.min(P.vy + 420 * dt, 30);
    if (an.done) { const ft = P.plg && P.plg.fallTag && pHas(P.plg.fallTag) ? P.plg.fallTag : 'plunge_fall'; an.set(ft, ft === 'plunge_fall'); P.vy = 330; sfx.swing(); }
  } else if (an.tag === 'plunge_fall' || (P.plg && an.tag === P.plg.fallTag)) {
    P.vy = Math.min(P.vy + 1100 * dt, 540); P.vx = approach(P.vx, ax * 45, 500 * dt);
    if (Math.random() < 0.7) particles.push({ x: P.x + P.face * rand(4, 14), y: P.y - rand(0, 20), vx: 0, vy: -rand(40, 90), life: 0.25, kind: P.plg && P.plg.pk || 'spark' });
    const r = rect(P.x - 4 + P.face * 2, P.y - 10, P.x + P.face * 26, P.y + 12);   // the blade leads the fall
    for (const t of targets()) { const hb = hbOf(t); if (hb && overlap(r, hb) && !t.prop) { plungeImpact(true); return; } }
    if (P.plungeT > 3) setP('air', 'jump_fall');
  } else {   // plunge_land
    P.vx = approach(P.vx, 0, 900 * dt); grav();
    if (an.done) setP('idle', 'idle', true);
  }
}
// ---- ground smashes (plunge + Cinder Slam) share a limit: two in a row, then they lock until you've
// been back on the ground for 0.25 s — no bouncing off a boss's head forever
const SMASH_CHAIN = 2, SMASH_CD = 0.25;
function smashReady() { if (P.smashLock) { if (!P.smashDenied) { P.smashDenied = true; sfx.deny(); } return false; } return true; }
function smashStart() { P.smashN = (P.smashN || 0) + 1; P.smashIdle = 0; P.smashDenied = false; if (P.smashN >= SMASH_CHAIN) { P.smashLock = true; P.smashCd = SMASH_CD; } }
function smashLanded() { P.smashIdle = 0; }
function smashTick(dt) {
  if (P.smashLock) {
    if (P.ground && !['plunge', 'slam'].includes(P.state)) { P.smashCd -= dt; if (P.smashCd <= 0) { P.smashLock = false; P.smashN = 0; P.smashDenied = false; } }
  } else if ((P.smashIdle = (P.smashIdle || 0) + dt) > 0.8 && P.ground) P.smashN = 0;   // a lone smash now and then doesn't count toward the chain
}
// ---- every airborne attack (strikes, pogo, plunge, slam, arts) shares a second limit: two per trip through
// the air, then nothing until you've stood on the ground for AIR_CD. Pogoing off spikes/brambles refunds one.
const AIR_CHAIN = 2, AIR_CD = 0.25;
function airAtkGate(canStart) {
  if (!canStart || P.ground || (typeof DBS !== 'undefined' && DBS.inWater)) return null;
  const inp = { a: peek('attack'), h: peek('heavy'), o: peek('art') };
  if (!(inp.a || inp.h || inp.o)) return null;
  if (P.airLock) { take('attack'); take('heavy'); take('art'); if (!P.airDenied) { P.airDenied = true; sfx.deny(); } return null; }
  return inp;
}
function airAtkStart() { P.airN = (P.airN || 0) + 1; if (P.airN >= AIR_CHAIN) { P.airLock = true; P.airCd = AIR_CD; P.airDenied = false; } }
function airRefund() { if (P.airN > 0) P.airN--; if (P.airN < AIR_CHAIN) P.airLock = false; }
function airTick(dt) {
  if (!P.ground || ['plunge', 'slam'].includes(P.state)) return;
  if (!P.airLock) { P.airN = 0; return; }
  if ((P.airCd -= dt) <= 0) { P.airLock = false; P.airN = 0; P.airDenied = false; }
}
// the plunge lands (on the floor, or on a foe mid-fall): heavy AoE, bounce off whatever it struck
function plungeImpact(midair) {
  smashLanded();
  const PL = P.plg || mvPlunge(), A = PLUNGE_A, W = D.W;   // dmg / poise from the type's table (no fall bonus: the table is the number)
  A.mult = PL.dmg; A.poise = PL.poise; A.cls = mvType();
  const r = rect(P.x + P.face * A.reach[0], P.y + A.ys[0] - 4, P.x + P.face * A.reach[1], P.y + A.ys[1] + (midair ? 34 : 6));   // mid-air: reach down onto the foe
  shake = Math.max(shake, 8); sfx.boom(); hitstop = Math.max(hitstop, 0.07);
  spawnFx('shockwave', P.x + P.face * 14, P.y + (midair ? 0 : 0), 1);
  if (!midair) spawnFx('ground_crack', P.x + P.face * 14, P.y, 1);
  for (let i = 0; i < 18; i++) particles.push({ x: P.x + P.face * 14 + rand(-22, 22), y: P.y - 2, vx: rand(-90, 90), vy: -rand(30, 130), g: 320, life: 0.6, kind: 'dust' });
  let n = 0;
  if (PL.shock) mvShockwave(PL.shock);   // 76: the maul's meteor plunge
  for (const t of targets()) {
    const hb = hbOf(t); if (!hb || !overlap(r, hb)) continue;
    const dmg = outgoing(D.light, PL.dmg, 'melee') * (P.twinBuff ? 1.25 : 1), fire = P.fireT > 0 || !!W.fire;
    const info = { dmg: dmg * (fire && W.fire ? 1 + W.fire : 1), poise: mvPoiseFor(t, A.poise, A, P.y - 12), dir: t.x > P.x ? 1 : -1, kind: 'heavy', charged: false, bleed: bleedAmt(true), fire, rotDot: !!W.rot,
                   x: clamp(P.x + P.face * 14, hb.x0 + 3, hb.x1 - 3), y: clamp(P.y - 12, hb.y0, hb.y1), melee: true, big: true };
    t.hit(info); n++;
    runHooks('strike', t, { dmg, heavy: true, x: info.x, y: info.y }, A);
    mvOnHit(t, info, A);
  }
  if (n) P.twinBuff = false;
  hitBreakables(r);
  if (n || midair) { P.vy = -250; P.ground = false; P.vx = -P.face * 40; setP('air', 'jump_up'); P.airDash = true; }   // bounce off
  else setP('plunge', 'plunge_land', false);
}
function startSpDive() {
  spend(16); P.hitSet = new Set(); P.diveT = 0;   // jump thrust dive: 1.5 / 40 / 16 (A8)
  setP('spdive', 'sp_jump', false, 1); P.vy = Math.min(P.vy, -60); sfx.swing();
}
function updateSpDive(dt, ax, grav) {
  const an = P.anim; P.diveT += dt;
  if (an.tag === 'sp_jump') {
    P.vx *= Math.pow(0.1, dt); P.vy = Math.min(P.vy + 380 * dt, 40);
    if (an.done) { an.set('sp_dive', true); P.vx = P.face * 240; P.vy = 290; sfx.spear(); }
    return;
  }
  P.vx = P.face * 240; P.vy = 290;
  if (Math.random() < 0.6) particles.push({ x: P.x - P.face * rand(0, 10), y: P.y - rand(4, 24), vx: -P.face * 40, vy: -60, life: 0.25, kind: 'spark' });
  const r = rect(P.x + P.face * 4, P.y - 12, P.x + P.face * 34, P.y + 14);
  const SD = ATK.sp_dive || PLUNGE_A;
  for (const t of targets()) {
    if (P.hitSet.has(t)) continue;
    const hb = hbOf(t); if (!hb || !overlap(r, hb)) continue;
    P.hitSet.add(t);
    const dmg = outgoing(D.light, 1.5, 'melee') * (P.twinBuff ? 1.25 : 1), fire = P.fireT > 0;
    const info = { dmg, poise: mvPoiseFor(t, 40, SD, P.y - 4), dir: P.face, kind: 'light', bleed: bleedAmt(false), fire, x: clamp(P.x + P.face * 26, hb.x0 + 3, hb.x1 - 3), y: clamp(P.y - 4, hb.y0, hb.y1), melee: true, big: true };
    t.hit(info); P.twinBuff = false;
    runHooks('strike', t, { dmg, heavy: false, x: info.x, y: info.y }, SD);
    mvOnHit(t, info, SD);
    if (!t.prop) { P.vy = -230; P.vx = -P.face * 70; P.ground = false; setP('air', 'jump_up'); P.airDash = true; spawnFx(fxOr('spear_impact', 'hit'), info.x, info.y, P.face); return; }
  }
  if (P.diveT > 1.4) setP('air', 'jump_fall');
}
function spikeHurt() {
  if (P.state === 'dead' || P.inv > 0) return;
  const dmg = Math.round(D.maxHp * 0.18 * (charmOn('c_thorn') ? 0.5 : 1));
  P.hp = Math.max(0, P.hp - dmg); P.flash = 1; shake = 5; hitstop = 0.12; sfx.hurt();
  spawnFx('blood', P.x, P.y - 10, 1);
  if (P.hp <= 0) return killPlayer(0);
  P.inv = 0.9; P.vx = 0; P.vy = 0;
  // never put you back somewhere that hurts again: fall back to where you first stood in this room
  const s = unsafeAt(P.safe.x, P.safe.y) && P.entry && P.entryRoom === room ? P.entry : P.safe;
  fadeTo(() => { P.x = s.x; P.y = s.y; P.safe = { ...s }; setP('idle', 'idle', true); updateCamera(0, true); });
}

function hurtPlayer(dmg, dir, id, opt = {}) {
  if (P.state === 'dead' || !playing()) return false;
  if (id !== undefined && id === P.lastHit) return false;
  // parry
  if (opt.parryable && P.state === 'parry' && P.parryWin > 0 && dir === -P.face) {
    P.lastHit = id; sfx.parry(); hitstop = 0.16; shake = 3;
    spawnFx(fxOr('parry_flash', 'parry_spark'), P.x + P.face * 12, P.y - 18, P.face);
    for (let i = 0; i < 12; i++) particles.push({ x: P.x + P.face * 12, y: P.y - 18, vx: P.face * rand(20, 120), vy: -rand(20, 100), g: 300, life: rand(0.3, 0.6), kind: 'spark' });
    if (opt.src && opt.src.onParried) opt.src.onParried();
    runHooks('parry', opt.src);
    // no opening for a riposte (bosses, elites): a guard counter is ready instead
    P.parried = true; P.gcT = 0.6; if (charmOn('c_twin')) P.twinBuff = true;
    mvGain('parry');
    return false;
  }
  // 76: the types' own answers to a blow (iai parry, foresight, snap counter, perfect dodge, brace, charge armour ...)
  const M = mvHurtPre(dmg, dir, id, opt);
  if (M.negate) { if (id !== undefined) P.lastHit = id; return false; }
  dmg = M.dmg;
  if (P.inv > 0) return false;
  if (SETTINGS.god) return false;   // test setting
  // guards (sword & shield, greatsword blade guard, spear heavy guard): frontal blows, projectiles and hazards are stopped
  // cold; stamina pays for it (76: mvGuardCost)
  let guardBroke = false;
  if (isBlocking() && dir === -P.face && !iframes()) {
    const G = mvGuardCost(dmg, opt);
    P.lastHit = id;
    if (P.st >= G.cost) {
      if (G.cost > 0) { spend(G.cost); P.stDelay = 0.8; }
      sfx.block(); tone(420, 0.18, 0.08, 'triangle', 0.7); hitstop = Math.max(hitstop, 0.06); shake = Math.max(shake, 2);
      spawnFx(fxOr('parry_spark', 'hit'), P.x + P.face * 12, P.y - 18, P.face);
      for (let i = 0; i < 8; i++) particles.push({ x: P.x + P.face * 12, y: P.y - rand(12, 24), vx: P.face * rand(20, 110), vy: -rand(10, 80), g: 300, life: rand(0.2, 0.45), kind: 'spark' });
      P.vx = dir * G.push; P.gcT = G.counterT; if (charmOn('c_twin')) P.twinBuff = true;
      if (G.chip > 0) { const c = Math.max(1, Math.round(G.chip)); P.hp = Math.max(1, P.hp - c); popup(P.x, P.y - 30, c, '#c08070'); P.flash = 0.4; }
      if (P.state !== 'parry' && !ATK[P.state]) mvBlockPose();
      mvBlocked(dmg, dir, opt, G, id);
      return false;
    }
    guardBroke = true; P.st = 0; P.stDelay = 1.2; dmg *= 0.5;   // guard break: half gets through and you reel
    sfx.crit(); spawnFx(fxOr('parry_flash', 'parry_spark'), P.x + P.face * 12, P.y - 20, P.face);
  }
  if (iframes()) {
    mvDodged(dmg, dir, id, opt);   // 76: the dual blades' perfect dodge
    if (has('second_wind') && P.state === 'roll' && !P.sw) {
      P.sw = true; slowmo = 0.55; P.st = Math.min(D.maxSt, P.st + 30); P.empower = 3;   // 57: 30 stamina, no longer the whole bar (v2 tree)
      spawnFx(fxOr('parry_flash', 'parry_spark'), P.x, P.y - 14, P.face, null, { alpha: 0.6 });
      sfx.glint();
    }
    if (HOOKS.negated) runHooks('negated', dmg, dir, opt);   // agent G: guard arts react to blows they soak
    return false;
  }
  P.lastHit = id;
  dmg = Math.round(dmg * (has('steadfast') ? 0.9 : 1) * (charmOn('c_greed') ? 1.1 : 1) * NGP.dmg * rand(0.95, 1.05));
  for (const f of HOOKS.playerHurt) dmg = Math.round(f(dmg, opt) ?? dmg);
  if (opt.rot) addRot(opt.rot);
  P.hp = Math.max(0, P.hp - dmg); P.flash = 1; P.inv = 0.55;
  shake = Math.max(shake, dmg > D.maxHp * 0.25 ? 7 : 5); hitstop = 0.1; sfx.hurt(); flashScreen = 0.22;
  spawnFx('blood', P.x - dir * 2, P.y - 16, dir);
  popup(P.x, P.y - 30, dmg, '#ff6a5a');
  if (P.hp <= 0) return killPlayer(dir);
  const attacking = !!ATK[P.state] || P.state === 'art';
  const armored = M.armor || (has('steadfast') && attacking && dmg < D.maxHp * 0.3) || (charmOn('c_horn') && attacking && dmg < D.maxHp * 0.35)
    || (P.cryT > 0 && dmg < D.maxHp * 0.3) || (P.state === 'art' && P.artId === 'stormleap')
    || (P.state === 'art' && ART_IMPL[P.artId] && ART_IMPL[P.artId].armor) || skArmored();   // 57: skill-tree hyper armour   // agent G's hyper-armoured arts
  if (guardBroke) { setP('gbreak', pHas('sh_break') ? 'sh_break' : 'hurt', false); P.vx = dir * 110; P.healPending = 0; P.combo = 0; P.spellFired = true; P.gcT = 0; mvInterrupted(); }
  else if (!armored) { setP('hurt', 'hurt'); P.vx = dir * 130; P.vy = P.ground ? -60 : P.vy; P.healPending = 0; P.combo = 0; P.spellFired = true; mvInterrupted(); }
  return true;
}
function killPlayer(dir) {
  if (SETTINGS.god) { P.hp = D.maxHp; return false; }   // test setting: nothing can kill you
  P.state = 'dead'; P.anim.set('death', false); P.vx = dir * 90; P.deadT = 1.6; slowmo = 0.9;
  sfx.died(); runHooks('death'); return true;
}

// ---- dealing damage
function outgoing(base, mult, kind, src) {
  let d = base * mult * skOutMul(kind, src);   // 57_skills.js: every skill-tree damage bonus (src: the projectile, if any)
  if (P.empower > 0) d *= 1.3;
  if (kind !== 'spell') { if (charmOn('c_crest')) d *= 1.1; if (P.cryT > 0) d *= P.cryBig ? 1.3 : 1.2; if (P.fireT > 0) d *= 1.25; }
  return d * rand(0.93, 1.07);
}
function bleedAmt(heavy) {
  const b = (D.W.bleed || 0) + (has('bloodthirst') ? 16 : 0);   // 57: tuned for the v2 tree (root node)
  return b * (heavy ? 1.5 : 1) * (charmOn('c_fang') ? 1.5 : 1);
}
// v9: scythes hook foes a little toward you; the whip's chain heavy drags small foes all the way in
function weaponPull(t, A) {
  if (!t || t.prop || t.boss || t.alive === false || (t.cfg && (t.cfg.elite || t.cfg.flying))) return;
  const goal = P.x + P.face * (A.chain ? 16 : 20), d = goal - t.x;
  if (Math.sign(d) !== -P.face && !A.chain) return;           // only ever toward you
  const step = A.chain ? d : clamp(d, -9, 9);
  const nx = t.x + step;
  if (solidAtPx(nx, t.y - 6) || solidAtPx(nx, t.y - 20)) return;
  if (A.chain) {   // reel it in over a moment, and it stays off balance
    if (typeof wfx === 'function') wfx({ life: 0.22, x0: t.x, update() { if (t.alive === false) return false; t.x = this.x0 + (goal - this.x0) * Math.min(1, this.t / 0.2); if (t.vx !== undefined) t.vx = 0; } });
    else t.x = nx;
    if (t.breakStance && t.state !== 'stagger') t.poise = (t.poise || 0) + 40;
    for (let i = 0; i < 8; i++) particles.push({ x: (t.x + P.x) / 2 + rand(-10, 10), y: t.y - rand(8, 20), vx: -P.face * rand(20, 60), vy: 0, life: 0.3, kind: 'spark' });
  } else { t.x = nx; if (t.vx !== undefined) t.vx = -P.face * 30; }
}
function reapHeal(t) {   // scythe heavy: a life taken feeds you
  const h = Math.round(D.maxHp * 0.05 + 4);
  P.hp = Math.min(D.maxHp, P.hp + h); popup(P.x, P.y - 34, h, '#8fe08a'); sfx.heal();
  for (let i = 0; i < 12; i++) particles.push({ x: t.x + rand(-8, 8), y: t.y - rand(4, 24), vx: (P.x - t.x) * rand(1.5, 2.5), vy: -rand(10, 40), life: 0.5, kind: 'gold' });
}
// one frame of a move's active window: every target in the box not yet struck this hit (75_moves.js: mvRect / mvHitCtx
// apply the type's rules: both-end staves, the whip's tip, the maul's stun, momentum, counters ...)
function playerStrike(A) {
  const W = D.W, d = A.mv || {};
  const r = mvRect(A);
  const heavy = A.kind === 'heavy';
  const fire = P.fireT > 0 || (W.fire && heavy);
  for (const t of targets()) {
    if (P.hitSet.has(t)) continue;
    const hb = hbOf(t); if (!hb || !overlap(r, hb)) continue;
    P.hitSet.add(t);
    const c = mvHitCtx(t, hb, A, r); if (c.skip) continue;
    const dmg = outgoing(D.light, c.mul, 'melee') * (A.counter ? P.counterMul || 1 : 1) * (P.twinBuff ? 1.25 : 1);
    const info = { dmg: dmg * (fire && W.fire ? 1 + W.fire : 1), poise: c.poise, dir: c.dir, kind: heavy ? 'heavy' : 'light', charged: heavy && !!P.charged, bleed: bleedAmt(heavy), fire, rotDot: !!W.rot,
            x: c.x, y: c.y, melee: true, big: heavy || !!A.big };
    t.hit(info);
    runHooks('strike', t, { dmg, heavy, x: info.x, y: info.y }, A);
    mvOnHit(t, info, A, c);
    if (A.down && !P.pogoed && d.pogo !== false) pogo();
    if (P.empower > 0) P.empower = 0;
    if (has('soul_siphon')) P.fp = Math.min(D.maxFp, P.fp + 2);
  }
  if (P.twinBuff && P.hitSet.size && [...P.hitSet].some(x => x !== 'brk')) P.twinBuff = false;
  // pogo off spikes + break walls/urns
  if (A.down && !P.pogoed && d.pogo !== false) {
    // (brambles too, for every type's down attack -- 30_thornveil.js only knows the sword's attack_down tag)
    const bram = typeof TV_T_BRAMBLE !== 'undefined' ? TV_T_BRAMBLE : -1;
    for (let x = r.x0; x <= r.x1; x += 6) { const t = tileAt(Math.floor(x / TILE), Math.floor(r.y1 / TILE)); if (t === T_SPIKE || t === bram) { pogo(); airRefund(); break; } }
  }
  hitBreakables(r);
}
function pogo() {
  P.pogoed = true; P.vy = -245; P.airDash = true; if (SAVE.items.wings) P.airJumps = 1;
  spawnFx(fxOr('pogo', 'hit'), P.x, P.y + 6, P.face); sfx.hit(); hitstop = 0.05;
}
const brkHits = {};
function hitBreakables(r) {
  if (P.hitSet.has('brk')) return;
  for (let ty = Math.floor(r.y0 / TILE); ty <= Math.floor(r.y1 / TILE); ty++)
    for (let tx = Math.floor(r.x0 / TILE); tx <= Math.floor(r.x1 / TILE); tx++) {
      if (tx < 0 || ty < 0 || tx >= room.w || ty >= room.h || room.grid[ty * room.w + tx] !== T_BREAK) continue;
      P.hitSet.add('brk');
      const k = brokenKey(room.def, tx, ty); brkHits[k] = (brkHits[k] || 0) + 1;
      shake = 3; sfx.hit(); spawnFx('hit', tx * TILE + 8, ty * TILE + 8, P.face);
      for (let i = 0; i < 6; i++) particles.push({ x: tx * TILE + 8, y: ty * TILE + 8, vx: rand(-60, 60), vy: -rand(20, 90), g: 400, life: 0.7, kind: 'rock' });
      if (brkHits[k] >= 3) breakWallAt(tx, ty);
      return;
    }
}
function breakWallAt(tx0, ty0) {
  // break the whole connected breakable column/cluster
  const stack = [[tx0, ty0]], seen = new Set();
  while (stack.length) {
    const [x, y] = stack.pop(), key = x + ',' + y;
    if (seen.has(key) || x < 0 || y < 0 || x >= room.w || y >= room.h || room.grid[y * room.w + x] !== T_BREAK) continue;
    seen.add(key); room.grid[y * room.w + x] = T_EMPTY; SAVE.flags[brokenKey(room.def, x, y)] = 1;
    for (let i = 0; i < 10; i++) particles.push({ x: x * TILE + rand(0, 16), y: y * TILE + rand(0, 16), vx: rand(-80, 80), vy: -rand(20, 120), g: 420, life: rand(0.6, 1.2), kind: 'rock' });
    stack.push([x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]);
  }
  renderRoomLayers(room); sfx.crumble(); shake = 8; toast('A hidden passage'); saveGame();
}
function critTarget() {
  for (const t of targets()) {
    if (!t.critable || !t.critable()) continue;
    const dx = t.x - P.x;
    if (Math.abs(dx) < (t.critRange || 34) && Math.abs(t.y - P.y) < 30) return t;
  }
  return null;
}
function critHit(t) {
  let dmg = outgoing(D.light, t.boss ? 3.2 : 4.5, 'melee') * (has('riposte_mastery') ? 1.5 : 1) * (D.W.crit || 1);
  sfx.crit(); hitstop = 0.22; shake = 9; slowmo = 0.35; flashScreen = 0.3;
  const hb = t.hurtbox() || rect(t.x - 8, t.y - 30, t.x + 8, t.y);
  spawnFx(fxOr('riposte', 'parry_spark'), (hb.x0 + hb.x1) / 2, (hb.y0 + hb.y1) / 2, P.face);
  spawnFx('blood', (hb.x0 + hb.x1) / 2, (hb.y0 + hb.y1) / 2, P.face);
  t.hit({ dmg, poise: 0, dir: P.face, kind: 'crit', x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2, melee: true, big: true, crit: true });
  if (has('riposte_mastery')) P.hp = Math.min(D.maxHp, P.hp + Math.round(D.maxHp * 0.05));   // 57: 5% (v2 tree)
}

// ---- spells
function castSpell(id) {
  const sp = D.spell;
  runHooks('cast', id);
  if (SPELL_CAST[id]) return SPELL_CAST[id](sp);
  if (id === 'ash_bolt') { fireProjectile('ashbolt'); sfx.bolt(); }
  else if (id === 'sunspear') { fireProjectile('sunspear'); sfx.spear(); flashScreen = 0.12; }
  else if (id === 'shards') { for (let k = 0; k < 3; k++) fireProjectile('shard', k); sfx.bolt(); }
  else if (id === 'lance') { fireProjectile('lance'); sfx.spear(); }
  else if (id === 'warmth') { P.regenT = 4; sfx.heal(); spawnFx(fxOr('warmth', 'heal'), P.x, P.y, 1, P, { bottom: true, loop: true, life: 4 }); }
  else if (id === 'rotmist') { fireProjectile('mist'); sfx.fire(); }
  else if (id === 'emberburst') {
    sfx.fire(); shake = 6;
    spawnFx(fxOr('flame_ring', 'shockwave'), P.x, P.y, 1, null, { bottom: true });
    const r = rect(P.x - 50, P.y - 40, P.x + 50, P.y + 2);
    for (const t of targets()) { const hb = t.hurtbox(); if (hb && overlap(r, hb)) t.hit({ dmg: 78 * sp * rand(0.95, 1.05), poise: 40, dir: t.x > P.x ? 1 : -1, kind: 'spell', x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2, big: true, fire: true }); }
    for (let i = 0; i < 30; i++) particles.push({ x: P.x + rand(-40, 40), y: P.y - rand(0, 10), vx: rand(-30, 30), vy: -rand(40, 140), life: rand(0.4, 1), kind: 'fire' });
  }
}
function fireProjectile(kind) {
  const sp = D.spell;
  const base = { owner: 'player', face: P.face, t: 0, hits: new Set() };
  if (kind === 'ashbolt') projectiles.push({ ...base, kind, x: P.x + P.face * 14, y: P.y - 18, vx: P.face * 270, vy: 0, dmg: 58 * sp, life: 1.4, r: 5, sh: 'fx_ashbolt' });
  if (kind === 'sunspear') projectiles.push({ ...base, kind, x: P.x + P.face * 14, y: P.y - 20, vx: P.face * 340, vy: 0, dmg: 86 * sp, life: 1.2, r: 6, pierce: true, sh: 'fx_light_spear' });
  if (kind === 'shard') projectiles.push({ ...base, kind, x: P.x + P.face * 10, y: P.y - 22 - arguments[1] * 5, vx: P.face * (150 + arguments[1] * 20), vy: -40 + arguments[1] * 40, dmg: 30 * sp, life: 2.2, r: 4, seek: 5, sh: 'fx_shards' });
  if (kind === 'lance') projectiles.push({ ...base, kind, x: P.x + P.face * 14, y: P.y - 18, vx: P.face * 390, vy: 0, dmg: 72 * sp, life: 1.0, r: 5, pierce: true, poise: 70, sh: 'fx_lance' });
  if (kind === 'mist') projectiles.push({ ...base, kind, x: P.x + P.face * 40, y: P.y, vx: P.face * 20, vy: 0, dmg: 16 * sp, life: 3.2, r: 26, pierce: true, tick: 0.45, static: true, sh: 'fx_rotmist' });
  if (kind === 'moonwave') projectiles.push({ ...base, kind, x: P.x + P.face * 20, y: P.y - 20, vx: P.face * 260, vy: 0, dmg: D.light * 2.3, life: 0.8, r: 14, pierce: true, poise: 50, sh: SAVE.weapon === 'kalden' && fxSheet('kalden_slash').ok ? 'fx_kalden_slash' : 'fx_moonwave', oath: SAVE.weapon === 'kalden' });
  if (kind === 'crescent') projectiles.push({ ...base, kind, x: P.x + P.face * 20, y: P.y - 16, vx: P.face * 230, vy: 0, dmg: D.heavy * 1.2, life: 0.6, r: 10, pierce: true, sh: 'fx_slash_air' });
}

// charged arts: crescent -> a towering triple crescent; moonwave -> a brighter wave with a second one in its wake
function fireChargedArt(id) {
  const base = { owner: 'player', face: P.face, t: 0, hits: new Set() };
  if (id === 'crescent') {
    for (let k = -1; k <= 1; k++) projectiles.push({ ...base, kind: 'crescent', x: P.x + P.face * 20, y: P.y - 16 + k * 10, vx: P.face * 250, vy: k * 12, dmg: D.heavy * 1.05, life: 0.75, r: 11, pierce: true, poise: 45, sh: 'fx_slash_air' });
    shake = Math.max(shake, 4);
  } else if (id === 'moonwave') {
    const sh = SAVE.weapon === 'kalden' && fxSheet('kalden_slash').ok ? 'fx_kalden_slash' : 'fx_moonwave';
    projectiles.push({ ...base, kind: 'moonwave', x: P.x + P.face * 20, y: P.y - 20, vx: P.face * 290, vy: 0, dmg: D.light * 3.4, life: 1.0, r: 16, pierce: true, poise: 90, sh, oath: SAVE.weapon === 'kalden' });
    projectiles.push({ ...base, hits: new Set(), kind: 'moonwave', x: P.x + P.face * 20, y: P.y - 20, vx: P.face * 260, vy: 0, dmg: D.light * 1.8, life: 0.9, r: 14, pierce: true, poise: 50, sh, delay: 0.16, oath: SAVE.weapon === 'kalden' });
    flashScreen = Math.max(flashScreen, 0.2); shake = Math.max(shake, 5);
  } else fireProjectile(id);
}

// ---- cooldowns: every spell and weapon art has one, tracked per id (switching spells doesn't reset them).
// Default from the FP cost; timed buffs/summons wait out their effect ("for 12 seconds" in the description) plus a gap.
const CD_OVERRIDE = { spell: { warmth: 14 }, art: {} };
function cdBase(kind, id) {
  const T = kind === 'spell' ? SPELLS[id] : ARTS[id]; if (!T) return 0;
  if (CD_OVERRIDE[kind][id] !== undefined) return CD_OVERRIDE[kind][id];
  if (T.cd !== undefined) return T.cd;
  let cd = kind === 'spell' ? clamp(1.2 + T.fp * 0.13, 2, 9) : clamp(1.5 + T.fp * 0.22, 3, 10);
  const m = /(\d+(?:\.\d+)?) seconds/.exec(T.desc || ''); if (m) cd = Math.max(cd, +m[1] + 6);
  if (/^Restore|heal/i.test(T.desc || '')) cd = Math.max(cd, 12);
  return cd;
}
function cdLeft(kind, id) { return SETTINGS.nocd ? 0 : Math.max(0, ((P.cds || {})[kind + ':' + id] || 0) - time); }
function cdStart(kind, id) { (P.cds = P.cds || {})[kind + ':' + id] = time + cdBase(kind, id) * (charmOn('c_scholar') && kind === 'spell' ? 0.9 : 1); }
function cdDeny(kind) { if ((P.cdDenyT || 0) < time) { sfx.deny(); P.cdDenyT = time + 0.3; } P.cdFlash = { kind, t: time }; }
function cdFrac(kind, id) { const L = cdLeft(kind, id), B = cdBase(kind, id); return B > 0 ? L / B : 0; }

// ---- weapon arts (swappable; O key)
function startArt() {
  const id = SAVE.art; if (!id || !ARTS[id]) { toast('No weapon art equipped'); return; }
  let cost = Math.round(ARTS[id].fp * skArtCostMul());   // 57: Kindling
  const echoFree = charmOn('c_echo') && (P.artCount + 1) % 3 === 0;   // Echo of the First Flame: every third art is free
  if (echoFree) cost = 0;
  if (cdLeft('art', id) > 0) { cdDeny('art'); return; }
  if (P.fp < cost) { sfx.deny(); toast('Not enough FP'); return; }
  if (id === 'stormleap' && !P.ground) { sfx.deny(); return; }
  cdStart('art', id);
  P.artCount++;
  if (echoFree) { spawnFx(fxOr('parry_flash', 'parry_spark'), P.x, P.y - 16, P.face, null, { alpha: 0.5 }); tone(660, 0.3, 0.05, 'sine', 1.5); }
  // hold O to charge (>= 0.6 s): the art is released charged; P.artCharged stays set while it plays
  P.artHold = true; P.artChargeT = 0; P.artCharged = false;
  P.fp -= cost; P.artId = id; P.artT = 0; P.artFired = false; P.artI = false; P.artLaunched = false; P.artGo = false; P.hitSet = new Set();
  const own = artTagFor(id);   // AA: the class's own take on the art (art_<id>__<cls>) if the sheet has one
  P.artTag = own; P.artOwn = pHas(own);
  const A = P.artOwn ? [own, 1] : ART_IMPL[id] ? ART_IMPL[id].fallback || ['attack1', 1] : { crescent: ['attack2', 1.0], moonwave: ['heavy', 1.35], bloodstep: ['air_attack', 1.2], stormleap: ['double_jump', 1], warcry: ['cast', 1.4], cinderblade: ['cast', 1.3] }[id];
  setP('art', pHas(A[0]) ? A[0] : 'attack1', false, A[1]);
  P.artRel = artRelease(id);
  if (id === 'stormleap' && !P.artOwn) { P.vy = -300; P.ground = false; sfx.jump(); spawnFx('dust', P.x, P.y, P.face); }
  if (P.artOwn) sfx.charge();
  if (id === 'bloodstep') { sfx.roll(); P.artI = true; }
  if (ART_IMPL[id] && ART_IMPL[id].start) ART_IMPL[id].start();
}
// v11 (AA): an art's animation in the wielder's class pose language: art_<id>__<cls> when the sheet has it, else art_<id>.
// The variant keeps the art's frame structure (release / held / looping frames), so ART_IMPL and ART_SYNC need no change.
const ART_CLS = { longsword: 'sw', katana: 'kt', greatsword: 'gs', maul: 'gs', sns: 'sh', dual: 'tw', spear: 'sp', staff: 'st', whip: 'wh' };
function artTagFor(id) { const v = 'art_' + id + '__' + (ART_CLS[wcls()] || 'sw'); return pHas(v) ? v : 'art_' + id; }
function artRelease(id) {
  const mv = ASSETS.player_meta && ASSETS.player_meta.moves, m = mv && ((P.artTag && mv[P.artTag]) || mv['art_' + id]);
  if (P.artOwn && m) return m.active[0];
  if (ART_IMPL[id]) return ART_IMPL[id].release ?? 3;
  return { crescent: 2, moonwave: 4, bloodstep: 0, stormleap: 0, warcry: 3, cinderblade: 3 }[id];
}
const ART_CHARGE_AT = { stormleap: 1, bloodstep: 1, warcry: 2, cinderblade: 1, magma_quake: 1, tolling_blow: 2 };
// v8 art_<id> bodies: keep the held / looping sections of each animation in step with agent G's ART_IMPL phases (P.g2)
const hold2 = (an, a, t, per) => { an.i = a + (Math.floor(t / per) % 2); an.t = 0; an.done = false; };
const jump = (an, i) => { if (an.i < i) { an.i = i; an.t = 0; an.done = false; } };
const ART_SYNC = {
  whirlwind(an, s) { if (s.rel && an.i < 1) { an.i = 1; an.t = 0; } },                       // the spin (frames 1-8) loops
  gale_vault(an, s) {
    if (!s.rel) return;
    if (s.phase === 1) { if (an.i > 4) hold2(an, 3, s.t, 0.07); }                              // tumble at the apex until the cut
    else if (s.phase === 2) { jump(an, 5); if (an.i > 6) { an.i = 6; an.t = 0; an.done = false; } }   // falling cut, hold the dive
    else if (s.phase === 3) jump(an, 7);                                                       // landing
  },
  aegis(an, s) { if (!s.rel) return; if (!s.done) hold2(an, 2, s.t, 0.12); else jump(an, 4); },
  frost_aegis(an, s) { ART_SYNC.aegis(an, s); },
  shield_charge(an, s) { if (!s.rel) return; if (!s.end) hold2(an, 2, s.t, 0.07); else jump(an, 4); },
  thunder_lunge(an, s) { if (!s.rel) return; if (s.phase === 1) hold2(an, 2, s.t, 0.05); else jump(an, 4); },
  twin_tempest(an, s) {
    if (!s.rel) return;
    if (s.n < 8) { if (an.i > 4 || an.i < 1) { an.i = 1 + (((an.i - 1) % 4) + 4) % 4; an.done = false; } }   // the flurry loops
    else jump(an, 5);                                                                                   // the closing X
  },
  backstep_slash(an, s) { if (!s.rel) return; if (s.phase === 1) { if (an.i > 2) hold2(an, 1, s.t, 0.06); } else if (s.phase === 2) jump(an, 3); },
  // v9 arts (agent G's 16_gear3.js drives them; frames from gen_player.py V9_ARTS)
  lash(an, s) {   // one arm-snap per crack (G draws the long lash): frames 2/4 crack, 3/5 recoil, 6 the last crack, then recover
    if (!s.rel || !s.n) return;
    if (s.n < s.max) { const base = s.n % 2 ? 2 : 4; an.i = s.crackT > 0.08 ? base + 1 : base; an.t = 0; an.done = false; }
    else if (s.crackT < 0.1) { an.i = 6; an.t = 0; an.done = false; } else jump(an, 7);
  },
  chain_drag(an, s) {   // 1/5 chain flying or reeling: throw pose · 2 hauling a small foe in · 3 hauling yourself · 4 the finishing crack
    if (!s.rel) return;
    if (s.phase === 1 || s.phase === 5) { if (an.i > 4) hold2(an, 3, s.t, 0.07); }
    else if (s.phase === 2) { an.i = 5; an.t = 0; an.done = false; }
    else if (s.phase === 3) { an.i = 6; an.t = 0; an.done = false; }
    else if (s.phase === 4) jump(an, 7);
  },
  blood_frenzy(an, s) {   // a thrust per hit of the frenzy, then the closing lunge
    if (!s.rel) return;
    if (s.n < s.max) { an.i = 2 + ((Math.max(1, s.n) - 1) % 5); an.t = 0; an.done = false; } else jump(an, 7);
  },
  overclock(an, s) { if (!s.rel) return; if (s.phase === 1) hold2(an, 2, s.t, 0.05); else jump(an, 4); },
};   // frame to hold while charging (default: release - 1)
const ART_CHARGE_MIN = 0.6, ART_CHARGE_MAX = 1.6;
function updateArtCharge(dt, grav) {
  const id = P.artId, an = P.anim;
  if (!P.artHold) return false;
  if (id === 'bloodstep') P.artI = false;
  if (!held.has('art') || P.artChargeT >= ART_CHARGE_MAX) { P.artHold = false; if (P.artCharged) { sfx.heavySwing(); shake = Math.max(shake, 3); } return false; }
  const cf = (ART_IMPL[id] && ART_IMPL[id].chargeAt !== undefined) ? ART_IMPL[id].chargeAt : (ART_CHARGE_AT[id] ?? Math.max(0, (P.artRel ?? 3) - 1));
  if (an.i < Math.min(cf, an.n - 1)) return false;   // still winding up to the hold frame
  an.i = Math.min(cf, an.n - 1); an.t = Math.min(an.t, 10); an.done = false;
  P.artChargeT += dt; P.vx = approach(P.vx, 0, 900 * dt); grav();
  if (Math.random() < 0.7) { const a = rand(0, 6.28), d = rand(14, 26); particles.push({ x: P.x + Math.cos(a) * d, y: P.y - 16 + Math.sin(a) * d * 0.7, vx: -Math.cos(a) * d * 3, vy: -Math.sin(a) * d * 2, life: 0.3, kind: P.artCharged ? 'ember' : 'gold' }); }
  addLight(P.x, P.y - 16, 30 + P.artChargeT * 30, P.artCharged ? '255,170,80' : '255,220,150', 0.7);
  if (P.artChargeT >= ART_CHARGE_MIN && !P.artCharged) { P.artCharged = true; sfx.glint(); tone(880, 0.4, 0.06, 'triangle', 1.5); spawnFx('telegraph', P.x + P.face * 4, P.y - 34, P.face); flashScreen = Math.max(flashScreen, 0.08); }
  return true;
}
function updateArt(dt, grav) {
  const id = P.artId, an = P.anim;
  if (updateArtCharge(dt, grav)) return;
  P.artT += dt;
  if (P.artOwn && an.i < P.artRel && Math.random() < 0.6) {   // gathering glow before the release (AA: a boss weapon gathers its boss's power)
    const sg = typeof SIGS !== 'undefined' && SIGS[SAVE.weapon] && SIGS[SAVE.weapon].pk ? SIGS[SAVE.weapon] : null, bossPk = sg && sg.pk && ['cinderblade', 'bloodstep'].indexOf(id) < 0;
    const c = bossPk ? sg.pk : id === 'moonwave' ? 'frost' : id === 'cinderblade' ? 'fire' : id === 'bloodstep' ? 'blood' : 'gold';
    particles.push({ x: P.x + P.face * rand(4, 18), y: P.y - rand(10, 34), vx: 0, vy: -rand(10, 40), life: 0.4, kind: c });
    addLight(P.x + P.face * 10, P.y - 20, 36, bossPk && sg.light ? sg.light : id === 'moonwave' ? '160,210,255' : '255,200,120', 0.6);
  }
  // AA: the First Ember's Echo plays its own short stance (a golden afterimage peels away) before the mirrored art takes over
  if (id === 'echo' && P.artOwn && an.i < P.artRel && !an.done) { P.vx = approach(P.vx, 0, 900 * dt); grav(); return; }
  if (ART_IMPL[id]) {
    ART_IMPL[id].update(dt, grav);
    if (P.state === 'art' && P.artOwn && P.g2 && ART_SYNC[id] && P.anim.tag === P.artTag) ART_SYNC[id](P.anim, P.g2);
    return;
  }
  if (P.artOwn && id === 'stormleap') return updateStormleap(dt, grav);
  if (P.artOwn && id === 'bloodstep' && P.artT < 0.05) P.artT = an.i < 2 ? 0.001 : P.artT;   // hold the dash until the sprint pose
  if (id === 'crescent' || id === 'moonwave') {
    P.vx = approach(P.vx, 0, 900 * dt); grav();
    if (!P.artFired && an.i >= P.artRel) { P.artFired = true; if (P.artCharged) fireChargedArt(id); else fireProjectile(id); (id === 'moonwave' ? sfx.spear : sfx.heavySwing)(); if (id === 'moonwave') flashScreen = 0.12; }
    if (an.done) setP('idle', 'idle', true);
  } else if (id === 'bloodstep') {
    if (P.artOwn && an.i < 2 && !P.artGo) { P.vx = approach(P.vx, 0, 900 * dt); grav(); P.artT = 0; return; }
    P.artGo = true;
    const ch = P.artCharged, dur = ch ? 0.36 : 0.24;   // charged: a longer, deeper cut
    const dashing = P.artT < dur;
    P.vx = dashing ? P.face * (ch ? 430 : 380) : P.vx * 0.8; P.vy = 0; P.artI = dashing;
    if (dashing) {
      ghosts.push({ f: P.anim.frame, x: P.x, y: P.y, face: P.face, life: ch ? 0.35 : 0.25, red: true });
      const r = rect(P.x - 14, P.y - 26, P.x + 14, P.y);
      for (const t of targets()) { if (P.hitSet.has(t)) continue; const hb = t.hurtbox(); if (hb && overlap(r, hb)) { P.hitSet.add(t); t.hit({ dmg: outgoing(D.light, ch ? 1.95 : 1.3, 'melee'), poise: ch ? 35 : 15, dir: P.face, kind: 'light', bleed: (ch ? 80 : 45) + bleedAmt(false), x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2, melee: true, big: ch }); } }
    }
    if (P.artT > dur && !P.artFired) { P.artFired = true; spawnFx(fxOr('bloodstep', 'slash'), P.x - P.face * 20, P.y - 14, P.face, null, ch ? { speed: 0.7 } : {}); if (ch) spawnFx(fxOr('bleed', 'blood'), P.x - P.face * 30, P.y - 14, P.face); }
    if (P.artOwn && dashing && an.i > 4) { an.i = 4; an.t = 0; }
    if (P.artT > (P.artCharged ? 0.54 : 0.42)) { P.artGo = false; setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); }
  } else if (id === 'stormleap') {
    grav(); P.vx = approach(P.vx, inputX() * MAXV * 0.5, 400 * dt);
    if (P.artT > 0.15 && P.ground && !P.artFired) {
      P.artFired = true; shake = 9; sfx.boom(); hitstop = 0.08;
      spawnFx(fxOr('stormleap', 'shockwave'), P.x, P.y, 1, null, { bottom: true });
      const cr = P.artCharged ? 92 : 62, r = rect(P.x - cr, P.y - 34, P.x + cr, P.y + 2);   // charged: wider, harder shockwave
      if (P.artCharged) { spawnFx('ground_crack', P.x - 34, P.y, -1); spawnFx('ground_crack', P.x + 34, P.y, 1); spawnFx('shockwave', P.x, P.y, 1, null, { speed: 0.7 }); flashScreen = Math.max(flashScreen, 0.12); }
      for (const t of targets()) { const hb = t.hurtbox(); if (hb && overlap(r, hb)) t.hit({ dmg: outgoing(D.heavy, P.artCharged ? 3.4 : 2.4, 'melee'), poise: P.artCharged ? 140 : 90, dir: t.x > P.x ? 1 : -1, kind: 'heavy', x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2, melee: true, big: true }); }
      for (let i = 0; i < 24; i++) particles.push({ x: P.x + rand(-50, 50), y: P.y - rand(0, 6), vx: rand(-90, 90), vy: -rand(30, 120), g: 300, life: rand(0.4, 0.9), kind: 'dust' });
      setP('art', 'land', false); P.artT = 1;
    }
    if (P.artFired && P.anim.done) setP('idle', 'idle', true);
    if (P.artT > 2.5) setP('idle', 'idle', true);
  } else {   // warcry / cinderblade
    P.vx = approach(P.vx, 0, 900 * dt); grav();
    if (!P.artFired && an.i >= P.artRel) {
      P.artFired = true;
      if (id === 'warcry') {
        P.cryT = P.artCharged ? 20 : 12; P.cryBig = P.artCharged; sfx.roar(); shake = P.artCharged ? 7 : 4; spawnFx(fxOr('warcry', 'roar_ring'), P.x, P.y - 16, 1);
        if (P.artCharged) { P.st = D.maxSt; spawnFx(fxOr('roar_ring', 'shockwave'), P.x, P.y - 16, 1, null, { speed: 0.7 }); }   // charged: longer, fiercer, second wind
      } else {
        P.fireT = P.artCharged ? 32 : 20; sfx.fire(); spawnFx(fxOr('cinderblade', 'hit'), P.x + P.face * 12, P.y - 18, P.face);
        if (P.artCharged) {   // charged: the blade flares, a ring of fire bursts off it
          spawnFx(fxOr('flame_ring', 'shockwave'), P.x, P.y, 1, null, { bottom: true }); shake = 5;
          const r = rect(P.x - 46, P.y - 36, P.x + 46, P.y + 2);
          for (const t of targets()) { const hb = t.hurtbox(); if (hb && overlap(r, hb)) t.hit({ dmg: outgoing(D.light, 1.3, 'melee'), poise: 30, dir: t.x > P.x ? 1 : -1, kind: 'heavy', x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2, big: true, fire: true, melee: true }); }
          for (let i = 0; i < 26; i++) particles.push({ x: P.x + rand(-36, 36), y: P.y - rand(0, 10), vx: rand(-30, 30), vy: -rand(40, 140), life: rand(0.4, 0.9), kind: 'fire' });
        }
      }
    }
    if (an.done) setP('idle', 'idle', true);
  }
}

// Storm Leap with its own animation: crouch, launch on frame 2, hold the plunge frame until landing, impact frame
function updateStormleap(dt, grav) {
  const an = P.anim, land = P.artRel || 9;
  if (!P.artLaunched) {
    P.vx = approach(P.vx, 0, 900 * dt); grav();
    if (an.i >= 2) { P.artLaunched = true; P.vy = P.artCharged ? -370 : -310; P.ground = false; P.vx = P.face * 40; sfx.jump(); spawnFx('dust', P.x, P.y, P.face); }
    return;
  }
  if (!P.artFired) {
    grav(); P.vx = approach(P.vx, inputX() * MAXV * 0.5, 400 * dt);
    if (an.i >= land - 1 && !P.ground) { an.i = land - 1; an.t = 0; P.vy = Math.max(P.vy, 260); }   // plunge until we touch down
    if (P.ground && P.artT > 0.2) {
      an.i = land; an.t = 0; an.changed = true;
      P.artFired = true; shake = 9; sfx.boom(); hitstop = 0.08;
      spawnFx(fxOr('stormleap', 'shockwave'), P.x, P.y, 1, null, { bottom: true });
      const cr = P.artCharged ? 92 : 62, r = rect(P.x - cr, P.y - 34, P.x + cr, P.y + 2);   // charged: wider, harder shockwave
      if (P.artCharged) { spawnFx('ground_crack', P.x - 34, P.y, -1); spawnFx('ground_crack', P.x + 34, P.y, 1); spawnFx('shockwave', P.x, P.y, 1, null, { speed: 0.7 }); flashScreen = Math.max(flashScreen, 0.12); }
      for (const t of targets()) { const hb = t.hurtbox(); if (hb && overlap(r, hb)) t.hit({ dmg: outgoing(D.heavy, P.artCharged ? 3.4 : 2.4, 'melee'), poise: P.artCharged ? 140 : 90, dir: t.x > P.x ? 1 : -1, kind: 'heavy', x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2, melee: true, big: true }); }
      for (let i = 0; i < 24; i++) particles.push({ x: P.x + rand(-50, 50), y: P.y - rand(0, 6), vx: rand(-90, 90), vy: -rand(30, 120), g: 300, life: rand(0.4, 0.9), kind: 'dust' });
    }
    if (P.artT > 3) { P.artLaunched = false; setP('idle', 'idle', true); }
    return;
  }
  P.vx = approach(P.vx, 0, 900 * dt); grav();
  if (an.done) { P.artLaunched = false; setP('idle', 'idle', true); }
}
