// ------------------------------------------------------------------ Expansion 2 gear (agent G): spells, weapon arts, charms
// Ids: docs/EXPANSION2_CONTRACT.md §4. Icons: ui_icons5 (art/gen_ui5.py). Effects: fx_g2_* (art/gen_fx5.py).
// Status effects go through the shared helpers: WSTATUS.frost/burn + wSlowWrap (13_weapons.js), GEAR2.stun (14_gear2.js).
ICON_SHEETS.push('ui_icons5');
const GEAR3 = (() => {
  // ================================================================ data
  registerGear({
    spells: {
      bramble_snare: { name: 'Bramble Snare', fp: 16, icon: 's_bramble_snare', sheet: 'ui_icons5',
        desc: 'Sow a coil of thorns on the floor ahead. When a foe treads on it the brambles lash up, cutting deep and rooting it in place. Up to two at once.' },
      drowning_hymn: { name: 'Drowning Hymn', fp: 22, icon: 's_drowning_hymn', sheet: 'ui_icons5',
        desc: 'The Choir’s song: a rolling wave of drowned voices that washes over foes, swallowing missiles and dragging at every limb it touches.' },
      blood_lance: { name: 'Blood Lance', fp: 14, icon: 's_blood_lance', sheet: 'ui_icons5',
        desc: 'Hurl a needle of blood that pierces every foe in its path. Each wound it opens flows back into you.' },
      crimson_rite: { name: 'Crimson Rite', fp: 12, icon: 's_crimson_rite', sheet: 'ui_icons5',
        desc: 'The Countess’s rite. Offer 15% of your life: for fifteen seconds every blow and spell deals 30% more.' },
      soul_chains: { name: 'Soul Chains', fp: 20, icon: 's_soul_chains', sheet: 'ui_icons5',
        desc: 'King Vael’s court still answers. Spectral chains burst from the ground and bind the nearest foe, then shatter.' },
      sunbeam: { name: 'Sunbeam', fp: 22, icon: 's_sunbeam', sheet: 'ui_icons5',
        desc: 'Call down a column of desert sun on the nearest foe. It follows its mark and burns while it lasts.' },
      sandstorm: { name: 'Sandstorm', fp: 26, icon: 's_sandstorm', sheet: 'ui_icons5',
        desc: 'The Pharaoh’s wrath: a whirling storm of sand crawls forward, flaying and drawing in all it passes and swallowing missiles.' },
      comet: { name: 'Comet', fp: 28, icon: 's_comet', sheet: 'ui_icons5',
        desc: 'Mark a foe; a heartbeat later a fallen star crashes down on it in a burst of starfire.' },
      pulse_shot: { name: 'Pulse Shot', fp: 12, icon: 's_pulse_shot', sheet: 'ui_icons5',
        desc: 'A burst of three neon bolts. Fast, light, precise. Nothing in the old world was ever this quick.' },
      null_field: { name: 'Null Field', fp: 24, icon: 's_null_field', sheet: 'ui_icons5',
        desc: 'SAINT-0’s firewall: a dome of light for five seconds that deletes every missile entering it and slows every foe inside.' },
    },
    arts: {
      reap: { name: 'Reap', fp: 14, desc: 'One full reaping circle around you, dragging foes in. Each foe cut returns a little life. Hold to reap twice and leave them bleeding.' },
      harvest_moon: { name: 'Harvest Moon', fp: 18, desc: 'Hurl the scythe as a spinning moon that carves through foes and returns to your hand. Hold for a greater moon that lingers at the far end.' },
      lash: { name: 'Lash', fp: 10, desc: 'Three quick cracks of the chain at long reach; the last snaps behind you too. Hold for five.' },
      chain_drag: { name: 'Chain Drag', fp: 14, desc: 'Cast the chain. Small foes are dragged to your feet and struck; against great foes the chain hauls you to them for a heavy blow. Hold to cast further.' },
      blood_frenzy: { name: 'Blood Frenzy', fp: 12, desc: 'Pay 8% of your life for a storm of rapier thrusts, each drinking blood. For a while after, every hit heals you. Hold for more thrusts and a longer frenzy.' },
      tidal_surge: { name: 'Tidal Surge', fp: 16, desc: 'Drive the harpoon into the ground and loose a wave that rushes forward, bowling foes over and swallowing missiles. Hold for a second wave.' },
      solar_flare: { name: 'Solar Flare', fp: 16, desc: 'Raise the blade to the sun: a disc of light swells and bursts, burning all around you. Hold for a wider, blinding flare.' },
      starfall: { name: 'Starfall', fp: 18, desc: 'A rising cut that calls a line of falling stars down before you. Hold for more stars and a last, greater one.' },
      overclock: { name: 'Overclock', fp: 14, desc: 'Flash forward in a glitching cut, then run hot: your attacks are 35% faster for six seconds. Hold to run hot longer.' },
      pale_pyre: { name: 'Pale Pyre', fp: 22, desc: 'Strike the ground and raise rings of pale fire on both sides, burning all they touch and warming you. Hold for a fourth ring and fire that lingers.' },
    },
    charms: {
      c_antler: { name: 'Warden’s Antler', desc: 'Heavy attacks root smaller foes in thorns for a moment.' },
      c_moss: { name: 'Mossheart', desc: 'After four seconds without being hurt, you slowly regenerate HP.' },
      c_gill: { name: 'Drowned Gill', desc: 'A gill cut from something that should not breathe. You can hold your breath far longer underwater.' },
      c_pearl: { name: 'Choir Pearl', desc: 'Crimson flasks also restore 20% FP; azure flasks also restore 15% HP.' },
      c_bloodvial: { name: 'Blood Vial', desc: 'Melee hits heal you for 1% of your maximum HP.' },
      c_countess: { name: 'Countess’s Brooch', desc: 'A successful parry or critical strike restores 10% HP and empowers your next blow.' },
      c_crown: { name: 'Crown of Vael', desc: 'When a foe falls near you, a spectral chain lashes out from it at the nearest other foe.' },
      c_court: { name: 'Court Signet', desc: 'Each foe you fell grants +5% damage for twenty seconds, stacking five times.' },
      c_scarab: { name: 'Scarab Amulet', desc: 'Rolling through an attack throws up a burst of sand that blinds nearby foes.' },
      c_sun: { name: 'Sun Disc', desc: 'Your spells call a small sunbeam down on the nearest foe.' },
      c_star: { name: 'Fallen Star', desc: 'A shard of star orbits you and darts at nearby foes.' },
      c_orrery: { name: 'Orrery Cog', desc: 'Weapon arts cost 30% less FP.' },
      c_hack: { name: 'Glitch Lens', desc: 'The world flickers where it is thin. Reveals breakable walls and hidden passages.' },
      c_neon: { name: 'Neon Halo', desc: 'Rolling through an attack empowers your next blow and fires a pulse at the nearest foe.' },
      c_lastflame: { name: 'The Last Flame', desc: 'Once per rest, a blow that would kill you leaves you at 1 HP, wreathed in pale fire and untouchable for three seconds.' },
    },
  }, 'ui_icons5');

  // ================================================================ helpers
  const S = { objs: [], ghosts: [], riteT: 0, frenzyT: 0, ocT: 0, court: [], moss: 0, star: { a: 0, cd: 0, dart: null },
              lastFlame: false, lastFlameT: 0, scarabCd: 0, neonCd: 0, sunCd: 0, myProj: new Set(), artCount: -1, heal: 0, dmgMul: 1 };
  const foes = () => targets().filter(t => !t.prop);
  const hbc = t => { const hb = t.hurtbox && t.hurtbox(); return hb ? { x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2, hb } : null; };
  const charged = () => !!P.artCharged;
  const isSmall = t => t instanceof Enemy && !t.cfg.elite;
  const meleeDmg = (base, mult) => outgoing(base, mult, 'melee');
  const spellDmg = base => outgoing(base, 1, 'spell');
  const heal = f => { if (!P || P.state === 'dead') return; const n = Math.max(1, Math.round(D.maxHp * f)); P.hp = Math.min(D.maxHp, P.hp + n); S.heal += n; };
  function floorBelow(x, y, max = 112) {
    for (let ty = Math.floor(y / TILE); ty <= Math.floor((y + max) / TILE); ty++) {
      const t = tileAt(Math.floor(x / TILE), ty);
      if ((isSolidT(t) || t === T_PLAT) && !isSolidT(tileAt(Math.floor(x / TILE), ty - 1))) return ty * TILE;
      for (const d of room.dyn) if (d.on() && x >= d.x0 && x < d.x1 && ty * TILE <= d.y0 && d.y0 < ty * TILE + TILE) return d.y0;
    }
    return null;
  }
  function floorAhead(dist) {
    let x = P.x + P.face * dist;
    for (let k = 0; k < 8 && solidAtPx(x, P.y - 8); k++) x -= P.face * 6;
    const fy = floorBelow(x, P.y - 12);
    return { x, y: fy === null ? P.y : fy };
  }
  function slow(t, s) {
    if (!t || t.prop) return;
    t._slowT = Math.max(t._slowT || 0, t.boss ? s * 0.6 : s);
    if (typeof wSlowWrap === 'function') wSlowWrap(t);
  }
  function burn(t, secs, dps) { if (typeof WSTATUS !== 'undefined') WSTATUS.burn(t, secs, dps); }
  function root(t, s) { if (typeof GEAR2 !== 'undefined' && GEAR2.stun) GEAR2.stun(t, s); }
  function bossStance(t, n) {
    if (!t.boss || t.state === 'stagger' || !(t.stanceImmune <= 0) || t.stanceMax === undefined) return;
    t.stance = (t.stance || 0) + n;
    if (t.stance >= t.stanceMax && (!t.canStagger || t.canStagger())) t.stagger();
  }
  function hitT(t, o) {
    const c = hbc(t); if (!c) return false;
    t.hit(Object.assign({ dir: t.x >= (o.from ?? P.x) ? 1 : -1, kind: 'spell', x: c.x, y: c.y, poise: 20 }, o));
    if (!t.prop) {
      if (o.slow) slow(t, o.slow);
      if (o.burnT) burn(t, o.burnT, o.burnDps || 10);
      if (o.root) { if (t.boss) slow(t, o.root); else root(t, o.root); }
      if (o.lifesteal) heal(o.lifesteal);
    }
    return true;
  }
  function areaHit(r, o, set) {
    const out = [];
    for (const t of targets()) {
      if (set && set.has(t)) continue;
      const hb = hbOf(t); if (!hb || !overlap(r, hb)) continue;
      if (set) set.add(t);
      hitT(t, o); out.push(t);
    }
    return out;
  }
  function nearestFoe(x, y, maxD, filter) {
    let best = null, bd = maxD;
    for (const t of foes()) { const c = hbc(t); if (!c || (filter && !filter(t, c))) continue; const d = Math.hypot(c.x - x, c.y - y); if (d < bd) { bd = d; best = t; } }
    return best;
  }
  const frontFoe = range => nearestFoe(P.x, P.y - 16, range, (t, c) => (c.x - P.x) * P.face > -10 && Math.abs(c.y - (P.y - 16)) < 90);
  function killEnemyProjectiles(test, fxTint) {
    for (const pr of projectiles) if (pr.owner !== 'player' && pr.life > 0 && !(pr.delay > 0) && !pr.static && !pr.fxName && test(pr)) {
      pr.life = 0; spawnFx('g_spark', pr.x, pr.y, 1, null, { tint: fxTint });
    }
  }
  function tagFrame(name, tag, t, loop = true) {
    const s = sheet(name); if (!s.ok) return null;
    const tg = s.tags[tag] || s.tag(Object.keys(s.tags)[0]); let ms = t * 1000, f = tg.from, total = 0;
    for (let i = tg.from; i <= tg.to; i++) total += s.frames[i].ms;
    if (loop && total) ms %= total;
    while (f < tg.to && ms >= s.frames[f].ms) { ms -= s.frames[f].ms; f++; }
    return { s, f, total: total / 1000 };
  }
  function drawTag(name, tag, t, x, y, face, opt = {}, loop = true) { const r = tagFrame(name, tag, t, loop); if (r) drawSprite(r.s, r.f, x, y, face, opt); }
  const tagLen = (name, tag) => { const r = tagFrame(name, tag, 0, false); return r ? r.total : 0.3; };
  function jagPts(x0, y0, x1, y1, seed, amp = 5, n = 0) {
    const L = Math.hypot(x1 - x0, y1 - y0); n = n || Math.max(3, Math.round(L / 10));
    const nx = -(y1 - y0) / (L || 1), ny = (x1 - x0) / (L || 1), pts = [[x0, y0]];
    for (let i = 1; i < n; i++) { const o = (hash2(seed, i) * 2 - 1) * amp; pts.push([x0 + (x1 - x0) * i / n + nx * o, y0 + (y1 - y0) * i / n + ny * o]); }
    pts.push([x1, y1]); return pts;
  }
  function drawPath(pts, a, glow, core) {
    for (const [w, col, al] of [[3, glow, 0.35 * a], [1, core, a]]) {
      g.fillStyle = `rgba(${col},${al})`;
      for (let i = 0; i < pts.length - 1; i++) {
        const [x0, y0] = pts[i], [x1, y1] = pts[i + 1], n = Math.max(1, Math.ceil(Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0))));
        for (let k = 0; k <= n; k++) g.fillRect(Math.round(x0 + (x1 - x0) * k / n) - (w >> 1), Math.round(y0 + (y1 - y0) * k / n) - (w >> 1), w, w);
      }
    }
  }
  // a chain/whip drawn link by link along a quadratic curve
  function drawChain(x0, y0, x1, y1, sag, cols, alpha = 1) {
    const L = Math.hypot(x1 - x0, y1 - y0), n = Math.max(2, Math.round(L / 3));
    const mx = (x0 + x1) / 2, my = (y0 + y1) / 2 + sag;
    g.globalAlpha = alpha;
    for (let i = 0; i <= n; i++) {
      const t = i / n, x = (1 - t) * (1 - t) * x0 + 2 * (1 - t) * t * mx + t * t * x1, y = (1 - t) * (1 - t) * y0 + 2 * (1 - t) * t * my + t * t * y1;
      g.fillStyle = cols[i % cols.length]; g.fillRect(Math.round(x), Math.round(y), i % 2 ? 1 : 2, i % 2 ? 1 : 2);
    }
    g.globalAlpha = 1;
  }
  function add(o) { o.t = 0; S.objs.push(o); return o; }
  function burstParticles(x, y, n, kind, sp = 90, up = 0) {
    for (let i = 0; i < n; i++) { const a = rand(0, 6.283), v = rand(sp * 0.4, sp); particles.push({ x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v * 0.6 - up, g: 120, life: rand(0.3, 0.8), kind }); }
  }
  const sndThorn = () => { noise(0.3, 1400, 1.2, 0.3, 'bandpass', 0.5); noise(0.2, 300, 0.8, 0.3, 'lowpass'); };
  const sndWater = () => { noise(0.8, 500, 0.5, 0.35, 'lowpass', 1.6); tone(196, 0.9, 0.06, 'sine', 0.8); tone(247, 0.9, 0.05, 'sine', 0.8, 0.1); };
  const sndBlood = () => { noise(0.25, 900, 0.9, 0.3, 'bandpass', 0.4); tone(160, 0.3, 0.12, 'sawtooth', 0.5); };
  const sndChain = () => { for (let i = 0; i < 4; i++) tone(1300 + i * 170, 0.06, 0.05, 'square', 0.8, i * 0.03); noise(0.2, 3000, 1.5, 0.2, 'highpass'); };
  const sndSun = () => { tone(523, 0.6, 0.08, 'triangle', 1.5); tone(784, 0.7, 0.06, 'sine', 1.2, 0.05); noise(0.5, 2000, 0.6, 0.2, 'bandpass', 1.5); };
  const sndSand = () => noise(1.2, 700, 0.5, 0.35, 'bandpass', 1.4);
  const sndStar = () => { tone(1568, 0.3, 0.06, 'triangle', 0.6); tone(2093, 0.35, 0.05, 'sine', 0.5, 0.04); };
  const sndNeon = () => { tone(880, 0.08, 0.07, 'square', 2); tone(1760, 0.06, 0.04, 'sawtooth', 0.5, 0.02); };
  const sndBoom = () => { noise(0.8, 150, 0.8, 0.9, 'lowpass', 0.3); tone(40, 0.8, 0.5, 'sine', 0.5); };

  // ================================================================ spells
  // ---- bramble snare: a thorn trap that roots
  SPELL_CAST.bramble_snare = sp => {
    const mine = S.objs.filter(q => q.snare && !q.sprung);
    if (mine.length >= 2) mine[0].life = 0;
    const p = floorAhead(34);
    sndThorn(); burstParticles(p.x, p.y - 2, 10, 'spore', 60, 30);
    add({ snare: true, x: p.x, y: p.y, life: 10, set: new Set(),
      update(dt) {
        if (this.sprung) {
          const k = this.t - this.t0;
          if (k < 0.3) areaHit(rect(this.x - 26, this.y - 40, this.x + 26, this.y + 2), { dmg: spellDmg(58 * sp), poise: 30, bleed: 45, root: 2.6, big: true, from: this.x }, this.set);
          addLight(this.x, this.y - 16, 40, '150,210,90', Math.max(0, 0.8 - k));
          return k < tagLen('fx_g2_bramble', 'g2_bramble_snap') + 0.05;
        }
        addLight(this.x, this.y - 4, 22, '150,210,90', 0.35);
        let trip = this.t > this.life;
        if (this.t > 0.3) for (const t of foes()) { const hb = hbOf(t); if (hb && overlap(hb, rect(this.x - 16, this.y - 20, this.x + 16, this.y + 2))) { trip = true; break; } }
        if (trip && this.t <= this.life) { this.sprung = true; this.t0 = this.t; sndThorn(); sfx.hit(); shake = Math.max(shake, 3); burstParticles(this.x, this.y - 10, 16, 'spore', 120, 40); }
        return this.t <= this.life || this.sprung;
      },
      draw() {
        if (this.sprung) drawTag('fx_g2_bramble', 'g2_bramble_snap', this.t - this.t0, this.x, this.y + 1, 1, { bottom: true }, false);
        else drawTag('fx_g2_bramble', 'g2_bramble_idle', this.t, this.x, this.y + 1, 1, { bottom: true, alpha: Math.min(1, this.t * 4) * (this.life - this.t < 1.5 && Math.floor(time * 10) % 2 ? 0.5 : 1) });
      } });
  };

  // ---- drowning hymn: a travelling wave that slows
  SPELL_CAST.drowning_hymn = sp => {
    sndWater();
    const fy = floorBelow(P.x, P.y - 12, 40);
    add({ x: P.x + P.face * 14, y: fy === null ? P.y : fy, face: P.face, life: 1.5, set: new Set(),
      update(dt) {
        const nx = this.x + this.face * 135 * dt;
        if (!solidAtPx(nx + this.face * 18, this.y - 12)) this.x = nx; else this.life = Math.min(this.life, this.t + 0.2);
        const r = rect(this.x - 20, this.y - 44, this.x + 24, this.y + 2);
        const r2 = this.face > 0 ? r : rect(this.x - 24, this.y - 44, this.x + 20, this.y + 2);
        for (const t of areaHit(r2, { dmg: spellDmg(50 * sp), poise: 20, slow: 4, from: this.x - this.face * 30 }, this.set)) if (isSmall(t)) t.vx = this.face * 90;
        killEnemyProjectiles(pr => overlap(r2, rect(pr.x - 3, pr.y - 3, pr.x + 3, pr.y + 3)), '#9ff0e0');
        addLight(this.x, this.y - 20, 50, '110,220,200', 0.7);
        if (Math.random() < 0.6) particles.push({ x: this.x + rand(-18, 18), y: this.y - rand(4, 40), vx: this.face * 40, vy: -rand(5, 20), life: 0.5, kind: 'teal' });
        return this.t < this.life;
      },
      draw() { drawTag('fx_g2_hymn', 'g2_hymn', this.t, this.x, this.y + 1, this.face, { bottom: true, alpha: Math.min(1, this.t * 6, (this.life - this.t) * 4) * 0.92 }); } });
  };

  // ---- blood lance: piercing, heals per wound
  SPELL_CAST.blood_lance = sp => {
    sndBlood(); sfx.spear();
    const pr = { owner: 'player', kind: 'g3_blood', face: P.face, t: 0, hits: new Set(), x: P.x + P.face * 14, y: P.y - 18, vx: P.face * 430, vy: 0,
                 dmg: 62 * sp, life: 0.9, r: 5, pierce: true, poise: 40, sh: 'fx_g2_blood_lance', g3: 'blood', healed: 0 };
    projectiles.push(pr); S.myProj.add(pr);
  };

  // ---- crimson rite: pay life for power
  SPELL_CAST.crimson_rite = sp => {
    const cost = Math.round(D.maxHp * 0.15);
    P.hp = Math.max(1, P.hp - cost); popup(P.x, P.y - 30, cost, '#ff5060'); P.flash = 0.6;
    S.riteT = 15; refreshDerived(true);
    sndBlood(); sfx.roar(); shake = Math.max(shake, 5); flashScreen = Math.max(flashScreen, 0.12);
    spawnFx('g2_rite', P.x, P.y - 8, 1);
    burstParticles(P.x, P.y - 16, 24, 'blood', 140, 60);
  };

  // ---- soul chains: bind a foe
  SPELL_CAST.soul_chains = sp => {
    const t0 = frontFoe(190) || nearestFoe(P.x, P.y - 16, 120);
    sndChain(); tone(220, 0.8, 0.08, 'triangle', 0.6);
    const p = t0 ? null : floorAhead(60);
    add({ tgt: t0, x: t0 ? t0.x : p.x, y: t0 ? t0.y : p.y, phase: 0, hold: t0 ? 3 : 0.4,
      update(dt) {
        const t = this.tgt;
        if (t && t.alive) { this.x = t.x; this.y = t.boss ? (t.floor ?? t.y) : t.y; }
        if (this.phase === 0 && this.t > tagLen('fx_g2_chains', 'g2_chains_bind')) {
          this.phase = 1; this.t1 = this.t;
          if (t && t.alive) {
            hitT(t, { dmg: spellDmg(40 * sp), poise: 30, big: true });
            if (t.boss) { slow(t, 3); bossStance(t, 60); } else root(t, 3);
            sndChain();
          }
        }
        if (this.phase === 1 && (this.t - this.t1 > this.hold || (t && !t.alive))) {
          this.phase = 2; this.t2 = this.t; sfx.crumble(); tone(330, 0.3, 0.06, 'triangle', 0.5);
          if (t && t.alive) hitT(t, { dmg: spellDmg(34 * sp), poise: 40, big: true });
        }
        addLight(this.x, this.y - 22, 44, '140,180,255', this.phase === 2 ? Math.max(0, 0.8 - (this.t - this.t2) * 3) : 0.8);
        return this.phase < 2 || this.t - this.t2 < tagLen('fx_g2_chains', 'g2_chains_break');
      },
      draw() {
        if (this.phase === 0) drawTag('fx_g2_chains', 'g2_chains_bind', this.t, this.x, this.y + 1, 1, { bottom: true }, false);
        else if (this.phase === 1) drawTag('fx_g2_chains', 'g2_chains_hold', this.t - this.t1, this.x, this.y + 1, 1, { bottom: true, alpha: 0.9 });
        else drawTag('fx_g2_chains', 'g2_chains_break', this.t - this.t2, this.x, this.y + 1, 1, { bottom: true }, false);
      } });
  };

  // ---- sunbeam: a tracking column of light
  function sunbeam(x0, target, ticks, dmgPer, small = false) {
    const fy0 = floorBelow(x0, (target ? target.y : P.y) - 12, 140);
    return add({ x: x0, y: fy0 === null ? P.y : fy0, tgt: target, tick: 0, n: 0, ticks, on: small ? 0.08 : 0.18,
      update(dt) {
        const t = this.tgt;
        if (t && t.alive) { const c = hbc(t); if (c) this.x = approach(this.x, c.x, 70 * dt); }
        const f = floorBelow(this.x, this.y - 24, 60); if (f !== null) this.y = f;
        const live = this.t > this.on && this.n < this.ticks;
        if (live && (this.tick -= dt) <= 0) {
          this.tick = 0.14; this.n++;
          areaHit(rect(this.x - (small ? 8 : 12), this.y - 150, this.x + (small ? 8 : 12), this.y + 2), { dmg: dmgPer, poise: small ? 6 : 14, quiet: this.n > 1, burnT: small ? 0 : 3, burnDps: dmgPer * 0.25, from: this.x });
        }
        if (live) { addLight(this.x, this.y - 40, small ? 40 : 70, '255,220,130', 1); if (Math.random() < 0.6) particles.push({ x: this.x + rand(-8, 8), y: this.y - rand(0, 60), vx: 0, vy: -rand(20, 70), life: 0.5, kind: 'gold' }); }
        this.end = this.end ?? null;
        if (this.n >= this.ticks && this.end === null) this.end = this.t;
        return this.end === null || this.t - this.end < 0.16;
      },
      draw() {
        const op = small ? { bottom: true, alpha: 0.75 } : { bottom: true };
        if (this.t < this.on) drawTag('fx_g2_sunbeam', 'g2_sunbeam_on', this.t / this.on * 0.12, this.x, this.y + 1, 1, op, false);
        else if (this.end === null) drawTag('fx_g2_sunbeam', 'g2_sunbeam_loop', this.t, this.x, this.y + 1, 1, op);
        else drawTag('fx_g2_sunbeam', 'g2_sunbeam_off', this.t - this.end, this.x, this.y + 1, 1, op, false);
      } });
  }
  SPELL_CAST.sunbeam = sp => {
    const t = frontFoe(190);
    const c = t ? hbc(t) : null;
    sndSun(); flashScreen = Math.max(flashScreen, 0.06);
    sunbeam(c ? c.x : floorAhead(60).x, t, 5, spellDmg(20 * sp));
  };

  // ---- sandstorm: a crawling multi-hit storm
  SPELL_CAST.sandstorm = sp => {
    sndSand();
    const p = floorAhead(24);
    add({ x: p.x, y: p.y, face: P.face, life: 3.2, tick: 0,
      update(dt) {
        const nx = this.x + this.face * 62 * dt;
        if (!solidAtPx(nx + this.face * 20, this.y - 12)) this.x = nx;
        const f = floorBelow(this.x, this.y - 20, 48); if (f !== null) this.y = f;
        const r = rect(this.x - 22, this.y - 70, this.x + 22, this.y + 2);
        if ((this.tick -= dt) <= 0 && this.t < this.life) {
          this.tick = 0.22;
          areaHit(r, { dmg: spellDmg(13 * sp), poise: 8, quiet: true, kind: 'spell', from: this.x });
        }
        for (const t of foes()) if (isSmall(t)) { const hb = hbOf(t); if (hb && overlap(hb, rect(this.x - 44, this.y - 70, this.x + 44, this.y + 2))) t.x = approach(t.x, this.x, 40 * dt); }
        killEnemyProjectiles(pr => overlap(r, rect(pr.x - 3, pr.y - 3, pr.x + 3, pr.y + 3)), '#f0d898');
        addLight(this.x, this.y - 30, 50, '240,200,130', 0.5);
        if (Math.random() < 0.7) particles.push({ x: this.x + rand(-30, 30), y: this.y - rand(0, 60), vx: rand(-80, 80), vy: -rand(0, 30), life: 0.5, kind: 'dust' });
        if (Math.floor(this.t * 3) !== this.snd) { this.snd = Math.floor(this.t * 3); if (this.snd % 2 === 0 && this.t < this.life) noise(0.5, 800, 0.5, 0.15, 'bandpass', 1.3); }
        return this.t < this.life + 0.3;
      },
      draw() { drawTag('fx_g2_sandstorm', 'g2_sandstorm', this.t, this.x, this.y + 1, this.face, { bottom: true, alpha: Math.min(1, this.t * 4, (this.life + 0.3 - this.t) * 3) }); } });
  };

  // ---- comet: telegraphed impact
  SPELL_CAST.comet = sp => {
    const t = nearestFoe(P.x, P.y - 16, 250);
    const c = t ? hbc(t) : null;
    const x = c ? c.x : floorAhead(100).x;
    sndStar(); tone(110, 0.7, 0.1, 'sawtooth', 0.5);
    add({ tgt: t, x, y: P.y, dir: x >= P.x ? 1 : -1, fall: 0.6, fy: null, hit: false,
      update(dt) {
        const tg = this.tgt;
        if (!this.hit && tg && tg.alive && this.t < this.fall - 0.18) { const q = hbc(tg); if (q) this.x = q.x; }
        const f = floorBelow(this.x, (tg && tg.alive ? tg.y : P.y) - 24, 160); this.fy = f === null ? (tg ? tg.y : P.y) : f;
        if (!this.hit && this.t >= this.fall + 0.22) {
          this.hit = true; this.th = this.t;
          spawnFx('g2_comet_hit', this.x, this.fy + 1, 1, null, { bottom: true });
          sndBoom(); sndStar(); shake = Math.max(shake, 8); flashScreen = Math.max(flashScreen, 0.18); hitstop = Math.max(hitstop, 0.05);
          areaHit(rect(this.x - 44, this.fy - 50, this.x + 44, this.fy + 4), { dmg: spellDmg(150 * sp), poise: 90, big: true, burnT: 3, burnDps: 10 * sp, from: this.x });
          for (let i = 0; i < 20; i++) particles.push({ x: this.x, y: this.fy - 4, vx: rand(-160, 160), vy: -rand(40, 200), g: 400, life: rand(0.4, 1), kind: i % 3 ? 'mote' : 'teal' });
        }
        if (!this.hit) addLight(this.x, this.fy - 4, 30, '190,160,255', 0.5 + 0.4 * Math.sin(time * 25));
        else addLight(this.x, this.fy - 20, 90, '200,180,255', Math.max(0, 1.2 - (this.t - this.th) * 3));
        return !this.hit || this.t - this.th < 0.4;
      },
      draw() {
        if (this.hit) return;
        const k = Math.min(1, this.t / this.fall), x = Math.round(this.x), y = Math.round(this.fy);
        const rx = Math.round(26 - 14 * k);
        g.fillStyle = `rgba(190,160,255,${0.3 + 0.55 * k})`;
        for (let a = 0; a < 6.283; a += 0.18) g.fillRect(Math.round(x + Math.cos(a - time * 2) * rx), Math.round(y - 2 + Math.sin(a - time * 2) * 3), 1, 1);
        g.fillStyle = `rgba(240,236,255,${0.7 * k})`; g.fillRect(x - 2, y - 3, 5, 1); g.fillRect(x, y - 5, 1, 5);
        if (this.t > this.fall) {   // the comet streaks in from the upper side
          const q = (this.t - this.fall) / 0.22, cx = this.x - this.dir * 120 * (1 - q), cy = this.fy - 190 * (1 - q) - 10;
          drawTag('fx_g2_comet', 'g2_comet', this.t, cx - this.dir * 10, cy - 10, this.dir, { center: true });
        }
      } });
  };

  // ---- pulse shot: three quick bolts
  SPELL_CAST.pulse_shot = sp => {
    for (let k = 0; k < 3; k++) {
      const pr = { owner: 'player', kind: 'g3_pulse', face: P.face, t: 0, hits: new Set(), x: P.x, y: P.y - 18, vx: 0, vy: 0, dmg: 24 * sp, life: 0.75, r: 3, poise: 10,
                   sh: 'fx_g2_pulse', g3: 'pulse', delay: 0.001 + k * 0.08,
                   onStart() { this.x = P.x + P.face * 14; this.y = P.y - 18 + (k - 1) * 1.5; this.vx = P.face * 540; this.face = P.face; sndNeon(); } };
      projectiles.push(pr); S.myProj.add(pr);
    }
  };

  // ---- null field: deletes missiles, slows foes
  SPELL_CAST.null_field = sp => {
    const fy = floorBelow(P.x, P.y - 12, 40);
    sndNeon(); tone(220, 0.8, 0.07, 'sawtooth', 2); noise(0.4, 4000, 2, 0.15, 'highpass');
    add({ x: P.x, y: fy === null ? P.y : fy, life: 5, tick: 0,
      update(dt) {
        const R = 56, inside = (x, y) => y <= this.y + 2 && Math.hypot((x - this.x) / R, (this.y - y) / 58) < 1;
        if (this.t < this.life) {
          killEnemyProjectiles(pr => inside(pr.x, pr.y), '#ff80f0');
          const doTick = (this.tick -= dt) <= 0; if (doTick) this.tick = 0.5;
          for (const t of foes()) { const c = hbc(t); if (!c || !inside(c.x, c.hb.y1 - 4)) continue; slow(t, 0.5); if (doTick) hitT(t, { dmg: spellDmg(8 * sp), poise: 0, quiet: true, from: this.x }); }
          addLight(this.x, this.y - 28, 70, '120,220,255', 0.45);
        }
        return this.t < this.life + 0.3;
      },
      draw() { drawTag('fx_g2_null', 'g2_null', this.t, this.x, this.y + 1, 1, { bottom: true, alpha: Math.min(1, this.t * 5, (this.life + 0.3 - this.t) * 3) * (0.75 + 0.1 * Math.sin(time * 8)) }); } });
  };

  // ================================================================ weapon arts
  // Same contract as 14_gear2.js: phase 0 waits for the release frame (and the charge hold, P.artHold), then a time-driven
  // phase in P.g2 (t, rel, ch, phase, ...). W's ART_SYNC can key dedicated art_<id> animations off P.g2.
  function artAnim(tag, speed = 1) { if (!P.artOwn) P.anim.set(pHas(tag) ? tag : 'attack1', false, speed); }
  function endArt() { P.artI = false; if (P.g2 && P.g2.face) P.face = P.g2.face; setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); }
  function released() { const an = P.anim; if (!P.g2.rel && !P.artHold && (an.i >= P.artRel || an.done)) { P.g2.rel = true; P.g2.t = 0; P.g2.ch = charged(); return 'now'; } return P.g2.rel; }
  function holdAt(i) { const an = P.anim; if (an.i > i) an.i = i; if (an.i === i) { an.t = 0; an.done = false; } }
  function gather(kind, col) {
    if (Math.random() < 0.6) particles.push({ x: P.x + P.face * rand(4, 18), y: P.y - rand(10, 34), vx: 0, vy: -rand(10, 40), life: 0.4, kind });
    addLight(P.x + P.face * 10, P.y - 20, 36, col, 0.6);
  }
  const ARMOR = { reap: 1, tidal_surge: 1, pale_pyre: 1, solar_flare: 1 };
  function impl(id, fallback, release, start, update) {
    ART_IMPL[id] = {
      fallback, release, armor: !!ARMOR[id], chargeAt: Math.max(0, Math.min(release - 1, 2)),   // charge early in the wind-up
      start() { P.g2 = { t: 0, rel: false, face: 0, set: new Set() }; start && start(); },
      update(dt, grav) {
        if (!P.g2) P.g2 = { t: 0, rel: false, face: 0, set: new Set() };
        P.g2.t += dt;
        update(dt, grav, P.g2);
        if (P.state === 'art' && P.artT > 6) endArt();
      },
    };
  }
  const frontRect = (x0, y0, x1, y1) => rect(P.x + P.face * x0, P.y + y0, P.x + P.face * x1, P.y + y1);
  const stop = (dt, k = 900) => { P.vx = approach(P.vx, 0, k * dt); };
  const IMPACT = (tag, d = 4) => (ASSETS.player_meta && ASSETS.player_meta.moves && ASSETS.player_meta.moves[tag] && ASSETS.player_meta.moves[tag].active[0]) || d;

  // ---- reap: full circle sweep, pull, lifesteal
  function reapSweep(s, mult, second) {
    spawnFx('g2_reap', P.x, P.y - 14, second ? -P.face : P.face);
    sfx.heavySwing(); noise(0.3, 1600, 0.8, 0.25, 'bandpass', 0.5);
    const hit = areaHit(rect(P.x - 54, P.y - 36, P.x + 54, P.y + 2), { dmg: meleeDmg(D.light, mult), poise: 40, kind: 'heavy', big: true, melee: true, bleed: s.ch ? 50 : 0, from: P.x }, new Set());
    for (const t of hit) if (isSmall(t)) { t.vx = sign(P.x - t.x) * 150; }
    if (hit.length) heal(0.025 * Math.min(4, hit.length));
    if (hit.length) for (let i = 0; i < 10; i++) particles.push({ x: P.x + rand(-40, 40), y: P.y - rand(6, 30), vx: 0, vy: -rand(10, 30), life: 0.6, kind: 'spore' });
  }
  impl('reap', ['gs_3', 1.15], IMPACT('gs_3', 5), null, (dt, grav, s) => {
    stop(dt); grav();
    const r = released();
    if (!r) { gather('spore', '150,210,90'); return; }
    if (r === 'now') { s.face = P.face; reapSweep(s, s.ch ? 2.3 : 1.9, false); }
    if (s.ch && !s.second && s.t > 0.2) { s.second = true; reapSweep(s, 1.6, true); }
    if (P.anim.done && (!s.ch || s.second)) endArt();
  });

  // ---- harvest moon: boomerang crescent
  impl('harvest_moon', ['heavy', 1.1], 4, null, (dt, grav, s) => {
    stop(dt); grav();
    const r = released();
    if (!r) { gather('gold', '255,220,140'); return; }
    if (r === 'now') {
      sfx.heavySwing(); sndStar();
      const ch = s.ch;
      add({ x: P.x + P.face * 18, y: P.y - 18, face: P.face, v: ch ? 330 : 300, phase: 0, rad: ch ? 18 : 13, cd: new Map(), hover: ch ? 0.45 : 0,
        update(dt) {
          if (this.phase === 0) { this.v -= 620 * dt; this.x += this.face * Math.max(0, this.v) * dt; if (solidAtPx(this.x + this.face * 8, this.y)) this.v = 0; if (this.v <= 0) { this.phase = 1; this.ph = this.t; } }
          else if (this.phase === 1) { if (this.t - this.ph > this.hover) this.phase = 2; }
          else { const dx = P.x - this.x, dy = P.y - 18 - this.y, d = Math.hypot(dx, dy) || 1, v = Math.min(420, 160 + (this.t - this.ph) * 500); this.x += dx / d * v * dt; this.y += dy / d * v * dt; if (d < 12) { sfx.menu(); return false; } }
          for (const t of targets()) {
            const hb = hbOf(t); if (!hb || !overlap(hb, rect(this.x - this.rad, this.y - this.rad, this.x + this.rad, this.y + this.rad))) continue;
            if ((this.cd.get(t) || 0) > this.t) continue;
            this.cd.set(t, this.t + 0.22);
            hitT(t, { dmg: meleeDmg(D.light, ch ? 1.0 : 0.8), poise: 12, kind: 'heavy', melee: true, slow: ch ? 1.5 : 0, from: this.x });
          }
          addLight(this.x, this.y, 40, '255,230,160', 0.8);
          if (Math.random() < 0.5) particles.push({ x: this.x + rand(-8, 8), y: this.y + rand(-8, 8), vx: 0, vy: rand(-10, 10), life: 0.4, kind: 'gold' });
          if (Math.floor(this.t * 7) !== this.wh) { this.wh = Math.floor(this.t * 7); noise(0.08, 1800, 1, 0.08, 'bandpass', 0.6); }
          return this.t < 3;
        },
        draw() { drawTag('fx_g2_moon', 'g2_moon', this.t, this.x, this.y, this.face, { center: true }); } });
    }
    if (P.anim.done) endArt();
  });

  // ---- lash: whip cracks at long reach
  impl('lash', ['sp_1', 1.6], 2, null, (dt, grav, s) => {
    grav();
    const r = released();
    if (!r) { stop(dt); return; }
    if (r === 'now') { s.face = P.face; s.n = 0; s.tick = 0; s.max = s.ch ? 5 : 3; s.reach = s.ch ? 92 : 78; }
    stop(dt, 600);
    if (s.n < s.max && (s.tick -= dt) <= 0) {
      s.tick = 0.15; s.n++; s.crackT = 0;
      const last = s.n === s.max, tip = P.x + P.face * s.reach, y = P.y - 16;
      s.tip = [tip, y + rand(-4, 2)];
      areaHit(rect(Math.min(P.x + P.face * 8, tip), y - 8, Math.max(P.x + P.face * 8, tip), y + 6), { dmg: meleeDmg(D.light, 0.9), poise: 14, kind: 'light', melee: true, bleed: 18 }, new Set());
      spawnFx('g2_crack', tip, s.tip[1], P.face);
      if (last) { const back = P.x - P.face * s.reach * 0.7; s.back = [back, y]; spawnFx('g2_crack', back, y, -P.face); areaHit(rect(Math.min(P.x, back), y - 8, Math.max(P.x, back), y + 6), { dmg: meleeDmg(D.light, 1.1), poise: 25, kind: 'heavy', melee: true, bleed: 18 }, new Set()); }
      noise(0.08, 5000, 2, 0.3, 'highpass'); sfx.swing();
      if (!P.artOwn) { const tg = s.n % 2 ? 'sp_2' : 'sp_1'; P.anim.set(pHas(tg) ? tg : 'attack1', false, 2.4); P.anim.i = 2; }
    }
    if (s.crackT !== undefined) s.crackT += dt;
    if (s.n >= s.max && s.crackT > 0.22) endArt();
  });

  // ---- chain drag: hook, then pull or be pulled
  impl('chain_drag', ['hook_throw', 1.2], 1, null, (dt, grav, s) => {
    const r = released();
    if (!r) { stop(dt); grav(); return; }
    if (r === 'now') { s.face = P.face; s.phase = 1; s.len = 0; s.max = s.ch ? 210 : 150; sndChain(); }
    if (s.phase === 1) {   // chain flies out
      stop(dt); grav();
      s.len += 620 * dt;
      const tx = P.x + P.face * s.len, ty = P.y - 18;
      s.tip = [tx, ty];
      let hit = null;
      for (const t of foes()) { const hb = hbOf(t); if (hb && overlap(hb, rect(tx - 5, ty - 6, tx + 5, ty + 6))) { hit = t; break; } }
      if (hit) {
        s.tgt = hit; sfx.hit(); spawnFx('g2_crack', tx, ty, P.face);
        if (isSmall(hit)) { s.phase = 2; s.t2 = 0; hitT(hit, { dmg: meleeDmg(D.light, 0.6), poise: 60, kind: 'heavy', melee: true }); root(hit, s.ch ? 2 : 1.3); }
        else { s.phase = 3; s.t2 = 0; P.artI = true; }
      } else if (s.len >= s.max || solidAtPx(tx, ty)) { s.phase = 5; s.t2 = 0; }
    } else if (s.phase === 2) {   // drag the foe in
      stop(dt); grav(); s.t2 += dt;
      const t = s.tgt;
      if (t && t.alive) { const want = P.x + P.face * 20; if (!solidAtPx(approach(t.x, want, 520 * dt), t.y - 8)) t.x = approach(t.x, want, 520 * dt); s.tip = [t.x, P.y - 18]; }
      if (!t || !t.alive || Math.abs(t.x - (P.x + P.face * 20)) < 4 || s.t2 > 0.45) { s.phase = 4; s.t2 = 0; artAnim('attack3', 1.4); sfx.heavySwing(); spawnFx('slash3', P.x + P.face * 24, P.y - 17, P.face);
        areaHit(frontRect(-4, -34, 46, 2), { dmg: meleeDmg(D.heavy, s.ch ? 2.1 : 1.6), poise: 60, kind: 'heavy', big: true, melee: true }, s.set); }
    } else if (s.phase === 3) {   // haul yourself to a great foe
      s.t2 += dt; P.vy = 0; P.artI = true;
      const t = s.tgt, c = t && t.alive ? hbc(t) : null;
      if (c) s.tip = [c.x, c.y];
      const gap = c ? Math.abs(c.x - P.x) - (c.hb.x1 - c.hb.x0) / 2 : 0;
      P.vx = P.face * 440;
      if (!c || gap < 18 || s.t2 > 0.5 || solidAtPx(P.x + P.face * 8, P.y - 12)) {
        s.phase = 4; s.t2 = 0; P.vx = P.face * 60; P.artI = false; artAnim('attack3', 1.3); sfx.heavySwing(); shake = 5;
        spawnFx(fxOr('slam_impact', 'heavy'), P.x + P.face * 22, P.y - 14, P.face);
        areaHit(frontRect(-4, -40, 50, 2), { dmg: meleeDmg(D.heavy, s.ch ? 2.8 : 2.2), poise: 80, kind: 'heavy', big: true, melee: true }, s.set);
      }
    } else if (s.phase === 4) { s.t2 += dt; stop(dt, 700); grav(); if ((P.artOwn ? P.anim.done : s.t2 > 0.4) || s.t2 > 0.8) endArt(); }
    else { s.t2 += dt; stop(dt); grav(); s.len = Math.max(0, s.len - 900 * dt); s.tip = [P.x + P.face * s.len, P.y - 18]; if (s.len <= 0) endArt(); }
  });

  // ---- blood frenzy: pay blood, thrust flurry, lifesteal window
  impl('blood_frenzy', ['sp_1', 2.6], 1, () => {
    const cost = Math.round(D.maxHp * 0.08); P.hp = Math.max(1, P.hp - cost); popup(P.x, P.y - 30, cost, '#ff5060'); sndBlood();
  }, (dt, grav, s) => {
    grav();
    const r = released();
    if (!r) { stop(dt); gather('blood', '255,90,100'); return; }
    if (r === 'now') { s.face = P.face; s.n = 0; s.tick = 0; s.max = s.ch ? 10 : 6; S.frenzyT = s.ch ? 12 : 8; }
    if (s.n < s.max) {
      P.vx = approach(P.vx, P.face * 60, 900 * dt);
      if ((s.tick -= dt) <= 0) {
        s.tick = 0.085; s.n++;
        const y = rand(-26, -10);
        const hit = areaHit(frontRect(-2, y - 8, 48, y + 8), { dmg: meleeDmg(D.light, s.ch ? 0.7 : 0.6), poise: 8, kind: 'light', melee: true, bleed: 12 }, new Set());
        if (hit.length) heal(0.01 * hit.length);
        spawnFx('g2_thrust', P.x + P.face * 26, P.y + y, P.face); sfx.swing();
        if (!P.artOwn) { const tg = s.n % 2 ? 'sp_2' : 'sp_1'; P.anim.set(pHas(tg) ? tg : 'attack1', false, 3); P.anim.i = 2; }
      }
    } else { stop(dt); s.tick -= dt; if (s.tick < -0.2) endArt(); }
  });

  // ---- tidal surge: a rushing wave along the ground
  function surgeWave(dir, delay, mult) {
    const fy = floorBelow(P.x, P.y - 12, 40);
    add({ x: P.x + dir * 16, y: fy === null ? P.y : fy, face: dir, delay, life: 0.85, set: new Set(),
      update(dt) {
        if (this.t < this.delay) return true;
        const k = this.t - this.delay;
        if (!this.go) { this.go = true; sndWater(); sfx.boom(); }
        const nx = this.x + this.face * 230 * dt;
        if (!solidAtPx(nx + this.face * 20, this.y - 12)) this.x = nx; else this.life = Math.min(this.life, k + 0.1);
        const r = rect(this.x - 22, this.y - 42, this.x + 26, this.y + 2), r2 = this.face > 0 ? r : rect(this.x - 26, this.y - 42, this.x + 22, this.y + 2);
        for (const t of areaHit(r2, { dmg: meleeDmg(D.heavy, mult), poise: 60, kind: 'heavy', big: true, melee: true, from: this.x - this.face * 30 }, this.set)) if (isSmall(t)) { t.vx = this.face * 260; t.vy = -140; }
        killEnemyProjectiles(pr => overlap(r2, rect(pr.x - 3, pr.y - 3, pr.x + 3, pr.y + 3)), '#9ff0e0');
        addLight(this.x, this.y - 20, 50, '110,220,200', 0.7);
        if (Math.random() < 0.8) particles.push({ x: this.x + this.face * rand(0, 20), y: this.y - rand(20, 44), vx: this.face * rand(40, 120), vy: -rand(20, 80), g: 300, life: 0.5, kind: 'teal' });
        return k < this.life;
      },
      draw() { if (this.t < this.delay) return; const k = this.t - this.delay; drawTag('fx_g2_wave', 'g2_wave', k, this.x, this.y + 1, this.face, { bottom: true, alpha: Math.min(1, k * 8, (this.life - k) * 5) }); } });
  }
  impl('tidal_surge', ['sp_heavy', 1.1], 4, null, (dt, grav, s) => {
    stop(dt); grav();
    const r = released();
    if (!r) { gather('teal', '110,220,200'); return; }
    if (r === 'now') {
      shake = 5; spawnFx(fxOr('slam_impact', 'dust'), P.x + P.face * 16, P.y, 1, null, { bottom: true });
      surgeWave(P.face, 0, s.ch ? 1.9 : 1.6);
      if (s.ch) surgeWave(P.face, 0.22, 1.2);
    }
    if (P.anim.done) endArt();
  });

  // ---- solar flare: a sun bursts above you
  impl('solar_flare', ['cast', 1.2], 4, null, (dt, grav, s) => {
    stop(dt); grav();
    const r = released();
    if (!r) { gather('gold', '255,220,130'); addLight(P.x, P.y - 40, 40, '255,220,140', 0.8); return; }
    if (r === 'now') {
      const R = s.ch ? 92 : 62, cx = P.x, cy = P.y - 26;
      spawnFx('g2_flare', cx, cy, 1); sndSun(); sfx.boom(); flashScreen = Math.max(flashScreen, s.ch ? 0.3 : 0.18); shake = 5;
      for (const t of foes()) {
        const hb = hbOf(t); if (!hb || Math.hypot(clamp(cx, hb.x0, hb.x1) - cx, (clamp(cy, hb.y0, hb.y1) - cy) * 1.2) > R) continue;   // nearest point of the hurtbox
        hitT(t, { dmg: meleeDmg(D.light, s.ch ? 2.4 : 2.0), poise: 45, kind: 'heavy', big: true, melee: true, burnT: 4, burnDps: D.light * 0.25, from: cx });
        if (s.ch && !t.boss) root(t, 1.2);
      }
      s.lit = 0.5;
    }
    if (s.lit > 0) { s.lit -= dt; addLight(P.x, P.y - 26, 120, '255,220,140', s.lit * 2); }
    if (P.anim.done) endArt();
  });

  // ---- starfall: a line of falling stars
  function fallingStar(x, delay, dmg, big) {
    add({ x, y: P.y - 150, delay, big, fy: null,
      update(dt) {
        if (this.t < this.delay) return true;
        if (this.fy === null) { const f = floorBelow(this.x, P.y - 40, 120); this.fy = f === null ? P.y : f; if (solidAtPx(this.x, this.fy - 8)) return false; }
        this.y += 720 * dt;
        addLight(this.x, this.y, 26, '200,180,255', 0.8);
        if (this.y >= this.fy) {
          spawnFx(this.big ? 'g2_comet_hit' : 'g2_star_hit', this.x, this.fy + 1, 1, null, { bottom: true });
          (this.big ? sndBoom : sndStar)(); shake = Math.max(shake, this.big ? 7 : 3);
          const w = this.big ? 40 : 16;
          areaHit(rect(this.x - w, this.fy - (this.big ? 48 : 30), this.x + w, this.fy + 2), { dmg: dmg, poise: this.big ? 70 : 22, kind: 'heavy', big: this.big, melee: true, from: this.x });
          return false;
        }
        return true;
      },
      draw() { if (this.t >= this.delay && this.fy !== null) drawTag('fx_g2_star', 'g2_star', this.t, this.x, this.y + 6, 1, { bottom: true }); } });
  }
  impl('starfall', ['kt_heavy', 1.1], IMPACT('kt_heavy', 6), null, (dt, grav, s) => {
    stop(dt); grav();
    const r = released();
    if (!r) { gather('mote', '200,180,255'); return; }
    if (r === 'now') {
      spawnFx('slash_up', P.x + P.face * 14, P.y - 26, P.face, null, { bottom: true }); sfx.heavySwing(); sndStar();
      areaHit(frontRect(-4, -44, 40, 2), { dmg: meleeDmg(D.light, 1.2), poise: 30, kind: 'heavy', melee: true });
      const n = s.ch ? 8 : 5;
      for (let i = 0; i < n; i++) {
        let x = P.x + P.face * (26 + i * 18);
        if (solidAtPx(x, P.y - 10)) break;
        fallingStar(x + rand(-4, 4), 0.1 + i * 0.07, meleeDmg(D.light, 0.9), false);
      }
      if (s.ch) { let x = P.x + P.face * 70; if (!solidAtPx(x, P.y - 10)) fallingStar(x, 0.1 + n * 0.07 + 0.15, meleeDmg(D.light, 2.6), true); }
    }
    if (P.anim.done) endArt();
  });

  // ---- overclock: glitch dash + attack-speed buff
  impl('overclock', ['kt_1', 1.6], 2, null, (dt, grav, s) => {
    const r = released();
    if (!r) { stop(dt); grav(); gather('teal', '120,220,255'); return; }
    if (r === 'now') { s.face = P.face; s.x0 = P.x; P.artI = true; sndNeon(); noise(0.2, 6000, 2, 0.25, 'highpass'); spawnFx('g2_glitch', P.x, P.y - 16, P.face); S.ocT = s.ch ? 9 : 6; s.phase = 1; }
    if (s.phase === 1) {
      holdAt(P.artOwn ? P.artRel : 3);
      P.vx = P.face * 520; P.vy = 0; P.artI = true;
      S.ghosts.push({ f: P.anim.frame, x: P.x, y: P.y, face: P.face, life: 0.22, col: Math.floor(s.t * 60) % 2 ? '#ff50e0' : '#50e8ff' });
      areaHit(rect(P.x - 16, P.y - 30, P.x + 16, P.y + 2), { dmg: meleeDmg(D.light, s.ch ? 1.8 : 1.5), poise: 40, kind: 'heavy', big: true, melee: true }, s.set);
      if (Math.abs(P.x - s.x0) > 90 || s.t > 0.2 || solidAtPx(P.x + P.face * 10, P.y - 12)) { s.phase = 2; s.t2 = 0; P.artI = false; P.vx = P.face * 60; spawnFx('g2_glitch', P.x, P.y - 16, P.face); sndNeon(); }
      return;
    }
    s.t2 += dt; stop(dt, 800); grav();
    if (P.anim.done || s.t2 > 0.35) endArt();
  });

  // ---- pale pyre: rings of white fire
  function pyre(x, delay, dmg, linger) {
    const fy = floorBelow(x, P.y - 16, 48);
    if (fy === null || Math.abs(fy - P.y) > 40 || solidAtPx(x, fy - 8)) return false;
    add({ x, y: fy, delay, set: new Set(),
      update(dt) {
        if (this.t < this.delay) return true;
        const k = this.t - this.delay;
        if (!this.go) { this.go = true; sfx.fire(); noise(0.4, 1500, 0.5, 0.2, 'bandpass', 1.5); spawnFx('g2_pyre', this.x, this.y + 1, 1, null, { bottom: true });
          if (linger) GEAR3_ground(this.x, this.y, 2.5, dmg * 0.25); }
        if (k > 0.05 && k < 0.3) { const hit = areaHit(rect(this.x - 11, this.y - 64, this.x + 11, this.y + 2), { dmg, poise: 30, kind: 'heavy', fire: true, burnT: 5, burnDps: dmg * 0.12, big: true, melee: true, from: this.x }, this.set); if (hit.length) heal(0.02 * hit.length); }
        addLight(this.x, this.y - 30, 50, '255,245,220', Math.max(0, 1 - k * 2));
        return k < 0.5;
      } });
    return true;
  }
  function GEAR3_ground(x, y, dur, dps) {
    add({ x, y, life: dur, tick: 0,
      update(dt) {
        if ((this.tick -= dt) <= 0) { this.tick = 0.4; areaHit(rect(this.x - 12, this.y - 20, this.x + 12, this.y + 2), { dmg: dps * 0.4, poise: 0, quiet: true, fire: true, from: this.x }); }
        if (Math.random() < 0.3) particles.push({ x: this.x + rand(-10, 10), y: this.y - rand(2, 10), vx: 0, vy: -rand(20, 50), life: 0.5, kind: 'mote' });
        return this.t < this.life;
      },
      draw() { drawTag('fx_g_fire_ground', 'g_fire_ground', this.t, this.x, this.y + 1, 1, { bottom: true, flash: 0.75, flashColor: '#fff2d8', alpha: Math.min(1, (this.life - this.t) * 2, this.t * 6) * 0.8 }); } });
  }
  impl('pale_pyre', ['gs_heavy', 1.0], IMPACT('gs_heavy', 7), null, (dt, grav, s) => {
    stop(dt); grav();
    const r = released();
    if (!r) { gather('mote', '255,245,220'); return; }
    if (r === 'now') {
      shake = 7; sfx.boom(); spawnFx(fxOr('slam_impact', 'shockwave'), P.x + P.face * 20, P.y, 1, null, { bottom: true });
      const waves = s.ch ? 4 : 3;
      for (const d of [1, -1]) for (let i = 0; i < waves; i++) if (!pyre(P.x + d * (22 + i * 26), i * 0.12, meleeDmg(D.heavy, s.ch ? 1.35 : 1.15), s.ch)) break;
    }
    if (P.anim.done) endArt();
  });

  // ================================================================ charms
  HOOKS.derive.push(d => {   // damage buffs: Crimson Rite, Court Signet
    const now = typeof SAVE !== 'undefined' ? SAVE.playTime || 0 : 0;
    const court = S.court.filter(t => t > now).length;
    const m = (S.riteT > 0 ? 1.3 : 1) * (1 + 0.05 * Math.min(5, court));
    S.dmgMul = m;
    if (m !== 1) { d.light *= m; d.heavy *= m; d.spell *= m; }
  });
  const reDerive = () => { if (P && D) refreshDerived(true); };
  HOOKS.strike.push((t, info) => {
    if (charmOn('c_bloodvial')) heal(0.01);
    if (S.frenzyT > 0) heal(0.015);
    if (charmOn('c_antler') && info && info.heavy && !t.prop) {
      if (t.boss) slow(t, 1); else root(t, 1.1);
      for (let i = 0; i < 6; i++) particles.push({ x: info.x + rand(-6, 6), y: info.y + rand(0, 14), vx: rand(-30, 30), vy: -rand(20, 60), g: 200, life: 0.5, kind: 'spore' });
    }
  });
  HOOKS.playerHurt.push((dmg, opt) => {
    S.moss = 0;
    if (charmOn('c_lastflame') && !S.lastFlame && dmg >= P.hp && P.hp > 1) {
      S.lastFlame = true; S.lastFlameT = 3; dmg = P.hp - 1;
      sfx.kindle(); flashScreen = Math.max(flashScreen, 0.3); slowmo = 0.6;
      spawnFx('g2_pyre', P.x, P.y + 1, 1, null, { bottom: true }); toast('The Last Flame holds', 2);
    }
    return dmg;
  });
  HOOKS.parry.push(() => { if (charmOn('c_countess')) { heal(0.1); P.empower = 3; burstParticles(P.x, P.y - 16, 10, 'blood', 70); } });
  (HOOKS.negated = HOOKS.negated || []).push((dmg, dir, opt) => {
    if (P.state !== 'roll') return;
    if (charmOn('c_scarab') && S.scarabCd <= 0) {
      S.scarabCd = 1.5; noise(0.4, 900, 0.6, 0.3, 'bandpass', 1.5);
      for (let i = 0; i < 20; i++) particles.push({ x: P.x + rand(-10, 10), y: P.y - rand(0, 20), vx: rand(-140, 140), vy: -rand(10, 80), g: 200, life: rand(0.4, 0.8), kind: 'dust' });
      for (const t of foes()) { const c = hbc(t); if (c && Math.hypot(c.x - P.x, c.y - P.y + 14) < 54) { if (t.boss) slow(t, 1.2); else root(t, 1.2); } }
    }
    if (charmOn('c_neon') && S.neonCd <= 0) {
      S.neonCd = 1; P.empower = 3; sndNeon();
      const t = nearestFoe(P.x, P.y - 16, 220), c = t && hbc(t);
      const a = c ? Math.atan2(c.y - (P.y - 18), c.x - P.x) : (P.face > 0 ? 0 : Math.PI);
      const pr = { owner: 'player', kind: 'g3_pulse', face: Math.cos(a) >= 0 ? 1 : -1, t: 0, hits: new Set(), x: P.x, y: P.y - 18, vx: Math.cos(a) * 520, vy: Math.sin(a) * 520, dmg: 26 * D.spell, life: 0.7, r: 3, poise: 10, sh: 'fx_g2_pulse', g3: 'pulse' };
      projectiles.push(pr); S.myProj.add(pr);
    }
  });
  HOOKS.cast.push(id => {
    if (!charmOn('c_sun') || S.sunCd > 0) return;
    const t = nearestFoe(P.x, P.y - 16, 180); if (!t) return;
    S.sunCd = 1.2; const c = hbc(t);
    sunbeam(c.x, t, 2, spellDmg(18 * D.spell), true);
  });
  HOOKS.rest.push(() => { S.lastFlame = false; S.court = []; S.riteT = 0; reDerive(); });
  HOOKS.death.push(() => { S.riteT = 0; S.frenzyT = 0; S.ocT = 0; S.court = []; });
  HOOKS.enter.push(() => { S.objs = []; S.ghosts = []; S.myProj.clear(); S.star.dart = null; });

  function onKill(e) {
    if (charmOn('c_court')) { const now = SAVE.playTime || 0; S.court = S.court.filter(t => t > now); if (S.court.length >= 5) S.court.shift(); S.court.push(now + 20); reDerive(); }
    if (charmOn('c_crown')) {
      const src = { x: e.x, y: e.y - (e.h || 24) / 2 };
      const t = nearestFoe(src.x, src.y, 160, q => q !== e);
      if (t) {
        const c = hbc(t);
        sndChain();
        add({ x0: src.x, y0: src.y, tgt: t, life: 0.35, done: false,
          update() { if (!this.done && this.t > 0.08) { this.done = true; if (this.tgt.alive) hitT(this.tgt, { dmg: meleeDmg(D.light, 1.6), poise: 30, big: true, from: this.x0 }); } return this.t < this.life; },
          draw() { const q = hbc(this.tgt) || c; drawChain(this.x0, this.y0, q.x, q.y, -10, ['#d8ecff', '#80b0ff', '#4060c0'], Math.max(0, 1 - this.t / this.life)); } });
      }
    }
  }

  // ================================================================ hooks: update / render / hud
  HOOKS.update.push(dt => {
    if (!P) return;
    for (const o of S.objs) o.t += dt;
    { const cur = S.objs; S.objs = []; const keep = cur.filter(o => o.update(dt) !== false); S.objs = keep.concat(S.objs); }
    for (const gh of S.ghosts) gh.life -= dt; S.ghosts = S.ghosts.filter(gh => gh.life > 0);
    // my projectiles: blood lance lifesteal + trails, pulse sparks
    for (const pr of S.myProj) {
      const alive = pr.life > 0 && projectiles.includes(pr);
      if (alive && !(pr.delay > 0)) {
        if (pr.g3 === 'blood') {
          addLight(pr.x, pr.y, 30, '255,80,90', 0.8);
          if (Math.random() < 0.6) particles.push({ x: pr.x - sign(pr.vx) * 12, y: pr.y + rand(-2, 2), vx: -pr.vx * 0.05, vy: rand(-10, 20), g: 120, life: 0.4, kind: 'blood' });
          while (pr.healed < Math.min(3, pr.hits.size)) {
            pr.healed++; heal(0.03);
            for (let i = 0; i < 6; i++) particles.push({ x: pr.x, y: pr.y, vx: (P.x - pr.x) * rand(1.5, 2.5), vy: (P.y - 16 - pr.y) * rand(1.5, 2.5) - 30, life: 0.45, kind: 'blood' });
          }
        } else if (pr.g3 === 'pulse') { addLight(pr.x, pr.y, 20, '255,120,240', 0.8); if (Math.random() < 0.5) particles.push({ x: pr.x - sign(pr.vx) * 6, y: pr.y, vx: 0, vy: 0, life: 0.2, kind: 'teal' }); }
      } else if (!alive) {
        S.myProj.delete(pr);
        if (pr.t > 0) spawnFx(pr.g3 === 'pulse' ? 'g2_pulse_hit' : 'hit', pr.x, pr.y, pr.face || 1, null, pr.g3 === 'blood' ? { tint: '#ff4050' } : {});
      }
    }
    // buffs
    if (S.riteT > 0) { S.riteT -= dt; if (Math.random() < 0.35) particles.push({ x: P.x + rand(-7, 7), y: P.y - rand(2, 28), vx: 0, vy: -rand(10, 30), life: 0.5, kind: 'blood' }); if (S.riteT <= 0) reDerive(); }
    if (S.frenzyT > 0) { S.frenzyT -= dt; if (Math.random() < 0.2) particles.push({ x: P.x + rand(-6, 6), y: P.y - rand(4, 24), vx: 0, vy: rand(10, 30), life: 0.4, kind: 'blood' }); }
    if (S.ocT > 0) {
      S.ocT -= dt;
      if (ATK[P.state]) { if (P.gOc !== P.anim.tag + P.combo) { P.gOc = P.anim.tag + P.combo; P.anim.speed *= 1.35; } if (Math.random() < 0.3) S.ghosts.push({ f: P.anim.frame, x: P.x, y: P.y, face: P.face, life: 0.14, col: Math.random() < 0.5 ? '#ff50e0' : '#50e8ff' }); }
      else P.gOc = null;
    }
    if (S.court.length && S.court[0] <= (SAVE.playTime || 0)) { S.court = S.court.filter(t => t > (SAVE.playTime || 0)); reDerive(); }
    S.scarabCd -= dt; S.neonCd -= dt; S.sunCd -= dt;
    // kills (c_crown, c_court)
    for (const e of enemies) if (!e.alive && !e.g3Seen) { e.g3Seen = true; if (Math.abs(e.x - P.x) < 260 && Math.abs(e.y - P.y) < 160) onKill(e); }
    // c_moss
    S.moss += dt;
    if (charmOn('c_moss') && S.moss > 4 && P.hp < D.maxHp && P.state !== 'dead') { P.hp = Math.min(D.maxHp, P.hp + D.maxHp * 0.012 * dt); if (Math.random() < 0.08) particles.push({ x: P.x + rand(-6, 6), y: P.y - rand(2, 20), vx: 0, vy: -rand(8, 20), life: 0.6, kind: 'spore' }); }
    // c_pearl: flask cross-restore (fires when the flask's effect lands)
    if (P.state === 'heal' && P.healPending) S.pearlPend = P.healPending;
    else if (S.pearlPend && !P.healPending) {
      if (charmOn('c_pearl') && P.state !== 'hurt') {
        if (S.pearlPend === 1) P.fp = Math.min(D.maxFp, P.fp + Math.round(D.maxFp * 0.2)); else P.hp = Math.min(D.maxHp, P.hp + Math.round(D.maxHp * 0.15));
        burstParticles(P.x, P.y - 14, 8, 'teal', 50, 30);
      }
      S.pearlPend = 0;
    }
    // c_countess: criticals heal too
    if (P.state === 'riposte' && !S.ripo) { S.ripo = true; if (charmOn('c_countess')) { heal(0.1); P.empower = 3; } } else if (P.state !== 'riposte') S.ripo = false;
    // c_orrery: arts cost 30% less
    if (P.artCount !== undefined && P.artCount !== S.artCount) {
      if (P.state === 'art' && P.artT < 0.2 && charmOn('c_orrery') && ARTS[P.artId]) P.fp = Math.min(D.maxFp, P.fp + Math.round(ARTS[P.artId].fp * 0.3));
      S.artCount = P.artCount;
    }
    // c_lastflame
    if (S.lastFlameT > 0) { S.lastFlameT -= dt; P.inv = Math.max(P.inv, 0.1); if (Math.random() < 0.6) particles.push({ x: P.x + rand(-8, 8), y: P.y - rand(0, 30), vx: 0, vy: -rand(20, 60), life: 0.5, kind: 'mote' }); addLight(P.x, P.y - 14, 60, '255,245,220', 0.9); }
    // c_star: an orbiting star that darts at foes
    const st = S.star;
    if (charmOn('c_star') && P.state !== 'dead') {
      st.a += dt * 3; st.cd -= dt;
      if (!st.dart && st.cd <= 0) {
        const t = nearestFoe(P.x, P.y - 16, 74);
        if (t) { st.dart = { t, k: 0, x: P.x + Math.cos(st.a) * 16, y: P.y - 18 + Math.sin(st.a) * 8 }; st.cd = 1.4; }
      }
      if (st.dart) {
        const d = st.dart, c = d.t.alive ? hbc(d.t) : null;
        d.k += dt;
        if (c && d.k < 0.4) { d.x = lerp(d.x, c.x, Math.min(1, dt * 14)); d.y = lerp(d.y, c.y, Math.min(1, dt * 14)); if (Math.hypot(c.x - d.x, c.y - d.y) < 6 && !d.hit) { d.hit = true; hitT(d.t, { dmg: meleeDmg(D.light, 0.45) + 6, poise: 6, from: P.x }); spawnFx('g2_star_hit', c.x, c.hb.y1 + 1, 1, null, { bottom: true, alpha: 0.7 }); sndStar(); } }
        if (!c || d.k >= 0.4 || d.hit && d.k > 0.2) st.dart = null;
      }
      const sx = st.dart ? st.dart.x : P.x + Math.cos(st.a) * 16, sy = st.dart ? st.dart.y : P.y - 18 + Math.sin(st.a) * 8;
      st.x = sx; st.y = sy; addLight(sx, sy, 16, '210,190,255', 0.8);
    } else st.x = null;
  });
  HOOKS.render.push(() => {
    if (!P) return;
    for (const o of S.objs) if (o.draw) o.draw();
    for (const gh of S.ghosts) drawSprite(sheet('player'), gh.f, gh.x, gh.y, gh.face, { alpha: Math.min(1, gh.life / 0.22) * 0.5, flash: 1, flashColor: gh.col });
    // whip / chain lines for the active art
    if (P.state === 'art' && P.g2 && P.g2.rel) {
      const s = P.g2, hx = P.x + P.face * 8, hy = P.y - 18;
      if (P.artId === 'lash' && s.tip && s.crackT < 0.16) {
        drawChain(hx, hy, s.tip[0], s.tip[1], 6 - s.crackT * 50, ['#e8d8b0', '#a08860', '#6a5438'], 1 - s.crackT * 4);
        if (s.back && s.n === s.max) drawChain(hx, hy, s.back[0], s.back[1], 6, ['#e8d8b0', '#a08860'], 1 - s.crackT * 5);
      }
      if (P.artId === 'chain_drag' && s.tip && s.phase !== 4) {
        drawChain(hx, hy, s.tip[0], s.tip[1], s.phase === 1 || s.phase === 5 ? 4 : 0, ['#c8cce0', '#8088a8', '#50566e']);
        g.fillStyle = '#e0e4f4'; g.fillRect(Math.round(s.tip[0]) - 1, Math.round(s.tip[1]) - 1, 3, 3);
      }
    }
    if (S.star.x !== null && S.star.x !== undefined && charmOn('c_star')) {
      const x = Math.round(S.star.x), y = Math.round(S.star.y);
      g.fillStyle = '#f4f0ff'; g.fillRect(x, y, 1, 1); g.fillStyle = 'rgba(200,180,255,0.9)'; g.fillRect(x - 1, y, 3, 1); g.fillRect(x, y - 1, 1, 3);
      g.fillStyle = 'rgba(150,120,230,0.5)'; g.fillRect(x - 2, y, 1, 1); g.fillRect(x + 2, y, 1, 1); g.fillRect(x, y - 2, 1, 1); g.fillRect(x, y + 2, 1, 1);
    }
  });
  HOOKS.renderTop.push(() => {
    if (S.riteT > 0) { g.fillStyle = `rgba(140,0,20,${0.06 + 0.03 * Math.sin(time * 4)})`; g.fillRect(0, 0, W, H); }
    if (S.ocT > 0 && Math.floor(time * 30) % 7 === 0) { g.fillStyle = 'rgba(255,80,230,0.06)'; g.fillRect(0, Math.floor(rand(0, H)), W, 2); g.fillStyle = 'rgba(80,230,255,0.06)'; g.fillRect(0, Math.floor(rand(0, H)), W, 1); }
  });
  HOOKS.hud.push(() => {
    if (!P || !D) return;
    let x = 150;
    const buff = (ic, t, max) => { icon(ic, x, 196, 8, t < 2 ? 0.4 + 0.6 * Math.abs(Math.sin(time * 8)) : 1); vctx.fillStyle = 'rgba(10,6,8,0.8)'; vctx.fillRect(ox + x * scale, oy + 205 * scale, 8 * scale, 1.2 * scale); vctx.fillStyle = '#e8c070'; vctx.fillRect(ox + x * scale, oy + 205 * scale, 8 * scale * clamp(t / max, 0, 1), 1.2 * scale); x += 11; };
    if (S.riteT > 0) buff('s_crimson_rite', S.riteT, 15);
    if (S.frenzyT > 0) buff('a_blood_frenzy', S.frenzyT, 12);
    if (S.ocT > 0) buff('a_overclock', S.ocT, 9);
    const now = SAVE.playTime || 0, court = S.court.filter(t => t > now).length;
    if (court && charmOn('c_court')) { icon('c_court', x, 196, 8); text('×' + court, x + 9, 203, 5, '#e6c77a', 'left'); x += 18; }
  });

  const api = { S, onKill, sunbeam, reDerive };
  if (typeof window !== 'undefined') window.__gear3 = api;
  return api;
})();
