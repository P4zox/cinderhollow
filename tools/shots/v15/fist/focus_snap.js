// Focus (perfect dodge) feedback in game: the flash, then the fist glow + HUD ring (WM prelude)
const out = {};
for (const st of ['swift', 'iron']) {
  W().reset('fist', 3); G.tp('C4', 8, 10); W().frame(4); W().reset('fist', 3); E(`P.face = 1; P.ftStyle = '${st}'; P.ftPdT = 0; P.inv = 0`); W().frame(20);
  W().tap('roll', 1); W().frame(3); E("P.inv = 0; hurtPlayer(20, -1, 'snap" + st + "', {})"); W().frame(2);
  E('hitstop = 0; areaCard = null; toasts.length = 0; render()'); await snap('focus_' + st + '_flash');
  W().frame(40); E('render()'); await snap('focus_' + st + '_buff');
  out[st] = E('P.ftPdT');
}
return out;
