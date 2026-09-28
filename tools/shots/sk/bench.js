// build bench: boss DPS and survivability for representative skill builds (same inputs for every build)
// SHOT_HTML=web/dist/sk.html node tools/shots/shot.js tools/shots/sk/bench.js tools/shots/sk/out
await boot(); G.giveArmory(); G.grantTechniques();
const E = G.sk.ev, by = G.sk.SKILL_BY, free = () => ['idle', 'run', 'land'].includes(G.P.state);
const withReq = ids => { const out = []; const go = x => { for (const r of by[x].req) go(r); if (!out.includes(x)) out.push(x); }; ids.forEach(go); return out; };
const full = (b, f1 = 'a', f2 = 'a') => G.sk.SKILLS.filter(s => s.br === b && (!/^f/.test(s.slot) || s.slot === 'f1' + f1 || s.slot === 'f2' + f2)).map(s => s.id);
const BUILDS = (typeof ONLY_BUILDS !== 'undefined' && ONLY_BUILDS) || {
  none: [],
  blade: full('blade'), blade_b: full('blade', 'b', 'b'), ash: full('ash'), ash_b: full('ash', 'b', 'b'), veil: full('veil'), veil_b: full('veil', 'b', 'b'),
  blood: full('blood'), blood_b: full('blood', 'b', 'b'), flame: full('flame'), flame_b: full('flame', 'b', 'b'),
  'blade+blood': [...full('blade'), ...full('blood')], 'blade+veil': [...full('blade'), ...full('veil')], 'ash+flame': [...full('ash'), ...full('flame')],
  'blood+flame': [...full('blood'), ...full('flame')], 'veil+ash': [...full('veil'), ...full('ash')], 'blade+flame': [...full('blade'), ...full('flame')],
  // casters: same stat total, spent on Faith and Mind; compared with none_c (a caster with no skills)
  // buff arts: the Flame branch played with Cinder Blade / War Cry (arts are swappable)
  none_cb: { a: 'cinderblade', s: [] }, flame_cb: { a: 'cinderblade', s: full('flame') }, flame_b_wc: { a: 'warcry', s: full('flame', 'b', 'b') }, 'ash+flame_cb': { a: 'cinderblade', s: [...full('ash'), ...full('flame')] },
  'blood+flame_cb': { a: 'cinderblade', s: [...full('blood'), ...full('flame')] }, 'blade+flame_cb': { a: 'cinderblade', s: [...full('blade'), ...full('flame')] },
  none_c: { c: [] }, ash_c: { c: full('ash') }, ash_b_c: { c: full('ash', 'b', 'b') }, 'ash+flame_c': { c: [...full('ash'), ...full('flame')] }, 'veil+ash_c': { c: [...full('veil'), ...full('ash')] },
};
const ST_M = { vig: 35, mnd: 25, end: 25, str: 30, dex: 30, fth: 25 }, ST_C = { vig: 35, mnd: 35, end: 20, str: 18, dex: 22, fth: 40 };
const WEAPON = (typeof ONLY_WEAPON !== 'undefined' && ONLY_WEAPON) || 'longsword';
const SECS = (typeof BENCH_SECS !== 'undefined' && BENCH_SECS) || 40, BLOW = 70;
const out = {};
for (const [name, bd] of Object.entries(BUILDS)) {
  { let seed = 12345; Math.random = () => (seed = (seed * 16807) % 2147483647) / 2147483647; }   // same dice for every build
  const cst = !Array.isArray(bd) && !!bd.c, skills = Array.isArray(bd) ? bd : bd.c || bd.s, art = !Array.isArray(bd) && bd.a;
  G.SAVE.weapon = WEAPON; G.SAVE.weapons[WEAPON] = 5; G.SAVE.art = art || E('WEAPONS[SAVE.weapon].art') || 'crescent';
  G.give({ stats: { ...(cst ? ST_C : ST_M) }, spellsOwned: ['ash_bolt', 'sunspear', 'emberburst'], spellsEq: ['ash_bolt', 'sunspear'], spell: 'ash_bolt', charmsEq: [], skills: [...skills] });
  delete G.SAVE.flags['boss:hound']; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'hound'] = 1;
  G.tp('C5', 6, 10); const b = G.boss;
  for (let i = 0; i < 200 && !b.active; i++) { G.step(4, ['right']); G.P.hp = 99999; if (G.state !== 'play') G.step(1, [], ['pause']); }
  const bx = b.x, by0 = b.y; b.update = function (dt) { this.x = bx; this.y = by0; this.commonUpdate(dt); if (this.state === 'stagger') { this.anim.update(dt); this.t -= dt; if (this.t <= 0) { this.state = 'idle'; this.anim.set('idle', true); } } };   // staggers open it to ripostes
  b.state = 'idle'; b.maxHp = 3500; b.hp = 1e7;   // bleed bursts scale with max HP: keep it boss-sized
  E('refreshDerived(false); P.hp = D.maxHp; P.fp = D.maxFp; P.st = D.maxSt; refillFlasks(); P.cds = {}; P.skRel = 0; hitstop = 0; slowmo = 0; clearBuffer()');
  G.P.x = bx - 34; G.P.face = 1;
  const caster = cst || skills.some(id => by[id] && by[id].br === 'ash');
  let dealt = 0, lost = 0, healed = 0, blows = 0, landed = 0, hp = G.P.hp;
  for (let f = 0; f < 60 * SECS; f++) {
    const tap = [], cyc = Math.floor(f / 120), dodge = cyc % 3 === 0;
    // greedy player: spells and arts whenever they're ready and paid for, light combos between, a roll's worth of stamina kept back
    const ready = E(`[(() => { const r = SAVE.spellsEq.find(id => cdLeft('spell', id) <= 0 && P.fp >= spellCost(id)); if (r && P.state !== 'cast') SAVE.spell = r; return !!r; })(), cdLeft('art', SAVE.art) <= 0 && P.fp >= Math.round(ARTS[SAVE.art].fp * skArtCostMul())]`);
    // souls rhythm: a 1.3 s opening to attack in, then the boss swings (one blow in three is dodged)
    const open = f % 120 < 80;
    const want = (ready[0] && caster) || ready[1];   // only Ash builds spend FP on spells; a ready spell or art waits for the combo to end
    if (open && free()) { if (ready[0] && caster) tap.push('cast'); else if (ready[1]) tap.push('art'); }
    if (open && !want && f % 6 === 0 && G.P.st > 35) tap.push('attack');   // mash: the combo chains as fast as it allows
    if (!tap.length && f % 360 === 20 && G.P.st > 45) tap.push('heavy');
    if (f % 120 === 84 && G.P.fp < 25 && G.P.flasksB > 0 && free()) tap.push('mana');   // drink the azure flask when FP runs dry
    if (f % 120 === 113 && dodge) E("hitstop = 0; if (P.state !== 'roll') { setP('idle', 'idle', true); P.st = Math.max(P.st, 20); doRoll(0); }");   // one blow in three is dodged, just in time
    const h0 = b.hp;
    G.step(1, [], tap);
    if (b.hp < h0) dealt += h0 - b.hp;
    if (f % 120 === 119) { blows++; const hpb = G.P.hp; E(`P.lastHit = null; hurtPlayer(${BLOW}, P.x < boss.x ? 1 : -1, 'bench' + time, { src: boss })`); if (G.P.hp < hpb) { landed++; lost += hpb - G.P.hp; } }
    if (G.P.hp > hp) healed += G.P.hp - hp;
    hp = G.P.hp;
    if (G.P.hp < G.D.maxHp * 0.25) { G.P.hp = G.D.maxHp * 0.6; hp = G.P.hp; }   // keep Last Stand / Blood on the edge now and then
    if (G.state !== 'play') G.step(1, [], ['pause']);
    if (G.P.ground && ['idle', 'run'].includes(G.P.state) && Math.abs(G.P.x - (bx - 34)) > 4) { G.P.x = bx - 34; G.P.face = 1; }
  }
  const net = (lost - healed) / SECS * 60, flaskHp = E('P.flasksR = 0; refillFlasks(); P.flasksR * Math.round((D.maxHp * 0.42 + 20) * flaskMul())');
  out[name] = { dps: Math.round(dealt / SECS), taken: Math.round(lost), healed: Math.round(healed), landed: `${landed}/${blows}`, netPerMin: Math.round(net), maxHp: G.D.maxHp, surviveS: net > 0 ? Math.round((G.D.maxHp + flaskHp) / net * 60) : 999, flaskHp, cost: E(`skillSpent(${JSON.stringify(skills)})`) };
}
return out;
