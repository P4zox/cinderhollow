// v17 A1: the Bow's art, Ashen Volley -- from real inputs (the art key O), tap and hold, on a wm dummy and on nothing.
// SHOT_HTML=$PWD/web/dist/v17_bow.html sh tools/shots/wm/run.sh tools/shots/v17/bow/art.js tools/shots/v17/bow/out
const out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
const f2 = x => (+x).toFixed(2);
arena();
const go = (dx = 24, lv = 1) => {
  W().reset('bow', 1); E(`P.x = 160; P.y = 304; P.vx = 0; P.vy = 0; P.ground = true; P.face = 1; P.bwLv = ${lv}; P.bwIdle = 0; P.bwSteps = 0; BW.log = []; BW.arrows = []; BW.stuck = []; projectiles.length = 0;
    AVS.log = []; AVS.arrows = []; AVS.bursts = []; P.cds = {}; P.fp = D.maxFp`);
  W().frame(2); if (dx !== null) W().dummy(dx); else E('enemies = enemies.filter(e => !e.wmDummy)'); E('AVS.log = []; window.__wm.log = []');
};
// play the art out, recording the states, the i-frames, the height and the anim frames
const play = (holdFrames = 0) => {
  const fp0 = E('P.fp');
  if (holdFrames) { W().down('art'); W().frame(holdFrames); W().up('art'); } else W().tap('art', 2);
  const tr = { states: [], inv: 0, minY: 1e9, frames: [], t: 0, fp0, fp1: E('P.fp'), started: false, charged: E('P.artCharged') };
  for (let i = 0; i < 200; i++) {
    W().frame(1);
    const s = E('[P.state, iframes(), P.y, P.anim.tag, P.anim.i, P.artCharged]');
    if (tr.states[tr.states.length - 1] !== s[0]) tr.states.push(s[0]);
    if (s[0] === 'art') { tr.started = true; tr.t += 1 / 60; if (s[1]) tr.inv += 1 / 60; tr.minY = Math.min(tr.minY, s[2]); if (tr.frames[tr.frames.length - 1] !== s[4]) tr.frames.push(s[4]); tr.tag = s[3]; tr.charged = tr.charged || s[5]; }
    if (tr.started && s[0] !== 'art') break;
  }
  W().frame(40);
  tr.end = E('P.state'); tr.ground = E('P.ground'); tr.dx = E('P.x') - 160; tr.lv = E('P.bwLv'); tr.log = E('AVS.log'); tr.bw = E('BW.log.map(h => [h.id, +h.dmg.toFixed(2), h.d])');
  return tr;
};
const sum = (tr, k) => tr.log.filter(h => h.kind === k).reduce((a, h) => a + h.dmg, 0);
const cnt = (tr, k) => tr.log.filter(h => h.kind === k).length;

// ---- the weapon's art, the lock, old saves
W().reset('bow', 1); W().frame(2);
ok(E('SAVE.weapon') === 'ashstring' && E('SAVE.art') === 'ashen_volley', 'the Ashstring carries Ashen Volley (SAVE.art ' + E('SAVE.art') + ')');
E("SAVE.art = 'backstep_slash'"); W().frame(1);
ok(E('SAVE.art') === 'ashen_volley', 'an old save holding the borrowed Backstep Slash is corrected to Ashen Volley (' + E('SAVE.art') + ')');
ok(E("WTYPE_INFO.bow.art") === 'ashen_volley' && E("WEAPONS.ashstring.art") === 'ashen_volley', 'WTYPE_INFO.bow.art / WEAPONS.ashstring.art = ashen_volley');
ok(E("ARTS.ashen_volley.fp") === 12 && E("cdBase('art', 'ashen_volley')") === 5, `12 FP, 5 s cooldown (cd ${E("cdBase('art', 'ashen_volley')")})`);
ok(E("(() => { const s = sheet('ui_icons17_bow'); return s.ok && s.has('a_ashen_volley'); })()"), 'the icon a_ashen_volley is in ui_icons17_bow');
const own = E("pHas('art_ashen_volley')");
out.push('INFO the player sheet ' + (own ? 'has' : 'does NOT have (fallback anims)') + ' art_ashen_volley');

// ---- tap: kick, flip, three arrows down into the spot you left
go(24, 1); const T = play(0);
ok(T.started && T.fp0 - T.fp1 === 12, `tap O starts the art and costs 12 FP (${T.fp0} -> ${T.fp1})`);
ok(cnt(T, 'kick') === 1 && Math.abs(sum(T, 'kick') - 0.5) < 0.03, 'the kick lands once: 0.5 (' + f2(sum(T, 'kick')) + ')');
ok(cnt(T, 'arrow') === 3 && Math.abs(sum(T, 'arrow') - 1.8) < 0.08, `three arrows land: 3 x 0.6 = 1.8 (${cnt(T, 'arrow')} for ${f2(sum(T, 'arrow'))}) ` + JSON.stringify(T.bw));
ok(T.lv === 2, 'a landed volley raises the charge level 1 -> 2 (' + T.lv + ')');
ok(T.inv > 0.2 && T.inv < 0.34, 'i-frames from the kick (incl. the kick\'s 0.05 s hitstop): ' + f2(T.inv) + ' s');
ok(304 - T.minY > 22 && 304 - T.minY < 45, 'the flip rises ' + f2(304 - T.minY) + ' px');
ok(T.dx < -15 && T.dx > -45, 'it lands back from the start: ' + f2(T.dx) + ' px');
ok(T.end === 'idle' && T.ground, 'it ends in idle on the floor (' + T.end + ', ' + T.states.join(' ') + ')');
ok(T.t > 0.6 && T.t < 1.25, 'it lasts ' + f2(T.t) + ' s; frames ' + T.frames.join(','));
ok(!T.charged, 'tapped: not charged');
const tapTotal = sum(T, 'kick') + sum(T, 'arrow') + sum(T, 'burst');

// level 3 stays 3; level 2 -> 3
go(24, 2); const T2 = play(0); ok(T2.lv === 3, 'level 2 -> 3 (' + T2.lv + ')');
go(24, 3); const T3 = play(0); ok(T3.lv === 3, 'level 3 stays 3 (' + T3.lv + ')');
// the level then feeds a power shot: a volley, then a tap K straight after looses at level 2
go(40, 1); play(0); E('BW.log = []'); W().tap('heavy', 2); W().frame(50);
const pw = E('BW.log.filter(h => h.id === "bw_power").map(h => h.lv)');
ok(pw.length === 1 && pw[0] === 2, 'the next power shot looses at the level the volley banked (' + JSON.stringify(pw) + ')');

// ---- hold: five arrows that stick and burst
go(24, 1); const H = play(50);
ok(H.started && H.charged, 'hold O 0.83 s: the art is charged');
ok(H.fp0 - H.fp1 === 12, 'hold costs 12 FP too (' + (H.fp0 - H.fp1) + ')');
ok(cnt(H, 'arrow') === 5 && Math.abs(sum(H, 'arrow') - 1.75) < 0.08, `five arrows land: 5 x 0.35 = 1.75 (${cnt(H, 'arrow')} for ${f2(sum(H, 'arrow'))})`);
ok(cnt(H, 'burst') >= 5 && Math.abs(sum(H, 'burst') - 1.25) < 0.08, `each bursts a beat later: 5 x 0.25 = 1.25 (${cnt(H, 'burst')} for ${f2(sum(H, 'burst'))})`);
ok(H.lv === 2 && H.end === 'idle' && H.ground, `hold: level 1 -> ${H.lv}, ends ${H.end}`);
const holdTotal = sum(H, 'kick') + sum(H, 'arrow') + sum(H, 'burst');

// ---- on nothing: the arrows go into the floor (a held volley's still burst there), no level
go(null, 1); const N = play(0);
ok(N.started && N.end === 'idle' && N.lv === 1 && N.log.length === 0, `on nothing: plays out (${N.end}), no level (${N.lv}), no hits`);
go(null, 1); E('window.__fl = 0'); const NH = (() => { const r = play(50); return r; })();
ok(E('AVS.bursts.length') === 0 && NH.end === 'idle', 'on nothing (held): arrows stick in the floor and the bursts go off, ends idle');
// the range rule: a foe far out of reach takes nothing from the volley
go(110, 1); const F = play(0);
ok(cnt(F, 'arrow') === 0, 'a foe 110 px away is out of the volley\'s reach (' + cnt(F, 'arrow') + ' arrows)');
// cooldown: a second press straight after is refused
go(24, 1); play(0); const fpA = E('P.fp'); W().tap('art', 2); W().frame(3);
ok(E('P.state') !== 'art' && E('P.fp') === fpA, 'the cooldown refuses a second press');
// facing left
go(null, 1); E('P.face = -1'); W().dummy(24); E('AVS.log = []'); const L = play(0);
ok(cnt(L, 'arrow') === 3 && L.dx > 15, `facing left: three arrows land, flips back to the right (${f2(L.dx)} px)`);
// mid-air start
go(24, 1); E('P.y = 284; P.ground = false; P.vy = 0'); const A = play(0);
ok(A.started && A.end === 'idle', 'started in mid-air: plays out to idle (' + A.states.join(' ') + ')');

out.push(`INFO per use (x light AR): tap ${f2(tapTotal)} (${f2(tapTotal / 12)}/FP, ${f2(tapTotal / 5)}/cd-s); hold ${f2(holdTotal)}`);
return { pass: fail.length === 0, fail, out };
