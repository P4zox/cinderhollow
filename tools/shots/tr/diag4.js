await new Promise(r=>setTimeout(r,300));
const T = G.trn, out = []; T.start(); G.step(5);
for (const k of ['pharaoh','librarian']) {
  T.summon(k); const b = G.boss; G.SETTINGS.god = 0;
  out.push(`${k} b=${Math.round(b.x)},${Math.round(b.y)} P=${Math.round(G.P.x)},${Math.round(G.P.y)} w=${G.sk.ev('room.w')} g=${G.P.ground}`);
  await new Promise(r=>setTimeout(r,1500));
  for (let i = 0; i < 8; i++) { const d = b.x - G.P.x; const hp = G.P.hp; G.step(40, Math.abs(d) > 40 ? [d < 0 ? 'left' : 'right'] : []); out.push(` s=${b.state} act=${b.active} P=${Math.round(G.P.x)},${Math.round(G.P.y)} hp ${Math.round(hp)}->${Math.round(G.P.hp)} b=${Math.round(b.x)},${Math.round(b.y)}`); if (i === 4) await snap('diag_' + k); G.P.hp = 999; }
  T.clear(); G.step(3);
}
return out;
