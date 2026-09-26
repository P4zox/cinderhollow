// every Kalden move: triggers, hits a standing player, is dodged by a well-timed roll; phase-2 moves apply rot
await boot(); G.give({ stats: { vig: 30, mnd: 15, end: 25, str: 22, dex: 18, fth: 10, arc: 8 } });
G.SAVE.flags['cut:kalden'] = 1; G.SAVE.flags['cutp2:kalden'] = 1; delete G.SAVE.flags['boss:kalden'];
G.tp('M5', 6, 10); const b = G.boss;
for (let i = 0; i < 200 && !b.active; i++) { G.step(2, ['right']); if (G.state === 'cut') G.step(1, [], ['pause']); }
for (let i = 0; i < 100 && b.introT > 0; i++) G.step(2);
const SNAP = window.__SNAP !== false;
const P1 = [['combo', 50], ['thrust', 90], ['leap', 140], ['quick3', 60], ['spin4', 55], ['rising3', 60], ['stab5', 70], ['charge', 160], ['kick', 45], ['plunge', 150], ['lunge', 130], ['feint', 55]];
const P2 = [['rotburst', 40], ['rotring', 40], ['rotcombo', 60], ['tendrils', 120], ['grab', 60], ['berserk', 60], ['quick3', 60], ['plunge', 150]];
const out = {};
function place(d) {
  b.x = 300; b.y = b.floor; b.air = null; G.P.x = b.x + d; G.P.y = b.floor; G.P.vx = G.P.vy = 0; b.face = 1;
  G.P.hp = 99999; G.P.rot = 0; G.P.rotT = 0; G.P.inv = 0; G.P.st = 200; G.P.face = -1;
}
function threat(bb, lead) {
  const an = bb.anim, w = (bb.sh.meta && bb.sh.meta.attacks && bb.sh.meta.attacks[bb.atk]) || null;
  if (!w || bb.state !== 'attack') return false;
  const wins = w.windows || [w], sh = bb.sh, P = G.P, hb = { x0: P.x - 5, x1: P.x + 5, y0: P.y - 25, y1: P.y };
  let t = -an.t;
  for (let k = an.i; k < an.n; k++) {
    for (const x of wins) if (k >= x.active[0] && k <= x.active[1] && t < lead * an.speed) {
      const r = x.hit, dx0 = r[0] - sh.ax, dx1 = r[0] + r[2] - sh.ax, y0 = bb.y - sh.ay + r[1], y1 = y0 + r[3];
      const R = bb.face === 1 ? { x0: bb.x + dx0 - 30, x1: bb.x + dx1 + 30 } : { x0: bb.x - dx1 - 30, x1: bb.x - dx0 + 30 };
      if (R.x0 < hb.x1 && R.x1 > hb.x0 && y0 < hb.y1 && y1 > hb.y0) return true;
    }
    t += an.ms(k); if (t > lead * an.speed) break;
  }
  return false;
}
function activeSoon(bb) {
  const an = bb.anim, w = (bb.sh.meta && bb.sh.meta.attacks && bb.sh.meta.attacks[bb.atk]) || null;
  if (!w || bb.state !== 'attack') return false;
  const wins = w.windows || [w];
  let t = an.ms(an.i) - an.t; // ms until next frame
  for (let k = an.i + 1; k < an.n && t < 140 * an.speed; k++) { if (wins.some(x => x.active[0] === k)) return true; t += an.ms(k); }
  return false;
}
let LEAD = 100, AWAY = false;
async function run(m, d, mode, tag) {
  for (let i = 0; i < 40; i++) { G.step(2); G.P.hp = 99999; }
  hazardsClear();
  place(d); b.cool = 99; b.chain = 99; b.state = 'idle'; b.cds = {}; b.stance = 0; b.stanceImmune = 99;
  b.start(m); b.chain = 99;
  const seen = new Set(); let taken = 0, hits = 0, maxRot = 0, rotT = 0, frames = 0, rollCd = 0, snapped = 0;
  for (let i = 0; i < 600; i++) {
    if (b.state === 'attack') seen.add(b.atk);
    let tap = [], hold = [];
    rollCd -= 1;
    if (mode === 'roll' && rollCd <= 0 && (threat(b, LEAD) || window.__kd.hazards.some(h => h.dmg > 0 && (h.delay > 0 && h.delay < 0.12 || h.wave) && Math.abs(h.x - G.P.x) < 40))) { tap = ['roll']; rollCd = 14; if (AWAY) hold = [G.P.x > b.x ? 'right' : 'left']; }
    const hp0 = G.P.hp;
    G.step(1, hold, tap); b.cool = Math.max(b.cool, 5);
    if (G.P.hp < hp0) { taken += hp0 - G.P.hp; if (G.P.inv > 0.45 || G.P.state === 'rest') hits++; }
    maxRot = Math.max(maxRot, G.P.rot); if (G.P.rotT > 0) rotT = 1;
    if (SNAP && mode === 'stand' && tag && b.state === 'attack' && i % 9 === 4 && snapped < 6) { await snap(`${tag}_${m}_${snapped++}`); }
    G.P.hp = Math.max(G.P.hp, 20000);
    if (G.P.state === 'dead') break;
    if (b.state !== 'attack' && window.__kd.hazards.filter(h => h.dmg > 0).length === 0 && i > 20) break;
    frames++;
  }
  return { seen: [...seen].join('+'), dmg: Math.round(taken), hits, rot: Math.round(maxRot), rotProc: rotT, t: +(frames / 60).toFixed(2) };
}
function hazardsClear() { window.__kd.hazards.length = 0; }
for (const [m, d] of P1) { { const a = await run(m, d, 'stand', 'p1'); let r = null; for (const L of [60, 110, 170]) for (const A of [false, true]) { LEAD = L; AWAY = A; const q = await run(m, d, 'roll'); q.how = `lead${L}${A ? ' away' : ''}`; if (!r || q.dmg < r.dmg) r = q; } out['p1.' + m] = `${a.seen} | stand dmg ${a.dmg} hits ${a.hits} rot ${a.rot} | roll dmg ${r.dmg} hits ${r.hits} (${r.how}) | ${a.t}s`; } }
b.hp = Math.round(b.maxHp * 0.45); b.stanceImmune = 0;
for (let i = 0; i < 400 && b.phase !== 2; i++) { G.step(2); G.P.hp = 99999; if (G.state === 'cut' || G.state === 'cine') G.step(1, [], ['pause']); }
for (let i = 0; i < 200 && (G.state === 'cut' || G.state === 'cine'); i++) G.step(1, [], ['pause']);
for (let i = 0; i < 120; i++) { G.step(2); G.P.hp = 99999; }
out.phase = b.phase;
b.hp = Math.round(b.maxHp * 0.2);
for (const [m, d] of P2) { { const a = await run(m, d, 'stand', 'p2'); let r = null; for (const L of [60, 110, 170]) for (const A of [false, true]) { LEAD = L; AWAY = A; const q = await run(m, d, 'roll'); q.how = `lead${L}${A ? ' away' : ''}`; if (!r || q.dmg < r.dmg) r = q; } out['p2.' + m] = `${a.seen} | stand dmg ${a.dmg} hits ${a.hits} rot ${a.rot} | roll dmg ${r.dmg} hits ${r.hits} (${r.how}) | ${a.t}s`; } }
// death / rewards / fog
b.stanceImmune = 0; b.chain = 0; b.cool = 0.5;
for (let n = 0; n < 60 && b.alive; n++) { b.hit({ dmg: 300, poise: 0, dir: 1, kind: 'light', x: b.x, y: b.y - 20, melee: true }); G.step(2); G.P.hp = 99999; }
for (let i = 0; i < 80; i++) { G.step(10); G.P.hp = 99999; if (G.state === 'cut' || G.state === 'cine') G.step(1, [], ['pause']); }
await snap('death'); await new Promise(r => setTimeout(r, 11500)); G.step(2);
out.end = { alive: b.alive, flag: !!G.SAVE.flags['boss:kalden'], items: ['w:kalden', 'c_crest', 'bell', 'letter'].map(k => k + ':' + (!!(G.SAVE.items[k] || G.SAVE.charms.includes(k) || G.SAVE.weapons.kalden !== undefined))), state: G.state, fogOn: G.props.filter(p => p.type === 'fog').map(p => p.on()).join(',') };
return out;
