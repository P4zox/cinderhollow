// feature A/B on one frame: old look (hard shadows, ring bloom) then each v15 feature alone, then all. ROOMS=[[id,tx,ty]]
await boot(); G.SETTINGS.god = 1;
const base = { shaders: 1, light: 2, lband: 0, bright: 1, tex: 0, bloom: 1, vig: 1, scan: 0, grain: 0, ca: 0, grade: 0, rays: 0, mood: 0, rim: 0 };
const LX = G.lx.LX, o = [], GF = G.GFX;
for (const [id, tx, ty] of ROOMS) {
  G.tp(id, tx, ty); for (let i = 0; i < 12; i++) G.step(30);
  G.P.hp = 99999; G.sk.ev('enemies.forEach(e => { e.x = -9999; })');
  Object.assign(G.SETTINGS, base, { rays: 2, light: 3 }); for (let i = 0; i < 40; i++) G.step(1);   // warm the shaft fades, then freeze: step(0) re-renders the same frame
  const shots = [['0old', {}, false], ['1soft', { light: 3 }, false], ['2rim', { rim: 1 }, false], ['3bloom', {}, true], ['4rays', { rays: 2 }, true], ['5mood', { mood: 1 }, false], ['6all', { light: 3, rim: 1, rays: 1, mood: 1 }, true]];
  for (const [n, s, chain] of shots) {
    Object.assign(G.SETTINGS, base, s); GF.chain = chain;
    G.step(0);
    await snap(`ab_${id}_${n}`);
  }
  GF.chain = true; o.push(id + ' ok');
}
return o;
