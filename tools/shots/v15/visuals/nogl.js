// WebGL unavailable: shaders + every v15 option on must fall back to the plain blit with no errors
const errs = []; window.addEventListener('error', e => errs.push(e.message));
await boot(); Object.assign(G.SETTINGS, { shaders: 1, light: 3, rim: 1, rays: 2, mood: 1, bloom: 2 });
G.tp('C2', 24, 10); for (let i = 0; i < 6; i++) G.step(30);
await snap('nogl_C2');
return { ok: G.GFX.ok, chain: G.GFX.chain, lx: G.lx.LX.on, errs };
