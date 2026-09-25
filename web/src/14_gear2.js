// ------------------------------------------------------------------ expansion gear (agent G): spells, weapon arts, charms
// Registers the 9 new spells, 12 weapon arts and 13 charms from docs/EXPANSION_CONTRACT.md §5 through registerGear(),
// implements SPELL_CAST / ART_IMPL for them and the charm effects that live in general combat (c_bead, c_quill, c_core,
// c_scale, c_clapper). Icons: ui_icons3 (art/gen_ui3.py). Effects: fx_g_* sheets (art/gen_fx4.py).
// Everything lives inside this closure; the only shared state it touches is through the registries/hooks.
const GEAR2 = (() => {
  // ================================================================ data
  registerGear({
    spells: {
      ink_seal: { name: 'Ink Seal', fp: 14, icon: 's_ink_seal', sheet: 'ui_icons3',
        desc: 'Write a seal of living ink on the floor before you. It bursts when a foe steps on it, or after four seconds. Up to three at once.' },
      glyph_swarm: { name: 'Glyph Swarm', fp: 20, icon: 's_glyph_swarm', sheet: 'ui_icons3',
        desc: 'The Unwritten’s last words: a volley of five runes that hunt down the nearest foes.' },
      glacial_wall: { name: 'Glacial Wall', fp: 18, icon: 's_glacial_wall', sheet: 'ui_icons3',
        desc: 'Raise a slab of glacier ice before you. It wounds and chills what it bursts through, and stops missiles for six seconds.' },
      frost_nova: { name: 'Frost Nova', fp: 24, icon: 's_frost_nova', sheet: 'ui_icons3',
        desc: 'The Twins’ cold breath: a ring of frost races out along the ground, building frostbite on all it touches.' },
      magma_orb: { name: 'Magma Orb', fp: 20, icon: 's_magma_orb', sheet: 'ui_icons3',
        desc: 'Lob a ball of molten slag. It bursts on impact and leaves the ground burning.' },
      chain_lightning: { name: 'Chain Lightning', fp: 22, icon: 's_chain_lightning', sheet: 'ui_icons3',
        desc: 'Loose a bolt that leaps from foe to foe, striking up to four.' },
      stormcall: { name: 'Stormcall', fp: 26, icon: 's_stormcall', sheet: 'ui_icons3',
        desc: 'Cindervane’s fury. Mark the three nearest foes; a heartbeat later, lightning falls on each.' },
      wind_ward: { name: 'Wind Ward', fp: 16, icon: 's_wind_ward', sheet: 'ui_icons3',
        desc: 'Oswin’s prayer. For three seconds a gale wraps you and turns missiles back on those who loosed them.' },
      ember_echo: { name: 'Ember Echo', fp: 14, icon: 's_ember_echo', sheet: 'ui_icons3',
        desc: 'A spark of the First Ember. The next spell you cast is cast a second time, free.' },
    },
    arts: {
      whirlwind: { name: 'Whirlwind', fp: 14, desc: 'Spin the staff and advance in a storm of blows that strikes both sides. Hold to spin longer.' },
      gale_vault: { name: 'Gale Vault', fp: 16, desc: 'Vault over foes on a gust of wind, kicking what you pass, then crash down with a cut. Hold for a trailing gale.' },
      ink_mark: { name: 'Ink Seal', fp: 12, desc: 'Draw a glyph trap on the floor ahead that bursts when a foe treads on it. Hold to draw three.' },
      aegis: { name: 'Aegis', fp: 10, desc: 'A perfect guard for a moment: every blow is turned aside and missiles are sent back. Hold for a longer stance that ends in a burst of light.' },
      frost_aegis: { name: 'Frost Aegis', fp: 12, desc: 'Brace behind a shield of rime. Blows are negated and whoever strikes it freezes. Hold to end with a frost burst.' },
      shield_charge: { name: 'Shield Charge', fp: 12, desc: 'Rush forward behind your shield, bowling small foes before you and slamming into large ones. Hold to charge further, trailing fire.' },
      magma_quake: { name: 'Magma Quake', fp: 20, desc: 'Smash the ground and split it open: fissures of lava erupt in a line before you. Hold to open them both ways.' },
      thunder_lunge: { name: 'Thunder Lunge', fp: 16, desc: 'Become lightning: a thrust across the room, untouchable while it lasts, followed by a thunderclap along its path.' },
      tolling_blow: { name: 'Tolling Blow', fp: 16, desc: 'A ringing overhead blow. Its peal stuns every foe nearby and rattles even great ones.' },
      twin_tempest: { name: 'Twin Tempest', fp: 18, desc: 'An eight-cut flurry of both blades, ending in a crossing strike.' },
      echo: { name: 'Echo', fp: 6, desc: 'Your weapon remembers. Repeat the last weapon art you used, without paying its cost again.' },
      backstep_slash: { name: 'Backstep Slash', fp: 10, desc: 'Hop back out of reach, then lunge in with a long cut. Hold to loose a crescent with it.' },
    },
    charms: {
      c_bead: { name: 'Pilgrim’s Bead', desc: 'Oswin’s prayer beads, worn smooth by a thousand miles. Stamina recovers 30% faster.' },
      c_lantern: { name: 'Librarian’s Lantern', desc: 'A lantern that burned in the Archives for a century. A wide light surrounds you that no darkness can snuff out, and breakable walls nearby glow faintly.' },
      c_quill: { name: 'Unwritten Quill', desc: 'The pen that wrote the Unwritten. Spells are cast 20% faster.' },
      c_frostheart: { name: 'Frostheart', desc: 'A heart of ice that never thawed. You are immune to frost buildup.' },
      c_aegis: { name: 'Warden’s Aegis', desc: 'A plate of the Ice Warden’s shell. Blocking with a shield costs 30% less stamina.' },
      c_twin: { name: 'Twinned Flame', desc: 'The Twins’ bond: flame and frost. After you block or parry, your next hit deals 25% more.' },
      c_slag: { name: 'Slag Ward', desc: 'A drop of cooled slag. Lava and fire hurt you half as much, and burn builds half as fast.' },
      c_brand: { name: 'Forge Brand', desc: 'The Overseer’s branding iron. Heavy attacks cost 20% less stamina.' },
      c_core: { name: 'Colossus Core', desc: 'The Colossus’ heart, still beating. Taking damage stokes it; when full, it erupts in fire around you.' },
      c_feather: { name: 'Stormdrake Feather', desc: 'A feather from a storm-drake’s wing. Glide longer, and dash a second time in the air.' },
      c_scale: { name: 'Cindervane’s Scale', desc: 'A scale of the storm-drake, black as a thundercloud. Take 15% less damage from great foes.' },
      c_clapper: { name: 'Bell-Ringer’s Clapper', desc: 'The tongue of the Spire’s great bell. A successful parry rings out, stunning foes nearby.' },
      c_echo: { name: 'Echo of the First', desc: 'All that remains of the First Ember. Every third weapon art costs no FP.' },
    },
  }, 'ui_icons3');

  // ================================================================ shared helpers
  const S = { objs: [], ghosts: [], echo: 0, echoing: false, ward: 0, lastArt: null, core: 0, coreFlash: 0, afflicted: new Set(), myProj: new Set() };
  const foes = () => targets().filter(t => !t.prop);
  const hbc = t => { const hb = t.hurtbox && t.hurtbox(); return hb ? { x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2, hb } : null; };
  const charged = () => !!P.artCharged;
  const isSmall = t => t instanceof Enemy && !t.cfg.elite;
  function tileIsFloor(t) { return isSolidT(t) || t === T_PLAT; }
  function floorBelow(x, y, max = 112) {
    for (let ty = Math.floor(y / TILE); ty <= Math.floor((y + max) / TILE); ty++) {
      if (tileIsFloor(tileAt(Math.floor(x / TILE), ty)) && !isSolidT(tileAt(Math.floor(x / TILE), ty - 1))) return ty * TILE;
      for (const d of room.dyn) if (d.on() && x >= d.x0 && x < d.x1 && ty * TILE <= d.y0 && d.y0 < ty * TILE + TILE) return d.y0;
    }
    return null;
  }
  // a point on the floor `dist` px ahead of the player, pulled back from walls
  function floorAhead(dist) {
    let x = P.x + P.face * dist;
    for (let k = 0; k < 8 && solidAtPx(x, P.y - 8); k++) x -= P.face * 6;
    const fy = floorBelow(x, P.y - 12);
    return { x, y: fy === null ? P.y : fy };
  }
  function hitT(t, o) {
    const c = hbc(t); if (!c) return false;
    t.hit(Object.assign({ dir: t.x >= (o.from ?? P.x) ? 1 : -1, kind: 'spell', x: c.x, y: c.y, poise: 20 }, o));
    if (!t.prop) {
      if (o.frost) frostUp(t, o.frost);
      if (o.burn) burnUp(t, o.burn);
      if (o.stun) stun(t, o.stun);
    }
    return true;
  }
  // damage everything whose hurtbox overlaps r; `set` avoids double hits; returns targets hit
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
  const spellDmg = base => outgoing(base, 1, 'spell');
  const meleeDmg = (base, mult) => outgoing(base, mult, 'melee');

  // ---- local status effects (frost / burn / stun). Agent W's generic buildup (strike hook) can replace these later:
  // everything funnels through frostUp / burnUp / stun below.
  function frostUp(t, n) {
    if (typeof WSTATUS !== 'undefined') return WSTATUS.frost(t, n);   // one shared frost meter with weapons (13_weapons.js)
    if (!t.alive) return;
    t.gFrost = (t.gFrost || 0) + n * (t.boss ? 0.55 : 1); t.gFrostT = 4; S.afflicted.add(t);
    if (t.gFrost < 100) return;
    t.gFrost = 0;
    const mh = t.maxHp || 400, dmg = t.boss ? mh * 0.035 + 45 : mh * 0.14 + 30;
    const c = hbc(t) || { x: t.x, y: t.y - 16 };
    t.hit({ dmg, poise: t.boss ? 40 : 60, dir: 0, kind: 'spell', x: c.x, y: c.y, big: true });
    popups.push({ x: c.x, y: c.y - 18, v: 'Frostbite', color: '#a8dcff', life: 0.9 });
    spawnFx('g_spark', c.x, c.y, 1, null, { tint: '#bfe8ff' });
    for (let i = 0; i < 16; i++) particles.push({ x: c.x + rand(-8, 8), y: c.y + rand(-10, 10), vx: rand(-70, 70), vy: -rand(20, 100), g: 260, life: rand(0.4, 0.9), kind: 'frost' });
    tone(1568, 0.25, 0.06, 'triangle', 0.7); noise(0.25, 3500, 1, 0.18, 'highpass');
    if (!t.boss) stun(t, 1.6, true);
  }
  function burnUp(t, n) {
    if (!t.alive) return;
    t.gBurn = (t.gBurn || 0) + n; S.afflicted.add(t);
    if (t.gBurn >= 100) { t.gBurn = 0; t.gBurnT = 5; t.gBurnTick = 0; sfx.fire(); }
  }
  function stun(t, s, frozen = false) {
    if (!t.alive || t.boss || t.noStun || !(t instanceof Enemy)) return;   // custom enemy classes can opt out with noStun
    const d = t.cfg.elite ? s * 0.5 : s;
    t.gStun = Math.max(t.gStun || 0, d); t.gFrozen = frozen || (t.gFrozen && t.gStun > 0); S.afflicted.add(t);
  }
  function bossStance(t, n) {   // rattle a boss's stance without dealing damage
    if (!t.boss || t.state === 'stagger' || !(t.stanceImmune <= 0) || t.stanceMax === undefined) return;
    t.stance = (t.stance || 0) + n;
    if (t.stance >= t.stanceMax && (!t.canStagger || t.canStagger())) t.stagger();
  }
  function updateStatus(dt) {
    for (const t of S.afflicted) {
      if (!t.alive) { S.afflicted.delete(t); continue; }
      if (t.gFrostT > 0) { t.gFrostT -= dt; if (t.gFrostT <= 0) t.gFrost = Math.max(0, (t.gFrost || 0) - 30 * dt); } else if (t.gFrost > 0) t.gFrost = Math.max(0, t.gFrost - 30 * dt);
      if (t.gBurn > 0) t.gBurn = Math.max(0, t.gBurn - 8 * dt);
      if (t.gBurnT > 0) {
        t.gBurnT -= dt; t.gBurnTick -= dt;
        if (Math.random() < 0.5) particles.push({ x: t.x + rand(-7, 7), y: t.y - rand(4, (t.h || 30)), vx: 0, vy: -rand(20, 50), life: 0.4, kind: 'fire' });
        addLight(t.x, t.y - 14, 30, '255,140,60', 0.6);
        if (t.gBurnTick <= 0) {
          t.gBurnTick = 0.5;
          const mh = t.maxHp || 400, d = t.boss ? mh * 0.004 + 6 : mh * 0.03 + 4;
          if (t instanceof Enemy) {
            t.hp -= d; t.dmgShown = (t.dmgT > 0 ? t.dmgShown : 0) + d; t.dmgT = 1.5; popup(t.x, t.y - (t.h || 26) - 6, d, '#ff9a4a');
            if (t.hp <= 0) { t.die({ dir: 0 }); continue; }
          } else { const c = hbc(t); if (c) t.hit({ dmg: d, poise: 0, dir: 0, kind: 'spell', x: c.x, y: c.y, quiet: true }); }
        }
      }
      if (t.gStun > 0) {
        t.gStun -= dt;
        if (!['stagger', 'parried', 'dead'].includes(t.state)) {
          t.state = 'hurt'; t.anim.set(t.sh.has('hurt') ? 'hurt' : (t.sh.has('idle') ? 'idle' : Object.keys(t.sh.tags)[0]), false);
          t.vx *= Math.pow(0.02, dt);
        }
        if (t.gFrozen && Math.random() < 0.15) particles.push({ x: t.x + rand(-6, 6), y: t.y - rand(2, t.h || 24), vx: 0, vy: -rand(4, 12), life: 0.5, kind: 'frost' });
        if (t.gStun <= 0) t.gFrozen = false;
      }
      if (!(t.gFrost > 0) && !(t.gBurnT > 0) && !(t.gStun > 0) && !(t.gBurn > 0)) S.afflicted.delete(t);
    }
  }
  function drawStatus() {
    for (const t of S.afflicted) {
      if (!t.alive || !(t instanceof Enemy)) continue;
      if (t.gStun > 0 && t.gFrozen) drawSprite(t.sh, t.anim.frame, t.x, t.y, t.face, { flash: 0.6, flashColor: '#b8e4ff', alpha: 0.75 });
      else if (t.gStun > 0) {   // ringing stars above the head
        for (let k = 0; k < 3; k++) {
          const a = time * 5 + k * 2.09, x = Math.round(t.x + Math.cos(a) * 7), y = Math.round(t.y - (t.h || 26) - 8 + Math.sin(a) * 2);
          g.fillStyle = k === 0 ? '#fff2c0' : '#e8b048'; g.fillRect(x, y, 1, 1); g.fillRect(x - 1, y, 3, 1); g.fillRect(x, y - 1, 1, 3);
        }
      }
      if (t.gFrost > 0 && t.hp < t.maxHp) {
        const w = t.cfg.elite ? 40 : 20, x = Math.round(t.x - w / 2), y = Math.round(t.y - t.h - (t.cfg.flying ? 0 : 6) - 4) + 3;
        g.fillStyle = 'rgba(10,6,8,0.8)'; g.fillRect(x - 1, y, w + 2, 2); g.fillStyle = '#8fd0ff'; g.fillRect(x, y, Math.max(0, w * t.gFrost / 100), 1);
      }
    }
  }

  // ---- drawing helpers
  function tagFrame(name, tag, t, loop = true) {
    const s = sheet(name); if (!s.ok) return null;
    const tg = s.tags[tag] || s.tag(Object.keys(s.tags)[0]); let ms = t * 1000, f = tg.from, total = 0;
    for (let i = tg.from; i <= tg.to; i++) total += s.frames[i].ms;
    if (loop && total) ms %= total;
    while (f < tg.to && ms >= s.frames[f].ms) { ms -= s.frames[f].ms; f++; }
    return { s, f, done: !loop && t * 1000 >= total, total: total / 1000 };
  }
  function drawTag(name, tag, t, x, y, face, opt = {}, loop = true) {
    const r = tagFrame(name, tag, t, loop); if (!r) return;
    drawSprite(r.s, r.f, x, y, face, opt);
  }
  function jagPts(x0, y0, x1, y1, seed, amp = 5, n = 0) {
    const L = Math.hypot(x1 - x0, y1 - y0); n = n || Math.max(3, Math.round(L / 10));
    const nx = -(y1 - y0) / (L || 1), ny = (x1 - x0) / (L || 1), pts = [[x0, y0]];
    for (let i = 1; i < n; i++) { const o = (hash2(seed, i) * 2 - 1) * amp; pts.push([x0 + (x1 - x0) * i / n + nx * o, y0 + (y1 - y0) * i / n + ny * o]); }
    pts.push([x1, y1]); return pts;
  }
  function drawBolt(pts, a = 1, glow = '110,204,255', core = '244,252,255') {
    for (const [w, col, al] of [[3, glow, 0.35 * a], [1, core, a]]) {
      g.fillStyle = `rgba(${col},${al})`;
      for (let i = 0; i < pts.length - 1; i++) {
        const [x0, y0] = pts[i], [x1, y1] = pts[i + 1], n = Math.max(1, Math.ceil(Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0))));
        for (let k = 0; k <= n; k++) { const x = Math.round(x0 + (x1 - x0) * k / n), y = Math.round(y0 + (y1 - y0) * k / n); g.fillRect(x - (w >> 1), y - (w >> 1), w, w); }
      }
    }
  }
  const sndThunder = () => { noise(0.6, 180, 0.7, 0.8, 'lowpass', 0.4); noise(0.15, 4000, 1, 0.3, 'highpass'); tone(52, 0.5, 0.3, 'sawtooth', 0.6); };
  const sndZap = () => { noise(0.18, 5000, 2, 0.25, 'bandpass', 0.5); tone(1760, 0.12, 0.05, 'square', 0.4); };
  const sndIce = () => { tone(1976, 0.3, 0.06, 'triangle', 0.8); noise(0.3, 4200, 1.5, 0.22, 'highpass'); tone(988, 0.2, 0.05, 'sine', 1.2, 0.05); };
  const sndInk = () => { noise(0.35, 700, 0.8, 0.35, 'lowpass', 0.5); tone(220, 0.3, 0.1, 'triangle', 0.5); };
  const sndWind = () => noise(0.5, 1200, 0.6, 0.25, 'bandpass', 1.8);
  const sndBell = (k = 1) => { [196, 247, 294, 392].forEach((f, i) => tone(f, 1.6 * k, 0.12, 'sine', 1, i * 0.02)); tone(98, 1.8 * k, 0.16, 'triangle'); };
  function add(o) { o.t = 0; S.objs.push(o); return o; }
  function ringParticles(x, y, n, kind, sp = 90, up = 0) {
    for (let i = 0; i < n; i++) { const a = rand(0, 6.283), v = rand(sp * 0.4, sp); particles.push({ x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v * 0.6 - up, g: 120, life: rand(0.3, 0.8), kind }); }
  }

  // ================================================================ glyph traps (Ink Seal spell + Ink Seal art)
  function placeGlyph(x, y, o) {
    const mine = S.objs.filter(q => q.glyph);
    if (mine.length >= (o.max || 3)) mine[0].boom = true;
    return add({
      glyph: true, x, y, dmg: o.dmg, melee: !!o.melee, r: o.r || 38, life: 4, arm: 0.35,
      update(dt) {
        addLight(this.x, this.y - 4, 34, '170,120,255', 0.55 + 0.25 * Math.sin(time * 9));
        if (Math.random() < 0.25) particles.push({ x: this.x + rand(-14, 14), y: this.y - 2, vx: 0, vy: -rand(8, 22), life: 0.6, kind: Math.random() < 0.3 ? 'gold' : 'ink' });
        if (!this.boom && this.t > this.arm) for (const t of foes()) { const hb = hbOf(t); if (hb && overlap(hb, rect(this.x - 15, this.y - 24, this.x + 15, this.y + 2))) { this.boom = true; break; } }
        if (this.t > this.life) this.boom = true;
        if (this.boom) { this.detonate(); return false; }
        return true;
      },
      detonate() {
        shake = Math.max(shake, 5); sndInk(); sfx.boom();
        spawnFx('g_ink_burst', this.x, this.y - 16, 1);
        ringParticles(this.x, this.y - 12, 18, 'ink', 140, 40); ringParticles(this.x, this.y - 12, 8, 'gold', 120, 40);
        const r = this.r;
        areaHit(rect(this.x - r, this.y - r - 10, this.x + r, this.y + 4), { dmg: this.melee ? meleeDmg(this.dmg, 1) : spellDmg(this.dmg), poise: 50, big: true, kind: this.melee ? 'heavy' : 'spell', from: this.x });
      },
      draw() {
        const a = Math.min(1, this.t / this.arm) * (this.life - this.t < 1 && Math.floor(time * 14) % 2 ? 0.45 : 1);
        drawTag('fx_g_glyph', 'g_glyph', this.t, this.x, this.y + 1, 1, { bottom: true, alpha: a });
      },
    });
  }
  SPELL_CAST.ink_seal = sp => {
    const p = floorAhead(30);
    placeGlyph(p.x, p.y, { dmg: 112 * sp });
    sndInk(); spawnFx('g_spark', p.x, p.y - 4, 1, null, { tint: '#a070ff' });
    for (let i = 0; i < 10; i++) particles.push({ x: P.x + P.face * 12, y: P.y - 18, vx: (p.x - P.x) * rand(1.5, 3), vy: rand(-40, 20), g: 200, life: 0.4, kind: 'ink' });
  };

  // ================================================================ glyph swarm (seeking runes)
  SPELL_CAST.glyph_swarm = sp => {
    sfx.bolt(); sndInk();
    for (let k = 0; k < 5; k++) {
      const ang = (-100 + k * 50) * Math.PI / 180;   // fan out behind/above the caster, then hunt
      const pr = { owner: 'player', kind: 'g_rune', face: P.face, t: 0, hits: new Set(), x: P.x, y: P.y - 20, vx: 0, vy: 0, dmg: 32 * sp, life: 2.6, r: 5, seek: 7.5, poise: 14, sh: 'fx_g_rune',
        delay: 0.02 + k * 0.07, onStart() { this.x = P.x - P.face * 4 + Math.cos(ang) * 10 * P.face; this.y = P.y - 22 + Math.sin(ang) * 10; this.vx = P.face * (70 + Math.cos(ang) * 90); this.vy = Math.sin(ang) * 130 - 30; tone(1200 + k * 180, 0.08, 0.04, 'triangle'); } };
      projectiles.push(pr); S.myProj.add(pr);
    }
  };

  // ================================================================ glacial wall
  SPELL_CAST.glacial_wall = sp => {
    const p = floorAhead(26);
    const walls = S.objs.filter(q => q.wall && !q.dying);
    if (walls.length >= 2) walls[0].shatter();
    sndIce(); shake = Math.max(shake, 4); sfx.crumble();
    const w = add({
      wall: true, x: p.x, y: p.y, life: 6, face: P.face, hitSet: new Set(),
      rect() { return rect(this.x - 9, this.y - 46 * Math.min(1, this.t / 0.16), this.x + 9, this.y); },
      shatter() { if (this.dying) return; this.dying = true; this.dt0 = this.t; sndIce(); for (let i = 0; i < 14; i++) particles.push({ x: this.x + rand(-8, 8), y: this.y - rand(4, 44), vx: rand(-90, 90), vy: -rand(20, 120), g: 400, life: rand(0.5, 1), kind: 'frost' }); },
      update(dt) {
        addLight(this.x, this.y - 24, 46, '150,210,255', 0.8);
        if (!this.dying) {
          if (this.t < 0.25) areaHit(rect(this.x - 18, this.y - 46 * Math.min(1, this.t / 0.16), this.x + 18, this.y), { dmg: spellDmg(64 * sp), poise: 60, frost: 45, big: true, from: this.x - this.face * 20 }, this.hitSet);
          const r = rect(this.x - 10, this.y - 48, this.x + 10, this.y + 2);
          for (const pr of projectiles) if (pr.owner !== 'player' && !(pr.delay > 0) && pr.life > 0 && !pr.static && !pr.fxName && overlap(r, rect(pr.x - pr.r, pr.y - pr.r, pr.x + pr.r, pr.y + pr.r))) {
            pr.life = 0; spawnFx('g_spark', pr.x, pr.y, 1, null, { tint: '#cfeaff' }); ringParticles(pr.x, pr.y, 6, 'frost', 70); tone(2200, 0.08, 0.05, 'triangle');
          }
          for (const h of hazards) if (h.wave && overlap(r, rect(h.x - 3, h.y - 10, h.x + 3, h.y))) h.life = 0;
          if (this.t > this.life) this.shatter();
          if (Math.random() < 0.1) particles.push({ x: this.x + rand(-9, 9), y: this.y - rand(0, 44), vx: 0, vy: -rand(4, 10), life: 0.7, kind: 'frost' });
          return true;
        }
        return this.t - this.dt0 < 0.32;
      },
      draw() {
        if (this.dying) drawTag('fx_g_icewall', 'g_icewall_shatter', this.t - this.dt0, this.x, this.y + 1, 1, { bottom: true }, false);
        else if (this.t < 0.2) drawTag('fx_g_icewall', 'g_icewall_rise', this.t, this.x, this.y + 1, 1, { bottom: true }, false);
        else drawTag('fx_g_icewall', 'g_icewall_idle', this.t, this.x, this.y + 1, 1, { bottom: true, alpha: this.life - this.t < 1 ? 0.6 + 0.4 * Math.abs(Math.sin(time * 10)) : 1 });
      },
    });
    for (let i = 0; i < 10; i++) particles.push({ x: w.x + rand(-12, 12), y: w.y - 2, vx: rand(-60, 60), vy: -rand(40, 130), g: 380, life: 0.6, kind: 'frost' });
  };

  // ================================================================ frost nova (ring travels outward)
  function frostNova(x, y, o) {
    spawnFx('g_frost_nova', x, y + 1, 1, null, { bottom: true });
    sndIce(); tone(330, 0.5, 0.08, 'sine', 0.5); shake = Math.max(shake, 5); flashScreen = Math.max(flashScreen, 0.08);
    for (let i = 0; i < 24; i++) particles.push({ x: x + rand(-8, 8), y: y - rand(4, 20), vx: rand(-160, 160), vy: -rand(10, 80), g: 120, life: rand(0.4, 0.9), kind: 'frost' });
    add({ x, y, set: new Set(), R: o.r || 62,
      update(dt) {
        const r = Math.min(this.R, 8 + this.t * 300);
        addLight(this.x, this.y - 10, r + 20, '150,210,255', Math.max(0, 1 - this.t * 1.6));
        areaHit(rect(this.x - r, this.y - 46, this.x + r, this.y + 4), { dmg: o.dmg, poise: 35, frost: o.frost, kind: o.kind || 'spell', from: this.x }, this.set);
        if (r < this.R) for (const pr of projectiles) if (pr.owner !== 'player' && pr.life > 0 && !pr.static && !pr.fxName && Math.hypot(pr.x - this.x, pr.y - (this.y - 14)) < r) { pr.life = 0; ringParticles(pr.x, pr.y, 5, 'frost', 60); }
        return this.t < 0.35;
      } });
  }
  SPELL_CAST.frost_nova = sp => frostNova(P.x, P.y, { dmg: spellDmg(70 * sp), frost: 65, r: 66 });

  // ================================================================ magma orb + burning ground
  function burningGround(x, y, dur, dps, w = 56) {
    add({ x, y, life: dur, w, tick: 0,
      update(dt) {
        addLight(this.x, this.y - 8, 44, '255,130,50', 0.8 * Math.min(1, (this.life - this.t) * 2));
        if (Math.random() < 0.3) particles.push({ x: this.x + rand(-this.w / 2, this.w / 2), y: this.y - rand(2, 10), vx: 0, vy: -rand(20, 60), life: 0.5, kind: Math.random() < 0.5 ? 'fire' : 'ember' });
        if ((this.tick -= dt) <= 0) { this.tick = 0.4; areaHit(rect(this.x - this.w / 2, this.y - 22, this.x + this.w / 2, this.y + 2), { dmg: dps * 0.4, poise: 0, burn: 22, quiet: true, fire: true, from: this.x }); }
        return this.t < this.life;
      },
      draw() { drawTag('fx_g_fire_ground', 'g_fire_ground', this.t, this.x, this.y + 1, 1, { bottom: true, alpha: Math.min(1, (this.life - this.t) * 2, this.t * 6) }); },
    });
  }
  SPELL_CAST.magma_orb = sp => {
    sfx.fire(); sfx.shoot();
    add({ x: P.x + P.face * 10, y: P.y - 22, vx: P.face * 185, vy: -175, face: P.face,
      update(dt) {
        this.vy += 560 * dt; this.x += this.vx * dt; this.y += this.vy * dt;
        addLight(this.x, this.y, 40, '255,140,60', 1);
        if (Math.random() < 0.8) particles.push({ x: this.x - sign(this.vx) * 3, y: this.y + rand(-2, 2), vx: -this.vx * 0.1, vy: rand(-20, 10), life: 0.4, kind: 'fire' });
        let hit = solidAtPx(this.x, this.y + 3) || solidAtPx(this.x + sign(this.vx) * 4, this.y) || this.t > 2.5;
        if (!hit) for (const t of foes()) { const hb = hbOf(t); if (hb && overlap(hb, rect(this.x - 5, this.y - 5, this.x + 5, this.y + 5))) { hit = true; break; } }
        if (!hit) return true;
        const fy = floorBelow(this.x, this.y - 10, 40);
        const gy = fy === null ? this.y : fy;
        spawnFx('g_magma_burst', this.x, fy === null ? this.y + 22 : gy + 1, 1, null, { bottom: true });
        sfx.boom(); sfx.fire(); shake = Math.max(shake, 5);
        areaHit(rect(this.x - 30, this.y - 30, this.x + 30, this.y + 16), { dmg: spellDmg(76 * sp), poise: 40, fire: true, burn: 45, big: true, from: this.x });
        if (fy !== null) burningGround(this.x, gy, 3.5, 34 * sp);
        for (let i = 0; i < 18; i++) particles.push({ x: this.x, y: this.y, vx: rand(-110, 110), vy: -rand(40, 180), g: 420, life: rand(0.4, 0.9), kind: 'fire' });
        return false;
      },
      draw() { drawTag('fx_g_magma_orb', 'g_magma_orb', this.t, this.x, this.y, this.face, { center: true }); },
    });
  };

  // ================================================================ chain lightning
  SPELL_CAST.chain_lightning = sp => {
    const ox = P.x + P.face * 12, oy = P.y - 18;
    const hit = [], pool = foes();
    let first = null, bd = 1e9;
    for (const t of pool) {
      const c = hbc(t); if (!c) continue;
      const dx = (c.x - P.x) * P.face, dy = Math.abs(c.y - oy);
      if (dx > -12 && dx < 200 && dy < 80) { const d = Math.hypot(dx, dy); if (d < bd && lineOfSight(ox, oy, c.x, c.y)) { bd = d; first = t; } }
    }
    const segs = [];
    if (first) {
      let cur = first, from = [ox, oy];
      while (cur && hit.length < 4) {
        const c = hbc(cur); hit.push(cur); segs.push([from[0], from[1], c.x, c.y, cur]);
        from = [c.x, c.y]; let nb = null, nd = 125;
        for (const t of pool) { if (hit.includes(t)) continue; const q = hbc(t); if (!q) continue; const d = Math.hypot(q.x - c.x, q.y - c.y); if (d < nd && lineOfSight(c.x, c.y, q.x, q.y)) { nd = d; nb = t; } }
        cur = nb;
      }
    } else {   // no foe: the bolt forks out ahead and fizzles against the first wall
      let x = ox; while (Math.abs(x - ox) < 150 && !solidAtPx(x, oy)) x += P.face * 4;
      segs.push([ox, oy, x, oy + rand(-6, 6), null]);
    }
    sndZap(); sfx.bolt(); flashScreen = Math.max(flashScreen, 0.08);
    add({ segs, seed: irand(0, 9999), fired: 0,
      update(dt) {
        while (this.fired < this.segs.length && this.t >= this.fired * 0.06) {
          const [, , x, y, t] = this.segs[this.fired];
          spawnFx('g_spark', x, y, 1);
          if (t) { hitT(t, { dmg: spellDmg(70 * sp * Math.pow(0.88, this.fired)), poise: 30, big: true, dir: sign(x - this.segs[this.fired][0]) }); }
          else ringParticles(x, y, 8, 'teal', 80);
          if (this.fired) sndZap();
          this.fired++;
        }
        for (let i = 0; i < this.fired; i++) addLight(this.segs[i][2], this.segs[i][3], 40, '140,210,255', Math.max(0, 1 - this.t * 2.5));
        return this.t < 0.42;
      },
      draw() {
        const fl = Math.floor(this.t * 30);
        for (let i = 0; i < this.fired; i++) {
          const [x0, y0, x1, y1] = this.segs[i], age = this.t - i * 0.06, a = Math.max(0, 1 - age / 0.32);
          if (a <= 0) continue;
          drawBolt(jagPts(x0, y0, x1, y1, this.seed + i * 17 + fl, 6), a);
          if (age < 0.12) drawBolt(jagPts(x0, y0, (x0 + x1) / 2 + rand(-10, 10), (y0 + y1) / 2 + rand(-14, 14), this.seed + i * 31 + fl, 4, 3), a * 0.6);
        }
      },
    });
  };

  // ================================================================ stormcall (three telegraphed strikes)
  SPELL_CAST.stormcall = sp => {
    const list = foes().map(t => ({ t, c: hbc(t) })).filter(o => o.c && Math.abs(o.c.x - P.x) < 250 && Math.abs(o.c.y - P.y) < 140)
      .sort((a, b) => Math.abs(a.c.x - P.x) - Math.abs(b.c.x - P.x)).slice(0, 3);
    const marks = list.map(o => ({ t: o.t, x: o.c.x }));
    for (let i = marks.length, n = marks.length; i < 3; i++) {   // leftover strikes: again on the marked foes (weaker), else ahead of you
      if (n) { const m = marks[(i - n) % n]; marks.push({ t: m.t, x: m.x, k: 0.6 }); continue; }
      let x = P.x + P.face * (48 + i * 36); for (let k = 0; k < 10 && solidAtPx(x, P.y - 10); k++) x -= P.face * 8;
      marks.push({ t: null, x });
    }
    tone(110, 0.9, 0.12, 'sawtooth', 0.7); noise(0.9, 300, 0.6, 0.25, 'lowpass', 0.5); flashScreen = Math.max(flashScreen, 0.05);
    marks.forEach((m, i) => add({
      m, when: 0.5 + i * 0.2, struck: false, fy: null,
      update(dt) {
        if (!this.struck && this.m.t && this.m.t.alive && this.t < this.when - 0.12) { const c = hbc(this.m.t); if (c) this.m.x = c.x; }
        if (this.fy === null || !this.struck) { const base = this.m.t && this.m.t.alive ? this.m.t.y - 4 : P.y - 12; const f = floorBelow(this.m.x, base, 160); this.fy = f === null ? base + 4 : f; }
        if (!this.struck) {
          addLight(this.m.x, this.fy - 6, 26, '140,210,255', 0.5 + 0.4 * Math.sin(time * 30));
          if (this.t >= this.when) {
            this.struck = true; sndThunder(); shake = Math.max(shake, 6); flashScreen = Math.max(flashScreen, 0.16);
            spawnFx('g_bolt', this.m.x, this.fy + 1, 1, null, { bottom: true });
            areaHit(rect(this.m.x - 16, this.fy - 110, this.m.x + 16, this.fy + 4), { dmg: spellDmg(96 * sp * (this.m.k || 1)), poise: 55, big: true, from: this.m.x });
            for (let k = 0; k < 14; k++) particles.push({ x: this.m.x, y: this.fy - 2, vx: rand(-120, 120), vy: -rand(20, 120), g: 400, life: rand(0.3, 0.7), kind: 'teal' });
          }
          return true;
        }
        addLight(this.m.x, this.fy - 50, 70, '170,225,255', Math.max(0, 1.2 - (this.t - this.when) * 4));
        return this.t < this.when + 0.3;
      },
      draw() {
        if (this.struck) return;
        const k = Math.min(1, this.t / this.when), x = Math.round(this.m.x), y = Math.round(this.fy);
        // ground sigil: a cyan ellipse closing in, and a thin flickering thread from the sky
        const rx = Math.round(18 - 10 * k);
        g.fillStyle = `rgba(120,210,255,${0.35 + 0.5 * k})`;
        for (let a = 0; a < 6.283; a += 0.25) g.fillRect(Math.round(x + Math.cos(a + time * 3) * rx), Math.round(y - 2 + Math.sin(a + time * 3) * 2.5), 1, 1);
        g.fillStyle = `rgba(230,250,255,${0.6 * k})`; g.fillRect(x - 1, y - 3, 3, 1);
        if (Math.floor(time * 24) % 3 && k > 0.35) { g.fillStyle = `rgba(160,225,255,${0.25 + 0.35 * k})`; for (let yy = y - 120; yy < y - 4; yy += 3) g.fillRect(x + Math.round(Math.sin(yy * 0.3 + time * 40) * 1.2), yy, 1, 2); }
      },
    }));
  };

  // ================================================================ wind ward (deflect missiles)
  function reflect(pr, mult = 1) {
    pr.owner = 'player'; pr.homing = 0; pr.hits = new Set(); pr.gRefl = true; pr.pool = false;
    let best = null, bd = 280;
    for (const t of foes()) { const c = hbc(t); if (!c) continue; const d = Math.hypot(c.x - pr.x, c.y - pr.y); if (d < bd) { bd = d; best = c; } }
    const v = Math.max(220, Math.hypot(pr.vx, pr.vy) * 1.35);
    if (best) { const a = Math.atan2(best.y - pr.y, best.x - pr.x); pr.vx = Math.cos(a) * v; pr.vy = Math.sin(a) * v; pr.seek = 3; }
    else { pr.vx = -sign(pr.vx || 1) * v; pr.vy = -Math.abs(pr.vy) * 0.3; }
    pr.g = (pr.g || 0) * 0.15; pr.dmg = Math.max(30, pr.dmg * 2.2) * mult; pr.life = Math.max(pr.life, 1.6); pr.poise = 30; pr.face = sign(pr.vx);
    spawnFx(fxOr('parry_spark', 'hit'), pr.x, pr.y, sign(pr.vx)); sfx.block(); tone(1760, 0.12, 0.05, 'triangle', 1.3);
  }
  const reflectable = pr => pr.owner !== 'player' && pr.life > 0 && !(pr.delay > 0) && !pr.static && !pr.fxName && !pr.tick && !pr.win && Math.hypot(pr.vx || 0, pr.vy || 0) > 30;
  SPELL_CAST.wind_ward = sp => { S.ward = 3; S.wardT = 0; sndWind(); tone(523, 0.4, 0.06, 'sine', 1.5); ringParticles(P.x, P.y - 14, 16, 'mote', 110); };

  // ================================================================ ember echo
  SPELL_CAST.ember_echo = sp => {
    S.echo = 30; sfx.fire(); tone(784, 0.5, 0.08, 'triangle'); tone(1175, 0.6, 0.06, 'triangle', 1, 0.12);
    spawnFx(fxOr('cinderblade', 'hit'), P.x, P.y - 16, P.face);
    ringParticles(P.x, P.y - 16, 20, 'ember', 90, 30);
  };
  HOOKS.cast.push(id => {
    if (S.echoing || id === 'ember_echo' || !(S.echo > 0)) return;
    S.echo = 0;
    add({ echo: true, update() {
      if (this.t < 0.32) { if (Math.random() < 0.5) particles.push({ x: P.x + rand(-8, 8), y: P.y - rand(6, 28), vx: 0, vy: -rand(20, 50), life: 0.4, kind: 'ember' }); return true; }
      if (P.state === 'dead') return false;
      S.echoing = true;
      try { castSpell(id); } finally { S.echoing = false; }
      spawnFx(fxOr('cinderblade', 'hit'), P.x + P.face * 8, P.y - 18, P.face, null, { alpha: 0.7 });
      tone(988, 0.3, 0.06, 'triangle', 0.8); S.ghosts.push({ f: P.anim.frame, x: P.x, y: P.y, face: P.face, life: 0.35, col: '#ffb060' });
      return false;
    } });
  });

  // ================================================================ weapon arts
  // Each art: phase 0 waits for the release frame (so a charge hold or a dedicated art_<id> animation stays in sync),
  // then a time-driven phase in P.g2. P.artCharged (set by the charge system) makes every art bigger.
  const A = {};   // id -> helpers
  function artAnim(tag, speed = 1) { if (!P.artOwn) P.anim.set(pHas(tag) ? tag : 'attack1', false, speed); }
  function endArt() { P.artI = false; if (P.g2 && P.g2.face) P.face = P.g2.face; setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); }
  function released() { const an = P.anim; if (!P.g2.rel && !P.artHold && (an.i >= P.artRel || an.done)) { P.g2.rel = true; P.g2.t = 0; P.g2.ch = charged(); return 'now'; } return P.g2.rel; }
  function holdAt(i) { const an = P.anim; if (an.i > i) an.i = i; if (an.i === i) { an.t = 0; an.done = false; } }
  function glowGather(kind, col) {
    if (Math.random() < 0.6) particles.push({ x: P.x + P.face * rand(4, 18), y: P.y - rand(10, 34), vx: 0, vy: -rand(10, 40), life: 0.4, kind });
    addLight(P.x + P.face * 10, P.y - 20, 36, col, 0.6);
  }
  const ARMOR = { magma_quake: 1, tolling_blow: 1, shield_charge: 1, whirlwind: 1 };   // hyper-armour (needs the hurtPlayer patch in NEEDS)
  function impl(id, fallback, release, start, update) {
    ART_IMPL[id] = {
      fallback, release, armor: !!ARMOR[id],
      start() { P.g2 = { t: 0, rel: false, face: 0, set: new Set() }; start && start(); },
      update(dt, grav) {
        if (!P.g2) P.g2 = { t: 0, rel: false, face: 0, set: new Set() };
        P.g2.t += dt;
        update(dt, grav, P.g2);
        if (P.state === 'art' && P.artT > 6) endArt();   // safety net
      },
    };
  }
  const frontRect = (x0, y0, x1, y1) => rect(P.x + P.face * x0, P.y + y0, P.x + P.face * x1, P.y + y1);
  const stop = (dt, k = 900) => { P.vx = approach(P.vx, 0, k * dt); };
  const IMPACT = tag => (ASSETS.player_meta && ASSETS.player_meta.moves && ASSETS.player_meta.moves[tag] && ASSETS.player_meta.moves[tag].active[0]) || 4;

  // ---- whirlwind: spinning advance, strikes both sides every 0.14 s
  impl('whirlwind', ['sp_1', 1.3], 1, null, (dt, grav, s) => {
    const r = released();
    if (!r) { stop(dt); grav(); glowGather('mote', '200,240,220'); return; }
    if (r === 'now') { s.face = P.face; s.dur = s.ch ? 1.45 : 0.95; s.tick = 0; s.n = 0; sndWind(); }
    const ax = inputX();
    P.vx = approach(P.vx, (ax || s.face) * (ax ? 110 : 70), 600 * dt); grav();
    if (ax) s.face = ax;
    if ((s.tick -= dt) <= 0 && s.t < s.dur) {
      s.tick = 0.14; s.n++; P.hitSet = new Set();
      areaHit(rect(P.x - 34, P.y - 36, P.x + 34, P.y + 2), { dmg: meleeDmg(D.light, s.ch ? 0.95 : 0.75), poise: 14, kind: 'light', melee: true, from: P.x }, P.hitSet);
      (s.n % 2 ? sfx.swing : sfx.heavySwing)();
      if (!P.artOwn) { P.face = s.n % 2 ? -s.face : s.face; P.anim.set(pHas(s.n % 2 ? 'sp_2' : 'sp_1') ? (s.n % 2 ? 'sp_2' : 'sp_1') : 'attack1', false, 2.6); P.anim.i = 2; }
      if (s.ch) for (const t of foes()) if (t instanceof Enemy && !t.cfg.elite && Math.abs(t.x - P.x) < 70 && Math.abs(t.y - P.y) < 30) t.vx = sign(P.x - t.x) * 60;   // the gale drags small foes in
      for (let i = 0; i < 4; i++) particles.push({ x: P.x + rand(-30, 30), y: P.y - rand(2, 26), vx: rand(-60, 60), vy: -rand(10, 40), life: 0.4, kind: 'mote' });
    }
    if (P.artOwn && s.t < s.dur && P.anim.done) P.anim.set(P.anim.tag, false, 1);
    addLight(P.x, P.y - 16, 50, '200,240,220', 0.6);
    if (s.t >= s.dur) {
      if (s.ch && !s.burst) { s.burst = true; spawnFx(fxOr('spin', 'shockwave'), P.x, P.y, 1); sfx.boom(); shake = 5;
        areaHit(rect(P.x - 54, P.y - 40, P.x + 54, P.y + 2), { dmg: meleeDmg(D.light, 1.6), poise: 60, kind: 'heavy', big: true, melee: true, from: P.x }); }
      if (s.t >= s.dur + 0.12) endArt();
    }
  });

  // ---- gale vault: vault kick over foes, then a downward cut
  impl('gale_vault', ['double_jump', 1.0], 0, null, (dt, grav, s) => {
    const r = released();
    if (!r) { stop(dt); grav(); glowGather('mote', '200,240,220'); return; }
    if (r === 'now') {
      s.face = P.face; P.vy = s.ch ? -380 : -330; P.vx = P.face * 150; P.ground = false; P.artI = true; s.phase = 1;
      sndWind(); sfx.jump(); spawnFx(fxOr('gale', 'dust'), P.x, P.y, P.face); spawnFx('dust', P.x, P.y, P.face);
    }
    grav();
    if (s.phase === 1) {
      P.vx = approach(P.vx, P.face * 150, 400 * dt);
      if (s.t > 0.3) P.artI = false;
      areaHit(frontRect(-6, -22, 24, 8), { dmg: meleeDmg(D.light, 1.0), poise: 25, kind: 'light', melee: true }, s.set);
      if (Math.random() < 0.6) particles.push({ x: P.x + rand(-6, 6), y: P.y, vx: rand(-20, 20), vy: rand(10, 40), life: 0.35, kind: 'mote' });
      if ((P.vy > 20 && s.t > 0.2) || s.t > 0.55) {
        s.phase = 2; s.t2 = 0; artAnim('air_attack', 1.3); P.vy = Math.max(P.vy, 120); sfx.heavySwing(); s.set = new Set();
        spawnFx('slash_air', P.x + P.face * 20, P.y - 10, P.face);
        if (s.ch) projectiles.push({ owner: 'player', kind: 'crescent', face: P.face, t: 0, hits: new Set(), x: P.x + P.face * 16, y: P.y - 8, vx: P.face * 200, vy: 110, dmg: D.light * 1.3, life: 0.7, r: 10, pierce: true, poise: 30, sh: 'fx_slash_air' });
      }
    } else if (s.phase === 2) {
      s.t2 += dt; P.vx = approach(P.vx, P.face * 90, 500 * dt);
      if (s.t2 < 0.22) areaHit(frontRect(-10, -40, 48, 16), { dmg: meleeDmg(D.light, s.ch ? 2.9 : 2.1), poise: 55, kind: 'heavy', big: true, melee: true }, s.set);
      if (P.ground || s.t2 > 1.5) { spawnFx('dust', P.x, P.y, P.face); sfx.land(); s.phase = 3; s.t3 = 0; if (!P.artOwn) P.anim.set(pHas('land') ? 'land' : 'idle', false); }
    } else { stop(dt, 1400); if ((s.t3 += dt) > 0.12) endArt(); }
  });

  // ---- ink seal (art): glyph traps from the quill
  impl('ink_mark', ['cast', 1.3], 4, null, (dt, grav, s) => {
    stop(dt); grav();
    const r = released();
    if (!r) { glowGather('ink', '170,120,255'); return; }
    if (r === 'now') {
      const n = s.ch ? 3 : 1;
      for (let k = 0; k < n; k++) { const p = floorAhead(34 + k * 28); placeGlyph(p.x, p.y, { dmg: D.light * (s.ch ? 2.0 : 2.4), melee: true, max: 3 }); spawnFx('g_spark', p.x, p.y - 4, 1, null, { tint: '#a070ff' }); }
      sndInk();
    }
    if (P.anim.done) endArt();
  });

  // ---- aegis / frost aegis: perfect-guard stance
  function guardStance(frost) {
    return (dt, grav, s) => {
      stop(dt, 1200); grav();
      const r = released();
      if (!r) return;
      const hold = P.artOwn ? P.artRel : 2;
      if (r === 'now') { s.dur = s.ch ? 1.8 : 1.2; s.blocked = new Set(); P.artI = true; sfx.block(); tone(frost ? 1318 : 880, 0.3, 0.07, 'triangle', 1.2); }
      if (s.t < s.dur) {
        holdAt(hold); P.artI = true;
        addLight(P.x + P.face * 10, P.y - 16, 44, frost ? '150,210,255' : '255,210,120', 0.8);
        // missiles are sent back
        const cx = P.x + P.face * 6, cy = P.y - 14;
        for (const pr of projectiles) if (reflectable(pr) && Math.hypot(pr.x - cx, pr.y - cy) < 30) { reflect(pr, frost ? 1.2 : 1.4); if (frost) { pr.gFrost = 35; } s.gl = 0.25; }
        // blows are turned aside: an enemy whose active hit window overlaps us is "blocked"
        const guard = rect(P.x - 16, P.y - 34, P.x + 16, P.y + 2);
        for (const e of enemies) {
          if (!e.alive || e.state !== 'attack' || s.blocked.has(e.id + ':' + e.atkId)) continue;
          for (const w of metaWindows(e.sh, e.atk)) {
            if (!w.hit || e.anim.i < w.active[0] || e.anim.i > w.active[1]) continue;
            if (!overlap(metaRect(e.sh, e, w.hit), guard)) continue;
            s.blocked.add(e.id + ':' + e.atkId); blocked(e, frost, s); break;
          }
        }
        for (const src of S.negated) if (!s.blocked.has(src)) { s.blocked.add(src); blocked(src, frost, s); }
        S.negated.length = 0;
        s.gl = Math.max(0, (s.gl || 0) - dt);
      } else if (!s.done) {
        s.done = true; P.artI = false;
        if (s.ch) {
          if (frost) frostNova(P.x + P.face * 10, P.y, { dmg: meleeDmg(D.light, 1.3), frost: 60, r: 52, kind: 'heavy' });
          else { spawnFx(fxOr('holy_burst', 'parry_flash'), P.x + P.face * 16, P.y - 16, P.face); sfx.boom(); shake = 5; flashScreen = 0.12;
            areaHit(frontRect(-6, -44, 56, 4), { dmg: meleeDmg(D.light, 1.8), poise: 60, kind: 'heavy', big: true, melee: true }); }
        }
      }
      if (s.done && P.anim.done) endArt();
    };
  }
  function blocked(e, frost, s) {
    const c = hbc(e) || { x: e.x, y: e.y - 20 };
    sfx.parry(); hitstop = Math.max(hitstop, 0.08); shake = Math.max(shake, 3); s.gl = 0.3;
    spawnFx(fxOr('parry_flash', 'parry_spark'), P.x + P.face * 12, P.y - 18, P.face, null, frost ? { tint: '#bfe8ff' } : {});
    for (let i = 0; i < 10; i++) particles.push({ x: P.x + P.face * 12, y: P.y - 18, vx: P.face * rand(20, 120), vy: -rand(20, 90), g: 300, life: rand(0.3, 0.6), kind: frost ? 'frost' : 'spark' });
    if (!e.hit) return;
    if (frost) hitT(e, { dmg: meleeDmg(D.light, 0.5), poise: 30, kind: 'heavy', melee: true, frost: e.boss ? 60 : 100 });
    else if (e.boss) bossStance(e, 60);
    else hitT(e, { dmg: meleeDmg(D.light, 0.3), poise: 60, kind: 'heavy', melee: true });
  }
  impl('aegis', ['parry', 1.0], 1, null, guardStance(false));
  impl('frost_aegis', ['parry', 1.0], 1, null, guardStance(true));

  // ---- shield charge: rush, bowling small foes, slamming big ones
  impl('shield_charge', ['sp_heavy', 1.0], 3, null, (dt, grav, s) => {
    const r = released();
    if (!r) { stop(dt); grav(); glowGather('ember', '255,160,90'); return; }
    if (r === 'now') { s.face = P.face; s.dur = s.ch ? 0.55 : 0.38; s.carry = new Set(); P.artI = true; sfx.roll(); sfx.heavySwing(); spawnFx('dust', P.x - P.face * 6, P.y, P.face); }
    grav();
    if (!s.end) {
      holdAt(P.artOwn ? P.artRel : 4);
      P.vx = P.face * (s.ch ? 380 : 330); P.artI = true;
      if (Math.random() < 0.7) particles.push({ x: P.x - P.face * 6, y: P.y - rand(0, 4), vx: -P.face * rand(20, 60), vy: -rand(10, 40), life: 0.4, kind: s.ch ? 'fire' : 'dust' });
      if (s.ch && Math.random() < 0.5) addLight(P.x, P.y - 10, 30, '255,140,60', 0.6);
      const front = frontRect(0, -28, 20, 0);
      for (const t of foes()) {
        const hb = hbOf(t); if (!hb || !overlap(front, hb)) continue;
        if (isSmall(t)) {
          if (!s.carry.has(t)) { s.carry.add(t); hitT(t, { dmg: meleeDmg(D.heavy, 1.3), poise: 80, kind: 'heavy', big: true, melee: true, burn: s.ch ? 40 : 0 }); }
          if (t.alive && !solidAtPx(P.x + P.face * 26, t.y - 8)) { t.x = P.x + P.face * 18; t.vx = P.vx; }
        } else if (!s.set.has(t)) {   // large foe or boss: slam and bounce off
          s.set.add(t); hitT(t, { dmg: meleeDmg(D.heavy, 2.0), poise: 110, kind: 'heavy', big: true, melee: true, burn: s.ch ? 40 : 0 });
          shake = 7; sfx.boom(); spawnFx(fxOr('slam_impact', 'hit'), P.x + P.face * 16, P.y - 14, P.face); s.end = true; s.te = 0; P.vx = -P.face * 120; P.vy = -80;
        }
      }
      if (!s.end && (s.t > s.dur || solidAtPx(P.x + P.face * 8, P.y - 12))) {
        s.end = true; s.te = 0;
        for (const t of s.carry) if (t.alive) { t.vx = P.face * 200; t.vy = -120; stun(t, 0.7); }
        if (solidAtPx(P.x + P.face * 8, P.y - 12)) { shake = 5; sfx.hit(); spawnFx('wall_dust', P.x + P.face * 6, P.y - 12, P.face); }
      }
      if (s.ch && Math.floor(s.t / 0.08) !== s.lastTrail) { s.lastTrail = Math.floor(s.t / 0.08); if (s.lastTrail % 2 === 0 && P.ground) burningGround(P.x - P.face * 8, P.y, 2.0, D.heavy * 0.5, 24); }
    } else {
      P.artI = false; s.te += dt; stop(dt, 1000);
      if (s.te > 0.22) endArt();
    }
  });

  // ---- magma quake: slam + a line of erupting fissures
  function fissure(x, y, delay, dmg, dir) {
    add({ x, y, delay, set: new Set(), dir,
      update(dt) {
        if (this.t < this.delay) return true;
        const k = this.t - this.delay;
        if (!this.go) { this.go = true; noise(0.4, 250, 0.7, 0.35, 'lowpass', 1.6); shake = Math.max(shake, 4); sfx.fire(); spawnFx('g_fissure', this.x, this.y + 1, 1, null, { bottom: true }); }
        if (k > 0.08 && k < 0.3) areaHit(rect(this.x - 12, this.y - 56, this.x + 12, this.y + 2), { dmg, poise: 30, kind: 'heavy', fire: true, burn: 35, big: true, melee: true, from: this.x - this.dir * 20 }, this.set);
        addLight(this.x, this.y - 20, 50, '255,130,50', Math.max(0, 1 - k * 2));
        return k < 0.45;
      } });
  }
  function slamImpact(front) {
    shake = 8; sfx.boom(); hitstop = Math.max(hitstop, 0.06);
    spawnFx(fxOr('slam_impact', 'shockwave'), P.x + P.face * front, P.y, 1, null, { bottom: true });
    spawnFx('ground_crack', P.x + P.face * front, P.y, 1);
    for (let i = 0; i < 16; i++) particles.push({ x: P.x + P.face * front + rand(-16, 16), y: P.y - 2, vx: rand(-80, 80), vy: -rand(30, 120), g: 320, life: 0.6, kind: 'dust' });
  }
  impl('magma_quake', ['gs_heavy', 1.0], IMPACT('gs_heavy'), null, (dt, grav, s) => {
    stop(dt); grav();
    const r = released();
    if (!r) { glowGather('fire', '255,140,60'); return; }
    if (r === 'now') {
      slamImpact(26);
      areaHit(frontRect(-4, -40, 46, 2), { dmg: meleeDmg(D.heavy, 2.2), poise: 80, kind: 'heavy', fire: true, burn: 30, big: true, melee: true });
      const n = s.ch ? 6 : 4, dirs = s.ch ? [P.face, -P.face] : [P.face];
      for (const d of dirs) {
        for (let k = 0; k < (d === P.face ? n : 3); k++) {
          const x = P.x + d * (44 + k * 26);
          const fy = floorBelow(x, P.y - 20, 48);
          if (fy === null || Math.abs(fy - P.y) > 40 || solidAtPx(x, fy - 8)) break;
          fissure(x, fy, 0.06 + k * 0.09, meleeDmg(D.heavy, s.ch ? 1.25 : 1.1), d);
        }
      }
    }
    if (P.anim.done) endArt();
  });

  // ---- thunder lunge: invulnerable lightning dash + thunderclap along the path
  impl('thunder_lunge', ['sp_heavy', 1.2], 3, null, (dt, grav, s) => {
    const r = released();
    if (!r) { stop(dt); grav(); glowGather('teal', '140,210,255'); return; }
    if (r === 'now') { s.x0 = P.x; s.max = s.ch ? 280 : 200; s.hitList = []; s.phase = 1; P.artI = true; sndZap(); sfx.spear(); flashScreen = Math.max(flashScreen, 0.1); s.y = P.y - 14; }
    if (s.phase === 1) {
      holdAt(P.artOwn ? P.artRel : 4);
      P.vx = P.face * 640; P.vy = 0; P.artI = true;
      if (Math.floor(s.t * 60) % 2 === 0) S.ghosts.push({ f: P.anim.frame, x: P.x, y: P.y, face: P.face, life: 0.25, col: '#8fe8ff' });
      addLight(P.x, P.y - 14, 50, '160,225,255', 1);
      for (const t of areaHit(rect(P.x - 16, P.y - 30, P.x + 16, P.y + 2), { dmg: meleeDmg(D.light, s.ch ? 2.5 : 1.9), poise: 60, kind: 'heavy', big: true, melee: true }, s.set)) s.hitList.push(t);
      if (Math.abs(P.x - s.x0) >= s.max || solidAtPx(P.x + P.face * 10, P.y - 12) || s.t > 0.5) {
        s.phase = 2; s.t2 = 0; s.x1 = P.x; P.vx = P.face * 60; P.artI = false; s.seed = irand(0, 9999);
        add({ x0: s.x0, x1: s.x1, y: P.y - 14, clap: false, list: s.hitList, ch: s.ch,
          update() {
            addLight((this.x0 + this.x1) / 2, this.y, Math.abs(this.x1 - this.x0) / 2 + 30, '140,210,255', Math.max(0, 0.9 - this.t * 2));
            if (!this.clap && this.t > 0.22) {
              this.clap = true; sndThunder(); shake = Math.max(shake, 6); flashScreen = Math.max(flashScreen, 0.14);
              const lo = Math.min(this.x0, this.x1), hi = Math.max(this.x0, this.x1);
              areaHit(rect(lo - 10, this.y - 22, hi + 10, this.y + 16), { dmg: meleeDmg(D.light, this.ch ? 1.6 : 0.9), poise: 30, kind: 'heavy', big: true, melee: true });
              for (let x = lo; x < hi; x += 22) spawnFx('g_spark', x + rand(-6, 6), this.y + rand(-8, 8), 1);
            }
            return this.t < 0.5;
          },
          draw() {
            const a = this.t < 0.22 ? 0.55 + 0.25 * Math.sin(this.t * 90) : Math.max(0, 1 - (this.t - 0.22) / 0.26);
            drawBolt(jagPts(this.x0, this.y, this.x1, this.y, Math.floor(this.t * 30) + 5, this.clap ? 8 : 3), a);
          } });
      }
      return;
    }
    s.t2 += dt; stop(dt, 700); grav();
    if (P.anim.done || s.t2 > 0.6) endArt();
  });

  // ---- tolling blow: overhead strike whose peal stuns
  impl('tolling_blow', ['gs_heavy', 0.95], IMPACT('gs_heavy'), null, (dt, grav, s) => {
    stop(dt); grav();
    const r = released();
    if (!r) { glowGather('gold', '255,210,120'); return; }
    if (r === 'now') {
      slamImpact(28);
      areaHit(frontRect(-4, -44, 48, 2), { dmg: meleeDmg(D.heavy, s.ch ? 3.3 : 2.6), poise: 100, kind: 'heavy', big: true, melee: true });
      sndBell(s.ch ? 1.4 : 1); flashScreen = Math.max(flashScreen, 0.1);
      spawnFx('g_toll', P.x + P.face * 24, P.y - 10, 1);
      const R = s.ch ? 130 : 90;
      for (const t of foes()) {
        const c = hbc(t); if (!c || Math.hypot(c.x - (P.x + P.face * 24), (c.y - P.y) * 1.4) > R) continue;
        if (t.boss) bossStance(t, s.ch ? 140 : 90); else stun(t, s.ch ? 3.2 : 2.4);
      }
    }
    if (P.anim.done) endArt();
  });

  // ---- twin tempest: eight-cut flurry
  impl('twin_tempest', ['dg_1', 2.2], 1, null, (dt, grav, s) => {
    grav();
    const r = released();
    if (!r) { stop(dt); glowGather('blood', '255,120,120'); return; }
    if (r === 'now') { s.face = P.face; s.n = 0; s.tick = 0; }
    if (s.n < 8) {
      P.vx = approach(P.vx, P.face * 55, 900 * dt);
      if ((s.tick -= dt) <= 0) {
        s.tick = 0.085; s.n++; P.hitSet = new Set();
        const last = s.n === 8;
        areaHit(frontRect(-4, -36, last ? 50 : 40, 2), { dmg: meleeDmg(D.light, last ? (s.ch ? 2.2 : 1.4) : (s.ch ? 0.7 : 0.55)), poise: last ? 50 : 9, kind: last ? 'heavy' : 'light', big: last, melee: true, bleed: bleedAmt(false) * 0.5 }, P.hitSet);
        if (last) { spawnFx('g_xcut', P.x + P.face * 24, P.y - 18, P.face); sfx.heavySwing(); shake = 4; }
        else { spawnFx(s.n % 2 ? 'slash' : 'slash2', P.x + P.face * rand(14, 22), P.y - rand(12, 24), P.face, null, { rot: rand(-0.5, 0.5) }); sfx.swing(); }
        if (!P.artOwn) { const tags = ['dg_1', 'dg_2', 'dg_3']; const tg = tags[s.n % 3]; P.anim.set(pHas(tg) ? tg : 'attack1', false, 2.6); P.anim.i = 1; }
      }
    } else { stop(dt); if (s.tick <= -0.22 || (P.artOwn && P.anim.done)) endArt(); s.tick -= dt; }
  });

  // ---- echo: repeat the last art used
  impl('echo', ['cast', 2.0], 0, () => {
    if (!S.lastArt || !ARTS[S.lastArt] || S.lastArt === 'echo') { P.fp = Math.min(D.maxFp, P.fp + ARTS.echo.fp); sfx.deny(); toast('No art to echo'); P.g2.fail = true; }
  }, (dt, grav, s) => {
    stop(dt); grav();
    if (s.fail) { if (s.t > 0.1) endArt(); return; }
    const id = S.lastArt, keepCh = charged();
    const saved = SAVE.art;
    P.fp += ARTS[id].fp;   // the echoed art is free
    S.echoFlash = 0.4; tone(1319, 0.4, 0.07, 'triangle'); tone(1976, 0.5, 0.04, 'sine', 1, 0.08);
    for (let i = 0; i < 16; i++) particles.push({ x: P.x + rand(-10, 10), y: P.y - rand(0, 30), vx: rand(-30, 30), vy: -rand(20, 60), life: 0.6, kind: 'ember' });
    S.ghosts.push({ f: P.anim.frame, x: P.x - P.face * 6, y: P.y, face: P.face, life: 0.4, col: '#ffd890' });
    SAVE.art = id; S.inEcho = true;
    try { startArt(); } finally { SAVE.art = saved; S.inEcho = false; }
    P.artCharged = keepCh;
  });

  // ---- backstep slash: hop back, then lunge
  impl('backstep_slash', ['jump_up', 1.0], 0, null, (dt, grav, s) => {
    const r = released();
    if (r === 'now') { s.face = P.face; P.vx = -P.face * 190; P.vy = -150; P.ground = false; P.artI = true; s.phase = 1; sfx.roll(); spawnFx('dust', P.x, P.y, P.face); }
    grav();
    if (s.phase === 1) {
      P.vx = approach(P.vx, 0, 260 * dt);
      if (s.t > 0.22) P.artI = false;
      if (Math.random() < 0.5) S.ghosts.push({ f: P.anim.frame, x: P.x, y: P.y, face: P.face, life: 0.2, col: '#c8d0e8' });
      if ((P.ground && s.t > 0.12) || s.t > 0.45) { s.phase = 2; s.t2 = 0; artAnim('attack3', 1.3); P.vx = P.face * (s.ch ? 390 : 340); sfx.heavySwing(); spawnFx('slash3', P.x + P.face * 24, P.y - 17, P.face);
        if (s.ch) fireProjectile('crescent'); }
    } else {
      s.t2 += dt; P.vx = approach(P.vx, 0, 650 * dt);
      if (s.t2 < 0.22) areaHit(frontRect(-4, -32, 46, 2), { dmg: meleeDmg(D.light, s.ch ? 2.7 : 2.0), poise: 45, kind: 'heavy', big: true, melee: true }, s.set);
      if ((P.artOwn ? P.anim.done : s.t2 > 0.45) || s.t2 > 0.9) endArt();
    }
  });

  // ================================================================ charms
  S.negated = [];
  // NEEDS (integrator): runHooks('negated', dmg, dir, opt) inside hurtPlayer's iframes() branch -> lets the guard arts react to bosses too
  if (!HOOKS.negated) HOOKS.negated = [];
  HOOKS.negated.push((dmg, dir, opt) => { if (P.state === 'art' && (P.artId === 'aegis' || P.artId === 'frost_aegis') && opt && opt.src && S.negated.length < 8) S.negated.push(opt.src); });

  HOOKS.playerHurt.push((dmg, opt) => {
    if (charmOn('c_scale') && ((opt.src && opt.src.boss) || (!opt.src && boss && boss.active && boss.alive))) dmg *= 0.85;
    if (charmOn('c_core')) S.core = Math.min(100, S.core + dmg / D.maxHp * 170 + 4);
    return dmg;
  });
  HOOKS.parry.push(src => {
    if (!charmOn('c_clapper')) return;
    sndBell(0.7); spawnFx('g_toll', P.x + P.face * 10, P.y - 14, 1, null, { alpha: 0.8 });
    for (const t of foes()) { const c = hbc(t); if (!c || Math.hypot(c.x - P.x, (c.y - P.y) * 1.4) > 76) continue; if (t.boss) bossStance(t, 40); else stun(t, 1.6); }
  });
  function coreBurst() {
    S.core = 0; S.coreFlash = 0.6;
    sfx.fire(); sfx.boom(); shake = Math.max(shake, 6); flashScreen = Math.max(flashScreen, 0.12);
    spawnFx(fxOr('flame_ring', 'shockwave'), P.x, P.y, 1, null, { bottom: true });
    spawnFx('g_magma_burst', P.x, P.y + 1, 1, null, { bottom: true });
    areaHit(rect(P.x - 58, P.y - 44, P.x + 58, P.y + 4), { dmg: 40 + D.heavy * 1.6, poise: 60, fire: true, burn: 60, big: true, kind: 'heavy', melee: true });
    for (let i = 0; i < 30; i++) particles.push({ x: P.x + rand(-40, 40), y: P.y - rand(0, 10), vx: rand(-40, 40), vy: -rand(50, 160), life: rand(0.4, 1), kind: 'fire' });
  }

  // ================================================================ hooks: update / render / hud / enter
  HOOKS.update.push(dt => {
    if (!P) return;
    // remember the last art actually performed (for Echo)
    if (P.state === 'art' && P.artId && P.artId !== 'echo') S.lastArt = P.artId;
    // objects
    for (const o of S.objs) o.t += dt;
    { const cur = S.objs; S.objs = []; const keep = cur.filter(o => o.update(dt) !== false); S.objs = keep.concat(S.objs); }   // objects may spawn objects
    for (const gh of S.ghosts) gh.life -= dt; S.ghosts = S.ghosts.filter(gh => gh.life > 0);
    updateStatus(dt);
    // my projectiles: light + impact sparks
    for (const pr of S.myProj) {
      if (pr.life > 0 && projectiles.includes(pr)) { if (!(pr.delay > 0)) { addLight(pr.x, pr.y, 22, '190,140,255', 0.9); if (Math.random() < 0.5) particles.push({ x: pr.x - sign(pr.vx) * 4, y: pr.y, vx: -pr.vx * 0.1, vy: rand(-10, 10), life: 0.3, kind: Math.random() < 0.3 ? 'gold' : 'ink' }); } }
      else { S.myProj.delete(pr); if (pr.life > -dt && pr.t > 0 && pr.hits && pr.hits.size) spawnFx('g_spark', pr.x, pr.y, 1, null, { tint: '#b080ff' }); }
    }
    // reflected missiles glow + frost on hit (frost aegis)
    for (const pr of projectiles) if (pr.gRefl && pr.life > 0) {
      addLight(pr.x, pr.y, 24, pr.gFrost ? '160,215,255' : '255,220,150', 0.8);
      if (pr.gFrost) for (const t of pr.hits) if (!pr.gFrostDone) { pr.gFrostDone = true; frostUp(t, pr.gFrost); }
    }
    // wind ward
    if (S.ward > 0) {
      S.ward -= dt; S.wardT += dt;
      addLight(P.x, P.y - 14, 44, '200,240,220', 0.5);
      for (const pr of projectiles) if (reflectable(pr) && Math.hypot(pr.x - P.x, pr.y - (P.y - 14)) < 30) reflect(pr, D.spell);
      if (Math.random() < 0.4) { const a = rand(0, 6.283); particles.push({ x: P.x + Math.cos(a) * 20, y: P.y - 14 + Math.sin(a) * 16, vx: -Math.sin(a) * 60, vy: Math.cos(a) * 50, life: 0.3, kind: 'mote' }); }
    }
    // ember echo aura
    if (S.echo > 0) { S.echo -= dt; if (Math.random() < 0.25) particles.push({ x: P.x + rand(-7, 7), y: P.y - rand(4, 26), vx: 0, vy: -rand(10, 30), life: 0.5, kind: 'ember' }); addLight(P.x, P.y - 14, 30, '255,160,80', 0.4); }
    S.echoFlash = Math.max(0, (S.echoFlash || 0) - dt);
    // ---- charms
    if (charmOn('c_bead') && P.stDelay <= 0 && P.state !== 'roll' && !ATK[P.state] && P.st < D.maxSt) P.st = Math.min(D.maxSt, P.st + (P.state === 'idle' ? 70 : 58) * 0.3 * dt);
    if (P.state === 'cast') { if (!P.gQuill && charmOn('c_quill')) { P.anim.speed *= 1.2; P.gQuill = true; } } else P.gQuill = false;
    if (charmOn('c_core')) {
      if (S.core >= 100 && P.state !== 'dead') coreBurst();
      if (S.core > 60 && Math.random() < S.core / 400) particles.push({ x: P.x + rand(-6, 6), y: P.y - rand(8, 22), vx: 0, vy: -rand(10, 30), life: 0.4, kind: 'fire' });
    }
    S.coreFlash = Math.max(0, S.coreFlash - dt);
  });
  HOOKS.render.push(() => {
    if (!P) return;
    for (const o of S.objs) if (o.draw && !o.wall) o.draw();
    for (const o of S.objs) if (o.draw && o.wall) o.draw();
    drawStatus();
    for (const gh of S.ghosts) drawSprite(sheet('player'), gh.f, gh.x, gh.y, gh.face, { alpha: Math.min(1, gh.life / 0.25) * 0.5, flash: 1, flashColor: gh.col });
    // whirlwind disc, guard barrier, wind ward
    if (P.state === 'art' && P.g2 && P.g2.rel) {
      const s = P.g2;
      if (P.artId === 'whirlwind' && s.t < (s.dur || 0)) drawTag('fx_g_whirl', 'g_whirl', s.t, P.x, P.y - 16, s.face || P.face, { center: true, alpha: 0.9 });
      if ((P.artId === 'aegis' || P.artId === 'frost_aegis') && s.t < (s.dur || 0)) {
        const fr = P.artId === 'frost_aegis';
        drawTag(fr ? 'fx_g_frost_aegis' : 'fx_g_aegis', fr ? 'g_frost_aegis' : 'g_aegis', s.t, P.x + P.face * 9, P.y - 16, P.face, { center: true, alpha: 0.75 + (s.gl > 0 ? 0.25 : 0.1 * Math.sin(time * 12)) });
      }
    }
    if (S.ward > 0) drawTag('fx_g_wind_ward', 'g_wind_ward', S.wardT, P.x, P.y - 14, 1, { center: true, alpha: Math.min(1, S.ward * 3, S.wardT * 6) * 0.9 });
  });
  HOOKS.hud.push(() => {
    if (!P || !D) return;
    if (S.echo > 0 && SAVE.spell) icon('s_ember_echo', 75, 181, 8, 0.6 + 0.4 * Math.sin(time * 6));
    if (charmOn('c_core')) {
      const x = ox + 104 * scale, y = oy + 212 * scale, w = 24 * scale;
      vctx.fillStyle = 'rgba(10,6,8,0.8)'; vctx.fillRect(x - scale * 0.5, y - scale * 0.5, w + scale, 2.5 * scale);
      vctx.fillStyle = S.core >= 90 ? '#ffd070' : '#e0662a'; vctx.fillRect(x, y, w * S.core / 100, 1.5 * scale);
    }
  });
  HOOKS.enter.push(() => { S.objs = []; S.ghosts = []; S.ward = 0; S.afflicted.clear(); S.myProj.clear(); S.negated.length = 0; });
  HOOKS.death.push(() => { S.echo = 0; S.core = 0; S.ward = 0; });

  // debug/test access (headless tests: window.__gear2)
  const api = { S, frostUp, burnUp, stun, placeGlyph, get projectiles() { return projectiles; } };
  if (typeof window !== 'undefined') window.__gear2 = api;
  return api;
})();
