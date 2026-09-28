window.__nohs = 1;
// WC: frame-time check. Same fight, same seed-free input script, feel on vs off, interleaved; update + render per frame.
await boot(); G.giveArmory(); G.grantTechniques(); G.SETTINGS.god = 1;
const F = G.feel, ev = F.ev, res = { on: [], off: [] };
const WPN = ['longsword', 'greatsword', 'twinfangs', 'headsman_chain', 'quarterstaff', 'kalden'];
const setup = w => {
  G.SAVE.weapon = w; ev('refreshDerived()'); G.tp('R1', 20, 10); G.step(20); G.P.face = 1;
  ev(`(() => { for (const e of enemies) e.gone = true; enemies = enemies.filter(e => !e.gone);
    for (const [t, dx] of [['grave_knight', 26], ['hollow_soldier', 40], ['cm_gargoyle', 54], ['rot_hulk', 34]]) { const e = new Enemy(t, P.x + dx, P.y, 'wcp' + dx); e.hp = e.maxHp = 1e7; e.cfg = { ...e.cfg, stance: 1e9, poise: 1e9 }; e.cool = 99; enemies.push(e); } })()`);
};
const run = () => {
  const t0 = performance.now();
  for (let f = 0; f < 240; f++) { const k = f % 24; G.step(1, [], k === 0 ? ['attack'] : k === 8 ? ['attack'] : k === 16 ? ['attack'] : f % 96 === 50 ? ['heavy'] : f % 96 === 80 ? ['jump'] : []); G.P.x = Math.min(G.P.x, 360); }
  return performance.now() - t0;
};
for (const w of WPN) { await ev('feelWsheet && 0'); G.SAVE.weapon = w; ev('refreshDerived()'); await ev('feelWsheet().img.decode()').catch(() => {}); }
for (let rep = 0; rep < 3; rep++) for (const w of WPN) for (const mode of (rep % 2 ? ['on', 'off'] : ['off', 'on'])) {
  ev('FEEL.off = ' + (mode === 'off') + '; FEEL.hs = !window.__nohs'); setup(w); run(); /* warm */ setup(w); res[mode].push(run());
}
ev('FEEL.off = false');
const sum = a => a.reduce((x, y) => x + y, 0), med = a => a.slice().sort((x, y) => x - y)[a.length >> 1];
return { perFrameMs_on: +(sum(res.on) / (res.on.length * 240)).toFixed(3), perFrameMs_off: +(sum(res.off) / (res.off.length * 240)).toFixed(3),
         median_on: +(med(res.on) / 240).toFixed(3), median_off: +(med(res.off) / 240).toFixed(3), ratio: +(sum(res.on) / sum(res.off)).toFixed(3), runs: res.on.length };
