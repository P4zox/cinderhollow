// Warbell dmg/s bench (tools/shots/wm/bench.js "table" rules): each route looped ROUTE_SECS against a dummy that never moves,
// infinite stamina; total damage / AR / time. Then the real-boss bench (Gravetusk held in place, swinging every 2 s).
const SECS = window.__wmSecs || 12;
const ROUTES = [
  ['J J J', ['J', 'J', 'J']],
  ['J J J K (knell)', ['J', 'J', 'J', 'K']],
  ['K K', ['K', 'K']],
  ['J K (backswing) J', ['J', 'K', 'J']],
  ['wind-up toll loop', [{ b: 'K', hold: 700 }], { idleOnly: true }],
  ['J J J I (perform)', ['J', 'J', 'J', 'I']],
  ['J J J + Fury', ['J', 'J', 'J'], { keep: 'P.belBuff.fury = 30' }],
  ['J J J I + Fury/Echo kept', ['J', 'J', 'J', 'I'], { keep: 'P.belBuff.fury = 30; P.belBuff.echo = 30; P.belEchoN = 3' }],
  ['K K I (Fury loop)', ['K', 'K', 'I']],
  ['J J J I I (encore, III)', ['J', 'J', 'J', 'I', 'I'], { rank: 3 }],
  ['J J J I, IV echo wave', ['J', 'J', 'J', 'I'], { rank: 4 }],
  ['↑J ↑J I (Echo) J J J', ['U', 'U', 'I', 'J', 'J', 'J']],
];
const out = [];
for (const [name, pat, o = {}] of ROUTES) {
  const rank = o.rank || 1;
  W().reset('bell', rank); arena(); W().reset('bell', rank); E('D.maxSt = 1e6; P.st = 1e6; P.belNotes = []; P.belBuff = {}; P.belEchoN = 0');
  W().dummy(26); E('window.__wm.follow = 26');
  let i = 0, holdLeft = 0, t0 = null;
  for (let f = 0; f < SECS * 60 + 600; f++) {
    if (holdLeft > 0 && --holdLeft === 0) W().up('heavy');
    E('P.st = 1e6; if (P.x > 330) P.x -= 200' + (o.keep ? '; ' + o.keep : ''));
    const busy = E('!!ATK[P.state] && !!P.mvQ'), free = o.idleOnly ? E("['idle','run','land'].includes(P.state)") : E("['idle','run','land'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && P.mvT > 40 && !ATK[P.state].mv.loop)");
    if (holdLeft === 0 && free && !busy) {
      const p = pat[i % pat.length];
      if (typeof p === 'string') {
        if (p === 'U') { W().down('up'); W().down('attack'); W().frame(1); W().up('attack'); W().up('up'); }
        else { const b = { J: 'attack', K: 'heavy', I: 'parry' }[p]; W().down(b); W().frame(1); W().up(b); }
      } else { W().down('heavy'); holdLeft = Math.round(p.hold / (1000 / 60)); W().frame(1); }
      i++;
      if (t0 === null) { t0 = W().ms; W().log = []; }
      continue;
    }
    W().frame(1);
    if (t0 !== null && W().ms - t0 >= SECS * 1000) break;
  }
  W().up('heavy');
  const secs = (W().ms - t0) / 1000, L = G.D.light;
  const dmg = W().log.filter(h => h.melee).reduce((a, h) => a + h.dmg, 0) / L;
  const tally = {}; for (const h of W().log.filter(h => h.melee)) tally[h.st] = (tally[h.st] || 0) + 1;
  out.push({ route: name, rank, dps: +(dmg / secs).toFixed(2), hits: Object.entries(tally).map(([k, v]) => k + 'x' + v).join(' ') });
}
return out;
