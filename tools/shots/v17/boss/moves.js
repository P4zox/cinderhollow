// every move of every phase: forced one at a time with the player in front (behind for the backhand); records the
// tags it played, the events that fired, hits on the player, errors; a snapshot at each move's first active frame.
const out = { summon: E(`window.__hk.summon()`), errs: [] };
out.wake = E('window.__hk.wake()');
const PH = { 1: ['slam', 'sweep', 'combo', 'grab', 'snap', 'ring', 'leap', 'sparks', 'backhand', 'temper'],
  2: ['blade', 'spear', 'chain', 'coal_kick', 'temper'],
  3: ['ft_sweep', 'ember_rain', 'bellows_lo', 'bellows_hi', 'flame_grab', 'nova', 'ft_combo', 'dark_lunge', 'temper'] };
const DIST = { flame_grab: 70, grab: 70, leap: 140, sparks: 130, ring: 90, spear: 130, chain: 100, ember_rain: 120, dark_lunge: 110, bellows_lo: 110, bellows_hi: 110, backhand: -45 };
const res = {};
for (const ph of [1, 2, 3]) {
  for (const m of (ARGS.only || PH[ph])) {
    if (!PH[ph].includes(m)) continue;
    const r = E(`(() => { const b = boss; b.phase = ${ph}; b.stanceMax = b.stanceBase = 9999; b.stance = 0; b.temper = 0; b.tWin = 99; b.applySpeed(); b.queue = []; b.weapon = null;
      b.x = (b.L + b.R) / 2; b.face = 1; b.airH = 0; b.y = b.floor; b.setS('idle', 'idle'); b.cool = 99; hkClearAttacks();
      window.__hk.front(${DIST[m] || 60}); window.__hk.hits = 0; window.__hk.hitLog = []; b.begin('${m}'); return b.state; })()`);
    const tags = [], evs = new Set(); let snapped = false, frames = 0, maxHits = 0;
    for (; frames < 1200; frames++) {
      E('window.__hk.frame(1); P.hp = D.maxHp; if (P.state === "dead") { P.state = "idle"; }');
      const s = E(`(() => { const b = boss; return { st: b.state, tag: b.tag, i: b.anim.i, ev: Object.keys(b.fired || {}), w: ((hkM('attacks', b.tag, b.sph) || {}).windows || []).map(w => w.active[0]) }; })()`);
      if (tags[tags.length - 1] !== s.tag) tags.push(s.tag);
      s.ev.forEach(e => evs.add(s.tag + ':' + e));
      if (!snapped && s.st === 'attack' && s.w.length && s.i === s.w[0] && (ARGS.snaps !== false)) { E('render()'); await snap(`mv_p${ph}_${m}`); snapped = true; }
      if (s.st === 'idle') E('boss.cool = 99');
      if (s.st === 'idle' && frames > 5 && E('!(HK.shots.length || HK.sparks.length || HK.ash.length || HK.jets.length || HK.spears.length || HK.rings.length)')) break;
      if (s.st === 'ready' && frames > 900) break;
    }
    const h = E('window.__hk.hits');
    res[`p${ph} ${m}`] = { frames, tags: tags.join('>'), events: [...evs].join(' '), hits: h, log: E('window.__hk.hitLog.slice(0, 6).map(q => q.join(":")).join(" ")'), temper: E('boss.temper') };
  }
}
out.res = res;
out.errs = E('window.__hk.errs.slice(0, 10)');
out.hkLog = E('HK.log.slice(-40).join(" ")');
return out;
