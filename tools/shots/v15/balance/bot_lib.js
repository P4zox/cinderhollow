// v15 balance: a scripted boss-fight bot (prepended by run.sh). Plain page script (no wm prelude: bosses need real randomness).
//   BB.fight(kind, type, o) -> { ttk, dmgTaken (x max HP), hits, staggers, parries, defended, ... }
// The bot: expected build for the boss's stage (69_adaptive's adaptExpected: level 5 + 6 / stage, weapon +min(5, stage/2)),
// expected mastery rank, no skills unless o.skills. It attacks with the type's main route while the boss is calm (between
// attacks or staggered), backs off while it attacks, and a "reactive oracle" answers a share of the blows that would land
// with the type's defensive tool (roll / sidestep / dash, Iai parry, Longsword parry, guard, brace) -- the share scales with
// how wide the tool's window is (o.skill sets the base). Damage taken is summed (HP is refilled every frame).
await boot(); G.grantTechniques();
const E = G.sk.ev;
E(`(() => {
  if (window.__bb) return;
  // deterministic but varied randomness (mulberry32)
  let seed = 1; const rng = () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  Math.random = rng;
  const BB = window.__bb = { ms: 0, on: false, log: [] };
  performance.now = () => BB.ms;
  const frame = () => { BB.ms += 1000 / 60; update(1 / 60); if (state !== 'play' && state !== 'dead') { menu = null; dialog = null; try { state = 'play'; } catch (e) {} } };
  BB.frame = frame;
  const KEY = { J: 'attack', K: 'heavy', I: 'parry', L: 'roll', jump: 'jump' };   // route steps may use 'I' too (Martial Arts shift)
  const tap = a => { press(a); BB.rel.push(a); };
  // ---- per type: spacing (edge distance to keep), route, defence profile, defence window (ms)
  const PROF = {
    longsword: { de: 12, route: ['J','J','J','J'], def: 'roll+parry', win: 280 },
    katana:    { de: 12, route: ['K'], main: ['J','J','J'], def: 'iai', win: 150, sheathe: true },
    greatsword:{ de: 12, route: [{ b: 'K', hold: 1200 }], main: ['J','J','J'], def: 'guard', win: 520 },
    maul:      { de: 8,  route: ['J','J','J'], def: 'roll', win: 280 },
    sns:       { de: 8,  route: ['J','J','K'], main: ['J','J','J','J'], def: 'guard', win: 520 },
    dual:      { de: 6,  route: ['J','J','J','J'], def: 'roll', win: 175 },
    spear:     { de: 28, route: ['J','J','J'], def: 'guard', win: 520 },
    staff:     { de: 12, route: ['J','J','J','J'], def: 'roll', win: 280 },
    whip:      { de: 40, route: ['K'], main: ['J','J','J'], def: 'roll', win: 280 },
    // v15 new types (docs/WEAPON_REVAMP.md Part C) -- profiles ready for phase 2b; iWhen presses I in an opening when true
    saxe:      { de: 12, route: ['J','J','J','J'], main: ['J','J','J','J'], def: 'roll', win: 220, iWhen: () => !P.sxAxe && (P.sxG || 0) >= 100 },
    bow:       { de: 30, route: ['J','J','J','J'], main: ['J','J','J','J'], def: 'tapI', win: 150 },
    fist:      { de: 4,  route: ['J','J','J','J'], main: ['J','J','J','J'], def: 'roll', win: 180 },
    scythe:    { de: 14, route: ['J','J','J','J'], main: ['J','J','J','J'], def: 'roll', win: 280 },
    bell:      { de: 8,  route: ['J','J','J'], main: ['J','J','J'], def: 'roll', win: 260, iWhen: () => (P.belNotes || []).length >= 2 },
  };
  BB.PROF = PROF;
  const ALT = {   // signature routes (o.route = 'sig')
    katana: ['K'], greatsword: [{ b: 'K', hold: 1200 }], maul: [{ b: 'K', hold: 600 }], whip: ['K'], longsword: ['J','J','K'], sns: ['J','J','K'], dual: ['J','J','J','J'], spear: ['J','J','K'], staff: ['J','K'],
    saxe: ['J','J','J','J','K','K'], bow: [{ b: 'K', hold: 850 }], fist: ['J','J','I','J','J'], scythe: [{ b: 'K', hold: 700 }], bell: ['J','K','J','J'],
  };
  BB.ALT = ALT;
  const CALM = new Set([...BREATH_CALM, 'stagger', 'prowl', 'fly', 'rest', 'wait', 'fight', 'parried']);
  BB.expected = (stage) => {
    const L = Math.round(5 + 6 * stage), U = Math.min(5, Math.round(stage / 2)), st = { ...BASE_STATS };
    const order = ['vig', 'str', 'dex', 'end', 'vig', 'str', 'dex', 'mnd'];
    for (let i = 0, n = L - levelOf(BASE_STATS); i < n; i++) st[order[i % order.length]]++;
    return { st, U, rank: stage < 2 ? 1 : stage < 5 ? 2 : stage < 9 ? 3 : stage < 12 ? 4 : 5 };
  };
  // ---- the oracle: the outermost hurtPlayer wrapper
  const _hurt = hurtPlayer;
  hurtPlayer = function (dmg, dir, id, opt = {}) {
    const F = BB.F;
    if (F && BB.on && boss && boss.active && P.state !== 'dead' && !(P.inv > 0) && !iframes() && !(id !== undefined && (id === P.lastHit || F.seen.has(id)))) {
      if (id !== undefined) F.seen.add(id);
      if (rng() < F.p) BB.defend(F, dmg, dir, opt);
    }
    return _hurt.call(this, dmg, dir, id, opt);
  };
  const freeNow = () => ['idle', 'run', 'land'].includes(P.state);
  const cancellable = () => { const A = ATK[P.state]; return A && A.mv && P.mvT >= A.mv.wind && !A.mv.commit; };
  BB.defend = (F, dmg, dir, opt) => {
    const pr = F.prof, away = dir || (P.x < boss.x ? -1 : 1);
    const ok = freeNow() || cancellable() || P.state === 'guard' || P.state === 'block' || (P.sheathed && (P.state === 'kt_sheathe' || freeNow()));
    if (!ok || P.st <= 0 || !P.ground) return;
    const parryable = opt.parryable || ((PARRY_MELEE[boss.kind] || []).includes((opt.src && opt.src.atk) || boss.atk));
    if (pr.def === 'iai' && P.sheathed) { P.face = -away; if (mvStart('kt_iaiw')) { F.iai++; return; } }
    if (pr.def === 'roll+parry' && parryable) { P.face = -away; setP('idle', 'idle', true); startParry(); F.parryTry++; return; }
    if (pr.def === 'guard') {   // a reactive guard: raised right as the blow comes, if the stamina can pay for it
      const c = BOSS_CURVE[boss.kind], est = dmg * (c ? c[1] : 1) * (adaptCur.kind === boss.kind ? adaptCur.dmg : 1) * diffCfg().bossDmg;
      const cost = mvGuardCost(est, opt).cost + (mvType() === 'sns' ? 10 : 0);
      if (P.st >= cost) {
        if (ATK[P.state]) mvInterrupted();
        P.face = -away;
        if (!isBlocking()) { setP('idle', 'idle', true); buffered.set('parry', performance.now()); mvT().onI(-away); }
        F.blocks++; return;
      }
    }
    if (pr.def === 'tapI' && mvT().onI) { setP('idle', 'idle', true); P.face = -away; buffered.set('parry', performance.now()); if (mvT().onI(-away)) { F.parryTry++; return; } }
    // roll away from the blow
    if (ATK[P.state]) mvInterrupted();
    setP('idle', 'idle', true); P.face = away; const rd = BB.F.rollToward ? -away : away; P.face = rd; mvDodge(mvT().dodge ? (typeof mvT().dodge === 'function' ? mvT().dodge(rd) : mvT().dodge) : MV_ROLL, rd); F.rolls++;
  };
  HOOKS.parry.push(() => { if (BB.F && BB.on) BB.F.parries++; });
  // ---- the fight
  BB.fight = (kind, type, o = {}) => {
    seed = o.seed || 1;
    const stage = BOSS_STAGE[kind] ?? 1, X = BB.expected(o.stage ?? stage);
    if (!TRAINING.on) trainingStart();
    for (let i = 0; i < 5; i++) frame();
    wmEquip(type, { quiet: true });
    SAVE.stats = { ...X.st }; SAVE.weapons[SAVE.weapon] = o.up ?? X.U; SAVE.skills = (o.skills || []).slice(); SAVE.charmsEq = []; SAVE.diff = o.diff ?? 1;
    SETTINGS.god = 0; SETTINGS.adapt = o.adapt ?? 1; MV.rank = o.rank ?? X.rank;
    refreshDerived(false);
    if (o.pre) eval(o.pre);
    held.clear(); clearBuffer();
    if (!trnSummonBoss(kind) || !boss) return { kind, type, err: 'nosummon' };
    refreshDerived(false); P.hp = D.maxHp; P.st = D.maxSt; P.fp = D.maxFp;
    const dmgBy = {}; for (const q of (boss.parts ? [boss, ...boss.parts] : [boss])) { if (!q || !q.hit || q._bbHit) continue; q._bbHit = 1; const _h = q.hit; q.hit = function (info, ...r) { const hp0 = this.hp; const res = _h.call(this, info, ...r); const d = Math.max(0, hp0 - this.hp); if (d > 0) { const k = info && info.dot ? 'dot' : P.state; dmgBy[k] = (dmgBy[k] || 0) + d; } return res; }; }
    const pr = o.de !== undefined ? { ...PROF[type], de: o.de } : PROF[type], route = o.route === 'sig' ? ALT[type] : o.route === 'main' ? (pr.main || pr.route) : (o.routeList || pr.route);
    const win = pr.win, base = o.skill ?? 0.45;
    BB.log = [];
    const F = BB.F = { rollToward: !!o.rollToward, prof: pr, p: o.noDef ? 0 : Math.min(0.92, base + win / 700), seen: new Set(), iai: 0, parryTry: 0, rolls: 0, parries: 0, blocks: 0 };
    BB.on = true; BB.rel = [];
    const byAtk = {}, bigHits = []; let flasksUsed = 0, lost = 0, hits = 0, oneShots = 0, maxHit = 0, ri = 0, holdLeft = 0, t = 0, actT = null, hp0 = null, phases = new Set(), stag0 = 0, firstHp = null, jumpCd = 0;
    const MAXF = Math.round((o.secs || 180) * 60);
    const flask = Math.round(D.maxHp * 0.42 + 20);
    let f = 0;
    for (; f < MAXF; f++) {
      for (const a of BB.rel) release(a); BB.rel = [];
      const B = boss; if (!B) break;
      if (!B.alive) break;
      const bodies = B.parts ? B.parts.filter(q => q && q.alive !== false && q.hurtbox && q.hurtbox()) : [B];
      let tb = null, best = 1e9; for (const q of bodies) { const d = Math.abs(q.x - P.x); if (d < best) { best = d; tb = q; } }
      const hb = tb && tb.hurtbox && tb.hurtbox() ? hbOf(tb) : null;
      held.delete('left'); held.delete('right'); held.delete('up');
      if (B.active && actT === null) { actT = f; firstHp = B.hp + (B.parts ? B.parts.reduce((a, q) => a + (q.hp || 0), 0) : 0); }
      if (!B.active || !hb) {   // walk toward it to wake it
        const dx = (tb ? tb.x : B.x) - P.x; if (Math.abs(dx) > 30) held.add(dx < 0 ? 'left' : 'right');
        frame(); continue;
      }
      phases.add(B.phase);
      const cx = (hb.x0 + hb.x1) / 2, dir = cx < P.x ? -1 : 1;
      const edge = P.x < hb.x0 ? hb.x0 - P.x : P.x > hb.x1 ? P.x - hb.x1 : 0;
      const st = tb.state ?? B.state, calm = CALM.has(st) || (B.parts && !CALM.has(B.state) && false);
      const high = hb.y1 < P.y - 30, reachY = hb.y1 > P.y - 64;
      const free = freeNow(), inMove = !!ATK[P.state];
      if (holdLeft > 0 && --holdLeft === 0) release('heavy');
      // katana: sheathe whenever it's quiet
      if (pr.iWhen && free && (calm || B.state === 'stagger') && edge <= pr.de + 14 && P.st > 10) { try { if (pr.iWhen()) tap('parry'); } catch (e) {} }
      if (pr.sheathe && !P.sheathed && free && P.st > 20 && (!calm || edge > 40)) tap('parry');
      // guards: raise it while a blow is coming and we're close
      const guardType = pr.def === 'guard';
      if (guardType && o.holdGuard) { if (!calm && edge < 110 && (free || P.state === 'guard' || P.state === 'block') && P.st > (o.guardSt ?? 0.4) * D.maxSt) { if (!held.has('parry')) press('parry'); P.face = dir; } else if (held.has('parry')) release('parry'); }
      if (calm || B.state === 'stagger') {
        if (edge > pr.de + 6 && !inMove) held.add(dir > 0 ? 'right' : 'left');
        else if (edge < pr.de - 14 && pr.de > 20 && free) held.add(dir > 0 ? 'left' : 'right');
        else if (free && P.face !== dir) P.face = dir;
        const inRange = edge <= pr.de + 14;
        if (inRange && holdLeft === 0 && P.st > 0) {
          const reserve = (o.reserve ?? 0.3) * D.maxSt, keep = (o.keep ?? 0.12) * D.maxSt;
          const canPress = (free && P.st >= reserve) || (inMove && !P.mvQ && P.mvT > 40 && !ATK[P.state].mv.loop && P.st >= keep);
          if (canPress) {
            if (high && !reachY) { if (P.ground && jumpCd <= 0 && free) { tap('jump'); jumpCd = 40; } }
            else {
              if (high) held.add('up');
              const p = route[ri % route.length];
              if (free && P.face !== dir) P.face = dir;
              if (typeof p === 'string') tap(KEY[p]); else { press('heavy'); holdLeft = Math.round(p.hold / (1000 / 60)); }
              ri++;
            }
          }
          if (!P.ground && P.vy > -60 && !inMove && P.st > 0 && edge < pr.de + 20) tap('attack');
        }
        if (free && !inMove && edge > pr.de + 20) ri = 0;
      } else {
        // a blow is coming: back off if close (not while committed)
        const rt = o.retreat ?? 70;
        if (edge < rt && !inMove && P.state !== 'roll') held.add(dir > 0 ? 'left' : 'right');
        else if (edge > rt + 30 && !inMove && P.state !== 'roll' && o.retreat !== undefined) held.add(dir > 0 ? 'right' : 'left');
        if (free) ri = 0;
      }
      jumpCd--;
      if (o.trace && f % o.trace === 0) BB.log.push([(f/60).toFixed(1), 'P', Math.round(P.x), Math.round(P.y), P.state, 'st' + Math.round(P.st), '| B', st, Math.round(tb.x), Math.round(tb.y), 'hb', Math.round(hb.x0) + '-' + Math.round(hb.x1), 'y' + Math.round(hb.y0) + '-' + Math.round(hb.y1), 'edge', Math.round(edge), calm ? 'CALM' : 'ATK', 'hp', Math.round(B.hp)].join(' '));
      const hpB = P.hp, pst0 = P.state;
      frame();
      if (P.hp < hpB) { const d = hpB - P.hp; lost += d; hits++; maxHit = Math.max(maxHit, d); const an = o.byP ? 'P:' + pst0 : (tb.atk || B.atk || '-') + '/' + (tb.state || B.state); byAtk[an] = (byAtk[an] || 0) + d / D.maxHp; if (d > D.maxHp * 0.35) bigHits.push(an + ' ' + (d / D.maxHp).toFixed(2)); }
      if (P.state === 'dead' || P.hp <= 0) { oneShots++; P.state = 'idle'; P.anim.set('idle', true); P.deadT = 0; P.hp = D.maxHp; }
      if (!o.hpReal) P.hp = D.maxHp;
      else if (P.hp < D.maxHp * 0.25) { P.hp = Math.min(D.maxHp, P.hp + D.maxHp * 0.5); flasksUsed++; }   // a flask (the bot drinks below 25%)
      if (o.infSt) P.st = D.maxSt;
    }
    for (const a of BB.rel) release(a); held.clear(); clearBuffer();
    BB.on = false;
    const B = boss, alive = B && B.alive;
    const hpNow = B ? Math.max(0, B.hp) + (B.parts ? B.parts.reduce((a, q) => a + Math.max(0, q.hp || 0), 0) : 0) : 0;
    const secs = (f - (actT || 0)) / 60;
    const res = { kind, type, stage, killed: !alive, secs: +secs.toFixed(1), hpLeft: firstHp ? +(hpNow / firstHp).toFixed(2) : null,
      dps: firstHp ? +((firstHp - hpNow) / secs / D.light).toFixed(2) : 0,
      taken: +(lost / D.maxHp).toFixed(2), flasks: +(lost / flask).toFixed(1), hits, maxHit: +(maxHit / D.maxHp).toFixed(2), oneShots, flasksUsed,
      staggers: B ? (B.staggers || 0) + (B.parts ? B.parts.reduce((a, q) => a + (q.staggers || 0), 0) : 0) : 0,
      parries: F.parries, iai: F.iai, rolls: F.rolls, parryTry: F.parryTry, blocks: F.blocks, light: Math.round(D.light), maxHp: D.maxHp, bossMax: firstHp, phases: [...phases].join('/'), dmgBy: Object.entries(dmgBy).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([k, v]) => k + ' ' + Math.round(v / D.light)).join(', '), byAtk: Object.entries(byAtk).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([k, v]) => k + ' ' + v.toFixed(2)).join(', '), bigHits: bigHits.slice(0, 6).join(', ') };
    trnClear(); for (let i = 0; i < 3; i++) frame();
    return res;
  };
})()`);
const BB = () => window.__bb;
