// each move twice: once standing still (must hit), once reacting with a roll at its tell (should be avoidable)
await boot();
G.SAVE.flags['cut:sanguine'] = 1; G.SAVE.flags['cutp2:sanguine'] = 1;
G.tp('CM7', 6, 14); G.step(30, ['right']);
const B = G.boss, P = G.P, out = {};
for (let i = 0; i < 60 && !B.active; i++) G.step(5);
G.step(170);
const meta = B.sh.meta;
const danger = () => {   // a hit is coming within ~2 frames
  if (B.state === 'attack' || B.state === 'recover') { const w = (meta.attacks[B.tag] || {}); const ws = w.windows || (w.active ? [w] : []); for (const x of ws) if (B.anim.i === x.active[0] - 1 && B.anim.t > B.anim.ms() * 0.55) return true; if (B.tag === 'grab' && B.anim.i === 3 && B.anim.t > B.anim.ms() * 0.5) return true; }
  if (B.state === 'charge' && B.anim.i === 1 && B.anim.t > B.anim.ms() * 0.6) return true;
  if (B.state === 'diveprep' && B.t < 0.06) return true;
  for (const l of window.__cm.CM.lances) if (l.t > l.warn - 0.07 && l.t < l.warn && Math.abs(l.x - P.x) < 18) return true;
  for (const w of window.__cm.CM.waves) if (w.t > w.tele && Math.abs(w.x - P.x) < 30 && Math.sign(P.x - w.x) === w.dir) return true;
  for (const s of window.__cm.CM.shots) if (Math.hypot(s.x - P.x, s.y - P.y + 13) < 34) return true;
  for (const d of window.__cm.CM.drops) if (d.t > d.warn && Math.abs(d.x - P.x) < 12) return 'move';
  return false;
};
for (const ph of [1, 2]) {
  if (ph === 2) { B.hp = Math.floor(B.maxHp * 0.5) - 5; B.state = 'idle'; B.cool = 0.1; for (let i = 0; i < 700 && !(B.phase === 2 && B.state === 'idle'); i++) G.step(1); }
  for (const m of ph === 1 ? ['combo', 'charge', 'sneak', 'lances', 'grab'] : ['combo', 'charge', 'sneak', 'lances', 'grab', 'fly']) {
    const r = {};
    for (const react of [false, true]) {
      window.__cm.CM.held = null; P.hp = G.D.maxHp; P.inv = 0; P.x = 300; P.y = 240; P.face = 1; B.alt = 0; B.hidden = false; B.x = 420; B.state = 'idle'; B.cool = 99; B.skyCd = 0; B.grabCd = 0; B.dirT = 99;
      window.__cm.force(m); let hits = 0, hp = P.hp, cd = 0;
      for (let k = 0; k < 360; k++) {
        let tap = [], hold = [];
        if (react && cd <= 0) { const dz = danger(); if (dz === 'move') hold = ['left']; else if (dz) { tap = ['roll']; cd = 14; P.face = B.x > P.x ? 1 : -1; } }
        cd--; G.step(1, hold, tap); B.cool = Math.max(B.cool, 50); B.dirT = 99;
        if (P.hp < hp) hits++; hp = P.hp = Math.max(P.hp, 80);
        if (k > 40 && B.state === 'idle' && !window.__cm.CM.lances.length && !window.__cm.CM.shots.length && !window.__cm.CM.drops.length) break;
      }
      r[react ? 'rolled' : 'still'] = hits;
    }
    out[`p${ph}_${m}`] = r;
  }
}
return out;
