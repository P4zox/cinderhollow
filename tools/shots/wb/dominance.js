// B2 check (agent WB): within a class, no found weapon may be strictly worse than another on every axis.
// Axes: attack rating at +5 for a strength, a dexterity and a faith build, speed, reach, stamina economy, poise, each status,
// criticals, guard, hyper-armour. Prints each found weapon's "reasons" (axes where it is its class's best) and any BAD pair.
// SHOT_HTML=web/dist/wb.html node tools/shots/shot.js tools/shots/wb/dominance.js tools/shots/wb/out
await boot();
const E = G.sk.ev;
return E(`(() => {
  const builds = { str: { str: 50, dex: 15, fth: 10 }, dex: { str: 15, dex: 50, fth: 10 }, fth: { str: 12, dex: 15, fth: 50 } };
  const axes = id => { const w = WEAPONS[id]; return {
    arStr: weaponAR(builds.str, id, 5), arDex: weaponAR(builds.dex, id, 5), arFth: weaponAR(builds.fth, id, 5),
    speed: w.speed, reach: w.reach, economy: 1 / w.stam, poise: w.poise, bleed: w.bleed || 0, frost: w.frost || 0, fire: w.fire || 0,
    holy: w.holy || 0, crit: w.crit || 1, guard: w.guard || 0, armor: w.armor ? 1 : 0, rot: w.rot ? 1 : 0 }; };
  const byCls = {}; for (const id of Object.keys(WEAPONS)) { const c = WEAPON_CLASS[id]; if (!c || c === 'mirror') continue; (byCls[c] = byCls[c] || []).push(id); }
  const boss = id => !!WEAPONS[id].boss || !!SIGS[id];
  const out = { bad: [], reasons: {} };
  for (const [cls, ids] of Object.entries(byCls)) {
    const found = ids.filter(id => !boss(id)), A = Object.fromEntries(ids.map(id => [id, axes(id)]));
    for (const a of found) {
      const best = Object.keys(A[a]).filter(k => found.every(b => A[a][k] >= A[b][k] - 1e-9) && found.some(b => A[a][k] > A[b][k] + 1e-9));
      out.reasons[a] = cls + ': ' + (best.join(', ') || '(none)');
      for (const b of found) { if (a === b) continue;
        const ge = Object.keys(A[a]).every(k => A[b][k] >= A[a][k] - 1e-9), gt = Object.keys(A[a]).some(k => A[b][k] > A[a][k] + 1e-9);
        if (ge && gt) out.bad.push(\`BAD \${cls}: \${a} is worse than \${b} on every axis\`); }
    }
  }
  return out;
})()`);
