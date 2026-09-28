// the Bellrope Trial: a scripted clear (pump each rope, let go swinging toward the next, double jump, grab)
await boot(); G.SAVE.items.wings = 1; G.SAVE.items.talon = 1; G.SETTINGS.god = false;
const S = window.__sys, out = [], ropes = [[15, 30], [8, 23], [15, 16], [8, 9]], goalX = 19;
const P = () => G.P;
const run = async (label) => {
  G.tp('K12', 20, 38); G.step(10); G.step(1, [], ['interact']); G.step(5);
  if (!S.SYS.trial) { out.push('no trial started'); return; }
  let i = 0, phase = 'floor', t = 0, dj = false, target = 0, log = [], jt = 0;
  for (let f = 0; f < 60 * 70 && S.SYS.trial && !S.SYS.trial.done; f++) {
    const p = P(), onRope = p.state === 'hook' && p.hook;
    let hold = [], tap = [];
    if (onRope) {
      const H = p.hook, cur = ropes.findIndex(r => Math.abs(r[0] * 16 + 8 - H.h.x) < 2 && Math.abs(r[1] * 16 + 2 - H.h.y) < 2);
      target = cur + 1; phase = 'rope'; dj = false;
      const tx = target < ropes.length ? ropes[target][0] * 16 + 8 : goalX * 16, dir = tx < H.h.x ? -1 : 1;
      if (H.len < 90) hold.push('down');
      hold.push(H.av > 0 ? 'right' : 'left');
      if (Math.abs(H.av) > 1.4 && H.av * dir > 0 && H.ang * dir > 0.85) { tap.push('jump'); hold = []; phase = 'fly'; jt = 0; }
    } else if (phase === 'floor') {
      target = ropes.findIndex(r => r[1] * 16 < p.y - 20); if (target < 0) target = ropes.length;
      const tx = target < ropes.length ? ropes[target][0] * 16 + 8 : goalX * 16, far = p.y > 36 * 16 ? 2.8 : 3.5;
      if (Math.abs(p.x - tx) > far * 16) hold.push(p.x < tx ? 'right' : 'left'); else { hold.push(p.x < tx ? 'right' : 'left'); if (p.ground) tap.push('jump'); phase = 'fly'; jt = 0; dj = false; }
    } else {
      const tx = target < ropes.length ? ropes[target][0] * 16 + 8 : goalX * 16;
      if (Math.abs(p.x - tx) > 6) hold.push(p.x < tx ? 'right' : 'left');
      jt++; if (jt < 14 || (dj && jt < 40)) hold.push('jump');
      if (!dj && !p.ground && p.vy > -60 && jt >= 14) { tap.push('jump'); dj = true; jt = 20; }
      if (p.ground && target >= ropes.length) hold = [goalX * 16 > p.x ? 'right' : 'left'];
      if (p.ground && target < ropes.length) { phase = 'floor'; }
    }
    G.step(1, hold, tap);
    if (f % 30 === 0) log.push(`${f} ${phase} ${(p.x / 16).toFixed(1)},${(p.y / 16).toFixed(1)} st=${p.state} tgt=${target} att=${S.SYS.trial && S.SYS.trial.attempts}`);
  }
  out.push(label + ': ' + JSON.stringify(S.SYS.result && { t: +S.SYS.result.time.toFixed(2), gold: S.SYS.result.gold, first: S.SYS.result.first }) + ' attempts ' + (S.SYS.trial ? S.SYS.trial.attempts : '-'));
  if (!S.SYS.result) out.push(log.slice(-25).join('\n'));
};
await run('first');
G.step(60); await snap('t_k12_done');
G.step(200); out.push('charms: ' + JSON.stringify(G.SAVE.charms) + ' eq ' + JSON.stringify(G.SAVE.charmsEq));
// the charm: double jump apex with and without it
const apex = (on) => { G.SAVE.charmsEq = on ? ['c_x3_chime'] : []; G.tp('K7', 40, 26); G.step(20); const y0 = G.P.y; let m = y0; G.step(1, ['jump'], ['jump']); for (let i = 0; i < 14; i++) G.step(1, ['jump']); G.step(1, ['jump'], ['jump']); for (let i = 0; i < 60; i++) { G.step(1, ['jump']); m = Math.min(m, G.P.y); } return Math.round(y0 - m); };
const a0 = apex(false), a1 = apex(true); out.push(`jump+double jump height: ${a0} px without, ${a1} px with the Chime of Ascent`);
out.push('charm got: ' + !!(G.SAVE.charms && G.SAVE.charms.includes('c_x3_chime')) + ' rec ' + JSON.stringify(S.x3().trials));
return out;
