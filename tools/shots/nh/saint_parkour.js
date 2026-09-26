await boot();
const out = [];
window.__nhLog = [];
G.SAVE.flags['cut:saint0'] = 1;
G.tp('NH7', 12, 10); G.step(10);
const B = G.boss; B.activate(); G.step(30);
const reset = (ph, px) => { B.state = 'idle'; B.cool = 99; B.cancelMove(); B.phase = ph; B.since = 0; G.P.hp = G.D.maxHp; if (px) { G.P.x = px; G.P.y = 176; G.P.vx = 0; } G.step(40); window.__nhLog = []; };
const hurt = () => window.__nhLog.length;
const goto = (x, f = 1) => { const k = Math.abs(G.P.x - x) < 3 ? [] : [G.P.x < x ? 'right' : 'left']; G.step(f, k); };
// ---------- limbo: jump the LOW beams, stay down for the HIGH ones (and stand still otherwise)
for (const ph of [1, 3]) {
  reset(ph, 200); B.startMove('limbo'); let n = 0;
  for (let f = 0; f < 900 && B.state === 'attack'; f++) {
    const low = B.fx.limbo.find(l => !l.wave && l.low && l.t < l.warn && l.warn - l.t < 0.2);
    if (low && G.P.ground) { G.step(1, ['jump'], ['jump']); n++; } else G.step(1, G.P.ground ? [] : ['jump']);
  }
  out.push(['limbo p' + ph, 'jumps', n, 'hits', hurt()]);
}
// stand still baseline: limbo must hurt a player who ignores it
reset(1, 200); B.startMove('limbo'); for (let f = 0; f < 900 && B.state === 'attack'; f++) G.step(1); out.push(['limbo idle player hits', hurt()]);
// ---------- grid: step into a gap of the pattern that is warming up
for (const ph of [1, 3]) {
  reset(ph, 300); B.startMove('grid');
  for (let f = 0; f < 900 && B.state === 'attack'; f++) {
    const warm = B.fx.grid.filter(c => c.t < c.warn + c.on);
    if (warm.length) { const near = warm.map(c => c.x).sort((a, b) => Math.abs(a - G.P.x) - Math.abs(b - G.P.x))[0]; if (Math.abs(near - G.P.x) < 12) goto(near + 16 * (G.P.x >= near ? 1 : -1)); else G.step(1); }
    else G.step(1);
  }
  out.push(['grid p' + ph, 'hits (not counting deflectable orbs)', window.__nhLog.filter(l => l[2] !== 'nh_orb').length]);
}
// ---------- purge: climb onto the nearest hard-light platform and ride it out
for (const ph of [2, 3]) {
  reset(ph, 330); B.startMove('burn'); let onPlat = 0, burned = 0;
  for (let f = 0; f < 1200 && B.state === 'attack'; f++) {
    const pl = B.fx.plats.slice().sort((a, b) => Math.abs(a.x - G.P.x) - Math.abs(b.x - G.P.x))[0];
    const standing = pl && Math.abs(G.P.y - pl.y0) < 1.5 && G.P.ground;
    if (standing) { onPlat++; goto(pl.x); }
    else if (pl && pl.k > 0.7) { const dk = Math.abs(G.P.x - pl.x) < 3 ? [] : [G.P.x < pl.x ? 'right' : 'left']; if (G.P.ground && Math.abs(G.P.x - pl.x) < 40) G.step(1, [...dk, 'jump'], ['jump']); else if (!G.P.ground) G.step(1, [...dk, 'jump']); else goto(pl.x); }
    else G.step(1);
    if (window.__nhLog.some(l => l[2] === 'boss' && l[0] > 0)) burned++;
  }
  out.push(['purge p' + ph, 'frames on a platform', onPlat, 'hits', window.__nhLog.filter(l => l[2] !== 'nh_orb').length, window.__nhLog.slice(0, 3)]);
}
// ---------- gaze: hide behind the cover on the far side from the eye
reset(1, 250); B.startMove('gaze');
for (let f = 0; f < 900 && B.state === 'attack'; f++) {
  const cs = B.fx.covers.filter(c => !c.gone); if (!cs.length) { G.step(1); continue; }
  const dir = B.x > G.P.x ? -1 : 1;   // hide on the side away from the eye
  const c = cs.sort((a, b) => Math.abs((a.x0 + a.x1) / 2 - G.P.x) - Math.abs((b.x0 + b.x1) / 2 - G.P.x))[0];
  goto((dir > 0 ? c.x1 : c.x0) + dir * 9);
}
out.push(['gaze behind cover', 'hits', hurt(), window.__nhLog, 'eye', Math.round(B.x), Math.round(B.y), 'player', Math.round(G.P.x), 'covers', B.fx.covers.map(c => c.x0)]);
reset(1, 250); B.startMove('gaze'); for (let f = 0; f < 900 && B.state === 'attack'; f++) G.step(1); out.push(['gaze in the open', 'hits', hurt()]);
// ---------- lighthouse: stay out of reach
reset(3, 330); B.startMove('lighthouse');
let side0 = null; for (let f = 0; f < 900 && B.state === 'attack'; f++) { if (side0 === null && B.mt > 0.3) side0 = G.P.x < B.x ? 60 : 610; if (side0 !== null) goto(side0); else G.step(1); }
out.push(['lighthouse outrun', 'hits', hurt(), Math.round(G.P.x), Math.round(B.x)]);
// ---------- every move hurts a player who does nothing
const hitlist = {};
for (const [m, ph] of [['orbs', 1], ['volley', 1], ['limbo', 1], ['grid', 1], ['gaze', 1], ['burn', 2], ['spiral', 2], ['dive', 2], ['lighthouse', 3], ['rain', 3]]) {
  reset(ph, 250); B.startMove(m); for (let f = 0; f < 900 && B.state === 'attack'; f++) { G.step(1); if (G.P.hp < G.D.maxHp * 0.3) G.P.hp = G.D.maxHp; }
  hitlist[m] = hurt();
}
out.push(['idle-player hits per move', JSON.stringify(hitlist)]);
return out;
