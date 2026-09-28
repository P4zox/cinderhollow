window.__shots='sanguine:home,butler:flat,unwritten:home,vael:home';
// mid-fight screenshots in the white chamber (waits real time so boss sheets decode)
await new Promise(r=>setTimeout(r,300));
const T = G.trn, out = []; T.start(); G.step(5); G.SETTINGS.god = 1;
const list = (window.__shots || 'hound:home,cindervane:home,sanguine:home,colossus:home,saint0:home,twins:home,omen:flat,orrery:flat,enforcer:flat,sovereign:home,warden:home,pharaoh:home').split(',');
for (const it of list) {
  const [k, mode] = it.split(':'); T.TRN.arena = mode; T.summon(k); const b = G.boss;
  G.step(2); await new Promise(r => setTimeout(r, 1800));
  for (let i = 0; i < 150; i++) { const d = b.x - G.P.x; G.step(2, Math.abs(d) > 70 ? [d < 0 ? 'left' : 'right'] : [], i % 9 === 0 && Math.abs(d) < 80 ? ['attack'] : []); if (G.state !== 'play') G.step(1, [], ['pause']); }
  await new Promise(r => setTimeout(r, 400)); G.step(1);
  await snap(`fight_${k}_${mode}`); out.push(`${k} ${mode} state=${b.state} ph=${b.phase}`);
  T.clear(); G.step(3);
}
return out;
