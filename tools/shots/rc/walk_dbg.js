await wlBoot();
G.tp('SP12', 18, 71); idle(20); wlWatch();
const r = await window.__plan('SP12', 18, 71, 'N', '10:13', 'talon', true); const R = JSON.parse(r);
const out = [R.slice(0, 5).map(e => e.name + '@' + (e.x/16).toFixed(1) + ',' + (e.y/16).toFixed(1) + '->' + (e.end||[]).slice(0,3).map(v => typeof v === 'number' ? (v/16).toFixed(1) : v)).join(' | ')];
let i0 = R.findIndex(e => e.kind === 'wall' && e.name === 'wj-1');
for (let i = 0; i < i0; i++) { await wlRoute([R[i]], 'SP12'); out.push(`after ${R[i].name}: ${(G.P.x/16).toFixed(2)},${(G.P.y/16).toFixed(2)} ${G.P.state}`); }
const B = { x: G.P.x, y: G.P.y, vx: G.P.vx, vy: G.P.vy, mode: G.P.state === 'wall' ? 'wall' : 'air', wall: G.P.wallDir, dash: !!G.P.airDash };
const K = G.xrc.kit(); out.push('crumbles ' + K.objs.filter(o => o.kind === 'crumble').map(o => `${(o.d.x0/16).toFixed(0)},${(o.d.y0/16).toFixed(0)}:${o.st || o.state}`).join(' '));
const tr = []; R[i0].inputs.forEach(([ax, jh, jp, rp], i) => { if (i % 6 === 0) tr.push(`${(G.P.x/16).toFixed(2)},${(G.P.y/16).toFixed(2)}${G.P.state[0]}`); st1(ax, jh, jp, rp); });
out.push('game ' + tr.join(' '));
const t2 = []; for (let i = 0; i < 20; i++) { st1(Math.abs(G.P.x - 267) > 6 ? sgn(267 - G.P.x) : 0, true, false, false); t2.push(`${(G.P.x/16).toFixed(2)},${(G.P.y).toFixed(1)},${G.P.vy.toFixed(0)}${G.P.state[0]}${G.P.ground?'G':''}`); }
out.push('post ' + t2.join(' '));
return { out, B: JSON.stringify(B), I: JSON.stringify(R[i0].inputs) };
