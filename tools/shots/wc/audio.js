// WC: loudness check. Renders each stock sound and its WC replacement offline (48 kHz, master gain 1) and compares peak / RMS.
await boot(); G.giveArmory(); const F = G.feel, ev = F.ev, rows = [];
const render = async (code, len = 0.8) => {
  ev(`AC = new OfflineAudioContext(1, Math.round(48000 * ${len}), 48000); AC.resume = () => Promise.resolve(); master = AC.createGain(); master.connect(AC.destination); muted = false;`);
  ev(code); const buf = await ev('AC.startRendering()'); const d = buf.getChannelData(0);
  let pk = 0, ss = 0; for (let i = 0; i < d.length; i++) { const a = Math.abs(d[i]); if (a > pk) pk = a; ss += d[i] * d[i]; }
  // RMS over the loud part (samples within 30 dB of the peak), so short and long sounds compare fairly
  let n = 0, s2 = 0; for (let i = 0; i < d.length; i++) if (Math.abs(d[i]) > pk * 0.03) { n++; s2 += d[i] * d[i]; }
  return { pk: +pk.toFixed(3), rms: +Math.sqrt(s2 / Math.max(1, n)).toFixed(3) };
};
const avg = async (code, k = 6) => { let pk = 0, rms = 0; for (let i = 0; i < k; i++) { const r = await render(code); pk += r.pk; rms += r.rms; } return { pk: +(pk / k).toFixed(3), rms: +(rms / k).toFixed(3) }; };
ev('FEEL.off = true'); const base = { swing: await avg('sfx.swing()'), heavy: await avg('sfx.heavySwing()'), hit: await avg('sfx.hit()'), big: await avg('sfx.bigHit()'), parry: await avg('sfx.parry()'), land: await avg('sfx.land()') }; ev('FEEL.off = false');
rows.push('stock  swing ' + JSON.stringify(base.swing) + ' heavy ' + JSON.stringify(base.heavy) + ' hit ' + JSON.stringify(base.hit) + ' bigHit ' + JSON.stringify(base.big) + ' parry ' + JSON.stringify(base.parry) + ' land ' + JSON.stringify(base.land));
const WPN = { sword: 'longsword', dagger: 'dagger', great: 'maul', spear: 'spear', katana: 'katana', staff: 'quarterstaff', shield: 'knight_shield', twin: 'twinfangs', scythe: 'antler_scythe', whip: 'headsman_chain' };
let worst = 0;
for (const [cls, id] of Object.entries(WPN)) {
  G.SAVE.weapon = id; ev('refreshDerived()');
  const c0 = ev('moveset().combo[0]'), hv = ev('moveset().heavy');
  const sw = await avg(`P.charged = false; WSFX.swing(ATK['${c0}'])`), hs = await avg(`P.charged = false; WSFX.swing(ATK['${hv}'])`), ch = await avg(`P.charged = true; WSFX.swing(ATK['${hv}']); P.charged = false`);
  const hi = await avg(`WSFX.impact(ATK['${c0}'], false)`), bh = await avg(`WSFX.impact(ATK['${hv}'], true)`);
  rows.push(`${cls.padEnd(7)} swing ${JSON.stringify(sw)} heavy ${JSON.stringify(hs)} charged ${JSON.stringify(ch)} hit ${JSON.stringify(hi)} big ${JSON.stringify(bh)}`);
  worst = Math.max(worst, sw.pk / base.swing.pk, hs.pk / base.heavy.pk, hi.pk / base.hit.pk, bh.pk / base.big.pk);
}
const extra = { crack: await avg('WSFX.crack(0.3)'), ring: await avg('WSFX.ring(1)'), land: await avg('WSFX.land(true, 1)'), metal: await avg('WSFX.matT = -1; WSFX.mat("metal", 0.5)'), stone: await avg('WSFX.matT = -1; WSFX.mat("stone", 1)'), pogo: await avg('WSFX.pogo()') };
rows.push('extras ' + JSON.stringify(extra));
// worst case stack: a charged hammer swing, its big hit, a metal layer and the stock boom on one frame -> must stay under 1.0
G.SAVE.weapon = 'maul'; ev('refreshDerived()');
const stack = await render(`P.charged = true; WSFX.swing(ATK['gs_heavy']); P.charged = false; WSFX.impact(ATK['gs_heavy'], true); WSFX.matT = -1; WSFX.mat('metal', 1); WSFX.impact(ATK['gs_heavy'], true);`);
const stockStack = await render(`FEEL.off = true; sfx.heavySwing(); sfx.bigHit(); sfx.bigHit(); FEEL.off = false;`);
rows.push('worst peak ratio vs stock (per sound type): ' + worst.toFixed(2));
rows.push('stack WC ' + JSON.stringify(stack) + '   stack stock ' + JSON.stringify(stockStack) + '   clip: ' + (stack.pk >= 1 ? 'YES' : 'no'));
return rows;
