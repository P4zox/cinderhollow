// v15 cores: the enchant colour reads on EVERY weapon type's empowered moves (the blade light: the weapon overlay washed
// in the Core's colour on the glow layer + a short afterimage + light), and never on light attacks. One snapshot per type
// mid-swing in Gravetusk's dark den, plus the v15 types' own effects (bow arrows, warbell rings, scythe / fist / axe lights).
// Run: SHOT_HTML=web/dist/v15_cores.html node tools/shots/shot.js tools/shots/v15/cores/types14.js <out>
await boot();
const R = [], T = (name, pass, detail = '') => R.push(`${pass ? 'OK ' : 'BAD'} ${name}${detail ? '  [' + detail + ']' : ''}`);
const C = G.cores, E = C.ev, sleep = ms => new Promise(r => setTimeout(r, ms)), step = (n = 1) => G.step(n);
E(`SETTINGS.god = 1; SAVE.flags['boss:hound'] = 1; for (const f of ['cut:', 'cutp2:', 'cutp3:']) SAVE.flags[f + 'hound'] = 1;
   SAVE.cores = {}; for (const k of Object.keys(CORES)) SAVE.cores[k] = 1; SAVE.enchants = {}`);
G.tp('C5', 20, 10); step(60);
const TYPES = E('WTYPES.slice()');
const COLS = ['overseer', 'ice_warden', 'sanguine', 'coven', 'omen', 'librarian', 'ferryman', 'cindervane', 'pharaoh', 'enforcer', 'first_ember', 'saint0', 'astrel', 'sentinels'];
T('fourteen weapon types', TYPES.length === 14, TYPES.join(' '));
const reset = () => E(`(() => { P.x = 330; P.y = 176; P.vx = 0; P.vy = 0; P.ground = true; P.face = 1; P.st = D.maxSt = 1e6; P.fp = D.maxFp; P.mvQ = null; P.mvQ2 = null; P.mvChain = null; P.charged = false; setP('idle', 'idle', true); fx = []; CR.blade = []; CR.swingK = 0; enemies = []; })()`);
for (let i = 0; i < TYPES.length; i++) {
  const t = TYPES[i], core = COLS[i % COLS.length];
  E(`wmEquip('${t}', { quiet: true }); MV.rank = 5; SAVE.enchants['${t}'] = '${core}'; sheet('wpn_' + SAVE.weapon).img;`); await sleep(400);
  // a light first: no glow, no tint
  reset(); step(4);
  const light = E(`(() => { const T = MV.types['${t}']; const id = T.light0 ? T.light0() : T.light[0]; return id; })()`);
  const g0 = E('CR.glowN'); E(`mvStart('${light}', { step: 0 })`); let tinted = false; for (let f = 0; f < 50 && E(`P.state === '${light}'`); f++) { step(1); if (E('fx.some(f => f.tint)')) tinted = true; }
  T(`${t}: light ${light} carries nothing`, !E(`crElig(ATK['${light}'])`) ? E('CR.glowN') === g0 && !tinted : true, E(`crElig(ATK['${light}'])`) ? '(its first light is itself a finisher)' : '');
  // the empowered moves of the type, heavies first
  const ids = E(`Object.keys(ATK).filter(id => ATK[id].mv && ATK[id].mv.type === '${t}' && crElig(ATK[id]) && !ATK[id].mv.loop).sort((a, b) => (ATK[b].kind === 'heavy') - (ATK[a].kind === 'heavy'))`);
  let ok = false, used = null, peak = 0;
  for (const id of ids) {
    reset(); step(3);
    if (!E(`mvStart('${id}', {})`)) continue;
    const g1 = E('CR.glowN');
    for (let f = 0; f < 70 && E(`P.state === '${id}'`); f++) {
      step(1); const k = E('CR.swingK || 0');
      if (k > peak) peak = k;
      if (!ok && k > 0.7) { G.step(0); await snap(`type_${t}`); ok = E('CR.glowN') > g1 && E('CR.glowCol') === E(`CORES['${core}'].col`); used = id; }
    }
    if (ok) break;
  }
  T(`${t}: ${used || '?'} glows ${core}'s colour mid-swing`, ok, `${ids.length} empowered moves, peak ${peak.toFixed(2)}`);
}
// the v15 types' own effects
{ E(`wmEquip('bow', { quiet: true }); SAVE.enchants.bow = 'cindervane'; CR.arrowN = 0`); await sleep(200); reset();
  const ids = E(`Object.keys(ATK).filter(id => ATK[id].mv && ATK[id].mv.type === 'bow' && crElig(ATK[id]))`);
  let n = 0; for (const id of ids) { reset(); if (!E(`mvStart('${id}', {})`)) continue; for (let f = 0; f < 60; f++) { step(1); if (E('CR.arrowN') > 0 && !n) { n = E('CR.arrowN'); G.step(0); await snap('type_bow_arrow'); } } if (n) break; }
  T('bow: an empowered shot\'s arrow streaks in the Core colour', n > 0, `${n} arrow frames`);
  reset(); E('BW.arrows = []; CR.arrowPlainN = 0'); const L = E(`MV.types.bow.light[0]`); E(`mvStart('${L}', { step: 0 })`); step(40);
  T('bow: a light shot\'s arrow does not', E('CR.arrowPlainN') > 0 && E('BW.arrows.every(a => !a.crCol)'), `${E('CR.arrowPlainN')} plain arrows`); }
{ E(`wmEquip('bell', { quiet: true }); SAVE.enchants.bell = 'omen'; CR.ringN = 0`); await sleep(200);
  const ids = E(`Object.keys(ATK).filter(id => ATK[id].mv && ATK[id].mv.type === 'bell' && crElig(ATK[id]))`);
  for (const id of ids) { reset(); if (!E(`mvStart('${id}', {})`)) continue; step(60); if (E('CR.ringN') > 0) break; }
  T('warbell: an empowered toll\'s rings take the Core colour', E('CR.ringN') > 0 || E(`BEL.rings.some(r => r.rgb === CORES.omen.rgb)`), `rings ${E('CR.ringN')}`); }
for (const [t, core] of [['scythe', 'pharaoh'], ['fist', 'overseer']]) {   // (the Switch Axe's own lights only burn in grind / axe states: its blade light is the generic one above)
  E(`wmEquip('${t}', { quiet: true }); SAVE.enchants['${t}'] = '${core}'; CR.lightN = 0`); await sleep(200);
  const ids = E(`Object.keys(ATK).filter(id => ATK[id].mv && ATK[id].mv.type === '${t}' && crElig(ATK[id]))`);
  for (const id of ids) { reset(); if (!E(`mvStart('${id}', {})`)) continue; for (let f = 0; f < 40; f++) { step(1); G.step(0); } if (E('CR.lightN') > 0) break; }
  T(`${t}: its own lights take the Core colour on empowered moves`, E('CR.lightN') > 0, `${E('CR.lightN')} lights`);
}
return R;
