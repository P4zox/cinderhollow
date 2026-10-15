// v15 Switch Axe bench (tools/shots/wm/bench.js style): routes looped against a still dummy with real key presses,
// infinite stamina, dmg/s in light-AR units; plus the gauge economy (seconds to fill) and the full cycle
// (fill in blade mode -> morph -> axe until it vents), which is what the weapon really deals over a fight.
// Run: SHOT_HTML=web/dist/v15_saxe.html sh tools/shots/wm/run.sh tools/shots/v15/saxe/bench.js tools/shots/v15/saxe/out
const SECS = 12, out = [];
const free = () => E("['idle','run','land'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && P.mvT > 40 && !ATK[P.state].mv.loop)");
const prep = (rank, pre) => { W().reset('saxe', rank); arena(); W().reset('saxe', rank); E('sxReset(); MV.sxVents = 0; D.maxSt = 1e6; P.st = 1e6'); if (pre) E(pre); W().dummy(26); E('window.__wm.follow = 26'); };
function route(name, rank, pat, o = {}) {
  prep(rank, o.pre);
  let i = 0, t0 = null, holdLeft = 0, heldMs = 0;
  for (let f = 0; f < SECS * 60 + 900; f++) {
    if (holdLeft > 0 && --holdLeft === 0) W().up('heavy');
    E('P.st = 1e6; if (P.x > 330) P.x -= 200' + (o.keep ? '; ' + o.keep : ''));
    if (holdLeft === 0 && free() && !E('!!ATK[P.state] && !!P.mvQ')) {
      if (o.beat && E('!!ATK[P.state]') && E('ATK[P.state].mv.total - P.mvT') > 110) { W().frame(1); continue; }
      const p = pat[i % pat.length];
      if (typeof p === 'string') { const b = { J: 'attack', K: 'heavy', I: 'parry' }[p]; W().down(b); W().frame(1); W().up(b); }
      else { W().down('heavy'); holdLeft = Math.round(p.hold / (1000 / 60)); W().frame(1); }
      i++; if (t0 === null) { t0 = W().ms; W().log = []; }
      continue;
    }
    W().frame(1);
    if (t0 !== null && W().ms - t0 >= SECS * 1000) break;
  }
  W().up('heavy');
  const secs = (W().ms - t0 - heldMs) / 1000, dmg = W().log.filter(h => h.melee).reduce((a, h) => a + h.dmg / h.light, 0);
  const tally = {}; for (const h of W().log) tally[h.st] = (tally[h.st] || 0) + 1;
  out.push(`${name.padEnd(38)} ${(dmg / secs).toFixed(2)} dmg/s   (${Object.entries(tally).map(([k, v]) => k + 'x' + v).join(' ')})`);
  return dmg / secs;
}
out.push('-- table bench (infinite stamina, dummy 26 px, ' + SECS + ' s per route)');
route('blade J J J J (main loop)', 1, ['J', 'J', 'J', 'J'], { keep: 'P.sxG = 0' });
route('blade J J J J on the beat', 1, ['J', 'J', 'J', 'J'], { beat: true, keep: 'P.sxG = 0' });
route('blade K K', 1, ['K', 'K'], { keep: 'P.sxG = 0' });
route('blade J K', 1, ['J', 'K'], { keep: 'P.sxG = 0' });
route('axe J J J (gauge held full)', 1, ['J', 'J', 'J'], { pre: 'sxSetAxe(true)', keep: 'P.sxAxe = true; P.sxG = 100' });
route('axe K (rev thrust) loop', 1, ['K'], { pre: 'sxSetAxe(true)', keep: 'P.sxAxe = true; P.sxG = 100' });
route('axe K K (II)', 2, ['K', 'K'], { pre: 'sxSetAxe(true)', keep: 'P.sxAxe = true; P.sxG = 100' });
route('axe hold K grind (3 s holds)', 1, [{ hold: 3000 }], { pre: 'sxSetAxe(true)', keep: 'P.sxAxe = true; P.sxG = 100' });

// ---- the gauge economy: seconds from 0 to 100
out.push('', '-- the Switch Gauge: seconds to fill from 0 (dummy, every blow lands; a real boss gives ~1.3 s openings)');
function fill(name, pat, o = {}) {
  prep(1); let i = 0, holdLeft = 0; const t0 = W().ms;
  for (let f = 0; f < 60 * 60; f++) {
    if (holdLeft > 0 && --holdLeft === 0) W().up('heavy');
    E('P.st = 1e6');
    if (E('P.sxLock')) break;
    if (holdLeft === 0 && free() && !E('!!ATK[P.state] && !!P.mvQ')) {
      if (o.beat && E('!!ATK[P.state]') && E('ATK[P.state].mv.total - P.mvT') > 110) { W().frame(1); continue; }
      const p = pat[i++ % pat.length];
      if (typeof p === 'string') { const b = { J: 'attack', K: 'heavy' }[p]; W().down(b); W().frame(1); W().up(b); }
      else { W().down('heavy'); holdLeft = Math.round(p.hold / (1000 / 60)); W().frame(1); }
      continue;
    }
    W().frame(1);
  }
  W().up('heavy');
  out.push(`${name.padEnd(38)} ${((W().ms - t0) / 1000).toFixed(1)} s`);
  return (W().ms - t0) / 1000;
}
fill('J J J J (early presses)', ['J', 'J', 'J', 'J']);
fill('J J J J on the beat', ['J', 'J', 'J', 'J'], { beat: true });
fill('K K', ['K', 'K']);
fill('Hone (hold K)', [{ hold: 20000 }]);

// ---- the full cycle: fill (on the beat) -> I morph -> axe J J J until it vents -> back to filling. 40 s.
out.push('', '-- full cycle, 40 s: J J J J on the beat to 100, I (Morph slash), axe J J J until the vent, repeat');
for (const [rank, rel] of [[1, false], [3, true], [5, true]]) {
  prep(rank); let t0 = W().ms; W().log = []; let morphs = 0;
  for (let f = 0; f < 40 * 60; f++) {
    E('P.st = 1e6; if (P.x > 330) P.x -= 200');
    if (!(free() && !E('!!ATK[P.state] && !!P.mvQ'))) { W().frame(1); continue; }
    if (E('!!ATK[P.state]') && E('ATK[P.state].mv.total - P.mvT') > 110) { W().frame(1); continue; }
    const axe = E('P.sxAxe'), g = E('P.sxG'), lock = E('P.sxLock');
    let b = 'attack';
    if (!axe && lock) { b = 'parry'; morphs++; }
    else if (axe && rel && g >= 40 && g < 52) b = 'parry';   // cash the rest in
    W().down(b); W().frame(1); W().up(b);
  }
  const secs = (W().ms - t0) / 1000, dmg = W().log.reduce((a, h) => a + h.dmg / h.light, 0);
  const tally = {}; for (const h of W().log) tally[h.st] = (tally[h.st] || 0) + 1;
  out.push(`rank ${rank}${rel ? ' (Full Release at 40-52)' : ''}`.padEnd(38) + ` ${(dmg / secs).toFixed(2)} dmg/s, ${morphs} morphs, vents ${E('MV.sxVents') || 0}   (${Object.entries(tally).map(([k, v]) => k + 'x' + v).join(' ')})`);
}
return out;
