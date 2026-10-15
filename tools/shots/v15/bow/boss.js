// v15 bow vs real bosses (Training Grounds summons): a simple hunter bot keeps the boss in the sweet spot (walks in past
// 64 px, charge-steps back inside 24 px), plays J J J J and a step -> draw -> power shot, rolls every ~2 s. The player is
// kept alive. Reports damage per second (light-AR units), arrow hits by distance factor, and snapshots mid-fight.
const out = {};
const POS = {};
for (const kind of (window.__bosses || ['hound', 'kalden', 'omen'])) {
  W().reset('bow', 3); G.trn.start(); W().frame(10);
  G.trn.summon(kind); W().reset('bow', 3); E('P.bwLv = 1; BW.log = []; BW.cap = 1e5');
  const B0 = G.boss; if (!B0) { out[kind] = 'no boss'; continue; }
  const hp0 = B0.hp; let f = 0, snaps = 0, presses = 0;
  const F = 60 * 30;
  for (; f < F; f++) {
    const B = G.boss; if (!B || B.hp <= 0) break;
    const hb = E('(() => { const b = boss; const h = b && hbOf(b); return h ? [h.x0, h.x1] : null; })()'); if (!hb) { W().frame(1); continue; }
    const px = G.P.x, face = hb[0] > px ? 1 : -1, d = face > 0 ? hb[0] - px : px - hb[1];
    const st = G.P.state, free = E("['idle','run','land'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && P.mvT > 40 && !ATK[P.state].mv.loop)");
    if (f % 130 === 100 && st !== 'roll') { W().tap('roll'); continue; }   // a roll every ~2 s (through or away)
    if (free) {
      if (d > 64) { W().down(face > 0 ? 'right' : 'left'); W().frame(1); W().up(face > 0 ? 'right' : 'left'); continue; }
      if (d < 22 && st !== 'roll') { E(`P.face = ${face}`); W().tap('roll'); presses++; continue; }   // neutral L: step back, +1 level
      E(`P.face = ${face}`);
      if (f % 400 < 200) { W().tap('attack'); presses++; continue; }
      W().down('heavy'); for (let k = 0; k < 16; k++) W().frame(1); W().up('heavy'); presses++; continue;
    }
    W().frame(1);
    E('P.hp = D.maxHp; P.st = Math.max(P.st, 30)');
    if (snaps < 3 && f > 300 + snaps * 400 && E("!!ATK[P.state] && ATK[P.state].mv.type === 'bow'")) {
      E('areaCard = null; toasts.length = 0; hitstop = 0; render()');
      POS[kind + snaps] = E('[Math.round((P.x - cam.x) * scale + ox), Math.round((P.y - cam.y) * scale + oy), scale, P.state, P.anim.tag, P.anim.i, P.bwLv]');
      await snap('s_' + kind + snaps); snaps++;
    }
  }
  const L = E('BW.log'), dealt = L.reduce((a, h) => a + h.dmg, 0);   // arrows only (the boss heals / changes phase)
  const byK = {}; for (const h of L) { const k = h.k >= 0.99 ? 'sweet' : h.k < 0.75 ? (h.d < 24 ? 'point-blank' : 'far') : 'edge'; byK[k] = (byK[k] || 0) + 1; }
  out[kind] = { secs: +(f / 60).toFixed(1), dps: +(dealt / (f / 60)).toFixed(2), arrowHits: L.length, byDistance: byK, presses, left: G.boss ? Math.round(G.boss.hp) : 0 };
  G.trn.clear(); W().frame(5);
}
out.POS = POS;
return out;
