// every boss: how long the player gets between the end of one attack and the start of the next (seconds of game time)
await new Promise(r => setTimeout(r, 300));
const T = G.trn, E = G.sk.ev, out = [], only = (window.__only || '').split(',').filter(Boolean);
const CALM = new Set(['idle', 'walk', 'run', 'glide', 'approach', 'dormant', 'intro', 'stagger', 'dead', 'transform', 'xform', 'fight', 'backstep', 'blinking', 'rising', 'toppled', 'sunk', 'hover', 'fly', 'circle', 'drift', 'recover', 'cyberWait', 'rest', 'summon', 'wait', 'pace', 'stalk']);
T.start(); G.step(10);
for (const k of T.bosses().map(b => b.kind).filter(k => !only.length || only.includes(k))) {
  if (!T.summon(k) || !G.boss) { out.push('NOBOSS ' + k); continue; }
  G.SETTINGS.god = 1;
  let prevCalm = true, calmStart = null, gaps = [], seen = new Set(), atks = 0;
  for (let i = 0; i < 1500; i++) {
    const B = G.boss; if (!B) break;
    const tb = (B.parts && B.parts.find(q => q.alive !== false && q.state)) || B, d = (tb.x || B.x) - G.P.x;
    G.step(1, Math.abs(d) > 40 ? [d < 0 ? 'left' : 'right'] : [], []); G.P.face = d < 0 ? -1 : 1;
    G.P.hp = 99999; if (G.state !== 'play') G.step(1, [], ['pause']);
    if (B.hp < B.maxHp * 0.3) B.hp = B.maxHp * 0.8;
    const st = tb.state, calm = CALM.has(st) || !B.active; seen.add(st);
    if (B.active && calm && !prevCalm) calmStart = i;
    if (B.active && !calm && prevCalm) { atks++; if (calmStart !== null) gaps.push((i - calmStart) / 60); calmStart = null; }
    prevCalm = calm;
  }
  gaps.sort((a, b) => a - b);
  const q = p => gaps.length ? gaps[Math.floor((gaps.length - 1) * p)].toFixed(2) : '-';
  out.push(`${k.padEnd(13)} attacks=${String(atks).padStart(3)} gap min ${q(0)} p25 ${q(0.25)} median ${q(0.5)}  states=${[...seen].slice(0, 8).join(',')}`);
  T.clear(); G.step(4);
}
G.SETTINGS.god = 0;
return out;
