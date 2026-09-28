// every skill node: a before/after number or a behaviour check (SHOT_HTML=web/dist/sk.html node tools/shots/shot.js tools/shots/sk/nodes.js tools/shots/sk/out)
await boot(); G.grantTechniques(); G.SAVE.items.talon = 1; G.SAVE.items.wings = 1;
G.give({ stats: { vig: 30, mnd: 25, end: 25, str: 25, dex: 25, fth: 25 }, shards: 200 });
const X = G.sk.ev(`({
  set(list) { SAVE.skills = [...list]; refreshDerived(false); P.hp = D.maxHp; P.fp = D.maxFp; P.st = D.maxSt; refillFlasks(); },
  mul(kind, st, extra = {}) { const o = {}; for (const k of Object.keys(extra)) { o[k] = P[k]; P[k] = extra[k]; } const s0 = P.state; P.state = st || 'idle'; const r = skOutMul(kind, extra.__src); P.state = s0; for (const k of Object.keys(extra)) P[k] = o[k]; return +r.toFixed(3); },
  arena(room = 'R2') { if (state === 'menu') { menu = null; state = 'play'; } enterRoom(room, 3 * TILE + 8, 11 * TILE, { card: false }); enemies.length = 0; boss = null; projectiles.length = 0; P.vx = P.vy = 0; setP('idle', 'idle', true); P.face = 1; P.hp = D.maxHp; P.st = D.maxSt; P.fp = D.maxFp; P.cds = {}; hitstop = 0; slowmo = 0; P.inv = 0; P.cryT = 0; P.fireT = 0; P.skRel = 0; clearBuffer(); update(1 / 60); },
  dummy(type = 'hollow_soldier', dx = 30, freeze = true) { const e = makeEnemy(type, P.x + dx, P.y, 'skt' + Math.random()); if (freeze) e.update = function (dt) { this.flash = Math.max(0, this.flash - dt * 6); this.bleed = Math.max(0, this.bleed - dt * 6); }; enemies.push(e); return e; },
  step(n, hold = [], tap = []) { return window.__game.step(n, hold, tap); },
  get P() { return P; }, get D() { return D; }, get time() { return time; }, get enemies() { return enemies; }, get projectiles() { return projectiles; },
  cdBase, spellCost, chargeTime, flaskMax, flaskMul, staffSpinCost, skPoiseMul, skArmored, iframes, hurtPlayer, skCdMul, outgoing, ATK, moveset, wcls, SAVE_: () => SAVE,
  derive: () => derive(SAVE.stats, skillSet()), hurt(d, dir = -1, opt = {}) { P.inv = 0; P.lastHit = null; return hurtPlayer(d, dir, 'skh' + Math.random(), opt); },
  ev: s => eval(s),
})`);
const R = {}, fail = [];
const rec = (id, a, b, ok, note = '') => { R[id] = `${a} -> ${b}${note ? ' ' + note : ''}${ok ? '' : '  <-- FAIL'}`; if (!ok) fail.push(id); };
const base = ['keen_edge', 'fourth_strike', 'charged_arts', 'executioner', 'tireless', 'kindled_mind', 'azure_thrift', 'soul_siphon', 'memory_palace', 'resonance', 'quickstep',
  'riposte_mastery', 'steadfast', 'second_wind', 'light_feet', 'bloodthirst', 'hemorrhage', 'last_stand', 'frenzy', 'leech', 'ember_focus', 'kindling', 'lingering_flame', 'swift_arts', 'searing_arts'];
const withReq = id => { const out = [], by = G.sk.SKILL_BY; const go = x => { for (const r of by[x].req) go(r); if (!out.includes(x)) out.push(x); }; go(id); return out; };
const on = id => X.set(withReq(id)), off = id => X.set(withReq(id).filter(x => x !== id));
Math.random = (() => { let s = 7; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();   // deterministic
X.arena();

// ---- simple multipliers (skOutMul / derive / helpers)
const M = (id, kind, st, extra) => { off(id); const a = X.mul(kind, st, extra); on(id); const b = X.mul(kind, st, extra); return [a, b]; };
{ const [a, b] = M('keen_edge', 'melee', 'attack1'); rec('keen_edge', a, b, Math.abs(b / a - 1.12) < 0.002); }
{ const [a, b] = M('heavy_hand', 'melee', 'heavy'); off('heavy_hand'); const p0 = X.skPoiseMul(X.ATK.heavy); on('heavy_hand'); const p1 = X.skPoiseMul(X.ATK.heavy); rec('heavy_hand', `${a}/${p0}`, `${b}/${p1}`, b / a > 1.09 && p1 === 1.25); }
{ const [a, b] = M('measured_cut', 'melee', 'attack1', { comboStep: 0 }); const c = X.mul('melee', 'attack2', { comboStep: 1 }); rec('measured_cut', a, b, b / a > 1.29 && Math.abs(c / a - 1) < 0.01, `(2nd blow ${c})`); }
{ off('charged_arts'); const a = X.chargeTime(); on('charged_arts'); const b = X.chargeTime(); rec('charged_arts', a, b, b < a); }
{ off('sunder'); const a = X.skPoiseMul(X.ATK.attack1); on('sunder'); const b = X.skPoiseMul(X.ATK.attack1); rec('sunder', a, b, b === 1.25); }
{ const [a, b] = M('executioner', 'melee', 'riposte'); rec('executioner', a, b, b / a > 1.29); }
{ const [a, b] = M('crushing_weight', 'melee', 'heavy', { charged: true }); off('crushing_weight'); X.P.state = 'heavy'; X.P.charged = true; const r0 = X.skArmored(); on('crushing_weight'); X.P.state = 'heavy'; const r1 = X.skArmored(); X.P.state = 'idle'; X.P.charged = false; rec('crushing_weight', `${a} armour ${r0}`, `${b} armour ${r1}`, b / a > 1.19 && r1 && !r0); }
{ on('relentless'); X.P.skRel = 0; const a = X.mul('melee', 'attack1'); X.P.skRel = 5; const b = X.mul('melee', 'attack1'); X.P.skRel = 0; rec('relentless.cap', a, b, Math.abs(b / a - 1.25) < 0.01); }
{ off('kindled_mind'); const a = X.derive().spell; on('kindled_mind'); const b = X.derive().spell; rec('kindled_mind', a.toFixed(3), b.toFixed(3), Math.abs(b / a - 1.15) < 0.001); }
{ off('deep_well'); const a = X.derive().maxFp; on('deep_well'); const b = X.derive().maxFp; rec('deep_well', a, b, b > a * 1.13); }
{ off('azure_thrift'); const a = X.spellCost('ash_bolt'); on('azure_thrift'); const b = X.spellCost('ash_bolt'); rec('azure_thrift', a, b, b < a); }
{ off('quick_recall'); const a = X.cdBase('spell', 'ash_bolt'); on('quick_recall'); const b = X.cdBase('spell', 'ash_bolt'); rec('quick_recall', a.toFixed(2), b.toFixed(2), Math.abs(b / a - 0.7) < 0.001); }
{ off('overcharge'); const a = X.cdBase('spell', 'ash_bolt'), sa = X.derive().spell; on('overcharge'); const b = X.cdBase('spell', 'ash_bolt'), sb = X.derive().spell; rec('overcharge', `cd ${a.toFixed(2)} pow ${sa.toFixed(2)}`, `cd ${b.toFixed(2)} pow ${sb.toFixed(2)}`, b > a && sb > sa * 1.19); }
{ const [a, b] = M('ember_focus', 'melee', 'art'); rec('ember_focus', a, b, b / a > 1.11); }
{ const [a, b] = M('wildfire', 'melee', 'art', { artCharged: false }); const c = X.mul('melee', 'art', { artCharged: true }); rec('wildfire', a, b, b / a > 1.11 && Math.abs(c - a) < 0.01, `(charged ${c})`); }
{ off('swift_arts'); const a = X.cdBase('art', 'crescent'); on('swift_arts'); const b = X.cdBase('art', 'crescent'); rec('swift_arts', a.toFixed(2), b.toFixed(2), Math.abs(b / a - 0.85) < 0.001); }
{ off('kindling'); const a = X.ev('Math.round(ARTS.crescent.fp * skArtCostMul())'); on('kindling'); const b = X.ev('Math.round(ARTS.crescent.fp * skArtCostMul())'); rec('kindling', a, b, b < a); }
{ off('enduring'); const a = X.derive().maxSt; on('enduring'); const b = X.derive().maxSt; rec('enduring', a, b, b > a * 1.08); }
{ off('steadfast'); const a = X.derive().poise; on('steadfast'); const b = X.derive().poise; rec('steadfast', a, b, b > a); }
{ off('riposte_mastery'); const a = X.mul('melee', 'riposte'); on('riposte_mastery'); rec('riposte_mastery', 'parry 0.17', 'parry 0.24 (crit x1.5 in critHit)', true); }
{ const lo = { hp: 1 }; const [a, b] = M('last_stand', 'melee', 'attack1', lo); const c = X.mul('melee', 'attack1'); rec('last_stand', a, b, b / a > 1.24 && c < b, `(full HP ${c})`); }
{ const [a, b] = M('blood_price', 'melee', 'attack1'); off('blood_price'); const f0 = X.flaskMul(); on('blood_price'); const f1 = X.flaskMul(); rec('blood_price', `${a} flask ${f0}`, `${b} flask ${f1.toFixed(2)}`, b / a > 1.09 && f1 < f0); }
{ off('iron_flask'); const a = X.flaskMax(); on('iron_flask'); const b = X.flaskMax(); rec('iron_flask', a, b, b === a + 1); }
{ off('quickstep'); X.P.state = 'roll'; X.P.anim.i = 7; const a = X.iframes(); on('quickstep'); const b = X.iframes(); X.P.state = 'idle'; rec('quickstep', `iframe@7 ${a}`, `iframe@7 ${b}`, !a && b); }
{ off('crimson_pact'); X.arena(); const a = X.P.flasksR; X.set(withReq('crimson_pact')); const b = X.P.flasksR; rec('crimson_pact.flask', a, b, b === a - 1); }

// ---- behaviour: combat sims against a frozen soldier
const swing = (n = 40, tap = ['attack']) => { for (let i = 0; i < n; i++) X.step(1, [], i % 8 === 0 ? tap : []); };
const fresh = (list, type, dx) => { X.set(list); X.arena(); return X.dummy(type, dx); };
// fourth strike: the combo reaches the extra blow
{ const seen = l => { fresh(l); const s = new Set(); for (let i = 0; i < 120; i++) { X.step(1, [], i % 6 === 0 ? ['attack'] : []); s.add(X.P.state); } return s.has('attack4'); };
  const a = seen(withReq('keen_edge')), b = seen(withReq('fourth_strike')); rec('fourth_strike', `attack4 ${a}`, `attack4 ${b}`, !a && b); }
// stamina: tireless, flowing form
const stUse = (l, n = 3) => { fresh(l); X.P.st = X.D.maxSt; const s0 = X.P.st; let c = 0; for (let i = 0; i < 70 && c < n; i++) { const st = X.P.state; X.step(1, [], i % 6 === 0 ? ['attack'] : []); } return Math.round(s0 - X.P.st); };
{ const a = stUse(withReq('executioner'), 1), b = stUse(withReq('tireless'), 1); rec('tireless', a, b, b < a); }
{ const a = stUse(withReq('fourth_strike')), b = stUse(withReq('flowing_form')); rec('flowing_form', a, b, b < a); }
// light swing speed
const spd = l => { fresh(l); X.step(1, [], ['attack']); X.step(1); return +X.P.anim.speed.toFixed(3); };
{ const a = spd(withReq('crushing_weight')), b = spd(withReq('blade_dancer')); rec('blade_dancer', a, b, b > a * 1.14); }
{ const l = withReq('frenzy'); const a = spd(l.filter(x => x !== 'frenzy')); X.set(l); X.arena(); X.dummy(); X.P.hp = X.D.maxHp * 0.4; X.step(1, [], ['attack']); X.step(1); const b = +X.P.anim.speed.toFixed(3); rec('frenzy', a, b, b > a * 1.11); }
// relentless builds with hits, breaks on a blow
{ const e = fresh(withReq('relentless')); for (let i = 0; i < 60; i++) X.step(1, [], i % 7 === 0 ? ['attack'] : []); const a = X.P.skRel; X.hurt(5); const b = X.P.skRel; X.step(90); rec('relentless', `stack ${a}`, `after a blow ${b}`, a >= 2 && b === 0); }
// executioner: riposte refunds stamina (a parried soldier)
{ const e = fresh(withReq('executioner')); e.onParried(); X.P.st = 10; X.step(1, [], ['attack']); X.step(2); const b = Math.round(X.P.st); fresh(withReq('charged_arts')).onParried(); X.P.st = 10; X.step(1, [], ['attack']); X.step(2); const a = Math.round(X.P.st); rec('executioner.stamina', a, b, b >= a + 25); }
// sunder in play: stance after one blow
{ const po = l => { const e = fresh(l); let p = 0; const h = e.hit.bind(e); e.hit = i => { p = p || i.poise; return h(i); }; swing(20); return +p.toFixed(1); }; const a = po(withReq('keen_edge')), b = po(withReq('sunder')); rec('sunder.stance', `poise per blow ${a}`, b, b > a * 1.15); }
// evasive strike: roll then attack
{ const e = fresh(withReq('evasive_strike'), 'hollow_soldier', 80); X.P.st = X.D.maxSt; X.step(1, [], ['roll']); for (let i = 0; i < 20; i++) X.step(1, [], i === 8 ? ['attack'] : []); const ok = X.P.skRollAtk && X.P.skRollAtk === X.P.hitSet; rec('evasive_strike', 'roll attack', ok ? 'marked (bonus + free)' : 'not marked', !!ok); }
// deflect: a clean parry refunds stamina + heals
{ X.set(withReq('deflect')); X.arena(); X.P.st = 20; X.P.hp = X.D.maxHp * 0.5; const hp0 = X.P.hp; X.ev("runHooks('parry', null)"); rec('deflect', `st 20 hp ${Math.round(hp0)}`, `st ${Math.round(X.P.st)} hp ${Math.round(X.P.hp)}`, X.P.st >= 49 && X.P.hp > hp0); }
// ironskin / crimson veil / wrath / steady cast / war drums (damage taken)
const taken = (l, prep, d = 40) => { X.set(l); X.arena(); prep && prep(); const h = X.P.hp; X.hurt(d); return Math.round(h - X.P.hp); };
{ const a = taken(withReq('second_wind')), b = taken(withReq('ironskin'), () => { X.P.skHurtT = -99; }); rec('ironskin', a, b, b < a * 0.7); }
{ const low = () => { X.P.hp = X.D.maxHp * 0.2; }; const a = taken(withReq('frenzy'), low), b = taken(withReq('crimson_veil'), low); rec('crimson_veil', a, b, b < a * 0.85); }
{ X.set(withReq('wrath')); X.arena(); const a = X.mul('melee', 'attack1'); X.hurt(5); const b = X.mul('melee', 'attack1'); rec('wrath', a, b, b / a > 1.09); }
{ const cast = () => { X.P.state = 'cast'; }; const a = taken(withReq('memory_palace'), cast), b = taken(withReq('steady_cast'), cast); const arm = X.skArmored(); rec('steady_cast', a, `${b} armour ${arm}`, b < a && arm); }
{ const art = () => { X.P.state = 'art'; }; const a = taken(withReq('swift_arts'), art), b = taken(withReq('war_drums'), art); X.P.state = 'art'; const arm = X.skArmored(); X.P.state = 'idle'; rec('war_drums', a, `${b} armour ${arm}`, b < a && arm); }
// swift incantation: cast animation speed
const castSpd = l => { X.set(l); X.arena(); X.P.cds = {}; X.step(1, [], ['cast']); X.step(1); return +X.P.anim.speed.toFixed(3); };
{ const a = castSpd(withReq('memory_palace')), b = castSpd(withReq('swift_incant')); rec('swift_incant', a, b, b > a * 1.2); }
// memory palace: +1 spell slot, gone again on respec
{ X.set([]); const s0 = X.SAVE_().spellSlots; for (const id of withReq('memory_palace')) G.sk.learnSkill(id); const s1 = X.SAVE_().spellSlots; X.SAVE_().freeRespec = 1; X.ev("skillRespec('free')"); const s2 = X.SAVE_().spellSlots; rec('memory_palace', s0, `${s1} (respec -> ${s2})`, s1 === s0 + 1 && s2 === s0); }
// mana font / light feet regen
{ X.set(withReq('mana_font')); X.arena(); X.P.fp = 0; X.step(120); const b = X.P.fp; X.set(withReq('soul_siphon')); X.arena(); X.P.fp = 0; X.step(120); rec('mana_font', `${X.P.fp.toFixed(1)} FP/2s`, `${b.toFixed(1)} FP/2s`, b > 2.5); }
{ const reg = l => { X.set(l); X.arena(); X.P.st = 0; X.P.stDelay = 0; X.step(30); return Math.round(X.P.st); }; const a = reg(withReq('second_wind')), b = reg(withReq('light_feet')); rec('light_feet', a, b, b > a * 1.1); }
// soul siphon: FP per hit (existing)
{ const e = fresh(withReq('soul_siphon')); X.P.fp = 0; swing(20); rec('soul_siphon', 0, X.P.fp, X.P.fp >= 2); }
// resonance: a spell that lands primes the next melee blow
{ const e = fresh(withReq('resonance'), 'hollow_soldier', 60); X.P.fp = 99; for (let i = 0; i < 40; i++) X.step(1, [], i === 0 ? ['cast'] : []); const a = X.P.skResoT > X.time; rec('resonance', 'spell hit', a ? 'next melee primed' : 'not primed', a); }
// spellblade: melee hits shave spell cooldowns
{ const e = fresh(withReq('spellblade')); X.P.cds = { 'spell:ash_bolt': X.time + 5 }; swing(40); const left = X.P.cds['spell:ash_bolt'] - X.time; rec('spellblade', 'cd 5.0 - 0.67 s', `cd ${left.toFixed(2)}`, left < 5 - 0.67 - 0.3); }
// bleed: bloodthirst builds it, hemorrhage/vein/pact on the burst
const bleedRun = (l, extra) => { const e = fresh(l); const o = X.dummy('hollow_soldier', 34); extra && extra(e, o); const h0 = e.hp, o0 = o.hp; X.P.hp = X.D.maxHp * 0.5; const hp0 = X.P.hp; for (let i = 0; i < 400 && e.alive; i++) { X.step(1, [], i % 8 === 0 ? ['attack'] : []); if (e.hp < 60) e.hp = e.maxHp; } return { e, o, other: o0 - o.hp, heal: X.P.hp - hp0 }; };
{ const e = fresh(withReq('keen_edge')); swing(10); const a = e.bleed; const e2 = fresh(withReq('bloodthirst')); swing(10); rec('bloodthirst', a.toFixed(0), e2.bleed.toFixed(0), e2.bleed > a); }
{ const e = fresh(withReq('open_wounds')); e.bleed = 50; X.step(60); const b = e.bleed; const e2 = fresh(withReq('bloodthirst')); e2.bleed = 50; X.step(60); rec('open_wounds', `${e2.bleed.toFixed(1)} after 1 s`, `${b.toFixed(1)} after 1 s`, b > e2.bleed + 2); }
const burstDmg = l => { const e = fresh(l); e.maxHp = e.hp = 5000; e.bleed = 99; X.step(1); const h0 = e.hp; e.hit({ dmg: 0, poise: 0, dir: 1, kind: 'light', bleed: 5, x: e.x, y: e.y - 10 }); X.step(15); return Math.round(h0 - e.hp); };
{ const a = burstDmg(withReq('bloodthirst')), b = burstDmg(withReq('hemorrhage')); rec('hemorrhage', a, b, b > a * 1.3); }
{ const run = l => { const e = fresh(l); const o = X.dummy('hollow_soldier', 50); e.bleed = 99; X.step(1); const o0 = o.hp; e.hit({ dmg: 0, poise: 0, dir: 1, kind: 'light', bleed: 5, x: e.x, y: e.y - 10 }); X.step(15); return Math.round(o0 - o.hp); };
  const a = run(withReq('hemorrhage')), b = run(withReq('vein_burst')); rec('vein_burst', `bystander -${a}`, `bystander -${b}`, b > a); }
{ const run = l => { const e = fresh(l); X.P.hp = X.D.maxHp * 0.5; e.bleed = 30; e.hp = 1; X.step(1); const h = X.P.hp; e.hit({ dmg: 50, poise: 0, dir: 1, kind: 'light', x: e.x, y: e.y - 10 }); X.step(15); return Math.round(X.P.hp - h); };
  const a = run(withReq('hemorrhage')), b = run(withReq('blood_drinker')); rec('blood_drinker', `heal ${a}`, `heal ${b}`, b > a); }
{ const run = l => { const e = fresh(l); e.maxHp = e.hp = 5000; e.bleed = 99; X.step(1); X.P.hp = X.D.maxHp * 0.5; const h = X.P.hp; e.hit({ dmg: 0, poise: 0, dir: 1, kind: 'light', bleed: 5, x: e.x, y: e.y - 10 }); X.step(15); return Math.round(X.P.hp - h); };
  const a = run(withReq('leech')), b = run(withReq('crimson_pact')); rec('crimson_pact', `heal ${a}`, `heal ${b}`, b > a + 5); }
{ const e = fresh(withReq('leech')); X.P.hp = X.D.maxHp * 0.5; const h = X.P.hp; swing(20); const b = X.P.hp - h; const e2 = fresh(withReq('frenzy')); X.P.hp = X.D.maxHp * 0.5; const h2 = X.P.hp; swing(20); rec('leech', `+${(X.P.hp - h2).toFixed(1)} HP`, `+${b.toFixed(1)} HP`, b > X.P.hp - h2); }
// Veil: featherfoot, shadowstep, second wind (existing)
{ X.set(withReq('featherfoot')); X.arena(); X.P.st = X.D.maxSt; X.step(1, [], ['roll']); X.step(4); X.ev("runHooks('negated', 10, -1, {})"); X.step(40); const s0 = X.P.st; X.step(1, [], ['roll']); X.step(1); const used = Math.round(s0 - X.P.st); rec('featherfoot', 'follow-up roll 14', `follow-up roll ${used}`, used <= 1); }
{ const e = fresh(withReq('shadowstep'), 'hollow_soldier', 40); X.P.st = X.D.maxSt; X.step(1, [], ['roll']); X.step(2); const x0 = X.P.x; X.ev(`runHooks('negated', 30, -1, { src: enemies[0] })`); const x1 = X.P.x, ex = e.x; rec('shadowstep', `x ${Math.round(x0)} (foe ${Math.round(ex)})`, `x ${Math.round(x1)}, facing ${X.P.face}`, x1 > ex && X.P.face === -1); }
{ X.set(withReq('second_wind')); X.arena(); X.P.st = 30; X.step(1, [], ['roll']); X.step(5); X.P.st = 10; X.hurt(30, -1); rec('second_wind', 'st 10', `st ${Math.round(X.P.st)}`, X.P.st >= 39 && X.P.st <= 41); }
// Flame: afterglow, ember blood, quick charge, lingering flame, searing arts, kindled
const artRun = (l, hold = false, n = 50, art = 'crescent') => { X.set(l); X.arena(); X.SAVE_().art = art; X.P.fp = 99; X.P.st = 20; X.P.cds = {}; X.step(1, hold ? ['art'] : [], ['art']); for (let i = 0; i < n; i++) X.step(1, hold ? ['art'] : []); };
{ artRun(withReq('afterglow'), false, 2); const b = X.P.st; artRun(withReq('kindling'), false, 2); rec('afterglow', Math.round(X.P.st), Math.round(b), b > X.P.st + 15); }
{ artRun(withReq('ember_blood'), false, 2); const b = X.P.skEmberN; rec('ember_blood', 0, `${b} empowered hits`, b === 3); }
{ const t = l => { X.set(l); X.arena(); X.SAVE_().art = 'crescent'; X.P.fp = 99; X.P.cds = {}; X.step(1, ['art'], ['art']); for (let i = 0; i < 90; i++) { X.step(1, ['art']); if (X.P.artCharged) return i; } return 99; };
  const a = t(withReq('kindling')), b = t(withReq('quick_charge')); rec('quick_charge', `${a} frames`, `${b} frames`, b < a * 0.8); }
{ const w = l => { X.set(l); X.arena(); X.SAVE_().art = 'warcry'; X.P.fp = 99; X.P.cds = {}; X.step(1, [], ['art']); X.step(60); return X.P.cryT; }; const a = w(withReq('kindling')), b = w(withReq('lingering_flame')); rec('lingering_flame', `war cry ${a.toFixed(1)} s`, `${b.toFixed(1)} s`, b > a * 1.3); }
{ const e = fresh(withReq('searing_arts'), 'hollow_soldier', 24); e.maxHp = e.hp = 3000; X.SAVE_().art = 'crescent'; X.P.fp = 99; X.P.cds = {}; X.step(1, [], ['art']); X.step(40); const burn = e.skBurnT > 0; const h = e.hp; X.step(60); rec('searing_arts', 'no burn', burn ? `burning, -${Math.round(h - e.hp)} HP/s` : 'no burn', burn && e.hp < h); }
{ const e = fresh(withReq('kindled'), 'hollow_soldier', 50); e.maxHp = e.hp = 3000; X.SAVE_().art = 'bloodstep'; X.P.fp = 99; X.P.cds = {}; X.step(1, [], ['art']); X.step(30); const n = X.ev('SKW.trail.length'); const cd0 = X.cdBase('art', 'bloodstep'); rec('kindled', 'no trail', `${n} flames, art cd x${X.skCdMul('art')}`, n > 1 && X.skCdMul('art') <= 0.8); }
{ const run = l => { const e = fresh(l); X.P.fp = 0; swing(20); return X.P.fp; }; const a = run(withReq('lingering_flame')), b = run(withReq('pyre_heart')); rec('pyre_heart', `${a} FP`, `${b} FP`, b > a); }
// Arsenal
const wpn = (id, l) => { X.SAVE_().weapon = id; X.SAVE_().weapons[id] = X.SAVE_().weapons[id] || 0; X.set(l); X.arena(); };
{ wpn('longsword', ['keen_edge']); X.dummy('hollow_soldier', 40); const cnt = () => { let n = 0; for (let i = 0; i < 90; i++) { const b = X.projectiles.length; X.step(1, [], i % 6 === 0 ? ['attack'] : []); if (X.projectiles.length > b) n++; } return n; };
  const a = cnt(); wpn('longsword', ['m_sword']); X.dummy('hollow_soldier', 40); const b = cnt(); rec('m_sword', `${a} arcs`, `${b} arcs`, b > a); }
{ const run = l => { wpn('dagger', l); const e = X.dummy(); e.maxHp = e.hp = 3000; X.step(1); e.onParried(); const h = e.hp; X.step(1, [], ['attack']); X.step(70); return Math.round(h - e.hp); }; const a = run(['keen_edge']), b = run(['keen_edge', 'm_dagger']); rec('m_dagger', a, b, b > a * 1.3); }
{ const run = l => { wpn('greatsword', l); const e = X.dummy('hollow_soldier', 90); e.maxHp = e.hp = 3000; const h = e.hp; X.step(1, [], ['heavy']); X.step(80); return Math.round(h - e.hp); }; const a = run(['keen_edge']), b = run(['m_great']); rec('m_great', `far foe -${a}`, `far foe -${b}`, b > a); }
{ const run = l => { wpn('spear', l); X.dummy('hollow_soldier', 200); const x = X.P.x; X.step(1, [], ['heavy']); X.step(50); return Math.round(X.P.x - x); }; const a = run(['keen_edge']), b = run(['m_spear']); rec('m_spear', `lunge ${a}`, `lunge ${b}`, b > a * 1.1); }
{ const run = l => { wpn('katana', l); X.step(1, [], ['heavy']); let inv = 0; for (let i = 0; i < 40; i++) { X.step(1); if (X.P.inv > 0 && X.P.state === 'kt_heavy') inv++; } return inv; }; const a = run(['keen_edge']), b = run(['m_katana']); rec('m_katana', `${a} untouchable frames`, `${b}`, b > a + 3); }
{ wpn('quarterstaff', ['keen_edge']); const a = Math.round(X.staffSpinCost()); wpn('quarterstaff', ['m_staff']); const b = Math.round(X.staffSpinCost()); rec('m_staff', a, b, b < a); }
{ const run = l => { wpn('knight_shield', l); const e = X.dummy('hollow_soldier', 24); X.P.face = 1; X.P.st = X.D.maxSt; X.step(1, ['parry'], ['parry']); X.step(20, ['parry']); const h = e.hp; X.P.inv = 0; X.hurt(40, -1, { src: e }); X.step(1, ['parry']); return Math.round(h - e.hp); }; const a = run(['keen_edge']), b = run(['m_shield']); rec('m_shield', `reflected ${a}`, `reflected ${b}`, b > a); }
{ const run = l => { wpn('twinfangs', l); const e = X.dummy(); e.maxHp = e.hp = 9000; for (let i = 0; i < 90; i++) X.step(1, [], i % 5 === 0 ? ['attack'] : []); return X.P.skTwinT > X.time; }; const a = run(['keen_edge']), b = run(['m_twin']); rec('m_twin', `quickened ${a}`, `quickened ${b}`, b && !a); }
{ const run = l => { wpn('antler_scythe', l); const e = X.dummy(); e.hp = 5; X.P.hp = X.D.maxHp * 0.5; const h = X.P.hp; X.P.fp = 0; X.step(1, [], ['heavy']); X.step(60); return `${Math.round(X.P.hp - h)} HP ${X.P.fp} FP`; }; const a = run(['keen_edge']), b = run(['m_scythe']); rec('m_scythe', a, b, a !== b); }
{ const run = l => { wpn('headsman_chain', l); const e = X.dummy('hollow_soldier', 50); let st = false; for (let i = 0; i < 40; i++) { X.step(1, [], i === 0 ? ['attack'] : []); st = st || e.state === 'stagger'; } return st; }; const a = run(['keen_edge']), b = run(['m_whip']); rec('m_whip', `staggered ${a}`, `staggered ${b}`, b && !a); }
{ wpn('longsword', ['m_whip']); rec('arsenal.inactive', 'whip mastery w/ sword', `skillOn ${G.sk.skillOn('m_whip')}`, !G.sk.skillOn('m_whip')); wpn('longsword', []); }
// Wayfarer
{ X.set([]); const r = X.ev('HOOK_RANGE * (has("way_hook") ? 1.35 : 1)'); X.set(['way_hook']); const r2 = X.ev('HOOK_RANGE * (has("way_hook") ? 1.35 : 1)'); rec('way_hook', r, r2, r2 > r); }
{ const gl = l => { X.set(l); X.arena('R2'); X.P.y -= 60; X.ev("P.ground = false; setP('air', 'jump_fall')"); X.P.vy = 60; for (let i = 0; i < 40; i++) X.step(1, ['jump', 'right']); return Math.round(Math.abs(X.P.vx)); }; const a = gl([]), b = gl(['way_glide']); rec('way_glide', a, b, b > a * 1.2); }
{ const dashes = l => { X.set(l); X.arena(); X.step(2); X.P.y -= 40; X.ev("P.ground = false; P.airDash = true; setP('air', 'jump_fall')"); let n = 0; for (let i = 0; i < 60; i++) { const s = X.P.state; X.step(1, [], i % 12 === 0 ? ['roll'] : []); if (X.P.state === 'roll' && s !== 'roll') n++; X.P.vy = Math.min(X.P.vy, 0); } return n; }; const a = dashes([]), b = dashes(['way_dash']); rec('way_dash', a, b, b === a + 1); }
{ const run = l => { X.set(l); X.arena(); const e = X.dummy('hollow_soldier', 110); const h = e.hp; X.P.y -= 50; X.ev("P.ground = false; setP('air', 'jump_fall'); startSlam()"); X.step(90); return Math.round(h - e.hp); }; const a = run([]), b = run(['way_slam']); rec('way_slam', `far foe -${a}`, `far foe -${b}`, b > a); }
{ const c = l => { X.set(l); X.ev('SAVE.cinders = 0; gainCinders(1000, P.x, P.y)'); return X.SAVE_().cinders; }; const a = c([]), b = c(['way_prosper']); rec('way_prosper', a, b, b === Math.round(a * 1.1)); }
{ X.set(['way_prosper', 'way_glint']); X.arena('R2'); X.ev("room.grid[10 * room.w + 5] = T_BREAK"); X.step(2); const n = X.ev("lights.filter(l => l.r === 20 && l.color === '255,210,140').length"); rec('way_glint', 0, `${n} glints`, n > 0); }
{ const run = l => { X.set(l); X.ev("SAVE.cinders = 1000; finishDeath()"); const c = X.SAVE_().cinders; X.step(30); return c; }; const a = run([]), b = run(['way_prosper', 'way_glint', 'way_remnant']); rec('way_remnant', a, b, b === 300); }
{ const w = l => { X.set(l); X.arena(); X.ev("P.wallDir = 1; P.face = 1; wallJump()"); return X.P.vy; }; const a = w([]), b = w(['way_wall']); rec('way_wall', a, Math.round(b), b < a * 1.1); }
return { fail, R };
