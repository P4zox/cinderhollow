// v14 Dual Blades: the perfect dodge against real bosses (Training Grounds summons). For each of a boss's first blows (found by
// standing next to it), re-run the fight and roll k frames before the blow lands, through the boss and away from it.
// P = perfect dodge, i = touched during the i-frames (too early to be perfect), h = hit, - = the blow missed (rolled out of it)
// run: SHOT_HTML=web/dist/v14_dual.html sh tools/shots/wm/run.sh tools/shots/v14/dual/bosses.js tools/shots/v14/dual/out
// (Kalden 240 / 251 show "h" at every k: the player is still reeling from the 216 blow, which the base run took, so no roll starts.)
E(`(() => { if (window.__hp0) return; window.__hp0 = hurtPlayer; window.__hl = []; hurtPlayer = function (dmg, dir, id, opt = {}) { window.__hl.push({ f: window.__wm.fr, id: String(id), st: P.state, gt: P.dg ? Math.round(P.dg.t) : null }); return window.__hp0(dmg, dir, id, opt); }; })()`);
function run(kind, rollAt, demon, maxF, away) {
  W().reset('dual', 1); G.trn.start(); W().frame(10);
  G.trn.summon(kind); W().reset('dual', 1); if (demon) E('P.demon = true');
  E('window.__hl = []; window.__wm.fr = 0; MV.pd = 0');
  for (let f = 0; f < maxF; f++) {
    E('window.__wm.fr = ' + f);
    const B = G.boss; if (!B) break;
    const d = B.x - G.P.x;
    if (f === rollAt) { const k = away ? (d < 0 ? 'right' : 'left') : null; if (k) W().down(k); W().tap('roll'); if (k) W().up(k); }
    else if ((rollAt < 0 || f < rollAt) && Math.abs(d) > 30) { W().down(d < 0 ? 'left' : 'right'); W().frame(1); W().up(d < 0 ? 'left' : 'right'); }
    else W().frame(1);
    E('P.hp = D.maxHp; P.inv = 0; P.st = Math.max(P.st, 40)' + (demon ? '; P.demon = true' : ''));
  }
  return { hl: E('window.__hl'), pd: E('MV.pd') };
}
const out = {};
for (const [kind, demon] of (window.__cases || [['hound', false], ['hound', true], ['kalden', false], ['omen', false]])) {
  const base = run(kind, -1, demon, 760);
  const firsts = []; const seen = new Set();
  for (const h of base.hl) if (!seen.has(h.id)) { seen.add(h.id); firsts.push(h); }
  const res = [];
  for (const h of firsts.slice(0, 4)) {
    for (const away of [false, true]) {
      const row = [];
      for (let k = 0; k <= 13; k++) {
        const r = run(kind, h.f - k, demon, h.f + 16, away);
        const hit = r.hl.filter(x => x.f >= h.f - k);
        row.push(k + (r.pd ? 'P' : hit.length ? (hit.some(x => x.st === 'roll') ? 'i' : 'h') : '-'));
      }
      res.push(`${h.f} ${away ? 'away' : 'thru'}: ${row.join(' ')}`);
    }
  }
  out[kind + (demon ? '_demon' : '')] = res;
}
return out;
