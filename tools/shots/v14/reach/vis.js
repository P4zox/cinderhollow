// in-game frames of the v14 reach moves (montage built by tools/shots/v14/reach/montage.py)
G.tp('C4', 8, 10); W().frame(10); E('SETTINGS.shaders = 0');
const POS = {};
const shot = async (name, type, rank, fn, frames, dx = 40) => { W().reset(type, rank); G.tp('C4', 8, 10); W().frame(4); W().reset(type, rank); E('P.face = 1; P.momLand = null; P.snapCd = 0'); W().dummy(dx); await fn(); W().frame(frames); E('areaCard = null; toasts.length = 0'); POS[name] = E('[Math.round((P.x - cam.x) * scale + ox), Math.round((P.y - cam.y) * scale + oy), P.state, P.anim.tag, P.anim.i]'); E('render()'); await snap(name); for (const a of ['heavy', 'attack', 'parry', 'right', 'left', 'jump', 'up', 'down']) W().up(a); W().frame(40); };
await shot('01_wh1_lash', 'whip', 1, () => W().tap('attack'), 11, 70);
await shot('02_whK_lash', 'whip', 1, () => W().tap('heavy'), 19, 70);
await shot('03_wh_trip', 'whip', 1, () => { W().tap('attack'); W().frame(8); W().tap('attack'); W().frame(8); W().tap('heavy'); }, 46, 70);
await shot('04_wh_coil', 'whip', 1, () => { W().tap('roll'); W().frame(14); W().tap('heavy'); }, 10, 90);
await shot('05_wh_reelkick', 'whip', 2, () => { W().tap('parry'); W().frame(12); W().tap('attack'); }, 10, 50);
await shot('06_wh_air2', 'whip', 1, () => { W().down('jump'); W().frame(8); W().tap('attack'); W().frame(8); W().tap('attack'); }, 32, 70);
await shot('07_wh_thunder', 'whip', 1, () => { E('P.crack = 100'); W().tap('heavy'); }, 19, 70);
await shot('08_st_rise', 'staff', 1, () => { W().tap('attack'); W().frame(8); W().tap('attack'); W().frame(8); W().tap('heavy'); }, 39, 24);
await shot('09_st_rise_air', 'staff', 1, () => { W().tap('attack'); W().frame(8); W().tap('attack'); W().frame(8); W().tap('heavy'); }, 46, 24);
await shot('10_st_vkick', 'staff', 1, () => { W().tap('parry'); W().frame(3); W().tap('attack'); }, 18, 40);
await shot('11_st_air2', 'staff', 1, () => { W().down('jump'); W().frame(6); W().tap('attack'); W().frame(8); W().tap('attack'); }, 24, 30);
await shot('12_st_pdrop', 'staff', 2, () => { W().down('jump'); W().frame(14); W().up('jump'); W().frame(20); E('mvStart("st_pdrop")'); }, 30, 40);
await shot('13_st_gale', 'staff', 5, () => { E('P.mom = 3'); W().tap('heavy'); }, 30, 50);
return POS;
