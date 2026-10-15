// ------------------------------------------------------------------ v15 CORES (agent `cores`, docs/v15/cores.md)
// 1. Boss Cores: every boss drops its Core on the first kill. SAVE.cores { kind: 1 } -- one per boss for the whole save
//    lineage: New Game+ keeps them (like Weapon Mastery) and a repeat kill never duplicates one.
// 2. Enchanting at the Ashwright ("Enchant a weapon"): socket one Core into the weapon in hand. SAVE.enchants { type: kind }:
//    each weapon type keeps its own; a Core sits in one weapon at a time; removing it is free and returns it.
//    The Core's TRAIT only touches the weapon's finishers, heavies, counters and charged releases (crElig), and every trait
//    is tuned to about +8-15% effective damage on those moves (or a utility of similar worth). Two channels:
//      * the edge: mvHitCtx is wrapped, the move's damage / stance multiplier grows (never stacks with itself)
//      * the proc: HOOKS.strike, status / delayed strikes / sustain, with internal cooldowns and per-target gates
// 3. Visuals: the enchanted move's slash light (spawnFx tint), the tip ribbon and impact sparks (feelElement) take the Core's
//    colour; an idle blade breathes a faint ember of it.
// 4. Rekindle: in a defeated boss's room an ember effigy offers "Rekindle <boss>": the boss's own spawn runs again (flag lifted
//    only for the synchronous room rebuild, so saves always hold it), the arena seals as it did, death costs nothing, a win
//    gives Mastery XP and 10% of its cinders, never a Core, items or story flags.
// Everything hooks in from this file (wrappers); no other file is edited.

const CR = { mv: 0, cd: {}, vfx: [], tint: null, reso: { n: 0, t: -9 }, kindle: 0, kindleT: -9, twin: 0, bell: 0, star: 0, log: [] };
const CR_COST = 400;                 // cinders to socket a Core (removing is free)
const CR_REMATCH_CINDERS = 0.1;      // a rekindled kill pays this share of the boss's cinders
const CR_REMATCH_XP = 150;           // and this much Weapon Mastery (the same as any repeat boss kill)
const CR_NO_REMATCH = new Set(['venn']);   // her death is the betrayal ending itself: not something to rekindle

// ================================================================== the 32 Cores
// col: the element colour (slash light, sparks, glow) · pk: the particle it sheds · edge: flat damage share on eligible moves
// poise: stance multiplier on eligible moves · edgeFn(t, A): situational extra · proc(t, info, A, x): on each eligible hit
const CORES = {
  hound: { name: 'Gravetusk’s Core', trait: 'Rend', col: '#c8342c', pk: 'blood',
    desc: 'Enchanted blows mark the foe. The third mark within 6 s tears it open for 30% of that blow.',
    proc(t, info, A, x) { if (!x.first) return; const m = t._crRend && P.clk - t._crRend.t < 6 ? t._crRend : (t._crRend = { n: 0, t: 0 });
      m.n++; m.t = P.clk; if (m.n >= 3) { m.n = 0; crStrike(t, x.acc.dmg * 0.30, { col: this.col }); crBurst(t, this.col, 'blood', 8); } } },
  oswin: { name: 'Pilgrim’s Core', trait: 'Wayfarer’s Wind', col: '#d6dccc', pk: 'dust', edge: 0.04,
    desc: '+4% damage, and the roll you take within 2 s of an enchanted blow costs no stamina.',
    proc(t, info, A, x) { if (x.first) { P._crFreeRoll = P.clk + 2; crU('rollArm', 1); } } },
  coven: { name: 'Coven Core', trait: 'Thornbind', col: '#7ab04c', pk: 'spore',
    desc: 'Thorns take root: 9% of each enchanted blow as damage over 3 s. Fresh thorns refresh the old, never stack past twice.',
    proc(t, info) { crDot(t, info.dmg * 0.09, 3, this); } },
  warden: { name: 'Antlered Core', trait: 'Antler’s Weight', col: '#b8b070', pk: 'dust', edge: 0.03, poise: 0.25,
    desc: '+25% stance damage and +3% damage: great foes break sooner under your heavier blows.' },
  omen: { name: 'Omen Core', trait: 'Omen Line', col: '#ffd27a', pk: 'gold',
    desc: 'A golden line flares under the foe and erupts 0.45 s later for 14% of the move’s damage (once every 1.5 s).',
    proc(t, info, A, x) { if (!x.first || !crCd('omen', 1.5)) return; const acc = x.acc, fy = crFloorY(t);
      CR.vfx.push({ k: 'line', x: t.x, y: fy, w: 30, life: 0.45, max: 0.45, col: this.col });
      mvLater(0.45, () => { if (crLive(t)) { crStrike(t, acc.dmg * 0.14, { col: this.col }); CR.vfx.push({ k: 'pillar', x: t.x, y: fy, life: 0.25, max: 0.25, col: this.col }); } }); } },
  vessel: { name: 'Vessel Core', trait: 'Rot Sap', col: '#9ab040', pk: 'spore',
    desc: 'Each enchanted move seeds rot: 10% of its damage over 5 s. Up to three rots run at once.',
    proc(t, info) { crRot(t, info.dmg * 0.10, 5, this); } },
  kalden: { name: 'Oathless Core', trait: 'Unbroken Oath', col: '#e8a858', pk: 'ember',
    desc: 'Enchanted moves can’t be flinched by blows under 20% of your max HP, and you take 10% less damage while they play.' },
  librarian: { name: 'Librarian’s Core', trait: 'Overdue', col: '#a080e0', pk: 'ink',
    desc: 'An enchanted move slips a page into the foe. Your next ordinary blow on it within 4 s tears the page for 15% of that move.',
    proc(t, info, A, x) { if (x.first) { t._crPage = { acc: x.acc, until: P.clk + 4 }; crBurst(t, this.col, 'ink', 4); } } },
  unwritten: { name: 'Unwritten Core', trait: 'Redaction', col: '#6a4ab4', pk: 'ink', edge: 0.04,
    desc: '+4% damage, and the foe is blotted for 3 s: its blows land 12% softer (8% for great foes).',
    proc(t, info, A, x) { if (x.first) { t._crInkT = 3; crU('ink', 1); } } },
  ferryman: { name: 'Ferryman’s Core', trait: 'Toll of Breath', col: '#60d0c0', pk: 'teal',
    desc: 'Enchanted blows return 8 stamina (at most every 0.6 s).',
    proc() { if (crCd('ferry', 0.6)) { P.st = Math.min(D.maxSt, P.st + 8); crU('stam', 8); crMote(this.col); } } },
  choir: { name: 'Choir Core', trait: 'Resonance', col: '#70e8d8', pk: 'teal',
    desc: 'Each enchanted move within 4 s of the last rings 4% harder than the one before, up to +12%. Pause and the chord fades.',
    edgeFn() { return 0.04 * CR.reso.n; } },
  champion: { name: 'Champion’s Core', trait: 'Unyielding', col: '#d8b878', pk: 'gold',
    desc: '+12% damage while you haven’t been hit for 6 s; +4% otherwise.',
    edgeFn() { return P.clk - (P._crHurtT ?? -99) > 6 ? 0.12 : 0.04; } },
  ice_warden: { name: 'Glacial Core', trait: 'Chill', col: '#a8dcff', pk: 'frost', edge: 0.05,
    desc: '+5% damage; the foe is chilled, 15% slower for 2 s. Great foes resist: 6% for under a second, less each time.',
    proc(t, info, A, x) { if (x.first) crSlow(t, 0.85, 2); } },
  twins: { name: 'Twinned Core', trait: 'Flame and Frost', col: '#ff9a50', col2: '#a8dcff', pk: 'fire', pk2: 'frost', edge: 0.03,
    desc: 'Enchanted moves alternate: flame burns for 8% of the blow over 3 s, frost chills the foe (10% slower). +3% damage.',
    proc(t, info, A, x) { if (CR.twinCur) crDot(t, info.dmg * 0.08, 3, { col: '#ff9a50', pk: 'fire' }); else if (x.first) crSlow(t, 0.9, 1.5); } },
  butler: { name: 'Vesper’s Core', trait: 'Attentive', col: '#c8ccdc', pk: 'spark',
    desc: 'An enchanted move hastens the move after it by 12% (if it starts within 1.5 s).',
    proc(t, info, A, x) { if (x.first) { P._crHaste = P.clk + 1.5; crU('hasteArm', 1); } } },
  sanguine: { name: 'Sanguine Core', trait: 'Blood Tithe', col: '#c0182c', pk: 'blood',
    desc: 'Heal 5% of the damage your enchanted blows deal, at most 2% of your max HP per move.',
    proc(t, info) { if (CR.leechMv !== CR.mv) { CR.leechMv = CR.mv; CR.leech = 0; }
      const h = Math.min(info.dmg * 0.05, D.maxHp * 0.02 - CR.leech); if (h > 0.05) { P.hp = Math.min(D.maxHp, P.hp + h); CR.leech += h; crU('heal', h); crMote(this.col); } } },
  executioners: { name: 'Headsman’s Core', trait: 'Verdict', col: '#b04838', pk: 'blood', edge: 0.03,
    desc: '+3% damage, and +25% against foes below 30% of their health.',
    edgeFn(t) { const mx = t && (t.maxHp || 0); return mx && t.hp / mx < 0.3 ? 0.25 : 0; } },
  vael: { name: 'Hollow Crown Core', trait: 'Grief’s Due', col: '#90a8e8', pk: 'mote',
    desc: 'Enchanted blows restore 3 FP (at most every 0.8 s).',
    proc() { if (crCd('vael', 0.8)) { P.fp = Math.min(D.maxFp, P.fp + 3); crU('fp', 3); crMote(this.col); } } },
  bellringer: { name: 'Bell Core', trait: 'Toll', col: '#d89848', pk: 'gold',
    desc: 'Every third enchanted move tolls: a ring of 56 px strikes every foe in it for 30% of the move and 40 stance.',
    proc(t, info, A, x) { if (!x.firstAny) return; if (++CR.bell < 3) return; CR.bell = 0; const acc = x.acc, cx = t.x, cy = crFloorY(t) - 16;
      mvLater(0.18, () => { CR.vfx.push({ k: 'ring', x: cx, y: cy, r: 56, life: 0.35, max: 0.35, col: this.col }); crTone(520, 0.5, 0.05);
        for (const q of targets()) { if (q.prop) continue; const hb = hbOf(q); if (!hb || Math.hypot((hb.x0 + hb.x1) / 2 - cx, (hb.y0 + hb.y1) / 2 - cy) > 56 + 10) continue; crStrike(q, acc.dmg * 0.30, { col: this.col, poise: 40 }); } }); } },
  cindervane: { name: 'Drake Core', trait: 'Stormcall', col: '#9ac8ff', pk: 'spark', edge: 0.04,
    desc: '+4% damage; lightning arcs to the nearest other foe within 90 px for 35% of the blow (every 0.5 s). Alone, it grounds into the foe for 4%.',
    proc(t, info) {
      let best = null, bd = 90;
      for (const q of targets()) { if (q === t || q.prop || q.alive === false) continue; const d = Math.hypot(q.x - t.x, (q.y - t.y)); if (d < bd) { bd = d; best = q; } }
      if (best && crCd('arc', 0.5)) { const hb = hbOf(best); CR.vfx.push({ k: 'arc', x0: info.x, y0: info.y, x1: hb ? (hb.x0 + hb.x1) / 2 : best.x, y1: hb ? (hb.y0 + hb.y1) / 2 : best.y - 14, life: 0.14, max: 0.14, col: this.col, seed: Math.random() });
        crStrike(best, info.dmg * 0.35, { col: this.col }); crTone(1800, 0.06, 0.03, 'square'); }
      else if (!best) crDmg(t, info.dmg * 0.04, { col: this.col }); } },
  overseer: { name: 'Overseer’s Core', trait: 'Forgefire', col: '#ff9038', pk: 'fire',
    desc: 'Enchanted blows set the foe alight: 10% of the blow as fire over 3 s. Fresh fire refreshes the old, never stacks past twice.',
    proc(t, info) { crDot(t, info.dmg * 0.10, 3, this); } },
  colossus: { name: 'Colossus Core', trait: 'Molten Crack', col: '#ff5a20', pk: 'fire',
    desc: 'An enchanted move cracks the foe’s shell: for 4 s it takes 6% more from every blow you land (refreshes, never stacks).',
    proc(t, info, A, x) { if (x.first) { t._crVulnT = 4; crU('crack', 1); } } },
  scarab: { name: 'Scarab Core', trait: 'Sun Shell', col: '#e8c060', pk: 'gold', edge: 0.03,
    desc: '+3% damage; an enchanted move raises a sun-shell that soaks 8% of your max HP from the next blow within 3 s (every 6 s).',
    proc(t, info, A, x) { if (x.first && crCd('shell', 6)) { P._crShell = D.maxHp * 0.08; P._crShellT = 3; crU('shell', 1); } } },
  pharaoh: { name: 'Pharaoh’s Core', trait: 'Dusk Count', col: '#c890e8', pk: 'mote',
    desc: 'An enchanted move marks the foe with dusk; 3 s later the mark falls for 25% of that move. One mark per foe at a time.',
    proc(t, info, A, x) { if (!x.first || (t._crDusk && t._crDusk > P.clk)) return; t._crDusk = P.clk + 3; const acc = x.acc;
      CR.vfx.push({ k: 'sigil', t, life: 3, max: 3, col: this.col });
      mvLater(3, () => { if (crLive(t)) { crStrike(t, acc.dmg * 0.25, { col: this.col }); crBurst(t, this.col, 'mote', 10); } }); } },
  orrery: { name: 'Orrery Core', trait: 'Orbit', col: '#d8e0ff', pk: 'mote', edge: 0.05, poise: 0.10,
    desc: '+5% damage, +10% stance; enchanted moves draw small foes within 72 px in toward the blow.',
    proc(t, info, A, x) { if (!x.firstAny) return; for (const q of targets()) { if (q.prop || crGreat(q) || q.alive === false || q === t) continue; const dx = info.x - q.x; if (Math.abs(dx) > 72 || Math.abs(q.y - t.y) > 40) continue;
      const step = clamp(dx * 0.5, -22, 22), nx = q.x + step; if (!solidAtPx(nx, q.y - 6)) { q.x = nx; crU('pull', 1); } } } },
  astrel: { name: 'Star Core', trait: 'Starfall', col: '#eef4ff', pk: 'mote',
    desc: 'Every third enchanted move calls a falling star onto its foe for 30% of the move.',
    proc(t, info, A, x) { if (!x.firstAny || ++CR.star < 3) return; CR.star = 0; const acc = x.acc, tx = info.x, ty = info.y;
      CR.vfx.push({ k: 'star', x: tx, y: ty, life: 0.25, max: 0.25, col: this.col });
      mvLater(0.25, () => { if (crLive(t)) { crStrike(t, acc.dmg * 0.30, { col: this.col }); crBurst(t, this.col, 'mote', 8); } }); } },
  enforcer: { name: 'Enforcer Core', trait: 'Curfew', col: '#ff4858', pk: 'spark', edge: 0.05,
    desc: '+5% damage; enchanted moves jolt foes: small foes stagger (once per 4 s each), great foes only slow 10% for a moment.',
    proc(t, info, A, x) { if (!x.first) return; if (crGreat(t)) crSlow(t, 0.9, 0.5); else if (t.breakStance && t.state !== 'stagger' && crTCd(t, 'curfew', 4)) { t.breakStance(); crU('stagger', 1); } } },
  saint0: { name: 'Null Core', trait: 'Nullify', col: '#a8f4ff', pk: 'spark', edge: 0.04,
    desc: '+4% damage; an enchanted move erases enemy projectiles within 64 px of the blow (every 2 s).',
    proc(t, info, A, x) { if (!x.firstAny || !crCd('null', 2)) return; let n = 0;
      projectiles = projectiles.filter(p => { if (p.owner === 'player' || Math.hypot(p.x - info.x, p.y - info.y) > 64) return true; n++; return false; });
      if (n) { CR.vfx.push({ k: 'ring', x: info.x, y: info.y, r: 64, life: 0.3, max: 0.3, col: this.col }); crTone(2400, 0.12, 0.03); crU('nulled', n); } } },
  sentinels: { name: 'Gilded Core', trait: 'Twin Oath', col: '#ffd870', pk: 'gold',
    desc: 'A gilded echo strikes 0.3 s after each enchanted move for 12% of its damage.',
    proc(t, info, A, x) { if (!x.first) return; const acc = x.acc;
      mvLater(0.3, () => { if (crLive(t)) { crStrike(t, acc.dmg * 0.12, { col: this.col }); const hb = hbOf(t); if (hb) spawnFx('slash', (hb.x0 + hb.x1) / 2, (hb.y0 + hb.y1) / 2, P.face, null, { tint: this.col, alpha: 0.7 }); } }); } },
  sovereign: { name: 'Sovereign Core', trait: 'Kneel', col: '#fff0c8', pk: 'petal', edge: 0.04, poise: 0.15,
    desc: '+15% stance damage and +4% damage; a staggered foe takes 8% more from enchanted moves.',
    edgeFn(t) { return t && t.state === 'stagger' ? 0.08 : 0; } },
  first_ember: { name: 'First Ember Core', trait: 'Kindling', col: '#ff6a24', pk: 'ember',
    desc: 'Enchanted moves build kindling. After three, the next enchanted move burns it all for +40% damage.',
    edgeFn() { return CR.kindleMv === CR.mv ? 0.40 : 0; } },
  venn: { name: 'Last Kindling Core', trait: 'Last Flame', col: '#f4eedc', pk: 'petal',
    desc: '+16% damage while you are below 40% health; +4% otherwise.',
    edgeFn() { return D && P.hp / D.maxHp < 0.4 ? 0.16 : 0.04; } },
};
// the order cores are listed in: the journey's own (BOSS_STAGE, 69_adaptive.js)
function crOrder() { const st = typeof BOSS_STAGE !== 'undefined' ? BOSS_STAGE : {}; return Object.keys(CORES).sort((a, b) => (st[a] ?? 99) - (st[b] ?? 99)); }
const crRGB = h => { const s = h.slice(1); return [0, 2, 4].map(i => parseInt(s.slice(i, i + 2), 16)).join(','); };
for (const [k, c] of Object.entries(CORES)) { c.kind = k; c.rgb = crRGB(c.col); if (c.col2) c.rgb2 = crRGB(c.col2); }

// ================================================================== saves
function crStore() { if (!SAVE) return { cores: {}, enchants: {} }; if (!SAVE.cores || typeof SAVE.cores !== 'object') SAVE.cores = {}; if (!SAVE.enchants || typeof SAVE.enchants !== 'object') SAVE.enchants = {}; return SAVE; }
function crOwned(kind) { return !!crStore().cores[kind]; }
function crOwnedList() { const S = crStore(); return crOrder().filter(k => S.cores[k]); }
function crWhere(kind) { const E = crStore().enchants; for (const [t, k] of Object.entries(E)) if (k === kind) return t; return null; }   // the type that holds it
function crTypeNow() { try { return wtype(); } catch (e) { return 'longsword'; } }
function crEnchantOf(type) { const k = crStore().enchants[type || crTypeNow()]; return k && CORES[k] && crOwned(k) ? k : null; }
function crCur() { if (!SAVE || !P) return null; const k = crEnchantOf(); return k ? CORES[k] : null; }
function crSocket(kind, type) {
  const S = crStore(); type = type || crTypeNow();
  if (!CORES[kind] || !S.cores[kind]) return false;
  const was = crWhere(kind); if (was) delete S.enchants[was];
  S.enchants[type] = kind; return true;
}
function crUnsocket(type) { const S = crStore(); type = type || crTypeNow(); const k = S.enchants[type]; delete S.enchants[type]; return k || null; }
function crGrant(kind, quiet) {
  const S = crStore(); if (!CORES[kind] || S.cores[kind]) return false;
  S.cores[kind] = 1; CR.log.push(['core', kind]);
  if (!quiet) { const c = CORES[kind]; banner(c.name, `${c.trait}: ${c.desc} The Ashwright can set it in a weapon.`, 'core_' + kind); if (typeof sfx !== 'undefined' && sfx.pickup) sfx.pickup(); }
  return true;
}
// New Game+ keeps every Core and every enchant (the same rule as Weapon Mastery)
{ const _ng = startNGPlus; startNGPlus = function (...a) {
  const c = SAVE.cores, e = SAVE.enchants;
  const r = _ng.apply(this, a);
  SAVE.cores = { ...(c || {}) }; SAVE.enchants = { ...(e || {}) }; saveGame();
  return r;
}; }

// ================================================================== which moves an enchant touches
// finishers (mv.fin), heavies (kind 'heavy'), counters, charged releases; never weapon arts ('tech'), plunges or criticals
function crElig(A) {
  if (!A || !A.mv || A.cls === 'tech' || A.plunge) return false;
  const d = A.mv;
  return !!(d.fin || A.kind === 'heavy' || A.counter || d.punish || (P && P.charged && P.state === d.id));
}
function crActive(A) { return !!(crCur() && crElig(A)); }
const crGreat = t => !!(t && (t.boss || (typeof boss !== 'undefined' && boss && (t === boss || (boss.parts && boss.parts.includes(t)))) || (t.cfg && t.cfg.elite)));
const crBossy = t => !!(t && typeof boss !== 'undefined' && boss && (t === boss || (boss.parts && boss.parts.includes(t))));
const crLive = t => !!t && t.alive !== false && !(t.hp <= 0 && !crBossy(t)) && (!crBossy(t) || (boss && boss.alive && boss.active));
// cooldowns: global (per key) and per target, on the player's own clock
function crU(k, n) { CR.u = CR.u || {}; CR.u[k] = (CR.u[k] || 0) + n; }
function crCd(key, s) { const now = P.clk || 0; if ((CR.cd[key] ?? -99) > now) return false; CR.cd[key] = now + s; return true; }
function crTCd(t, key, s) { const now = P.clk || 0; t._crCd = t._crCd || {}; if ((t._crCd[key] ?? -99) > now) return false; t._crCd[key] = now + s; return true; }
function crFloorY(t) { const hb = t && t.hurtbox && t.hurtbox(); return hb ? hb.y1 : t.y; }

// ---- damage helpers
// a quiet tick (DoT, grounding bolt): bosses lose it straight from their health, never the killing blow (as burn does)
function crDmg(t, d, o = {}) {
  if (!t || t.prop || !(d > 0.5) || !crLive(t)) return;
  d = Math.max(1, Math.round(d));
  const hb = t.hurtbox && t.hurtbox(), x = hb ? (hb.x0 + hb.x1) / 2 : t.x, y = hb ? hb.y0 + 6 : t.y - 20;
  CR.dealt = (CR.dealt || 0) + d;
  if (crBossy(t)) {
    if (t.hidden || t.offmap) return;
    t.hp = Math.max(1, t.hp - d); t.dmgShown = (t.dmgT > 0 ? t.dmgShown || 0 : 0) + d; t.dmgT = Math.max(t.dmgT || 0, 1.0);
    if (boss && boss !== t && boss.parts) { boss.dmgShown = (boss.dmgT > 0 ? boss.dmgShown || 0 : 0) + d; boss.dmgT = Math.max(boss.dmgT || 0, 1.0); }
    if (typeof popup === 'function') popup(x, y, d, o.col || '#f1e6c8');
  } else t.hit({ dmg: d, poise: 0, dir: 0, kind: 'burn', x, y, quiet: true, cr: o.tag || 'tick' });
}
// a discrete proc strike (the omen line, an echo, a star, the bell's ring): a real (spell) hit, its sparks in the Core's colour
function crStrike(t, d, o = {}) {
  if (!t || t.prop || !(d > 0.5) || !crLive(t)) return;
  const hb = hbOf(t) || rect(t.x - 8, t.y - 30, t.x + 8, t.y), x = (hb.x0 + hb.x1) / 2, y = (hb.y0 + hb.y1) / 2;
  const was = CR.tint; CR.tint = o.col || was;
  CR.dealt = (CR.dealt || 0) + d;
  try { t.hit({ dmg: d, poise: o.poise || 0, dir: t.x > P.x ? 1 : -1, kind: 'spell', x, y, big: false, cr: o.tag || 'strike' }); } finally { CR.tint = was; }
  if (typeof feelFlash === 'function' && o.col) feelFlash(x, y, 26, crRGB(o.col), 0.8);
}
// damage over time as a pool: a fresh dose refreshes the timer and adds to what's left, capped at twice one dose
function crDot(t, amt, secs, c) {
  if (!t || t.prop || !(amt > 0)) return;
  const o = t._crDot;
  if (o && o.left > 0) { o.pool = Math.min(o.pool + amt, Math.max(o.cap, amt * 2)); o.left = secs; o.cap = Math.max(o.cap, amt * 2); o.col = c.col; o.pk = c.pk; }
  else t._crDot = { pool: amt, left: secs, tick: 0, cap: amt * 2, col: c.col, pk: c.pk };
}
function crRot(t, amt, secs, c) {   // stacking rots (up to three run at once)
  if (!t || t.prop || !(amt > 0)) return;
  const L = t._crRot = (t._crRot || []).filter(r => r.left > 0);
  if (L.length >= 3) L.shift();
  L.push({ pool: amt, left: secs, tick: 0, col: c.col, pk: c.pk });
}
// control: small foes take it whole; great foes (bosses, their parts, elites) resist: 40% of the strength, half the time,
// and each application within 10 s of the last on the same foe lasts half as long again (to a floor of 25%)
function crSlow(t, f, secs) {
  if (!t || t.prop || typeof t.update !== 'function') return;
  if (crGreat(t)) {
    f = 1 - (1 - f) * 0.4; secs *= 0.5;
    const dr = t._crDR && P.clk - t._crDR.t < 10 ? t._crDR : (t._crDR = { n: 0, t: 0 });
    secs *= Math.max(0.25, Math.pow(0.5, dr.n)); dr.n++; dr.t = P.clk;
  }
  if (!t._crSlowWrap) { const o = t.update; t._crSlowWrap = true; t.update = function (dt, ...a) { return o.call(this, this._crSlowT > 0 ? dt * (this._crSlowF || 1) : dt, ...a); }; }
  crU('slowS', secs); crU('slowN', 1);
  t._crSlowF = Math.min(t._crSlowT > 0 ? t._crSlowF || 1 : 1, f); t._crSlowT = Math.max(t._crSlowT || 0, secs);
}

// ---- small feedback
function crTone(f, d, v, type = 'sine') { try { if (typeof wsTone === 'function') wsTone(f, d, v, type, 0.8); else tone(f, d, v, type, 0.8); } catch (e) {} }
function crBurst(t, col, pk, n) { const hb = t && t.hurtbox && t.hurtbox(); if (!hb) return; const x = (hb.x0 + hb.x1) / 2, y = (hb.y0 + hb.y1) / 2;
  for (let i = 0; i < n; i++) particles.push({ x: x + rand(-4, 4), y: y + rand(-6, 6), vx: rand(-60, 60), vy: -rand(20, 90), g: 160, life: rand(0.3, 0.6), kind: pk }); }
function crMote(col) { if (!P || typeof feelSpark !== 'function') return; const c = crRGB(col); for (let i = 0; i < 3; i++) feelSpark(P.x + rand(-5, 5), P.y - rand(6, 24), rand(-10, 10), -rand(30, 60), c, rand(0.25, 0.4), -20, 0.02); }

// ================================================================== the engine hooks
// a token per started move: per-move gates ("first hit of this move on this foe") and the haste / kindling / twin flips
{ const _ms = mvStart; mvStart = function (id, o) {
  const ok = _ms.apply(this, arguments);
  if (!ok) return ok;
  CR.mv++;
  P._crHasteMv = null;
  if (P._crHaste > P.clk) { P._crHasteMv = id; P._crHaste = 0; crU('hasted', 1); }
  const A = ATK[id], c = crCur();
  if (c && crElig(A)) {
    if (c.kind === 'choir') { CR.reso.n = P.clk - CR.reso.t < 4 ? Math.min(3, CR.reso.n + 1) : 0; CR.reso.t = P.clk; }
    if (c.kind === 'first_ember') { if (CR.kindle >= 3 && P.clk - CR.kindleT < 10) { CR.kindleMv = CR.mv; CR.kindle = 0; } }
    if (c.kind === 'twins') CR.twinCur = (CR.twin = (CR.twin + 1) % 2) === 1;
    CR.curMv = { id: CR.mv, landed: false };
  } else CR.curMv = null;
  return ok;
}; }
// the edge: the move's own damage and stance multipliers (the player's swing only: playerStrike's context)
{ const _ctx = mvHitCtx; mvHitCtx = function (t, hb, A, r) {
  const c = _ctx.apply(this, arguments);
  if (!t || t.prop) return c;
  if (t._crVulnT > 0 && crEnchantOf() === 'colossus') c.mul *= 1.06;   // the cracked shell: every blow you land
  const k = crCur(); if (!k || !crElig(A)) return c;
  const e = (k.edge || 0) + (k.edgeFn ? k.edgeFn.call(k, t, A) : 0);
  if (e) c.mul *= 1 + e;
  if (k.poise) c.poise *= 1 + k.poise;
  c.crEdge = e;
  return c;
}; }
// the proc: every melee blow that lands (strikes, shockwaves, echoes of the move)
HOOKS.strike.push((t, info, A) => {
  if (!t || t.prop || !P || !D || !info) return;
  const k = crCur(); if (!k) return;
  // Overdue: an ordinary blow on a paged foe tears the page
  if (k.kind === 'librarian' && t._crPage && !crElig(A)) { const pg = t._crPage; t._crPage = null; if (pg.until > P.clk) { crStrike(t, pg.acc.dmg * 0.15, { col: k.col, tag: 'page' }); crBurst(t, k.col, 'ink', 8); } }
  if (!crElig(A)) return;
  // the move's damage on this foe so far (delayed procs read it when they fire: a multi-hit finisher counts whole)
  if (!t._crAcc || t._crAcc.mv !== CR.mv) t._crAcc = { mv: CR.mv, dmg: 0, first: true }; else t._crAcc.first = false;
  t._crAcc.dmg += info.dmg || 0;
  const firstAny = !!(CR.curMv && !CR.curMv.landed); if (CR.curMv) CR.curMv.landed = true;
  const x = { first: t._crAcc.first, firstAny, acc: t._crAcc, great: crGreat(t) };
  if (k.kind === 'first_ember' && x.firstAny && CR.kindleMv !== CR.mv) { CR.kindle = P.clk - CR.kindleT < 10 ? Math.min(3, CR.kindle + 1) : 1; CR.kindleT = P.clk; }
  CR.procs = (CR.procs || 0) + 1;
  const was = CR.tint; CR.tint = CR.twinCur === false && k.col2 ? k.col2 : k.col;
  try { if (k.proc) k.proc.call(k, t, info, A, x); } finally { CR.tint = was; }
});
// DoTs, rots, chill, ink, vulnerability, the shell: per frame
HOOKS.update.push(dt => {
  if (!P || typeof targets !== 'function' || !room) return;
  for (const t of targets()) {
    if (t.prop) continue;
    if (t._crSlowT > 0) { t._crSlowT -= dt; if (Math.random() < 0.15) { const hb = t.hurtbox && t.hurtbox(); if (hb) particles.push({ x: rand(hb.x0, hb.x1), y: rand(hb.y0, hb.y1), vx: 0, vy: rand(5, 20), life: 0.5, kind: 'frost' }); } }
    if (t._crInkT > 0) t._crInkT -= dt;
    if (t._crVulnT > 0) t._crVulnT -= dt;
    const tickPool = (o, every = 0.5) => {
      o.left -= dt; o.tick += dt;
      if (o.tick >= every || o.left <= 0) {
        const n = o.left <= 0 ? 1 : Math.min(1, o.tick / Math.max(every, o.left + o.tick)); o.tick = 0;
        const d = o.pool * n; o.pool -= d; o.carry = (o.carry || 0) + d;   // whole numbers only; the fraction carries to the next tick
        const dd = o.left <= 0 ? Math.round(o.carry) : Math.floor(o.carry); if (dd >= 1) { o.carry -= dd; crDmg(t, dd, { col: o.col, tag: 'dot' }); }
        const hb = t.hurtbox && t.hurtbox(); if (hb) for (let i = 0; i < 2; i++) particles.push({ x: rand(hb.x0, hb.x1), y: rand(hb.y0 + (hb.y1 - hb.y0) * 0.3, hb.y1), vx: rand(-8, 8), vy: -rand(20, 50), life: rand(0.3, 0.5), kind: o.pk || 'ember' });
      }
    };
    if (t._crDot && t._crDot.left > 0) tickPool(t._crDot);
    if (t._crRot && t._crRot.length) { for (const r of t._crRot) if (r.left > 0) tickPool(r); t._crRot = t._crRot.filter(r => r.left > 0); }
  }
  if (P._crShellT > 0 && (P._crShellT -= dt) <= 0) P._crShell = 0;
  for (const v of CR.vfx) v.life -= dt;
  if (CR.vfx.length) CR.vfx = CR.vfx.filter(v => v.life > 0);
});
HOOKS.enter.push(() => { CR.vfx = []; CR.cd = {}; CR.curMv = null; });
// Unbroken Oath (kalden): hyper armour and 10% less damage during enchanted moves
{ const _hp = mvHurtPre; mvHurtPre = function (dmg, dir, id, opt) {
  const c = _hp.apply(this, arguments);
  if (crEnchantOf() === 'kalden' && crElig(ATK[P.state])) { if (dmg < D.maxHp * 0.2) c.armor = true; c.dmg *= 0.9; crU('oath', 1); if (typeof mvAura === 'function') CR.oathT = 0.2; }
  return c;
}; }
// incoming blows: Redaction (inked foes hit softer), the Sun Shell, and "when were you last hit" (Unyielding)
{ const _hurt = hurtPlayer; hurtPlayer = function (dmg, dir, id, opt = {}) {
  if (P && crCur()) {
    const k = crEnchantOf();
    if (k === 'unwritten') {
      const src = opt && opt.src, bossInk = boss && boss.alive && (boss._crInkT > 0 || (boss.parts && boss.parts.some(q => q._crInkT > 0)));
      if (src && src._crInkT > 0) dmg *= crGreat(src) ? 0.92 : 0.88;
      else if (!src && bossInk) dmg *= 0.92;
      else if (!src) { for (const e of enemies) if (e._crInkT > 0 && e.alive && Math.abs(e.x - P.x) < 90) { dmg *= 0.88; break; } }
    }
    if (k === 'scarab' && P._crShell > 0 && dmg > 0) { const s = Math.min(P._crShell, dmg - 1); if (s > 0) { dmg -= s; P._crShell = 0; P._crShellT = 0; CR.vfx.push({ k: 'ring', x: P.x, y: P.y - 18, r: 22, life: 0.3, max: 0.3, col: CORES.scarab.col }); crTone(900, 0.2, 0.04, 'triangle'); } }
  }
  const r = _hurt.call(this, dmg, dir, id, opt);
  if (r === true && P) P._crHurtT = P.clk;
  return r;
}; }
// Attentive (butler): the hastened move
{ const _sp = mvSpeed; mvSpeed = function (A) { const s = _sp.apply(this, arguments); return P && P._crHasteMv && A && A.mv && A.mv.id === P._crHasteMv && crEnchantOf() === 'butler' ? s * 1.12 : s; }; }
// Wayfarer's Wind (oswin): the free roll
{ const _dg = mvDodge; mvDodge = function (o, ax) {
  const st0 = P.st, free = crEnchantOf() === 'oswin' && P._crFreeRoll > P.clk;
  const r = _dg.apply(this, arguments);
  if (r && free) { crU('rollFree', Math.max(0, st0 - P.st)); P.st = Math.max(P.st, st0); P._crFreeRoll = 0; crMote(CORES.oswin.col); }
  return r;
}; }

// ================================================================== visuals
// the element the feel layer reads (tip ribbon, impact sparks, the charged flare) while an enchanted move plays
{ const _fe = feelElement; feelElement = function (fire) {
  const c = P && crCur(); const A = P && ATK[P.state];
  if (c && crElig(A)) { const two = CR.twinCur === false && c.col2, col = two ? c.col2 : c.col, rgb = two ? c.rgb2 : c.rgb; return { pk: two ? c.pk2 : c.pk, pk2: two ? c.pk2 : c.pk, light: rgb, glow: col, core: c.kind }; }
  return _fe.apply(this, arguments);
}; }
// the slash light and the hit sparks of an enchanted move: spawnFx tinted in its colour
{ const _sf = spawnFx; spawnFx = function (name, x, y, face, follow, extra) {
  if (CR.tint && name && !(extra && extra.tint)) extra = { ...(extra || {}), tint: CR.tint };
  return _sf.call(this, name, x, y, face, follow, extra);
}; }
{ const _mu = mvUpdate; mvUpdate = function () {
  const A = ATK[P.state], c = crCur();
  if (!c || !crElig(A)) return _mu.apply(this, arguments);
  const was = CR.tint; CR.tint = CR.twinCur === false && c.col2 ? c.col2 : c.col;
  try { return _mu.apply(this, arguments); } finally { CR.tint = was; }
}; }
// an idle enchanted blade: a faint ember of its colour at the tip, and a breath of light
CR.idleT = 0;
HOOKS.update.push(dt => {
  if (!P || state !== 'play' || P.state === 'dead') return;
  const c = crCur(); if (!c) return;
  const A = ATK[P.state], swinging = A && crElig(A);
  CR.idleT -= dt; if (CR.idleT > 0 || typeof feelTip !== 'function') return;
  CR.idleT = swinging ? 0.05 : rand(0.22, 0.4);
  const ws = sheet('wpn_' + (SAVE.weapon || 'longsword')); if (!ws.ok) return;
  const tp = feelTip(ws, P.anim.frame, 'a'); if (!tp) return;
  const k = rand(0.35, 1), x = P.x + (ws.native === P.face ? tp.dx : -tp.dx) * k, y = P.y + tp.dy * k + (1 - k) * -18;
  const two = CR.twinCur === false && c.col2;
  if (typeof feelSpark === 'function') feelSpark(x, y, rand(-8, 8), -rand(12, 30), two ? c.rgb2 : c.rgb, rand(0.3, 0.6), -10, 0.025);
});
HOOKS.render.push(() => {
  if (!P || !SAVE) return;
  const c = crCur();
  if (c && state === 'play' && P.state !== 'dead' && typeof feelTip === 'function') {
    const ws = sheet('wpn_' + (SAVE.weapon || 'longsword')), tp = ws.ok && feelTip(ws, P.anim.frame, 'a');
    if (tp) { const x = P.x + (ws.native === P.face ? tp.dx : -tp.dx) * 0.6, y = P.y + tp.dy * 0.6 - 7; addLight(x, y, 16 + Math.sin(time * 3) * 2, c.rgb, 0.22); }
  }
  if (CR.oathT > 0 && typeof mvAura === 'function') { CR.oathT -= 1 / 60; mvAura(CORES.kalden.col, 0.35, 1); }
  if (P._crShell > 0) { const k = 0.5 + 0.5 * Math.sin(time * 6); addLight(P.x, P.y - 16, 22, CORES.scarab.rgb, 0.25 + 0.15 * k); }
  if (!CR.vfx.length) return;
  drawGlow(() => {
    g.save(); g.globalCompositeOperation = 'lighter';
    for (const v of CR.vfx) {
      const k = clamp(v.life / v.max, 0, 1), rgb = crRGB(v.col);
      if (v.k === 'line') { const a = 0.4 + 0.5 * (1 - k); g.fillStyle = `rgba(${rgb},${a})`; g.fillRect(Math.round(v.x - v.w / 2), Math.round(v.y) - 1, v.w, 1); g.fillStyle = `rgba(255,255,255,${a * 0.6})`; g.fillRect(Math.round(v.x - v.w * (1 - k) / 2), Math.round(v.y) - 1, Math.round(v.w * (1 - k)), 1); addLight(v.x, v.y - 2, 20, rgb, 0.5 * (1 - k)); }
      else if (v.k === 'pillar') { g.fillStyle = `rgba(${rgb},${0.7 * k})`; g.fillRect(Math.round(v.x) - 2, Math.round(v.y) - 46, 4, 46); g.fillStyle = `rgba(255,255,255,${0.8 * k})`; g.fillRect(Math.round(v.x), Math.round(v.y) - 46, 1, 46); addLight(v.x, v.y - 24, 40, rgb, k); }
      else if (v.k === 'ring') { g.strokeStyle = `rgba(${rgb},${0.8 * k})`; g.lineWidth = 1; g.beginPath(); g.arc(Math.round(v.x), Math.round(v.y), v.r * (1 - k * 0.7), 0, 6.2832); g.stroke(); addLight(v.x, v.y, v.r, rgb, 0.4 * k); }
      else if (v.k === 'arc') { let s = v.seed * 1000; const rn = () => ((s = (s * 9301 + 49297) % 233280) / 233280) - 0.5; g.strokeStyle = `rgba(${rgb},${k})`; g.lineWidth = 1; g.beginPath(); g.moveTo(v.x0, v.y0);
        for (let i = 1; i < 6; i++) { const f = i / 6; g.lineTo(v.x0 + (v.x1 - v.x0) * f + rn() * 8, v.y0 + (v.y1 - v.y0) * f + rn() * 8); } g.lineTo(v.x1, v.y1); g.stroke(); addLight((v.x0 + v.x1) / 2, (v.y0 + v.y1) / 2, 40, rgb, k); }
      else if (v.k === 'star') { const f = 1 - k, y = v.y - 90 * (1 - f); g.strokeStyle = `rgba(${rgb},0.9)`; g.lineWidth = 1; g.beginPath(); g.moveTo(v.x + 30 * (1 - f) + 6, y - 14); g.lineTo(v.x + 30 * (1 - f), y); g.stroke(); g.fillStyle = '#fff'; g.fillRect(Math.round(v.x + 30 * (1 - f)), Math.round(y), 1, 1); addLight(v.x + 30 * (1 - f), y, 26, rgb, 0.8); }
      else if (v.k === 'sigil') { const t = v.t, hb = t && t.hurtbox && t.hurtbox(); if (!hb || !crLive(t)) { v.life = 0; continue; } const x = Math.round((hb.x0 + hb.x1) / 2), y = Math.round(hb.y0 - 8 - 2 * Math.sin(time * 4)), r = 2 + (1 - k) * 2;
        g.strokeStyle = `rgba(${rgb},${0.5 + 0.4 * (1 - k)})`; g.lineWidth = 1; g.beginPath(); g.moveTo(x, y - r); g.lineTo(x + r, y); g.lineTo(x, y + r); g.lineTo(x - r, y); g.closePath(); g.stroke(); addLight(x, y, 14, rgb, 0.5); }
    }
    g.restore();
  });
});

// ================================================================== icons: a cut gem in the Core's colour, caged in dark iron
const CR_ICON = {};
function crIconCanvas(kind) {
  if (CR_ICON[kind]) return CR_ICON[kind];
  const c = CORES[kind] || { col: '#e6c77a' }, N = 16, cv = document.createElement('canvas'); cv.width = cv.height = N;
  const x = cv.getContext('2d'), [r, gg, b] = crRGB(c.col).split(',').map(Number);
  const mix = (k, to = 0) => `rgb(${Math.round(r + (to - r) * k)},${Math.round(gg + (to - gg) * k)},${Math.round(b + (to - b) * k)})`;
  const px = (X, Y, col) => { x.fillStyle = col; x.fillRect(X, Y, 1, 1); };
  // the gem: a tall rhombus, lit from the upper left
  for (let y = 2; y <= 13; y++) { const h = y <= 7 ? (y - 2) : (13 - y) * 5 / 6, w = Math.round(h * 0.8);
    for (let X = 8 - w; X <= 7 + w; X++) { const lit = (X < 8 ? 0.15 : 0.45) + (y > 7 ? 0.2 : 0); px(X, y, mix(lit, 0)); } }
  for (let y = 3; y <= 7; y++) px(7, y, mix(0.35, 255));                          // the bright facet edge
  px(6, 5, '#ffffff'); px(7, 4, mix(0.6, 255));                                   // a glint
  if (c.col2) for (let y = 7; y <= 12; y++) { const w = Math.round((13 - y) * 5 / 6 * 0.8); for (let X = 8; X <= 7 + w; X++) px(X, y, `rgb(${crRGB(c.col2)})`); }
  // the cage: two thin iron prongs and a collar
  x.fillStyle = '#2a2420'; x.fillRect(3, 7, 1, 4); x.fillRect(12, 7, 1, 4); x.fillRect(4, 13, 8, 1); x.fillRect(6, 14, 4, 1);
  x.fillStyle = '#6a5a44'; x.fillRect(3, 7, 1, 1); x.fillRect(12, 7, 1, 1); x.fillRect(5, 13, 6, 1);
  return (CR_ICON[kind] = cv);
}
{ const _ic = icon; icon = function (name, x, y, size = 16, alpha = 1) {
  if (typeof name !== 'string' || !name.startsWith('core_')) return _ic.apply(this, arguments);
  const kind = name.slice(5), cv = crIconCanvas(kind === 'cat' ? 'omen' : kind);
  vctx.globalAlpha = alpha; vctx.imageSmoothingEnabled = false;
  if (CORES[kind] || kind === 'cat') { const X = ox + (x + size / 2) * scale, Y = oy + (y + size / 2) * scale, G = vctx.createRadialGradient(X, Y, 0, X, Y, size * 0.55 * scale), c = CORES[kind] || CORES.omen;
    G.addColorStop(0, `rgba(${c.rgb},0.28)`); G.addColorStop(1, `rgba(${c.rgb},0)`); vctx.fillStyle = G; vctx.fillRect(ox + x * scale, oy + y * scale, size * scale, size * scale); }
  vctx.drawImage(cv, 0, 0, 16, 16, ox + x * scale, oy + y * scale, size * scale, size * scale);
  vctx.globalAlpha = 1;
}; }

// ================================================================== the drop: first kill only, on top of the boss's own rewards
{ const _rw = BossBase.prototype.rewards; BossBase.prototype.rewards = function (...a) {
  if (typeof TRAINING !== 'undefined' && TRAINING.on) return _rw.apply(this, a);
  if (this.rematch) return crRematchRewards(this);
  const B = BOSS_INFO[this.kind], n = B && Array.isArray(B.reward) ? B.reward.length : 0;
  const r = _rw.apply(this, a);
  const kind = this.kind;
  if (CORES[kind] && !crOwned(kind)) {
    crStore().cores[kind] = 1; CR.log.push(['core', kind]); saveGame();
    setTimeout(() => { const c = CORES[kind]; if (!c || !SAVE.cores || !SAVE.cores[kind]) return; banner(c.name, `${c.trait}: ${c.desc} The Ashwright can set it in a weapon.`, 'core_' + kind); if (sfx.pickup) sfx.pickup(); }, 2600 + n * 2400 + 600);
  }
  return r;
}; }

// ================================================================== inventory: Boss Cores
function crEntry(kind) {
  const c = CORES[kind], where = crWhere(kind);
  return { kind: 'key', core: kind, id: 'core_' + kind, name: c.name, icon: 'core_' + kind, desc: c.desc, eq: !!where, where };
}
if (typeof INV_CATS !== 'undefined') INV_CATS.push({ k: 'core', name: 'Boss Cores', icon: 'core_cat', entries: () => crOwnedList().map(crEntry), total: () => Object.keys(CORES).length });
function crDetail(e, px, py, pw, ph) {
  const c = CORES[e.core], x = px + 9, R = px + pw - 9;
  uiCell(x, py + 9, 26, { eq: e.eq }); icon(e.icon, x + 2, py + 11, 22);
  text(c.name, x + 33, py + 21, uiFit(c.name, pw - 50, 8, 5.2), UIC.gold);
  text('Boss Core', x + 33, py + 30, 5, UIC.muted, 'left', { weight: 500 });
  if (e.where) text(`In the ${wmName(e.where)}`, R, py + 30, 5, UIC.gold, 'right', { weight: 600 });
  uiHair(x, py + 39, pw - 18, UIC.line, 0.8);
  let y = py + 50;
  text(c.trait.toUpperCase(), x, y, 6, c.col, 'left', { spacing: 1, weight: 700 }); y += 9;
  for (const l of wrap(c.desc, pw - 20, 5.6)) { text(l, x, y, 5.6, UIC.body, 'left', { weight: 400 }); y += 7.4; }
  y += 4; uiHead('Empowers', x, y, pw - 18); y += 8;
  for (const l of wrap('Finishers, heavy attacks, counters and charged releases of the weapon it is set in. Ordinary blows are untouched.', pw - 20, 5)) { text(l, x, y, 5, UIC.dim, 'left', { weight: 400 }); y += 6.6; }
  y += 3;
  const B = BOSS_INFO[e.core]; if (B) { const q = `From ${B.name}.`; text(q, x, y + 2, uiFit(q, pw - 20, 5, 3.8, 500), UIC.faint, 'left', { weight: 500 }); }
  text('The Ashwright sets Cores in weapons.', x, py + ph - 8, 4.8, UIC.faint, 'left', { weight: 400 });
}
if (typeof drawDetail === 'function') { const _dd = drawDetail; drawDetail = function (e) { if (e && e.core) return crDetail.apply(this, arguments); return _dd.apply(this, arguments); }; }

// ================================================================== the Ashwright: "Enchant a weapon"
{ const _npc = npcScript; npcScript = function (id) {
  const steps = _npc(id);
  if (id !== 'ashwright') return steps;
  const ch = steps.find(s => s.choice); if (!ch) return steps;
  const have = crOwnedList().length;
  const i = Math.max(1, ch.choice.findIndex(c => /^Temper/.test(c[0])) + 1);
  ch.choice.splice(i, 0, ['Enchant a weapon', have ? [{ do() { crOpenEnchant(); } }, { t: '', lore: true }] : [
    { w: 'ashwright', t: 'A core? When a great thing burns out it leaves its heart behind, hard as slag and still warm.' },
    { w: 'ashwright', t: 'Bring me one and I’ll set it in your blade. Only the big swings carry it, mind. A heart’s too heavy for the small ones.' }]]);
  return steps;
}; }
function crOpenEnchant() { menu = { screen: 'enchant', sel: 0, back: 'dialog', t0: time }; state = 'menu'; if (dialog) dialog.resume = true; clearBuffer(); }
function crRows() {   // [{ remove: kind } | { core: kind }]
  const cur = crEnchantOf(), L = [];
  if (cur) L.push({ remove: cur });
  for (const k of crOwnedList()) L.push({ core: k });
  return L;
}
function crEnchantInput(a) {
  const M = menu, L = crRows(), n = Math.max(1, L.length), conf = ['confirm', 'interact', 'attack', 'jump'].includes(a);
  M.sel = clamp(M.sel || 0, 0, n - 1);
  if (a === 'up') { M.sel = (M.sel + n - 1) % n; sfx.menu(); return; }
  if (a === 'down') { M.sel = (M.sel + 1) % n; sfx.menu(); return; }
  if (['pause', 'back', 'heavy', 'roll'].includes(a)) { menu = null; if (dialog && dialog.resume) { dialog.resume = false; state = 'dialog'; advanceDialog(); } else { state = 'play'; } clearBuffer(); return; }
  if (!conf || !L.length) return;
  const r = L[M.sel], type = crTypeNow(), wname = wmName(type);
  if (r.remove) { crUnsocket(type); sfx.menu(); tone(380, 0.25, 0.06, 'triangle', 0.6); toast(`${CORES[r.remove].name} taken from the ${wname}`, 2.4); saveGame(); M.sel = 0; return; }
  const k = r.core, where = crWhere(k);
  if (where === type) { sfx.deny(); toast(`The ${wname} already carries it`, 1.8); return; }
  if (SAVE.cinders < CR_COST) { sfx.deny(); toast(`Setting a Core costs ${CR_COST} cinders`, 2.2); return; }
  SAVE.cinders -= CR_COST; crSocket(k, type);
  sfx.levelup(); tone(1500, 0.3, 0.08, 'square', 0.5); shake = 3; flashScreen = 0.2; M.flash = { t: time, col: CORES[k].col };
  toast(`${CORES[k].name} set in the ${wname}${where ? ` (taken from the ${wmName(where)})` : ''}`, 3); saveGame();
  M.sel = crRows().findIndex(q => q.remove) >= 0 ? 0 : M.sel;
}
function renderEnchant() {
  const M = menu, L = crRows(), type = crTypeNow(), cur = crEnchantOf(), wid = SAVE.weapon;
  M.sel = clamp(M.sel || 0, 0, Math.max(0, L.length - 1));
  vctx.fillStyle = 'rgba(5,4,8,0.62)'; vctx.fillRect(ox, oy, W * scale, H * scale);
  panel(20, 22, 188, 176);
  text('ENCHANT A WEAPON', 30, 38, 7.5, '#e6c77a', 'left', { spacing: 1 });
  icon('cinder', 168, 30, 10); text(String(SAVE.cinders), 202, 38, 6.6, '#e8dcc0', 'right');
  // the weapon in hand and what it carries
  uiCell(30, 44, 18, { eq: !!cur }); icon('w_' + wid, 32, 46, 14);
  text(`${(WEAPONS[wid] || {}).name || wmName(type)}`, 52, 51, 6, UIC.hi, 'left', { weight: 600 });
  text(cur ? `${CORES[cur].trait} · ${CORES[cur].name}` : 'No Core set', 52, 59, 5, cur ? CORES[cur].col : UIC.faint, 'left', { weight: 500 });
  uiFade(30, 200, 66, UI_RGB.accent, 0.5);
  if (!L.length) { for (const [i, l] of wrap('You carry no Cores. A great foe leaves one behind the first time it falls.', 166, 5.8).entries()) text(l, 30, 82 + i * 8, 5.8, UIC.dim, 'left', { weight: 400 }); }
  const top = clamp(M.sel - 6, 0, Math.max(0, L.length - 9));
  L.slice(top, top + 9).forEach((r, j) => {
    const i = top + j, y = 76 + j * 13.4, sel = i === M.sel;
    uiHit(26, y - 9, 176, 12.6, () => { M.sel = i; });
    if (sel) uiSel(26, y - 9, 176, 12.6);
    if (r.remove) { text('✕', 33, y - 0.5, 6, '#c07060', 'left'); text(`Remove ${CORES[r.remove].name}`, 44, y, 5.8, sel ? UIC.hi : UIC.text, 'left', { weight: sel ? 600 : 500 }); text('free', 198, y, 5, UIC.faint, 'right', { weight: 500 }); return; }
    const c = CORES[r.core], where = crWhere(r.core);
    icon('core_' + r.core, 30, y - 9, 11);
    text(c.name, 44, y, uiFit(c.name, 100, 5.8, 4.4), sel ? UIC.hi : where === type ? UIC.gold : UIC.text, 'left', { weight: sel ? 600 : 500 });
    text(where ? (where === type ? 'in hand' : wmName(where)) : `${CR_COST}`, 198, y, 4.8, where === type ? UIC.gold : where ? UIC.faint : SAVE.cinders >= CR_COST ? '#e6c77a' : '#8a6050', 'right', { weight: 500 });
  });
  if (L.length > 9) text(`${M.sel + 1} / ${L.length}`, 198, 194, 4.4, UIC.faint, 'right', { weight: 500 });
  // the chosen Core
  panel(214, 22, 150, 176, 0.75);
  const r = L[M.sel], k = r && (r.core || r.remove);
  if (k) {
    const c = CORES[k], fl = M.flash && time - M.flash.t < 0.6 ? 1 - (time - M.flash.t) / 0.6 : 0;
    stGlowSafe(240, 46, 22 + 6 * fl, c.rgb, 0.25 + 0.3 * fl + 0.05 * Math.sin(time * 3));
    icon('core_' + k, 226, 32, 28);
    text(c.name, 258, 42, uiFit(c.name, 100, 6.6, 4.6), UIC.gold, 'left');
    text(c.trait.toUpperCase(), 258, 51, 5, c.col, 'left', { spacing: 0.8, weight: 700 });
    let y = 70; for (const l of wrap(c.desc, 134, 5.4)) { text(l, 222, y, 5.4, UIC.body, 'left', { weight: 400 }); y += 7.2; }
    y += 3; uiHead('Carried by', 222, y, 134); y += 8;
    for (const l of wrap('finishers · heavies · counters · charged releases', 134, 4.8)) { text(l, 222, y, 4.8, UIC.dim, 'left', { weight: 400 }); y += 6.4; }
    const where = crWhere(k);
    y += 4; text(r.remove ? 'Removing it is free; the Core returns to you.' : where === type ? 'Set in the weapon in your hand.' : where ? `Now in the ${wmName(where)}: setting it here moves it.` : `Setting it costs ${CR_COST} cinders.`, 222, y, uiFit('Now in the Sword & Shield: setting it here moves it.', 134, 4.8, 3.6, 400), UIC.faint, 'left', { weight: 400 });
  } else text('Each weapon keeps its own Core.', 289, 110, 5.4, UIC.dim, 'center', { weight: 400 });
  text('Enter — set / remove    Esc — leave', W / 2, 205, 5.5, '#7f745f', 'center', { weight: 400 });
}
{ const _mi = menuInput; menuInput = function (a) { if (menu && menu.screen === 'enchant') return crEnchantInput(a); return _mi.apply(this, arguments); }; }
{ const _rm = renderMenu; renderMenu = function () { if (menu && menu.screen === 'enchant') return renderEnchant(); return _rm.apply(this, arguments); }; }

// ================================================================== Rekindle: the ember effigy and the rematch
// where each boss lives: the Training Grounds' scan of every room (65_training.js), else our own
let CR_HOMES = null;
function crHomes() {
  if (CR_HOMES) return CR_HOMES;
  CR_HOMES = {};
  try { if (typeof trnBosses === 'function') for (const b of trnBosses()) if (!CR_HOMES[b.room]) CR_HOMES[b.room] = []; } catch (e) {}
  try { for (const b of trnBosses()) if (!CR_NO_REMATCH.has(b.kind)) CR_HOMES[b.room].push(b); } catch (e) {}
  return CR_HOMES;
}
// where the effigy stands: the player's start in the boss's arena (the Training Grounds' table), else a dozen tiles from the boss
function crEffigySpot(B, def) {
  let st = typeof TRN_PSTART !== 'undefined' && TRN_PSTART[B.kind];
  if (!st && typeof trnStartNear === 'function') try { st = trnStartNear(def, B.hx, B.hy); } catch (e) {}
  if (!st) st = [Math.max(3, B.hx - 12), B.hy];
  let [tx, ty] = st;
  // stand it on the floor under that tile
  for (let y = ty; y < def.h - 1; y++) { if (isSolidT(cellType(def.map[y + 1][tx]))) { ty = y; break; } }
  // it must be dry, standable ground clear of the fog gates (the Choir's pool has none inside: then the doorway ledge)
  const cell = (x, y) => (def.map[y] || '')[x] || '#';
  const ok = (x, y) => { const c = cellType(cell(x, y)), b = cellType(cell(x, y + 1)); if (isSolidT(c) || c === T_WATER || c === T_SPIKE || cell(x, y) === '"') return false;
    if (!(isSolidT(b) || b === T_PLAT)) return false; for (let k = 0; k < 5; k++) if (cell(x, y - k) === 'F' || cell(x, y + 1 - k) === 'F') return false; return true; };
  if (!ok(tx, ty)) {
    let best = null, bd = 1e9;
    for (let y = 1; y < def.h - 1; y++) for (let x = 0; x < def.w; x++) if (ok(x, y)) { const d = Math.abs(x - tx) + 2 * Math.abs(y - ty); if (d < bd) { bd = d; best = [x, y]; } }
    if (best) [tx, ty] = best;
  }
  return { x: tx * TILE + 8, y: (ty + 1) * TILE };
}
const REM = { on: null, entering: false, effigyT: 0, wins: 0, deaths: 0 };
// a story beat still to come after a kill (the First Ember's epilogue, Venn's last flame): no rekindling until it has played
function crStoryPending() { return (typeof SC_EPI !== 'undefined' && SC_EPI.t > 0) || (typeof VN !== 'undefined' && VN.endT > 0) || (typeof victoryBanner !== "undefined" && victoryBanner && !!victoryBanner.ending); }
function crRematchOK(kind) { return !!(kind && SAVE && SAVE.flags['boss:' + kind] && !CR_NO_REMATCH.has(kind) && BOSS_INFO[kind] && !(typeof TRAINING !== 'undefined' && TRAINING.on)); }
function crMakeEffigy(B) {
  const pos = crEffigySpot(B, room.def), kind = B.kind, c = CORES[kind] || CORES.omen;
  const p = { type: 'cr_effigy', kind, x: pos.x, y: pos.y, face: 1, anim: { update() {} }, t: 0, lit: 0,
    prompt() { return crRematchOK(kind) && !(boss && boss.alive) ? `Rekindle ${BOSS_INFO[kind].name.split(',')[0]}` : null; },
    interact() { if (!this.prompt()) return false; crAskRekindle(this); return true; },
    update(dt) {
      this.t += dt; this.lit = Math.max(0, this.lit - dt);
      const k = 0.75 + 0.25 * Math.sin(this.t * 2.2) + this.lit;
      addLight(this.x, this.y - 22, 34 + 6 * k, c.rgb, 0.55 * k);
      if (Math.random() < 0.08 + this.lit) particles.push({ x: this.x + rand(-2, 2), y: this.y - 22 + rand(-2, 2), vx: rand(-4, 4), vy: -rand(8, 20), life: rand(0.6, 1.2), kind: 'ember' });
    },
    draw() {
      const X = Math.round(this.x), Y = Math.round(this.y), bob = Math.round(Math.sin(this.t * 2.2) * 1);
      g.fillStyle = 'rgba(30,26,28,0.85)'; g.beginPath(); g.ellipse(X, Y - 0.5, 9, 2, 0, 0, 6.2832); g.fill();            // the ash it stands in
      g.fillStyle = 'rgba(70,62,60,0.9)'; g.fillRect(X - 6, Y - 2, 12, 1); g.fillRect(X - 4, Y - 3, 8, 1);
      g.fillStyle = '#1c1816'; g.fillRect(X - 1, Y - 18, 2, 16); g.fillRect(X - 3, Y - 3, 6, 1);                         // a slender iron stake
      g.fillStyle = '#3a322c'; g.fillRect(X - 1, Y - 18, 1, 16);
      g.fillStyle = '#1c1816'; g.fillRect(X - 5, Y - 19, 1, 3); g.fillRect(X + 4, Y - 19, 1, 3); g.fillRect(X - 4, Y - 17, 8, 1);   // the cradle
      drawGlow(() => {   // the core, hovering
        const cy = Y - 24 + bob, a = 0.85;
        g.fillStyle = `rgba(${c.rgb},${a})`; g.fillRect(X - 1, cy - 3, 2, 7); g.fillRect(X - 2, cy - 1, 4, 3);
        g.fillStyle = 'rgba(255,255,255,0.85)'; g.fillRect(X - 1, cy - 1, 1, 1);
        if (this.lit > 0) { g.fillStyle = `rgba(${c.rgb},${0.5 * this.lit})`; g.fillRect(X - 3, cy - 6, 6, 13); }
      });
    } };
  return p;
}
function crAskRekindle(p) {
  const B = BOSS_INFO[p.kind];
  startDialogue([
    { t: `The ashes of ${B.name} still hold a little heat. Breathe on them, and it will rise to meet you again.`, lore: true },
    { choice: [[`Rekindle ${B.name.split(',')[0]}`, [{ do() { dialog.after = () => crRekindle(p.kind); } }]], ['Let the ash lie', []]] },
  ], null);
}
function crRekindle(kind) {
  if (!crRematchOK(kind) || !room || crStoryPending()) return false;
  const id = room.id, px = P.x, py = P.y, flag = 'boss:' + kind;
  for (const f of ['cut:', 'cutp2:', 'cutp3:']) SAVE.flags[f + kind] = 1;   // the story scenes played the first time
  REM.on = { kind, room: id, t0: time, cinders: SAVE.cinders };
  REM.entering = true;
  delete SAVE.flags[flag];
  try { enterRoom(id, px, py, { quiet: true }); }
  finally { SAVE.flags[flag] = 1; REM.entering = false; }   // the flag only lifts for the rebuild: every save still holds it
  const b = boss;
  if (!b || b.kind !== kind) { REM.on = null; toast('The ashes stay cold.', 2.4); return false; }
  b.rematch = true; if (b.parts) for (const q of b.parts) q.rematch = true;
  if (kind === 'champion') b.called = true;   // normally woken by the banner's gauntlet
  setP('idle', 'idle', true); P.vx = 0;
  flashScreen = Math.max(flashScreen || 0, 0.35); shake = Math.max(shake, 4); if (sfx.kindle) sfx.kindle();
  const c = CORES[kind] || CORES.omen;
  for (let i = 0; i < 26; i++) particles.push({ x: px + rand(-6, 6), y: py - rand(4, 30), vx: rand(-50, 50), vy: -rand(30, 120), g: 80, life: rand(0.5, 1.1), kind: 'ember' });
  if (typeof feelFlash === 'function') feelFlash(px, py - 20, 60, c.rgb, 1.2, 0.3);
  toast(`The ash stirs: ${BOSS_INFO[kind].name.split(',')[0]}, rekindled. Fall here and you lose nothing.`, 4);
  REM.count = (REM.count || 0) + 1;
  return true;
}
// a rekindled kill: Mastery XP and a tithe of cinders; no Core, no items, no flags, no ending
function crRematchRewards(b) {
  const B = BOSS_INFO[b.kind] || {}, n = Math.round((B.cinders || 0) * CR_REMATCH_CINDERS);
  if (typeof masteryGain === 'function') { b._wmXp = 1; masteryGain(wtype(), CR_REMATCH_XP, 'boss-rematch'); }
  if (n > 0) gainCinders(n, b.x, b.y - 40);
  if (victoryBanner && victoryBanner.ending) victoryBanner.ending = false;
  REM.wins++; if (REM.on) REM.on.won = true;
  setTimeout(() => { if (state === 'play') toast(`Rekindled and felled again · +${CR_REMATCH_XP} Mastery`, 3); }, 2800);
  saveGame();
}
// effigies: in a boss's home room once it has fallen and nothing is alive; after a rematch they return
HOOKS.enter.push(def => {
  if (!REM.entering && REM.on) REM.on = null;   // left the fight (or died, or rested): the rematch is over
  REM.effigyT = 0.8;
});
HOOKS.update.push(dt => {
  if (!room || !SAVE || !P || (typeof TRAINING !== 'undefined' && TRAINING.on)) return;
  // the ending scenes stay where they belong (a rekindled Sovereign / First Ember never replays them)
  if (REM.on && boss && boss.rematch && !boss.alive) {
    if (victoryBanner && victoryBanner.ending) victoryBanner.ending = false;
    if (typeof SC_EPI !== 'undefined' && SC_EPI.t > 0 && SAVE.flags.true_epilogue) SC_EPI.t = 0;
    if (typeof VN !== 'undefined' && VN.endT > 0 && boss.kind !== 'venn') VN.endT = 0;
  }
  if ((REM.effigyT -= dt) > 0) return;
  REM.effigyT = 0.5;
  const L = crHomes()[room.id]; if (!L || !L.length) return;
  if (boss && (boss.alive || (victoryBanner && victoryBanner.t < 4))) return;
  if (state !== 'play' || crStoryPending()) return;
  for (const B of L) {
    if (!crRematchOK(B.kind) || props.some(p => p.type === 'cr_effigy' && p.kind === B.kind)) continue;
    const p = crMakeEffigy(B); props.push(p);
    if (REM.on && REM.on.won) { p.lit = 1; for (let i = 0; i < 12; i++) particles.push({ x: p.x + rand(-4, 4), y: p.y - rand(2, 10), vx: rand(-20, 20), vy: -rand(20, 60), life: rand(0.5, 1), kind: 'ember' }); }
  }
});
// a save made while the room is being rebuilt for a rematch (an enter hook that saves) still writes the boss as defeated
{ const _sg = saveGame; saveGame = function (...a) {
  if (!(REM.entering && REM.on && SAVE && SAVE.flags)) return _sg.apply(this, a);
  const f = 'boss:' + REM.on.kind, had = SAVE.flags[f]; SAVE.flags[f] = 1;
  try { return _sg.apply(this, a); } finally { if (had === undefined) delete SAVE.flags[f]; else SAVE.flags[f] = had; }
}; if (_sg.trnWrap) saveGame.trnWrap = true; }
// death in a rekindled fight: nothing is lost (no remnant, cinders kept); you wake at your shrine as ever
{ const _fd = finishDeath; finishDeath = function (...a) {
  const R = REM.on;
  if (!R || R.won || !room || room.id !== R.room || (typeof TRAINING !== 'undefined' && TRAINING.on)) return _fd.apply(this, a);   // after the win it is an ordinary death again
  const keepC = SAVE.cinders, keepR = SAVE.remnant;
  SAVE.cinders = 0; SAVE.remnant = null;
  const r = _fd.apply(this, a);
  SAVE.cinders = keepC; SAVE.remnant = keepR; REM.on = null; REM.deaths++;
  toast('The rekindled flame gutters out. It took nothing from you.', 3.5); saveGame();
  return r;
}; }

// ---- Training Grounds: a row to try any Core on the weapon in hand (the sandbox SAVE; nothing flows back)
if (typeof wmTrainingRows === 'function') { const _tr = wmTrainingRows; wmTrainingRows = function (R, head) {
  const r = _tr.apply(this, arguments);
  const L = crOrder(), i = R.findIndex(q => q && q.label === 'Master every weapon');
  const set = k => { const S = crStore(); for (const c of L) S.cores[c] = 1; if (k) S.enchants[crTypeNow()] = k; else delete S.enchants[crTypeNow()]; };
  const cyc = d => { const cur = crEnchantOf(), j = cur ? L.indexOf(cur) : -1, n = (j + 1 + d + L.length + 1) % (L.length + 1) - 1; set(n < 0 ? null : L[n]); };
  const row = { label: 'Boss Core', val: () => { const k = crEnchantOf(); return k ? CORES[k].trait : 'none'; }, lr: d => cyc(d), conf: () => cyc(1), wpn: SAVE.weapon,
    desc: 'Set any boss Core in the weapon in hand (◂ ▸). It empowers finishers, heavies, counters and charged releases.' };
  R.splice(i >= 0 ? i + 1 : R.length, 0, row);
  return r;
}; }

// ---- debug handles for headless tests (tools/shots/v15/cores)
if (typeof window !== 'undefined' && window.__game) window.__game.cores = {
  CR, CORES, REM, crElig, crSocket, crUnsocket, crGrant, crEnchantOf, crRekindle, crHomes, crOwnedList, crRows,
  ev: s => eval(s),
};
