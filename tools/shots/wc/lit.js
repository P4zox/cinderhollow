// WC: same swings with shaders + dynamic lighting (glow layer path), checks for errors and snaps an impact
await boot(); G.giveArmory(); G.SETTINGS.god = 1; G.SETTINGS.shaders = 1; G.SETTINGS.light = 2; const F = G.feel, ev = F.ev, o = [];
for (const w of ['colossus_hammer', 'kalden', 'katana']) {
  G.SAVE.weapon = w; ev('refreshDerived()'); await ev('feelWsheet().img.decode()').catch(() => {}); G.tp('R1', 20, 10); G.step(30); G.P.face = 1;
  ev(`(() => { for (const e of enemies) e.gone = true; enemies = enemies.filter(e => !e.gone); const e = new Enemy('grave_knight', P.x + 30, P.y, 'wcl'); e.hp = e.maxHp = 1e6; e.cool = 99; enemies.push(e); })()`);
  ev('FEEL.swingHit = 0'); G.step(1, [], ['attack']); for (let i = 0; i < 40 && !ev('FEEL.swingHit'); i++) G.step(1); for (let i = 0; i < 12 && ev('hitstop') > 0; i++) G.step(1); G.step(2);
  await snap('lit_' + w); o.push(w + ' LX.on=' + ev('LX.on') + ' sparks=' + F.FEEL.sparks.length + ' flashes=' + F.FEEL.flashes.length);
}
G.SETTINGS.shaders = 0; return o;
