// Every King Vael move: forced at a fitting range, (a) standing still -> it must hit; (b) rolling through on the telegraph -> it should miss.
window.__errs = []; console.error = (...a) => { if (window.__errs.length < 5) window.__errs.push(String(a[0] && a[0].stack || a[0]).slice(0, 300)); };
await boot(); G.give({ stats: { vig: 60, end: 60 } }); window.__nvLog = [];
for (const k of ['boss:vael']) delete G.SAVE.flags[k]; G.SAVE.flags['cut:vael'] = 1; G.SAVE.flags['cutp2:vael'] = 1; G.SAVE.flags['cutp3:vael'] = 1;
G.tp('NV7', 30, 12); const b = G.boss; b.activate(); G.step(5);
const moves = { combo: 60, string: 60, spin: 60, overhead: 70, thrust: 150, charge: 250, leap: 250, chain: 200, ghostfire: 140, rain: 120, nova: 90 };
const out = [];
const trial = async (m, dist, roll) => {
  window.__nvLog = []; G.NVR.fires = []; G.NVR.waves = []; G.NVR.swords = []; G.NVR.rings = [];
  G.P.inv = 0; b.x = 24 * 16; b.face = 1; b.state = 'idle'; b.cds = {}; b.chain = 99; b.cool = 99; G.P.x = b.x + dist; G.P.y = b.floor; G.P.vx = 0; for (let k = 0; k < 40; k++) { G.step(1); G.P.x = b.x + dist; } G.P.inv = 0; window.__nvLog = [];
  if (m === 'rain' || m === 'nova') { if (b.phase < 3) b.phase = 3; }
  b.startMove(m); let rolled = 0, snapDone = false;
  const tels = new Set(((b.sh.meta.telegraph || {})[m] || []).map(t => t.frame));
  const at = b.sh.meta.attacks && b.sh.meta.attacks[m] ? Object.keys(b.sh.meta.attacks[m].frames).map(Number) : [];
  for (let i = 0; i < 260; i++) {
    let tap = [];
    if (roll && b.state === 'attack' && (at.includes(b.anim.i + 1) || (m === 'charge' && b.anim.i === 1)) && (b.anim.ms() - b.anim.t) / b.anim.speed < 110 && b.__rolledAt !== b.anim.i + ':' + b.atkId) { b.__rolledAt = b.anim.i + ':' + b.atkId; tap = ['roll']; }
    if (roll && (G.NVR.swords.some(s => Math.abs(s.x - G.P.x) < 10 && s.t > s.warn - 0.25 && s.t < s.warn - 0.2) || G.NVR.fires.some(f => Math.abs(f.x - G.P.x) < 14 && f.t > f.warn - 0.2 && f.t < f.warn - 0.15))) tap = ['roll'];
    if (roll && G.NVR.waves.some(w => Math.abs(w.x - G.P.x) < 40 && Math.sign(G.P.x - w.x) === Math.sign(w.vx))) tap = ['jump'];
    if (roll && G.NVR.rings.some(r => !r.harmless && Math.abs(Math.hypot(G.P.x - r.x, G.P.y - 13 - r.y) - r.r) < 30)) tap = ['roll'];
    if (roll && G.NVR.chains.some(c => c.st === 'out' && Math.abs(c.x - G.P.x) < 60)) tap = ['roll'];
    if (tap.length) rolled++;
    G.step(1, tap.includes('roll') ? [b.x < G.P.x ? 'left' : 'right'] : [], tap); G.P.hp = 9999; G.P.st = 999;
    if (!roll && !snapDone && b.state === 'attack' && at.includes(b.anim.i)) { snapDone = true; await snap(`mv_${m}`); }
    if (b.state !== 'attack' && i > 10 && !G.NVR.fires.length && !G.NVR.waves.length && !G.NVR.swords.length && !G.NVR.chains.length) break;
  }
  const hits = window.__nvLog.filter(h => h[1].startsWith('King Vael')).length;
  return `${hits}${roll ? '(rolled ' + rolled + ') ' + JSON.stringify(window.__nvLog.map(h => h[1] + '/' + h[2])) : ''}`;
};
for (const [m, dist] of Object.entries(moves)) out.push(`${m}: stand ${await trial(m, dist, false)} | roll ${await trial(m, dist, true)}`);
out.push(JSON.stringify(window.__errs));
return out;
