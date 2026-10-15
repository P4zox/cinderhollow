// stamina spent by one full route with / without the stamina nodes (does the refund fire once per move, or once per hit?)
const out = [];
const cases = [['longsword', ['J','J','J','J']], ['dual', ['J','J','J','J']], ['dual', ['J','J','J','J','J','J'], 'P.demon = true'], ['greatsword', ['J','J','J']], ['staff', ['J','J','J','J']], ['whip', ['J','J','J']], ['katana', ['K', 'K', 'K']]];
for (const [type, pat, pre] of cases) for (const sk of [[], ['tireless'], ['tireless', 'flowing_form'], ['blade_dancer'], ['evasive_strike']]) {
  W().reset(type, 1); arena(); W().reset(type, 1); E('SAVE.skills = ' + JSON.stringify(sk) + '; refreshDerived(false); D.maxSt = 1e4; P.st = 1e4; P.stDelay = 99; P.mvT = 0'); if (pre) E(pre);
  W().dummy(26); E('window.__wm.follow = 26');
  let i = 0, f = 0, ms0 = W().ms, newMoves = 0, last = null;
  for (; f < 600 && i <= pat.length; f++) {
    E('P.stDelay = 99');
    const st = E('P.state'); if (st !== last && E('!!ATK[P.state]')) newMoves++; last = st;
    const free = E("['idle','run','land'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && P.mvT > 40 && !ATK[P.state].mv.loop)");
    if (free && i < pat.length) { W().tap({ J: 'attack', K: 'heavy' }[pat[i]]); i++; continue; }
    if (i >= pat.length && E("['idle','run','land'].includes(P.state)")) break;
    W().frame(1);
  }
  const spent = 1e4 - E('P.st'), dmg = W().log.reduce((a, h) => a + h.dmg, 0) / E('D.light');
  out.push(`${type.padEnd(10)} ${(pre ? 'demon ' : '') + pat.join('')} skills=${sk.join('+') || '-'}: stamina ${spent.toFixed(1)}  dmg ${dmg.toFixed(2)}  time ${((W().ms - ms0) / 1000).toFixed(2)}s  hits ${W().log.length}`);
}
return out;
