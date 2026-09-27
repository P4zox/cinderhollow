// replays a plan.py route in the live game. Globals injected above: ROUTE, ROOM, SX, SY, PRE (setup code as a function)
await boot(); G.SETTINGS.god = 0; G.grantTechniques(); G.SAVE.items.talon = 1; const S = window.__sys, log = [];
G.SAVE.seenAreas = G.SAVE.seenAreas || {}; for (const b of ['spire','deep','crown','lastfield']) G.SAVE.seenAreas[b] = 1;
if (typeof PRE === 'function') await PRE(G, S, log);
const step1 = (ax, jh, jp, rp) => { const hold = []; if (ax > 0) hold.push('right'); if (ax < 0) hold.push('left'); if (jh) hold.push('jump'); const tap = []; if (jp) tap.push('jump'); if (rp) tap.push('roll'); return G.step(1, hold, tap); };
const P = () => G.P;
let ei = 0, fails = 0;
const DELAYS = (typeof WAITS !== 'undefined') ? WAITS : [0];
for (let attempt = 0; attempt < DELAYS.length; attempt++) {
if (attempt > 0) { const sg = G.props.find(p => p.type === 'sys_sigil'); G.P.x = sg.x; G.P.y = sg.y; G.step(5); G.step(1, [], ['interact']); G.step(3); }
const att0 = TRIAL && S.SYS.trial ? S.SYS.trial.attempts : 0; let failed = false; ei = 0;
for (const e of ROUTE) {
  ei++;
  if (!(S.SYS.trial || !TRIAL)) { log.push('trial dropped before edge ' + ei); break; }
  if (TRIAL && S.SYS.trial.attempts !== att0) { failed = true; log.push('reset before edge ' + ei + ' (' + S.SYS.trial.why + ')'); break; }
  if (ei === 2 && DELAYS[attempt]) for (let i = 0; i < DELAYS[attempt] * 60; i++) step1(0, false, false, false);
  if (e.kind === 'stand') {
    // settle on the ground, then line up: run-ups arrive at full speed, standing starts are still
    for (let i = 0; i < 90 && !P().ground; i++) step1(0, false, false, false);
    if (e.d) {
      const back = e.x - e.d * 26;
      for (let i = 0; i < 120 && Math.abs(P().x - back) > 2; i++) step1(sign(back - P().x), false, false, false);
      for (let i = 0; i < 20; i++) step1(0, false, false, false);
      for (let i = 0; i < 120 && (e.d > 0 ? P().x < e.x - 2 : P().x > e.x + 2); i++) step1(e.d, false, false, false);
    } else {
      for (let i = 0; i < 160 && Math.abs(P().x - e.x) > 0.8; i++) step1(Math.abs(P().x - e.x) > 6 ? sign(e.x - P().x) : 0, false, false, false) , (Math.abs(P().x - e.x) <= 6 && (G.P.x += (e.x - G.P.x) * 0.5));
      for (let i = 0; i < 6; i++) step1(0, false, false, false);
    }
  }
  let fi = 0, tr = [];
  for (const [ax, jh, jp, rp] of e.inputs) { step1(ax, jh, jp, rp); if (typeof TRACE !== 'undefined' && TRACE === ei && fi++ % 6 === 0) tr.push(`${(P().x/16).toFixed(1)},${(P().y/16).toFixed(1)}${P().state[0]}${Math.round(P().vy)}`); }
  if (tr.length) log.push('trace ' + tr.join(' '));
  // close the loop: a planned cling or landing may come a few frames late in the real game
  const last = e.inputs[e.inputs.length - 1] || [0, false, false, false];
  if (e.end && e.end[0] === 'wall') for (let i = 0; i < 24 && P().state !== 'wall' && !P().ground; i++) step1(e.end[3] > 0 ? 1 : e.end[3] < 0 ? -1 : last[0], last[1], false, false);
  if (e.end && e.end[0] === 'stand') for (let i = 0; i < 40 && !P().ground; i++) step1(last[0], last[1], false, false);
  const got = `${(P().x / 16).toFixed(1)},${(P().y / 16).toFixed(1)} ${P().state}`;
  const want = e.end ? e.end.map(v => typeof v === 'number' ? (v / 16).toFixed(1) : v).join(',') : '';
  log.push(`#${ei} ${e.kind}:${e.name} -> ${got} (plan ${want})`);
  if (SHOTS && ei % SHOTS === 0 && attempt === DELAYS.length - 1) await snap('rp_' + ROOM + '_' + ei);
}
for (let i = 0; i < 30; i++) step1(0, false, false, false);
if (!TRIAL || S.SYS.result) { log.push('cleared on attempt ' + attempt + ' wait ' + DELAYS[attempt]); break; }
}
for (let i = 0; i < 60; i++) step1(0, false, false, false);
log.push('result ' + JSON.stringify(S.SYS.result && { t: +S.SYS.result.time.toFixed(2), gold: S.SYS.result.gold, first: S.SYS.result.first }) + ' trial ' + !!S.SYS.trial + ' rec ' + JSON.stringify(S.x3().trials));
await snap('rp_' + ROOM + '_end');
return log;
