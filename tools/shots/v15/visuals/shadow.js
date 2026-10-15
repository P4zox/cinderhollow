// soft vs hard shadows from one strong test light near the floor edges of C2 (light-only debug view + final)
await boot(); G.SETTINGS.god = 1;
Object.assign(G.SETTINGS, { shaders: 1, light: 3, rim: 0, rays: 0, mood: 0, bloom: 1 });
const E = G.sk.ev, LX = G.lx.LX;
G.tp('C2', 24, 10); for (let i = 0; i < 10; i++) G.step(30); E('regionCard = null; enemies.length = 0');
E("HOOKS.render.push(() => addLight(P.x + 50, P.y - 6, 190, '255,200,140', 1.3, { flicker: false }))");
for (const [n, l, d] of [['hard_L', 2, 3], ['soft_L', 3, 3], ['hard', 2, 0], ['soft', 3, 0]]) { G.SETTINGS.light = l; LX.dbg = d; G.step(0); await snap('shadow_C2_' + n); }
LX.dbg = 0; return [];
