await boot(); G.SETTINGS.god = true; G.SAVE.items.talon = 1; const out = [];
const R = () => window.__ra.RA;
const probe = async (r, sx, sy, dir, name) => {
  G.tp(r, sx, sy); G.step(10);
  const dorm = () => R().amb.filter(e => e.ra.dormant).length;
  const d0 = dorm(); let woke = -1;
  for (let i = 0; i < 300; i++) { G.step(1, [dir]); if (dorm() < d0 && woke < 0) { woke = i; G.step(12); await snap('amb_' + name); } }
  out.push(`${name}: ${d0} dormant at start, first woke after ${woke} frames, ${dorm()} still dormant, alive ${R().amb.filter(e => e.alive).length}`);
};
await probe('K5', 3, 10, 'right', 'K5_statues');
await probe('K8', 30, 10, 'left', 'K8_booths');
await probe('C7', 3, 12, 'right', 'C7_roots');
await probe('C10', 2, 10, 'right', 'C10_niches');
await probe('K6', 6, 24, 'right', 'K6_water');
// chandeliers: stand on one, it sways, then falls; it comes back
G.tp('K9', 10, 10); G.step(5); const o = G.KIT.byId.ch0; const st = [];
for (let i = 0; i < 200; i++) { G.step(1); if (!st.length || st[st.length - 1][0] !== o.st) st.push([o.st, i]); if (i === 40) await snap('chand_sway'); }
out.push('chandelier states: ' + JSON.stringify(st));
return out;
