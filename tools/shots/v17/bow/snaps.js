// v17 Ashen Volley in game: the coil, the kick, the flip, the shot at the top, the volley in flight, the landing; the held
// volley's stuck arrows and their bursts. A real chasing foe (a hollow soldier). Returns the player's screen position per
// shot; montage: python3 tools/shots/v15/bow/crop.py <outdir> <pos.json> <out.png>
const POS = {};
const setup = (lv = 1) => {
  W().reset('bow', 1); arena(); W().reset('bow', 1); E('P.x = 160; P.y = 304; P.vx = 0; P.vy = 0; P.ground = true');
  E(`P.face = 1; P.bwLv = ${lv}; P.bwIdle = 0; P.cds = {}; P.fp = D.maxFp; enemies = enemies.filter(e => !e.wmDummy && Math.abs(e.x - P.x) > 300);
     const e = makeEnemy('hollow_soldier', P.x + 26, P.y, 'av_snap' + Math.random()); e.hp = e.maxHp = 30000; e.face = -1; enemies.push(e); window.__t = e;`);
  W().frame(2);
};
const shot = async name => { E('areaCard = null; toasts.length = 0; try { regionCard = null; } catch (e) {} if (window.__ui) window.__ui.regionCard = null; hitstop = 0; render()'); POS[name] = E('[Math.round((P.x - cam.x) * scale + ox), Math.round((P.y - cam.y) * scale + oy), scale, P.state, P.anim.tag, P.anim.i, (P.g2 || {}).phase, P.bwLv]'); await snap('s_' + name); };
const until = (cond, n = 120) => { for (let i = 0; i < n && !E(cond); i++) W().frame(1); };
// tap
setup(1); W().frame(10);
W().down('art'); W().frame(2); await shot('t0_coil'); W().up('art');
until('P.g2 && P.g2.rel'); W().frame(1); await shot('t1_kick');
until('P.g2 && P.g2.phase === 2'); W().frame(3); await shot('t2_launch');
W().frame(4); await shot('t3_turn');
until('P.g2 && P.g2.phase === 3', 60); await shot('t4_loose');
W().frame(3); await shot('t5_volley');
W().frame(3); await shot('t6_hits');
until('P.g2 && P.g2.phase === 4', 60); W().frame(3); await shot('t7_round');
until('P.g2 && P.g2.phase === 5', 90); W().frame(1); await shot('t8_land');
W().frame(8); await shot('t9_rise');
until("P.state !== 'art'", 90); W().frame(6); await shot('t10_after_lv2');
// hold
setup(1); W().frame(10);
W().down('art'); W().frame(44); await shot('h0_charged'); W().frame(6); W().up('art');
until('P.g2 && P.g2.phase === 3', 90); W().frame(3); await shot('h1_volley5');
W().frame(6); await shot('h2_stuck');
until('AVS.fx.length', 60); W().frame(1); await shot('h3_burst');
W().frame(5); await shot('h4_burst_late');
// held, on nothing: the arrows stick in the floor and burst there
setup(1); E('enemies = enemies.filter(e => e !== window.__t)'); W().frame(4);
W().down('art'); W().frame(44); W().up('art');
until('P.g2 && P.g2.phase === 3', 90); W().frame(16); await shot('h5_floor_stuck');
until('AVS.fx.length', 60); W().frame(2); await shot('h6_floor_burst');
return POS;
