// every Lighting x Light shafts x Bloom x Rim x Region mood combination renders without a GL error or a fallback
const errs = []; window.addEventListener('error', e => errs.push(e.message));
const warns = []; const ow = console.warn; console.warn = (...a) => { warns.push(a.join(' ')); ow(...a); };
await boot(); G.SETTINGS.god = 1;
const gl = G.GFX.gl || null, o = [];
for (const id of ['R1', 'K1']) {
  G.tp(id, 20, 6); G.step(30);
  let n = 0, bad = 0;
  for (const light of [0, 1, 2, 3]) for (const rays of [0, 1, 2]) for (const bloom of [0, 1, 2]) for (const rim of [0, 1]) for (const mood of [0, 1]) for (const lband of [0, 1]) {
    Object.assign(G.SETTINGS, { shaders: 1, light, rays, bloom, rim, mood, lband });
    G.step(1); n++;
    const e = G.GFX.gl.getError(); if (e || !G.GFX.ok) { bad++; if (bad < 4) o.push(`${id} light ${light} rays ${rays} bloom ${bloom} rim ${rim} mood ${mood}: glErr ${e} ok ${G.GFX.ok}`); }
  }
  o.push(`${id}: ${n} combos, ${bad} bad, chain ${G.GFX.chain}, lx.bad ${G.lx.LX.bad}`);
}
G.SETTINGS.grade = 0;
for (let i = 0; i < 7; i++) { G.SETTINGS.grade = i % 5; G.SETTINGS.scan = i % 3; G.SETTINGS.ca = i % 2; G.SETTINGS.tex = i % 3; G.step(1); }
o.push('looks cycled, ok ' + G.GFX.ok);
o.push('errors ' + JSON.stringify(errs.slice(0, 3)) + ' warns ' + JSON.stringify(warns.slice(0, 3)));
return o;
