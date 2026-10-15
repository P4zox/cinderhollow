// in-game snapshots of the bow in a dark room: the draw at each level (arrowhead glow), the sweet-spot glint, arrows
// in flight, the arc rain, stuck arrows. Returns the player's screen position per shot (crop.py cuts the montage).
const POS = {};
const setup = (rank = 5, dx = 44) => { W().reset('bow', rank); G.tp('C4', 8, 10); W().frame(4); W().reset('bow', rank); E('P.face = 1; P.bwLv = 1; P.bwSteps = 0; P.bwIdle = 0'); W().dummy(dx); W().frame(2); };
const shot = async name => { E('areaCard = null; toasts.length = 0; hitstop = 0; render()'); POS[name] = E('[Math.round((P.x - cam.x) * scale + ox), Math.round((P.y - cam.y) * scale + oy), scale, P.state, P.anim.tag, P.anim.i, P.bwLv, P.bwDrawLv || 0]'); await snap('s_' + name); };
setup(5, 120); W().frame(30); await shot('idle_far');
setup(5, 44); W().frame(30); await shot('idle_sweet');
W().down('heavy'); W().frame(14); await shot('draw_lv1');
W().frame(24); await shot('draw_lv2');
W().frame(26); await shot('draw_lv3');
E('window.__wm.follow = 60'); W().down('right'); W().frame(12); await shot('draw_walk'); W().up('right');
W().up('heavy'); W().frame(4); await shot('power_lv3_flight'); W().frame(40);
setup(5, 90); for (let i = 0; i < 3; i++) { W().tap('attack', 2); W().frame(8); } W().frame(6); await shot('volley_lv3'); W().frame(60);
setup(5, 60); W().down('up'); W().tap('attack', 2); W().up('up'); W().frame(36); await shot('arc_rain'); W().frame(22); await shot('arc_stuck');
setup(5, 40); W().tap('roll', 2); W().frame(4); await shot('step'); W().frame(30); await shot('after_step_lv2');
return POS;
