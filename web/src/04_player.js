// ------------------------------------------------------------------ player
// attack table: active = frame indices within the tag; reach/ys = hitbox relative to feet (facing right)
const ATK = {
  attack1: { active: [2, 3], mult: 1.0, poise: 12, reach: [-2, 36], ys: [-36, -2], cost: 12, fx: 'slash', fxAt: [18, -17], lunge: 55, speed: 1.15, kind: 'light' },
  attack2: { active: [2, 3], mult: 1.05, poise: 12, reach: [-2, 36], ys: [-40, -2], cost: 12, fx: 'slash2', fxAt: [18, -20], lunge: 55, speed: 1.15, kind: 'light' },
  attack3: { active: [2, 3], mult: 1.4, poise: 22, reach: [4, 48], ys: [-26, -6], cost: 16, fx: 'slash3', fxAt: [24, -17], lunge: 150, speed: 1.05, kind: 'light' },
  attack4: { anim: 'riposte', active: [3, 4], mult: 1.7, poise: 30, reach: [-4, 46], ys: [-34, -2], cost: 18, fx: 'heavy', fxAt: [20, -18], lunge: 120, speed: 1.35, kind: 'light' },
  heavy: { active: [4, 5], mult: 1.0, poise: 45, reach: [-2, 42], ys: [-42, 0], cost: 28, fx: 'heavy', fxAt: [18, -17], lunge: 70, speed: 1, kind: 'heavy' },
  attack_up: { active: [2, 3], mult: 1.0, poise: 12, reach: [-18, 18], ys: [-60, -16], cost: 12, fx: 'slash_up', fxAt: [0, -26], lunge: 0, speed: 1.15, kind: 'light', up: true },
  attack_down: { active: [1, 3], mult: 1.0, poise: 12, reach: [-8, 8], ys: [-8, 22], cost: 10, fx: null, lunge: 0, speed: 1.1, kind: 'light', down: true },
  air_attack: { active: [1, 2], mult: 1.0, poise: 12, reach: [-2, 36], ys: [-36, -4], cost: 12, fx: 'slash_air', fxAt: [18, -18], lunge: 0, speed: 1.15, kind: 'light' },
};
// ---- per-weapon movesets: class animations authored in gen_player.py, hitboxes from assets/player_meta.json
const WEAPON_CLASS = { longsword: 'sword', oathbrand: 'sword', kalden: 'sword', dagger: 'dagger', greatsword: 'great', maul: 'great', spear: 'spear', katana: 'katana',
  gravetusk: 'great', omen: 'sword', rotmaw: 'great', scepter: 'spear',
  // v8 expansion (data in 13_weapons.js)
  frostbrand: 'sword', pagecutter: 'dagger', colossus_hammer: 'great', glacier_maul: 'great', bell_hammer: 'great', forge_cleaver: 'great',
  stormfang: 'spear', stormvein: 'katana', quarterstaff: 'staff', windstaff: 'staff', inkquill: 'staff', lantern_staff: 'staff',
  knight_shield: 'shield', twinborne: 'shield', overseer_bulwark: 'shield', twinfangs: 'twin', first_ember: 'mirror' };
const MOVESETS = {
  sword: { combo: ['attack1', 'attack2', 'attack3'], extra: 'attack4', heavy: 'heavy' },
  dagger: { combo: ['dg_1', 'dg_2', 'dg_3', 'dg_4'], extra: 'dg_2', heavy: 'dg_heavy' },
  great: { combo: ['gs_1', 'gs_2', 'gs_3'], extra: 'gs_1', heavy: 'gs_heavy' },
  spear: { combo: ['sp_1', 'sp_2', 'sp_3'], extra: 'sp_1', heavy: 'sp_heavy' },
  katana: { combo: ['kt_1', 'kt_2', 'kt_3'], extra: 'kt_1', heavy: 'kt_heavy' },
  staff: { combo: ['st_1', 'st_2', 'st_3', 'st_4'], extra: 'st_2', heavy: 'st_heavy' },
  shield: { combo: ['sh_1', 'sh_2', 'sh_3'], extra: 'sh_1', heavy: 'sh_heavy' },
  twin: { combo: ['tw_1', 'tw_2', 'tw_3', 'tw_4', 'tw_5'], extra: 'tw_2', heavy: 'tw_heavy' },
};
const CLASS_TUNING = {   // per-class feel: damage mults along the combo, poise, stamina, lunge, fx
  dagger: { mult: [0.8, 0.8, 0.85, 1.25], poise: 7, cost: 7, lunge: 45, fx: ['slash', 'slash2', 'slash', 'slash3'], heavy: { mult: 1.3, poise: 25, cost: 16, lunge: 160, fx: 'slash3' } },
  great: { mult: [1.0, 1.05, 1.4], poise: 32, cost: 22, lunge: 40, fx: ['heavy', 'slash_up', 'slash3'], heavy: { mult: 1.25, poise: 70, cost: 34, lunge: 30, fx: 'heavy', slam: true } },
  spear: { mult: [0.95, 1.0, 1.3], poise: 14, cost: 13, lunge: 80, fx: ['slash_air', 'slash_air', 'slash3'], heavy: { mult: 1.15, poise: 45, cost: 26, lunge: 230, fx: 'slash_air' } },
  katana: { mult: [1.0, 1.0, 1.35], poise: 12, cost: 12, lunge: 60, fx: ['slash2', 'slash', 'slash3'], heavy: { mult: 1.35, poise: 45, cost: 26, lunge: 200, fx: 'slash3' } },
  // v8: staff hits ~75-80% of the spear's, faster; its heavy is an instant 360-degree spin paid with 80% of max stamina
  staff: { mult: [0.74, 0.76, 0.8, 1.02], poise: 12, cost: 11, lunge: 60, fx: ['slash_air', null, 'slash', 'heavy'],
           heavy: { mult: 1.2, poise: 95, cost: 0, lunge: 20, fx: null, staffSpin: true, noCharge: true, spin: true } },
  shield: { mult: [0.92, 0.96, 1.3], poise: 12, cost: 10, lunge: 50, fx: ['slash', 'slash2', 'slash_air'],
            heavy: { mult: 0.85, poise: 110, cost: 26, lunge: 210, fx: null, bash: true } },
  twin: { mult: [0.7, 0.7, 0.78, 0.85, 1.15], poise: 8, cost: 7, lunge: 50, fx: ['slash', 'slash2', 'slash_up', 'slash', 'slash3'],
          heavy: { mult: 1.5, poise: 40, cost: 24, lunge: 300, fx: 'slash3' } },
};
// v8 techniques (any class): guard counter, shield counter, backstep strike (hitboxes from player_meta too)
const TECH_ATK = {
  counter: { mult: 1.7, poise: 40, cost: 10, lunge: 90, fx: 'slash_up', counter: true },
  sh_counter: { mult: 1.9, poise: 45, cost: 10, lunge: 130, fx: 'slash_air', counter: true },
  backstep: { mult: 1.5, poise: 30, cost: 14, lunge: 250, fx: 'slash3' },
};
const PLUNGE_A = { active: [0, 0], mult: 1, poise: 70, reach: [-26, 40], ys: [-30, 0], cost: 18, fx: null, fxAt: [22, -6], lunge: 0, speed: 1, kind: 'heavy', cls: 'tech', big: true, plunge: true };
(function buildMovesets() {
  const PM = (typeof ASSETS !== 'undefined' && ASSETS.player_meta && ASSETS.player_meta.moves) || {};
  const pad = h => { if (!h) return h; let [x0, y0, x1, y1] = h; if (y1 - y0 < 18) { const c = (y0 + y1) / 2; y0 = Math.min(y0, c - 9); y1 = Math.min(2, Math.max(y1, c + 9)); } return [Math.min(x0, x1 - 14), y0, x1, y1]; };
  for (const k of Object.keys(PM)) PM[k].hit = pad(PM[k].hit);
  for (const [cls, set] of Object.entries(MOVESETS)) {
    if (cls === 'sword') continue;
    const T = CLASS_TUNING[cls];
    set.combo.forEach((tag, i) => {
      const m = PM[tag] || {};
      ATK[tag] = { active: m.active || [2, 3], mult: T.mult[i], poise: T.poise, reach: m.hit ? [m.hit[0], m.hit[2]] : [-2, 36], ys: m.hit ? [m.hit[1], m.hit[3]] : [-36, -2],
                   cost: T.cost, fx: T.fx[i], fxAt: m.fxAt || [18, -17], lunge: T.lunge, speed: 1, kind: 'light', cls, big: i === set.combo.length - 1 || cls === 'great' };
    });
    const m = PM[set.heavy] || {}, Hh = T.heavy;
    ATK[set.heavy] = { active: m.active || [4, 5], mult: Hh.mult, poise: Hh.poise, reach: m.hit ? [m.hit[0], m.hit[2]] : [-2, 42], ys: m.hit ? [m.hit[1], m.hit[3]] : [-42, 0],
                       cost: Hh.cost, fx: Hh.fx, fxAt: m.fxAt || [18, -17], lunge: Hh.lunge, speed: 1, kind: 'heavy', cls, slam: Hh.slam, big: true,
                       staffSpin: Hh.staffSpin, noCharge: Hh.noCharge, spin: Hh.spin, bash: Hh.bash };
  }
  for (const [tag, T] of Object.entries(TECH_ATK)) {
    const m = PM[tag] || {};
    ATK[tag] = { active: m.active || [1, 2], mult: T.mult, poise: T.poise, reach: m.hit ? [m.hit[0], m.hit[2]] : [-2, 40], ys: m.hit ? [m.hit[1], m.hit[3]] : [-38, -2],
                 cost: T.cost, fx: T.fx, fxAt: m.fxAt || [18, -17], lunge: T.lunge, speed: 1, kind: 'light', cls: 'tech', big: true, counter: T.counter };
  }
  const pl = PM.plunge_land || {};   // plunging attack impact box (used by the plunge logic, not a state of its own)
  PLUNGE_A.reach = pl.hit ? [pl.hit[0], pl.hit[2]] : [-26, 40]; PLUNGE_A.ys = pl.hit ? [pl.hit[1], pl.hit[3]] : [-30, 0];
})();
// the mirror weapon (First Ember) borrows the class of the last non-mirror weapon you fought with
function wcls() {
  const c = WEAPON_CLASS[SAVE.weapon] || 'sword';
  if (c !== 'mirror') return c;
  const l = SAVE.lastCls; return l && l !== 'mirror' && MOVESETS[l] ? l : 'sword';
}
function moveset() {
  const cls = wcls(), set = MOVESETS[cls];
  // fall back to the sword animations if this class's frames aren't in the sheet yet
  if (cls !== 'sword' && !(pHas(set.combo[0]) && ATK[set.combo[0]])) return MOVESETS.sword;
  return set;
}
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
  if (st === 'idle' && tag === 'idle' && P.shArmed && pHas('sh_rest') && wcls() === 'shield') { P.shArmed = false; P.state = 'idle'; P.anim.set('sh_rest', false, 1); return; }
  P.shArmed = (SH_ARMED.has(st) || (ATK[st] && ATK[st].cls === 'shield')) ? true : (st === 'idle' ? P.shArmed : false);
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
  if (P.state !== 'roll') return false;
  return P.anim.i >= 1 && P.anim.i <= 6 + (has('quickstep') ? 1 : 0) + (charmOn('c_heel') ? 1 : 0);
}

function startAttack(name) {
  const A = ATK[name];
  let cost = A.staffSpin ? staffSpinCost() : A.cost * D.W.stam;
  if (A.kind === 'heavy' && charmOn('c_brand') && !A.staffSpin) cost *= 0.8;   // Brand of the Forge: heavies cost 20% less
  spend(cost); P.comboStep = -1; P.counterMul = 1; P.hitSet = new Set(); P.charge = 0; P.charged = false; P.pogoed = false;
  const tag = A.anim || name;
  setP(name, pHas(tag) ? tag : 'attack1', false, A.speed * (A.kind === 'light' ? D.castSpeed : 1) * (A.cls ? 1 : D.W.speed));
}
function staffSpinCost() { return D.maxSt * 0.8 * (charmOn('c_brand') ? 0.8 : 1); }
function startHeavy() {
  const A = ATK[moveset().heavy];
  if (A && A.staffSpin && P.st < staffSpinCost() - 0.5) { sfx.deny(); P.denyT = 0.5; toast('The spin needs 80% of your stamina', 1.4); return false; }
  startAttack(moveset().heavy); return true;
}
// guard counter: attack right after a clean parry / block. Katana: +40% and quicker.
function startCounter() {
  const cls = wcls(), tag = cls === 'shield' && pHas('sh_counter') ? 'sh_counter' : 'counter';
  if (!ATK[tag] || !pHas(tag)) return false;
  startAttack(tag); P.gcT = 0;
  P.counterMul = cls === 'katana' ? 1.4 : 1; if (cls === 'katana') P.anim.speed *= 1.3;
  sfx.glint(); spawnFx(fxOr('parry_flash', 'parry_spark'), P.x + P.face * 10, P.y - 18, P.face, null, { alpha: 0.6 });
  return true;
}
// dagger backstab: slip behind a foe that isn't facing you and open it up
function backstabTarget() {
  if (wcls() !== 'dagger' || !P.ground) return null;
  for (const t of enemies) {
    if (!t.alive || t.boss || !t.breakStance || (t.cfg && t.cfg.flying) || t.state === 'stagger' || t.state === 'parried') continue;
    const dx = t.x - P.x, sd = dx < 0 ? -1 : 1;
    if (Math.abs(dx) < 26 && Math.abs(t.y - P.y) < 20 && t.face === sd && P.face === sd) return t;
  }
  return null;
}
function tryRiposte() {
  const bs = backstabTarget();
  if (bs) { bs.breakStance(); P.backstab = true; }
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
  if (P.fp < cost) { sfx.deny(); toast('Not enough FP'); return; }
  P.fp -= cost; P.spellFired = false; P.castId = id;
  setP('cast', pHas('cast') ? 'cast' : 'heal', false, D.castSpeed * (id === 'emberburst' ? 0.9 : 1.1));
  sfx.charge();
}

function updatePlayer(dt) {
  const ax = inputX();
  P.inv = Math.max(0, P.inv - dt); P.flash = Math.max(0, P.flash - dt * 6); P.ctrlLock -= dt; P.drop -= dt; P.empower -= dt; P.parryWin -= dt;
  if (P.state === 'dead') {
    P.anim.update(dt); P.vx *= Math.pow(0.01, dt); P.vy = Math.min(P.vy + GRAV_DN * dt, FALL_MAX); moveBody(P, dt);
    if (P.deadT > 0 && (P.deadT -= dt) <= 0) onPlayerDeath();
    return;
  }
  if (P.state === 'rest') { P.anim.update(dt); if (P.anim.done) P.anim.hold(); P.vx = 0; return; }
  P.coyote = P.ground ? 0.12 : P.coyote - dt;
  if (P.ground) { P.airJumps = SAVE.items.wings ? 1 : 0; P.airDash = true; }
  if (peek('interact') && free() && P.ground) { if (interactNearby()) take('interact'); }

  // ---- action starts (buffered inputs)
  const canStart = free() || (P.state === 'land' && P.anim.i >= 1);
  if (canStart && traversalStart(ax)) { /* technique started */ }
  else if (canStart) {
    if (peek('roll') && P.st > 0 && (P.ground || P.coyote > 0 || P.airDash)) { take('roll'); doRoll(ax); }
    else if (peek('jump')) {
      if (P.ground && held.has('down') && onPlatform()) { take('jump'); P.drop = 0.25; P.y += 2; P.ground = false; setP('air', 'jump_fall'); }
      else if (P.ground || P.coyote > 0) { take('jump'); doJump(JUMP_V); }
      else if (P.state === 'wall') { take('jump'); wallJump(); }
      else if (P.airJumps > 0) { take('jump'); P.airJumps--; doJump(JUMP_V * 0.9, true); }
    }
    else if (peek('attack') && tryRiposte()) take('attack');
    else if (peek('attack') && P.gcT > 0 && P.ground && P.st > 0 && startCounter()) take('attack');
    else if (peek('attack') && P.bsT > 0 && P.backRoll && P.ground && P.st > 0) { take('attack'); startBackstep(); }
    else if (peek('heavy') && P.st > 0 && P.ground) { take('heavy'); if (ax) P.face = ax; startHeavy(); }
    else if (peek('heavy') && P.st > 0 && !P.ground && P.state !== 'wall' && pHas('plunge')) { take('heavy'); if (ax) P.face = ax; startPlunge(); }
    else if (peek('attack') && P.st > 0) {
      take('attack'); if (ax) P.face = ax;
      if (held.has('up')) startAttack('attack_up');
      else if (!P.ground && held.has('down')) startAttack('attack_down');
      else if (!P.ground && P.vy < -30 && wcls() === 'spear' && pHas('sp_jump')) startSpDive();
      else if (!P.ground) startAttack('air_attack');
      else { P.combo = 1; startAttack(moveset().combo[0]); P.comboStep = 0; }
    }
    else if (peek('parry') && P.ground && P.st > 0) { take('parry'); startParry(); }
    else if (peek('art')) { take('art'); startArt(); }
    else if (peek('cast')) { take('cast'); startCast(); }
    else if (peek('heal') && P.ground) { take('heal'); if (P.flasksR > 0) { P.flasksR--; setP('heal', 'heal'); P.healPending = 1; } else { sfx.deny(); toast('Your crimson flasks are empty'); } }
    else if (peek('mana') && P.ground) { take('mana'); if (P.flasksB > 0) { P.flasksB--; setP('heal', 'heal'); P.healPending = 2; } else { sfx.deny(); toast('Your azure flasks are empty'); } }
  }

  // apex hang: holding jump near the top of an arc softens gravity for a smoother, floatier peak
  const grav = () => { const apex = !P.ground && P.state === 'air' && Math.abs(P.vy) < 55 && held.has('jump'); P.vy = Math.min(P.vy + (P.vy > 0 ? GRAV_DN : GRAV_UP) * (apex ? 0.55 : 1) * dt, FALL_MAX); };
  const tv = traversalUpdate(dt);
  if (tv === 'skip-physics') { P.anim.update(dt); P.stDelay -= dt; if (P.stDelay <= 0) P.st = Math.min(D.maxSt, P.st + 40 * dt); return; }
  if (!tv) switch (ATK[P.state] ? 'ATTACK' : P.state) {
    case 'idle': case 'run': case 'land': {
      const target = ax * MAXV;
      const acc = (ax ? (Math.sign(target) !== Math.sign(P.vx) && P.vx ? 2200 : 1150) : 1600) * (P.fric ?? 1);   // fric < 1 on ice
      P.vx = approach(P.vx, target, acc * dt);
      if (ax) P.face = ax;
      grav();
      if (P.state === 'land') { if (P.anim.done || ax) { const m = Math.abs(P.vx) > 5 || ax ? 'run' : 'idle'; setP(m, m, true); } }
      else {
        const want = (ax || Math.abs(P.vx) > 20) ? 'run' : 'idle';
        if (P.state !== want) setP(want, want, true);
        else if (P.anim.tag === 'sh_rest' && P.anim.done) P.anim.set('idle', true);
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
      P.vy = Math.min(P.vy + 600 * dt, 55); P.vx = P.wallDir * 10;
      if (Math.random() < 0.25) spawnFx('wall_dust', P.x + P.wallDir * 6, P.y - 8, P.face);
      if (!wallAt(P, P.wallDir) || (ax && ax !== P.wallDir) || P.ground) { P.wallDir = 0; setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); }
      break;
    }
    case 'roll': {
      const dashing = P.anim.i <= 6;
      if (dashing) P.vx = P.face * (charmOn('c_heel') ? 250 : 225); else P.vx = approach(P.vx, inputX() * MAXV, 900 * dt);
      if (P.airRoll && dashing) P.vy = 0; else grav();
      P.ghostT -= dt;
      if (P.ghostT <= 0 && dashing) { P.ghostT = 0.035; ghosts.push({ f: P.anim.frame, x: P.x, y: P.y, face: P.face, life: 0.22 }); }
      if (P.anim.i >= 6 && P.ground && peek('jump')) { take('jump'); doJump(JUMP_V); break; }
      if (P.backRoll && P.anim.i >= 5 && P.ground && P.st > 0 && peek('attack') && pHas('backstep')) { take('attack'); startBackstep(); break; }
      if (P.anim.i >= 7 && P.ground && take('attack')) { const ms = moveset(); P.combo = ms.combo.length; startAttack(ms.combo[ms.combo.length - 1]); break; }
      if (P.anim.done) { if (P.backRoll) P.bsT = 0.35; setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); }
      break;
    }
    case 'ATTACK': {
      const A = ATK[P.state], an = P.anim;
      if (A.kind === 'heavy' && !A.noCharge && an.i === (A.cls ? Math.max(1, A.active[0] - 2) : 2) && held.has('heavy') && P.charge < chargeTime()) {
        P.charge += dt; an.t = Math.min(an.t, 10); P.vx *= 0.8;
        if (Math.random() < 0.5) particles.push({ x: P.x + rand(-10, 10), y: P.y - rand(0, 30), vx: 0, vy: -rand(20, 50), life: 0.4, kind: 'gold' });
        if (P.charge >= chargeTime() && !P.charged) { P.charged = true; sfx.glint(); spawnFx('telegraph', P.x - P.face * 2, P.y - 36, P.face); }
      }
      if (an.changed && an.i === A.active[0]) {
        if (A.lunge) P.vx = P.face * A.lunge;
        const sig = SIGS[SAVE.weapon];
        if (sig && sig.swing) sig.swing(A, sigRect(A));
        if (sig && sig.finisher && (A.kind === 'heavy' || isFinisher(P.state))) sig.finisher(A, sigRect(A));
        if (!(sig && sig.replaceFx) && A.fx) spawnFx(fxOr(A.fx, 'slash'), P.x + P.face * A.fxAt[0], P.y + A.fxAt[1], P.face, null, A.up ? { bottom: true } : {});
        (A.kind === 'heavy' || A.big || P.state === 'attack3' || P.state === 'attack4' ? sfx.heavySwing : sfx.swing)();
        if (A.kind === 'heavy' && P.charged && has('charged_arts')) fireProjectile('crescent');
        if (A.slam) { shake = 7; sfx.boom(); spawnFx('shockwave', P.x + P.face * 22, P.y, 1); spawnFx('ground_crack', P.x + P.face * 22, P.y, 1); for (let i = 0; i < 14; i++) particles.push({ x: P.x + P.face * 22 + rand(-16, 16), y: P.y - 2, vx: rand(-80, 80), vy: -rand(30, 110), g: 320, life: 0.6, kind: 'dust' }); }
      }
      if (P.ground) { P.vx *= Math.pow(0.0008, dt); grav(); }
      else if (P.state === 'attack_down') { P.vx = approach(P.vx, ax * MAXV * 0.6, 500 * dt); grav(); }
      else { P.vx = approach(P.vx, ax * MAXV * 0.8, 500 * dt); grav(); }
      if (an.i >= A.active[0] && an.i <= A.active[1]) { playerStrike(A); const sg = SIGS[SAVE.weapon]; if (sg) sigTrail(A, sg); }
      if (an.i > A.active[1]) {   // recovery: chain combo or roll-cancel
        const ms = moveset(), seq = has('fourth_strike') ? [...ms.combo, ms.extra] : ms.combo;
        if (P.comboStep >= 0 && P.comboStep + 1 < seq.length && P.ground && take('attack', 330) && P.st > 0) {
          const step = P.comboStep + 1; P.combo++; if (ax) P.face = ax; startAttack(seq[step]); P.comboStep = step; break;
        }
        if (peek('roll') && P.st > 0) { take('roll'); doRoll(ax); break; }
        if (!P.ground && peek('jump') && P.airJumps > 0) { take('jump'); P.airJumps--; doJump(JUMP_V * 0.9, true); break; }
      }
      if (an.done || (!P.ground && !['air_attack', 'attack_down', 'attack_up'].includes(P.state) && P.vy > 60)) {
        P.combo = 0; setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground);
      }
      break;
    }
    case 'riposte': {
      P.vx = P.anim.i >= 2 && P.anim.i <= 3 ? P.face * 60 : P.vx * 0.8; grav();
      if (P.anim.changed && P.anim.i === 3 && P.crit) critHit(P.crit);
      if (P.anim.done) { P.crit = null; setP('idle', 'idle', true); }
      break;
    }
    case 'parry':
      P.vx = approach(P.vx, 0, 900 * dt); grav();
      if (P.parried && peek('attack', 400) && P.st > 0) { take('attack', 400); if (!tryRiposte()) startCounter(); break; }
      if (P.shieldParry && held.has('parry') && P.anim.i >= 2) { setP('guard', 'sh_guard', true); break; }
      if (P.anim.done) setP('idle', 'idle', true);
      break;
    case 'guard': case 'block': updateGuard(dt, ax, grav); break;
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
      P.vx = approach(P.vx, 0, 900 * dt); grav();
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
  }

  // ---- physics
  const wasAir = !P.ground, fallV = P.vy, preState = P.state;
  { const pv = P.pushVx || 0; P.vx += pv; moveBody(P, dt); if (P.vx) P.vx -= pv; P.pushVx = 0; }   // pushVx: wind/conveyors (set by hooks each frame)
  if (P.ground && wasAir) {
    spawnFx('dust', P.x, P.y, P.face); if (fallV > 150) sfx.land();
    P.dj = false;
    if (preState === 'slam') traversalAfterMove('slam');
    else if (P.state === 'air' || P.state === 'wall' || P.state === 'glide') setP('land', pHas('land') ? 'land' : 'idle', false);
    if (P.state === 'air_attack' || P.state === 'attack_down') { P.combo = 0; setP('land', 'land', false); }
    if (preState === 'plunge' && P.state === 'plunge' && P.anim.tag !== 'plunge_land') plungeImpact(false);
    if (preState === 'spdive' && P.state === 'spdive') { setP('land', 'land', false); shake = Math.max(shake, 3); sfx.land(); spawnFx('dust', P.x + P.face * 10, P.y, P.face); }
  }
  traversalAfterMove(null);
  if (spikeHit(P)) spikeHurt();
  // remember safe ground for spike respawns
  P.safeT -= dt;
  if (P.ground && P.safeT <= 0 && !nearSpikes()) { P.safe = { x: P.x, y: P.y }; P.safeT = 0.25; }

  P.stDelay -= dt;
  if (P.stDelay <= 0 && P.state !== 'roll' && !ATK[P.state])
    P.st = Math.min(D.maxSt, P.st + (P.state === 'idle' ? 70 : 58) * dt * (P.state === 'guard' || P.state === 'block' ? 0.35 : 1));
  P.gcT -= dt; P.bsT -= dt; P.denyT = (P.denyT || 0) - dt;
  if (P.bsT <= 0 && P.state !== 'roll') P.backRoll = 0;
  { const c = WEAPON_CLASS[SAVE.weapon]; if (c && c !== 'mirror') SAVE.lastCls = c; }   // the mirror weapon copies this
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
function onPlatform() { return tileAt(Math.floor(P.x / TILE), Math.floor((P.y + 1) / TILE)) === T_PLAT; }
function nearSpikes() {
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
function doRoll(ax) {
  P.backRoll = P.ground && ax && ax === -P.face ? P.face : 0; P.bsT = 0;   // rolling away from where you faced: backstep strike ready
  spend(has('quickstep') ? 14 : 20); if (ax) P.face = ax; P.combo = 0; P.sw = false;
  P.airRoll = !P.ground; if (P.airRoll) P.airDash = false;
  setP('roll', P.airRoll && SAVE.items.emberdash && pHas('ember_dash') ? 'ember_dash' : 'roll'); P.vx = P.face * 225; sfx.roll(); P.ghostT = 0;
  if (P.ground) spawnFx('dust', P.x - P.face * 6, P.y, P.face);
}

// ---- v8 techniques: parry / shield guard, backstep strike, plunging attack, spear jump thrust
function startParry() {
  spend(10); P.parried = false;
  P.shieldParry = wcls() === 'shield' && pHas('sh_parry');
  setP('parry', P.shieldParry ? 'sh_parry' : pHas('parry') ? 'parry' : 'hurt', false, 1);
  P.parryWin = (has('riposte_mastery') ? 0.24 : 0.17) * (charmOn('c_thorn') ? 1.5 : 1) * (P.shieldParry ? 1.6 : 1);   // shield: wider window
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
    P.combo = 1; startAttack(moveset().combo[0]); P.comboStep = 0; return;
  }
  if (peek('heavy') && P.st > 0) { take('heavy'); if (ax) P.face = ax; startHeavy(); return; }
  if (peek('roll') && P.st > 0) { take('roll'); doRoll(ax); return; }
  if (P.state === 'guard' && !held.has('parry')) { setP('idle', 'idle', true); return; }
  if (ax && P.state === 'guard') P.face = ax;   // turn in place behind the shield
}
function isBlocking() { return P.state === 'guard' || P.state === 'block' || (P.state === 'parry' && P.shieldParry && P.anim.i <= 3); }
function startBackstep() {
  if (!pHas('backstep')) return;
  P.face = P.backRoll || P.face; P.backRoll = 0; P.bsT = 0;
  startAttack('backstep'); P.vx = P.face * 60;
  spawnFx('dust', P.x - P.face * 6, P.y, P.face);
}
function startPlunge() {
  spend(18 * D.W.stam * (charmOn('c_brand') ? 0.8 : 1)); P.hitSet = new Set(); P.plungeT = 0; P.charge = 0; P.charged = false; P.combo = 0;
  setP('plunge', 'plunge', false, 1); P.vy = Math.min(P.vy, -70); sfx.heavySwing();
}
function updatePlunge(dt, ax, grav) {
  const an = P.anim; P.plungeT += dt;
  if (an.tag === 'plunge') {   // heave overhead: hang for a beat
    P.vx *= Math.pow(0.05, dt); P.vy = Math.min(P.vy + 420 * dt, 30);
    if (an.done) { an.set('plunge_fall', true); P.vy = 330; sfx.swing(); }
  } else if (an.tag === 'plunge_fall') {
    P.vy = Math.min(P.vy + 1100 * dt, 540); P.vx = approach(P.vx, ax * 45, 500 * dt);
    if (Math.random() < 0.7) particles.push({ x: P.x + P.face * rand(4, 14), y: P.y - rand(0, 20), vx: 0, vy: -rand(40, 90), life: 0.25, kind: SIGS[SAVE.weapon] ? SIGS[SAVE.weapon].pk : 'spark' });
    const r = rect(P.x - 4 + P.face * 2, P.y - 10, P.x + P.face * 26, P.y + 12);   // the blade leads the fall
    for (const t of targets()) { const hb = hbOf(t); if (hb && overlap(r, hb) && !t.prop) { plungeImpact(true); return; } }
    if (P.plungeT > 3) setP('air', 'jump_fall');
  } else {   // plunge_land
    P.vx = approach(P.vx, 0, 900 * dt); grav();
    if (an.done) setP('idle', 'idle', true);
  }
}
// the plunge lands (on the floor, or on a foe mid-fall): heavy AoE, bounce off whatever it struck
function plungeImpact(midair) {
  const fall = Math.min(1.5, 1 + P.plungeT * 0.45), A = PLUNGE_A, W = D.W;
  const r = rect(P.x + P.face * A.reach[0], P.y + A.ys[0] - 4, P.x + P.face * A.reach[1], P.y + A.ys[1] + (midair ? 34 : 6));   // mid-air: reach down onto the foe
  shake = Math.max(shake, 8); sfx.boom(); hitstop = Math.max(hitstop, 0.07);
  spawnFx('shockwave', P.x + P.face * 14, P.y + (midair ? 0 : 0), 1);
  if (!midair) spawnFx('ground_crack', P.x + P.face * 14, P.y, 1);
  for (let i = 0; i < 18; i++) particles.push({ x: P.x + P.face * 14 + rand(-22, 22), y: P.y - 2, vx: rand(-90, 90), vy: -rand(30, 130), g: 320, life: 0.6, kind: 'dust' });
  let n = 0;
  const sig = SIGS[SAVE.weapon];
  if (sig && sig.finisher) sig.finisher(A, r);
  for (const t of targets()) {
    const hb = hbOf(t); if (!hb || !overlap(r, hb)) continue;
    const dmg = outgoing(D.heavy * 2.0, 1.2 * fall, 'melee') * (P.twinBuff ? 1.25 : 1), fire = P.fireT > 0 || !!W.fire;
    const info = { dmg: dmg * (fire && W.fire ? 1 + W.fire : 1), poise: A.poise * W.poise, dir: t.x > P.x ? 1 : -1, kind: 'heavy', charged: false, bleed: bleedAmt(true), fire, rotDot: !!W.rot,
                   x: clamp(P.x + P.face * 14, hb.x0 + 3, hb.x1 - 3), y: clamp(P.y - 12, hb.y0, hb.y1), melee: true, big: true };
    t.hit(info); n++;
    runHooks('strike', t, { dmg, heavy: true, x: info.x, y: info.y }, A);
    if (sig && sig.hit) sig.hit(t, info, A);
  }
  if (n) P.twinBuff = false;
  hitBreakables(r);
  if (n || midair) { P.vy = -250; P.ground = false; P.vx = -P.face * 40; setP('air', 'jump_up'); P.airDash = true; }   // bounce off
  else setP('plunge', 'plunge_land', false);
}
function startSpDive() {
  spend(14 * D.W.stam); P.hitSet = new Set(); P.diveT = 0;
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
  const W = D.W, sig = SIGS[SAVE.weapon];
  for (const t of targets()) {
    if (P.hitSet.has(t)) continue;
    const hb = hbOf(t); if (!hb || !overlap(r, hb)) continue;
    P.hitSet.add(t);
    const dmg = outgoing(D.light, 1.7, 'melee') * (P.twinBuff ? 1.25 : 1), fire = P.fireT > 0;
    const info = { dmg, poise: 45 * W.poise, dir: P.face, kind: 'light', bleed: bleedAmt(false), fire, x: clamp(P.x + P.face * 26, hb.x0 + 3, hb.x1 - 3), y: clamp(P.y - 4, hb.y0, hb.y1), melee: true, big: true };
    t.hit(info); P.twinBuff = false;
    runHooks('strike', t, { dmg, heavy: false, x: info.x, y: info.y }, ATK.sp_1 || PLUNGE_A);
    if (sig && sig.hit) sig.hit(t, info, ATK.sp_1 || PLUNGE_A);
    if (sig && sig.dive) sig.dive(t, info);
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
  fadeTo(() => { P.x = P.safe.x; P.y = P.safe.y; setP('idle', 'idle', true); updateCamera(0, true); });
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
    if (P.shieldParry) { const sg = SIGS[SAVE.weapon]; if (sg && sg.block) sg.block(opt.src); }
    return false;
  }
  if (P.inv > 0) return false;
  if (SETTINGS.god) return false;   // test setting
  // shield guard: frontal blows, projectiles and hazards are stopped cold; stamina pays for it
  let guardBroke = false;
  if (isBlocking() && dir === -P.face && !iframes()) {
    const cost = (6 + dmg * 0.8) * (D.W.guard || 1) * (charmOn('c_aegis') ? 0.7 : 1);
    P.lastHit = id;
    if (P.st >= cost) {
      spend(cost); P.stDelay = 0.8;
      sfx.block(); tone(420, 0.18, 0.08, 'triangle', 0.7); hitstop = Math.max(hitstop, 0.06); shake = Math.max(shake, 2);
      spawnFx(fxOr('parry_spark', 'hit'), P.x + P.face * 12, P.y - 18, P.face);
      for (let i = 0; i < 8; i++) particles.push({ x: P.x + P.face * 12, y: P.y - rand(12, 24), vx: P.face * rand(20, 110), vy: -rand(10, 80), g: 300, life: rand(0.2, 0.45), kind: 'spark' });
      P.vx = dir * 70; P.gcT = 0.6; if (charmOn('c_twin')) P.twinBuff = true;
      if (P.state !== 'parry') setP('block', pHas('sh_block') ? 'sh_block' : 'sh_guard', false);
      const sg = SIGS[SAVE.weapon]; if (sg && sg.block) sg.block(opt.src);
      return false;
    }
    guardBroke = true; P.st = 0; P.stDelay = 1.2; dmg *= 0.5;   // guard break: half gets through and you reel
    sfx.crit(); spawnFx(fxOr('parry_flash', 'parry_spark'), P.x + P.face * 12, P.y - 20, P.face);
  }
  if (iframes()) {
    if (has('second_wind') && P.state === 'roll' && !P.sw) {
      P.sw = true; slowmo = 0.55; P.st = D.maxSt; P.empower = 3;
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
  const armored = (has('steadfast') && attacking && dmg < D.maxHp * 0.3) || (D.W.armor && ATK[P.state] && ATK[P.state].kind === 'heavy') || (charmOn('c_horn') && attacking && dmg < D.maxHp * 0.35)
    || (P.cryT > 0 && dmg < D.maxHp * 0.3) || (P.state === 'art' && P.artId === 'stormleap')
    || (P.state === 'art' && ART_IMPL[P.artId] && ART_IMPL[P.artId].armor);   // agent G's hyper-armoured arts
  if (guardBroke) { setP('gbreak', pHas('sh_break') ? 'sh_break' : 'hurt', false); P.vx = dir * 110; P.healPending = 0; P.combo = 0; P.spellFired = true; P.gcT = 0; }
  else if (!armored) { setP('hurt', 'hurt'); P.vx = dir * 130; P.vy = P.ground ? -60 : P.vy; P.healPending = 0; P.combo = 0; P.spellFired = true; }
  return true;
}
function killPlayer(dir) {
  if (SETTINGS.god) { P.hp = D.maxHp; return false; }   // test setting: nothing can kill you
  P.state = 'dead'; P.anim.set('death', false); P.vx = dir * 90; P.deadT = 1.6; slowmo = 0.9;
  sfx.died(); runHooks('death'); return true;
}

// ---- dealing damage
function outgoing(base, mult, kind) {
  let d = base * mult;
  if (kind !== 'spell' && has('keen_edge')) d *= 1.12;
  if (has('last_stand') && P.hp < D.maxHp * 0.3) d *= 1.25;
  if (P.empower > 0) d *= 1.3;
  if (kind !== 'spell') { if (charmOn('c_crest')) d *= 1.1; if (P.cryT > 0) d *= P.cryBig ? 1.3 : 1.2; if (P.fireT > 0) d *= 1.25; }
  return d * rand(0.93, 1.07);
}
function bleedAmt(heavy) {
  const b = (D.W.bleed || 0) + (has('bloodthirst') ? 22 : 0);
  return b * (heavy ? 1.5 : 1) * (charmOn('c_fang') ? 1.5 : 1);
}
function playerStrike(A) {
  const W = D.W, side = !A.up && !A.down;
  const front = side ? A.reach[1] * (A.cls ? 1 : W.reach) * REACH_MUL : A.reach[1], top = A.up ? A.ys[0] * Math.min(1.25, W.reach) : A.ys[0];
  const r = rect(P.x + P.face * A.reach[0], P.y + top, P.x + P.face * front, P.y + A.ys[1]);
  const heavy = A.kind === 'heavy';
  const base = heavy ? D.heavy * 2.0 * (P.charged ? 1.55 : 1) : D.light;
  const fire = P.fireT > 0 || (W.fire && heavy);
  for (const t of targets()) {
    if (P.hitSet.has(t)) continue;
    const hb = hbOf(t); if (!hb || !overlap(r, hb)) continue;
    P.hitSet.add(t);
    const dmg = outgoing(base, A.mult, 'melee') * (A.counter ? P.counterMul || 1 : 1) * (P.twinBuff ? 1.25 : 1);
    const hdir = A.spin ? ((hb.x0 + hb.x1) / 2 > P.x ? 1 : -1) : P.face;   // the staff spin strikes both sides
    const info = { dmg: dmg * (fire && W.fire ? 1 + W.fire : 1), poise: A.poise * W.poise * (P.charged ? 1.8 : 1) * (heavy ? 1 + (SAVE.stats.str - 10) * 0.015 : 1), dir: hdir, kind: heavy ? 'heavy' : 'light', charged: heavy && !!P.charged, bleed: bleedAmt(heavy), fire, rotDot: !!W.rot,
            x: clamp(A.spin ? (hb.x0 + hb.x1) / 2 : (r.x0 + r.x1) / 2, hb.x0 + 3, hb.x1 - 3), y: clamp(P.y + (A.ys[0] + A.ys[1]) / 2, hb.y0, hb.y1), melee: true, big: heavy || !!A.big || P.state === 'attack3' || P.state === 'attack4' };
    t.hit(info);
    runHooks('strike', t, { dmg, heavy, x: info.x, y: info.y }, A);
    if (A.bash && t.alive && !t.boss && !t.prop && t.breakStance && !(t.cfg && t.cfg.elite) && t.state !== 'stagger') t.breakStance();   // shield bash: most foes reel
    { const sg = SIGS[SAVE.weapon]; if (sg && sg.hit) sg.hit(t, info, A); }
    if (A.down && !P.pogoed) pogo();
    if (P.empower > 0) P.empower = 0;
    if (has('soul_siphon')) P.fp = Math.min(D.maxFp, P.fp + 2);
  }
  if (P.twinBuff && P.hitSet.size && [...P.hitSet].some(x => x !== 'brk')) P.twinBuff = false;
  // pogo off spikes + break walls/urns
  if (A.down && !P.pogoed) {
    for (let x = r.x0; x <= r.x1; x += 6) { const t = tileAt(Math.floor(x / TILE), Math.floor(r.y1 / TILE)); if (t === T_SPIKE) { pogo(); break; } }
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
  let dmg = outgoing(D.light, t.boss ? 3.2 : 4.5, 'melee') * (has('riposte_mastery') ? 1.5 : 1) * (D.W.crit || 1) * (P.backstab ? 1.15 : 1);
  P.backstab = false;
  sfx.crit(); hitstop = 0.22; shake = 9; slowmo = 0.35; flashScreen = 0.3;
  const hb = t.hurtbox() || rect(t.x - 8, t.y - 30, t.x + 8, t.y);
  spawnFx(fxOr('riposte', 'parry_spark'), (hb.x0 + hb.x1) / 2, (hb.y0 + hb.y1) / 2, P.face);
  spawnFx('blood', (hb.x0 + hb.x1) / 2, (hb.y0 + hb.y1) / 2, P.face);
  t.hit({ dmg, poise: 0, dir: P.face, kind: 'crit', x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2, melee: true, big: true, crit: true });
  if (has('riposte_mastery')) P.hp = Math.min(D.maxHp, P.hp + Math.round(D.maxHp * 0.1));
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

// ---- weapon arts (swappable; O key)
function startArt() {
  const id = SAVE.art; if (!id || !ARTS[id]) { toast('No weapon art equipped'); return; }
  let cost = ARTS[id].fp;
  const echoFree = charmOn('c_echo') && (P.artCount + 1) % 3 === 0;   // Echo of the First Flame: every third art is free
  if (echoFree) cost = 0;
  if (P.fp < cost) { sfx.deny(); toast('Not enough FP'); return; }
  if (id === 'stormleap' && !P.ground) { sfx.deny(); return; }
  P.artCount++;
  if (echoFree) { spawnFx(fxOr('parry_flash', 'parry_spark'), P.x, P.y - 16, P.face, null, { alpha: 0.5 }); tone(660, 0.3, 0.05, 'sine', 1.5); }
  // hold O to charge (>= 0.6 s): the art is released charged; P.artCharged stays set while it plays
  P.artHold = true; P.artChargeT = 0; P.artCharged = false;
  P.fp -= cost; P.artId = id; P.artT = 0; P.artFired = false; P.artI = false; P.artLaunched = false; P.artGo = false; P.hitSet = new Set();
  const own = 'art_' + id;
  P.artOwn = pHas(own);
  const A = P.artOwn ? [own, 1] : ART_IMPL[id] ? ART_IMPL[id].fallback || ['attack1', 1] : { crescent: ['attack2', 1.0], moonwave: ['heavy', 1.35], bloodstep: ['air_attack', 1.2], stormleap: ['double_jump', 1], warcry: ['cast', 1.4], cinderblade: ['cast', 1.3] }[id];
  setP('art', pHas(A[0]) ? A[0] : 'attack1', false, A[1]);
  P.artRel = artRelease(id);
  if (id === 'stormleap' && !P.artOwn) { P.vy = -300; P.ground = false; sfx.jump(); spawnFx('dust', P.x, P.y, P.face); }
  if (P.artOwn) sfx.charge();
  if (id === 'bloodstep') { sfx.roll(); P.artI = true; }
  if (ART_IMPL[id] && ART_IMPL[id].start) ART_IMPL[id].start();
}
function artRelease(id) {
  const m = ASSETS.player_meta && ASSETS.player_meta.moves && ASSETS.player_meta.moves['art_' + id];
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
  if (P.artOwn && an.i < P.artRel && Math.random() < 0.6) {   // gathering glow before the release
    const c = id === 'moonwave' ? 'frost' : id === 'cinderblade' ? 'fire' : id === 'bloodstep' ? 'blood' : SAVE.weapon === 'kalden' ? 'teal' : 'gold';
    particles.push({ x: P.x + P.face * rand(4, 18), y: P.y - rand(10, 34), vx: 0, vy: -rand(10, 40), life: 0.4, kind: c });
    addLight(P.x + P.face * 10, P.y - 20, 36, id === 'moonwave' ? '160,210,255' : '255,200,120', 0.6);
  }
  if (ART_IMPL[id]) {
    ART_IMPL[id].update(dt, grav);
    if (P.state === 'art' && P.artOwn && P.g2 && ART_SYNC[id] && P.anim.tag === 'art_' + id) ART_SYNC[id](P.anim, P.g2);
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
