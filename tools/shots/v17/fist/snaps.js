// v17 A2 Litany of Fists: in-game snapshots (WM prelude) from real inputs, a Hollow soldier in front.
// SHOT_HTML=$PWD/web/dist/v17_fist.html sh tools/shots/wm/run.sh tools/shots/v17/fist/snaps.js tools/shots/v17/fist/snaps
const POS = {}, shots = [];
const go = (style, focus) => {
  W().reset('fist', 1); G.tp('C4', 8, 10); W().frame(4); W().reset('fist', 1);
  E(`P.vx = 0; P.vy = 0; P.face = 1; P.ftStyle = '${style}'; P.ftFlow = 0; P.inv = 0; P.cds = {}; P.fp = D.maxFp; P.ftPdT = ${focus ? 6 : 0}; enemies = enemies.filter(e => !e.wmDummy && false)`); W().frame(20);
  E(`const e = makeEnemy('hollow_soldier', P.x + 30, P.y, 'lt_s' + Math.random()); e.hp = e.maxHp = 99999; e.face = -1; e.update0 = e.update; e.update = function (dt) { const s = this.state; if (s === 'idle' || s === 'walk' || s === 'attack') { this.state = 'idle'; this.vx = 0; } return this.update0(dt); }; enemies.push(e); window.__t = e; 1`);
  W().frame(2);
};
const shot = async (name) => { E('hitstop = 0; areaCard = null; toasts.length = 0; render()'); POS[name] = E('[Math.round((P.x - cam.x) * scale + ox), Math.round((P.y - cam.y) * scale + oy), scale]'); await snap(name); shots.push(name); };
const until = (cond, max = 300) => { for (let i = 0; i < max; i++) { if (E(cond)) return true; W().frame(1); } return false; };
// Swift tap
go('swift'); W().down('art'); W().frame(1); W().up('art'); W().frame(8); await shot('01_sw_prayer');
until('P.g2 && P.g2.n >= 2'); await shot('02_sw_flurry_2');
until('P.g2 && P.g2.n >= 5'); await shot('03_sw_flurry_5');
until('P.g2 && P.g2.phase === 3'); W().frame(2); await shot('04_sw_knee');
until('P.g2 && P.g2.phase === 3 && P.g2.t2 > 0.15'); await shot('05_sw_float');
// Swift hold (charging, then the long flurry)
go('swift'); W().down('art'); W().frame(30); await shot('06_sw_charge'); W().frame(20); W().up('art');
until('P.g2 && P.g2.n >= 8'); await shot('07_sw_hold_flurry_8');
// Swift with Focus
go('swift', true); W().down('art'); W().frame(1); W().up('art'); until('P.g2 && P.g2.n >= 3'); await shot('08_sw_focus_flurry');
// Iron tap
go('iron'); W().down('art'); W().frame(1); W().up('art'); W().frame(10); await shot('09_ir_coil');
until('P.g2 && P.g2.rel'); W().frame(1); await shot('10_ir_palm');
W().frame(6); await shot('11_ir_wave_a');
W().frame(8); await shot('12_ir_wave_b');
// Iron hold: the bigger wave
go('iron'); W().down('art'); W().frame(40); await shot('13_ir_charge'); W().frame(10); W().up('art');
until('P.g2 && P.g2.rel'); W().frame(4); await shot('14_ir_hold_palm');
W().frame(10); await shot('15_ir_hold_wave');
// Iron with Focus
go('iron', true); W().down('art'); W().frame(1); W().up('art'); until('P.g2 && P.g2.rel'); W().frame(3); await shot('16_ir_focus_palm');
return { shots, POS, own: E('[pHas("art_litany"), pHas("art_litany_iron")]') };
