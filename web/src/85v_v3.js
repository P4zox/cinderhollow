// ------------------------------------------------------------------ v17 vistas, agent V3 (docs/v17/vista_v3.md)
// SF16 The Stargazer's Seat, SF17 The Crater Edge, NH15 Neon Skyline, E6 The Last Hearth, H3 The Hermit's Garden,
// CT2 The Last Gate. Art: art/gen_vista_<room>.py -> assets/vista_<room>_<layer>.png. Engine: 85_vistas.js.
// Layers are 240 tall (bottom-anchored, 24 px of extra sky); each layer's dy is set from the room's camera so the painting
// covers the frame both standing (cam.y measured at the bench) and seated (the view rises up to 160 px into the sky).
// fx(t, cam) draws over the layers in screen space; v3At() maps a point painted in a layer to the screen the same way
// vistaLayer() places that layer, so the motion stays on its painting.
function v3At(L, x, y) {
  const sh = sheet(L.sheet); if (!sh || !sh.ok) return null;
  const f = sh.frames[0], oy = Math.round(clamp(-cam.y * (L.vfac || 0), -(f.h - H) - 20, 20)) + (H - f.h) + (L.dy || 0);
  return { x: L.wrap === false ? (L.x || 0) + x - cam.x * (L.fac || 0) : x - cam.x * (L.fac || 0), y: y + oy };
}
const v3R = (x, y, w, h, c) => { g.fillStyle = c; g.fillRect(Math.round(x), Math.round(y), w, h); };
function v3Twinkle(L, seed, n, x0, x1, y0, y1, cols, rate = 1) {   // stars that breathe: a few at a time, slow
  for (let i = 0; i < n; i++) {
    const p = v3At(L, x0 + hash2(i, seed) * (x1 - x0) | 0, y0 + hash2(i, seed + 1) * (y1 - y0) | 0); if (!p) return;
    const k = Math.sin(time * (0.6 + hash2(i, seed + 2) * 1.6) * rate + i * 2.3); if (k < 0.35) continue;
    g.globalAlpha = (k - 0.35) / 0.65; v3R(p.x, p.y, 1, 1, cols[i % cols.length]);
    if (k > 0.93 && i % 3 === 0) { g.globalAlpha *= 0.5; v3R(p.x - 1, p.y, 3, 1, cols[i % cols.length]); v3R(p.x, p.y - 1, 1, 3, cols[i % cols.length]); }
  }
  g.globalAlpha = 1;
}

// ================================================================== SF16 The Stargazer's Seat: the galactic arch at night
const V3_SF16 = [
  { sheet: 'vista_sf16_sky', fac: 0.02, vfac: 0.03, dy: 2 },
  { sheet: 'vista_sf16_ridge', fac: 0.06, vfac: 0.05, dy: 4 },
  { sheet: 'vista_sf16_near', fac: 0.16, vfac: 0.1, dy: 7 },
];
const V3_MET = [];
vistaRegister('SF16', { tint: '#070716', layers: V3_SF16, fx(t) {
  const L = V3_SF16[0];
  v3Twinkle(L, 161, 70, 0, 420, 20, 190, ['#fff6e6', '#d0c8e4', '#b6b0dc']);
  // far meteors: rare, small, from the radiant at the top of the arch (the near shower is the room's own prop)
  if (Math.random() < 0.012 && V3_MET.length < 3) { const a = rand(-2.6, -0.5); V3_MET.push({ x: 190 + rand(-30, 30), y: 70 + rand(-14, 14), a: a + Math.PI, s: rand(50, 90), t: 0, life: rand(0.45, 0.9) }); }
  const o = v3At(L, 0, 0); if (!o) return;
  for (const m of V3_MET) {
    m.t += 1 / 60; const d = m.s * m.t, ca = Math.cos(m.a), sa = Math.sin(m.a), k = Math.min(1, m.t * 6) * Math.max(0, 1 - m.t / m.life);
    for (let i = 0; i < 9; i++) { g.globalAlpha = k * (1 - i / 9); v3R(o.x + m.x + ca * (d - i * 1.5), o.y + m.y + sa * (d - i * 1.5), 1, 1, i < 2 ? '#fff6e6' : '#9c98d0'); }
  }
  g.globalAlpha = 1;
  for (let i = V3_MET.length - 1; i >= 0; i--) if (V3_MET[i].t > V3_MET[i].life) V3_MET.splice(i, 1);
} });

// ================================================================== SF17 The Crater Edge: first light over the crater
const V3_SF17 = [
  { sheet: 'vista_sf17_sky', fac: 0.02, vfac: 0.03, dy: 2 },
  { sheet: 'vista_sf17_far', fac: 0.05, vfac: 0.04, dy: 2 },
  { sheet: 'vista_sf17_mid', fac: 0.12, vfac: 0.08, dy: 12 },
];
vistaRegister('SF17', { tint: '#0a1024', layers: V3_SF17, fx(t) {
  v3Twinkle(V3_SF17[0], 171, 34, 0, 420, 4, 60, ['#d8ecff', '#a8a8c8', '#fff0dc'], 0.7);
  // the heart breathes: its column of light swells and settles, slow as sleep
  const h = v3At(V3_SF17[1], 196, 150), b = 0.5 + 0.5 * Math.sin(t * 0.7);
  if (h) {
    g.globalCompositeOperation = 'lighter';
    const gr = g.createRadialGradient(h.x, h.y, 0, h.x, h.y, 34); gr.addColorStop(0, `rgba(150,200,255,${0.16 + 0.14 * b})`); gr.addColorStop(1, 'rgba(150,200,255,0)');
    g.fillStyle = gr; g.fillRect(h.x - 34, h.y - 34, 68, 68);
    const cg = g.createLinearGradient(0, h.y - 150, 0, h.y); cg.addColorStop(0, 'rgba(170,210,255,0)'); cg.addColorStop(1, `rgba(170,210,255,${0.08 + 0.1 * b})`);
    g.fillStyle = cg; g.fillRect(Math.round(h.x) - 2, h.y - 150, 5, 150);
    // frost motes rising off the heart
    for (let i = 0; i < 14; i++) {
      const life = 5 + hash2(i, 3) * 4, k = ((t + hash2(i, 4) * 20) % life) / life;
      g.globalAlpha = Math.sin(k * Math.PI) * 0.8; v3R(h.x + (hash2(i, 5) - 0.5) * 30 + Math.sin(t * 0.8 + i) * 3, h.y - k * 70, 1, 1, i % 3 ? '#a8d0ff' : '#e0f0ff');
    }
    g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  }
  // glints on the black glass: the dawn's reflection trembles
  for (let i = 0; i < 10; i++) {
    const p = v3At(V3_SF17[1], 276 + hash2(i, 7) * 60, 132 + hash2(i, 8) * 40); if (!p) break;
    const k = Math.sin(t * (1 + hash2(i, 9)) + i * 1.9); if (k < 0.6) continue;
    g.globalAlpha = (k - 0.6) * 2; v3R(p.x, p.y, 2, 1, '#e8b490');
  }
  g.globalAlpha = 1;
} });

// ================================================================== NH15 Neon Skyline: the city in the rain, the Root through it
const V3_NH15 = [
  { sheet: 'vista_nh15_sky', fac: 0.02, vfac: 0.03, dy: 3 },
  { sheet: 'vista_nh15_far', fac: 0.05, vfac: 0.04, dy: 4 },
  { sheet: 'vista_nh15_mid', fac: 0.12, vfac: 0.08, dy: 8 },
];
const V3_NH_BLINK = [[15, 110], [64, 86], [84, 143], [120, 114], [181, 128], [196, 151], [347, 156], [358, 121], [394, 148], [410, 99], [453, 140]];
const V3_NH_SIGN = [[63, 126, 30], [104, 148, 40], [366, 158, 26], [404, 140, 34], [488, 140, 28]];
const V3_NH_LANE = [[[-20, 104], [120, 112], [250, 106], [400, 116], [540, 108]], [[-20, 128], [160, 122], [300, 132], [540, 126]], [[-20, 90], [200, 96], [540, 88]]];
function v3Lane(P, u) {   // a point along a polyline lane, u in 0..1
  const n = P.length - 1, f = clamp(u, 0, 0.9999) * n, i = Math.floor(f), k = f - i;
  return [P[i][0] + (P[i + 1][0] - P[i][0]) * k, P[i][1] + (P[i + 1][1] - P[i][1]) * k];
}
vistaRegister('NH15', { tint: '#08081a', layers: V3_NH15, fx(t) {
  const F = V3_NH15[1], M = V3_NH15[2], o = v3At(F, 0, 0), om = v3At(M, 0, 0); if (!o || !om) return;
  g.globalCompositeOperation = 'lighter';
  // two searchlights from the far city sweep the cloud deck, slow
  for (const [bx, ph, c] of [[150, 0, '170,220,255'], [330, 2.1, '255,170,230']]) {
    const a = -Math.PI / 2 + 0.38 * Math.sin(t * 0.13 + ph), x0 = o.x + bx, y0 = o.y + 186, L = 190;
    const x1 = x0 + Math.cos(a) * L, y1 = y0 + Math.sin(a) * L, px = -Math.sin(a), py = Math.cos(a);
    const gr = g.createLinearGradient(x0, y0, x1, y1); gr.addColorStop(0, `rgba(${c},0.07)`); gr.addColorStop(1, `rgba(${c},0)`);
    g.fillStyle = gr; g.beginPath(); g.moveTo(x0 - px, y0 - py); g.lineTo(x1 - px * 16, y1 - py * 16); g.lineTo(x1 + px * 16, y1 + py * 16); g.lineTo(x0 + px, y0 + py); g.fill();
  }
  // rivers of light: tail lights one way, head lights the other, along three lanes between the towers
  V3_NH_LANE.forEach((P, li) => {
    for (let i = 0; i < 16; i++) {
      const dir = (i + li) % 2 ? 1 : -1, sp = 0.018 + 0.006 * li, u = ((t * sp * dir + hash2(i, li + 30)) % 1 + 1) % 1, [x, y] = v3Lane(P, u);
      g.globalAlpha = 0.85; v3R(o.x + x, o.y + y + (dir > 0 ? 0 : 1), 2, 1, dir > 0 ? '#ff5a6a' : '#f8e8c8');
    }
  });
  g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  // red aviation lights on the masts, each on its own beat
  for (let i = 0; i < V3_NH_BLINK.length; i++) {
    const [x, y] = V3_NH_BLINK[i], k = (t * 0.7 + hash2(i, 41)) % 1;
    if (k < 0.5) { g.globalAlpha = k < 0.25 ? 1 : 0.5; v3R(om.x + x, om.y + y, 1, 1, '#ff3a4a'); }
  }
  // the neon signs stutter now and then
  for (let i = 0; i < V3_NH_SIGN.length; i++) {
    const [x, y, h] = V3_NH_SIGN[i], s = Math.floor(t * 12 + i * 37);
    if (hash2(s, i) < 0.04 || (hash2(Math.floor(t * 0.5), i + 9) < 0.12 && hash2(s, i + 3) < 0.5)) { g.globalAlpha = 0.65; v3R(om.x + x, om.y + y, 4, h, '#100c22'); }
  }
  g.globalAlpha = 1;
} });

// ================================================================== E6 The Last Hearth: the ember hollow through the broken window
// After SAVE.flags['w2:open'] the hearth burns low (82_forge.js) and the view answers: the taproot has gone out, the lake
// is a dull crust, and a pale cold light has come up on the horizon. The *cold sheets are the same painting regraded.
const V3_E6 = c => [
  { sheet: 'vista_e6_sky' + c, fac: 0.02, vfac: 0.03, dy: 2 },
  { sheet: 'vista_e6_far' + c, fac: 0.05, vfac: 0.04, dy: 3 },
  { sheet: 'vista_e6_mid' + c, fac: 0.12, vfac: 0.08, dy: 6 },
];
const V3_E6W = V3_E6(''), V3_E6C = V3_E6('cold');
const v3Cold = () => !!(typeof SAVE !== 'undefined' && SAVE.flags && SAVE.flags['w2:open']);
vistaRegister('E6', { tint: '#0c0606', get layers() { return v3Cold() ? V3_E6C : V3_E6W; }, fx(t) {
  const cold = v3Cold(), F = (cold ? V3_E6C : V3_E6W)[1], r = v3At(F, 104, 168); if (!r) return;
  if (!cold) {   // the taproot's foot breathes in the lake; sparks climb its flank
    g.globalCompositeOperation = 'lighter';
    const b = 0.5 + 0.5 * Math.sin(t * 1.3) * Math.sin(t * 0.37 + 1);
    const gr = g.createRadialGradient(r.x, r.y, 0, r.x, r.y, 40); gr.addColorStop(0, `rgba(255,170,80,${0.12 + 0.1 * b})`); gr.addColorStop(1, 'rgba(255,120,40,0)');
    g.fillStyle = gr; g.fillRect(r.x - 40, r.y - 40, 80, 80);
    for (let i = 0; i < 18; i++) {
      const life = 3 + hash2(i, 2) * 3, k = ((t + hash2(i, 3) * 9) % life) / life;
      g.globalAlpha = Math.sin(k * Math.PI) * 0.9; v3R(r.x + (hash2(i, 4) - 0.5) * 50 + Math.sin(t * 2 + i) * 2, r.y - 4 - k * 90, 1, 1, i % 3 ? '#f0a040' : '#ffe0a0');
    }
    g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  }
  // ash drifting down outside, slow (grey; after the fire goes out it falls a little thicker)
  const n = cold ? 34 : 22;
  for (let i = 0; i < n; i++) {
    const sp = 6 + hash2(i, 5) * 8, y = ((t * sp + hash2(i, 6) * H) % (H + 10)) - 5, x = (hash2(i, 7) * W + Math.sin(t * 0.5 + i) * 6 + t * 3) % W;
    g.globalAlpha = 0.35 + 0.35 * hash2(i, 8); v3R(x, y, 1, 1, cold ? '#6a6060' : '#8a5a48');
  }
  g.globalAlpha = 1;
} });

// ================================================================== god rays per vista room (40_gfx.js GFX_SUN is keyed per biome)
// The painted light of a view is not where its biome's sun is: in these rooms the biome entry is swapped on entry and
// restored on leaving. NH15: the Root is the brightest shape behind a standing player and the rays bloomed it, so they are
// faint there (the city's light comes from below, not from a sun).
const V3_SUN = { NH15: [0.5, 1.25, 0.08, '230,170,255'] };
const V3_AMB = {};   // (per-room ambient overrides: none needed; CT2 was tried at 0.16 and only washed the room out)
const V3_SUN_SAVED = {}, V3_AMB_SAVED = {};
HOOKS.enter.push(def => {
  for (const b in V3_SUN_SAVED) { GFX_SUN[b] = V3_SUN_SAVED[b]; delete V3_SUN_SAVED[b]; }
  for (const b in V3_AMB_SAVED) { AREAS[b].ambient = V3_AMB_SAVED[b]; delete V3_AMB_SAVED[b]; }
  const o = V3_SUN[def.id];
  if (o && typeof GFX_SUN !== 'undefined') { V3_SUN_SAVED[def.biome] = GFX_SUN[def.biome]; GFX_SUN[def.biome] = o; }
  const a = V3_AMB[def.id];
  if (a !== undefined && AREAS[def.biome]) { V3_AMB_SAVED[def.biome] = AREAS[def.biome].ambient; AREAS[def.biome].ambient = a; }
});

// ================================================================== H3 The Hermit's Garden: dusk over the lake, through the long window
const V3_H3 = [
  { sheet: 'vista_h3_sky', fac: 0.02, vfac: 0.03 },
  { sheet: 'vista_h3_far', fac: 0.05, vfac: 0.04 },
  { sheet: 'vista_h3_mid', fac: 0.12, vfac: 0.08 },
];
vistaRegister('H3', { tint: '#140e18', layers: V3_H3, fx(t) {
  v3Twinkle(V3_H3[0], 131, 22, 0, 420, 2, 40, ['#c8c8e0', '#fff0c8'], 0.6);
  // the sun's path on the lake shivers
  for (let i = 0; i < 16; i++) {
    const p = v3At(V3_H3[1], 214 + hash2(i, 11) * 24 + (hash2(i, 13) - 0.5) * (hash2(i, 12) * 20), 152 + hash2(i, 12) * 24); if (!p) break;
    const k = Math.sin(t * (1.4 + hash2(i, 14)) + i * 2.1); if (k < 0.5) continue;
    g.globalAlpha = (k - 0.5) * 1.6; v3R(p.x, p.y, 2 + (i % 2), 1, i % 3 ? '#fff0c8' : '#f8d8a8');
  }
  // fireflies over the near slope: slow, few, warm
  g.globalCompositeOperation = 'lighter';
  const o = v3At(V3_H3[2], 0, 0);
  for (let i = 0; o && i < 12; i++) {
    const x = o.x + 20 + hash2(i, 15) * 340 + Math.sin(t * 0.4 + i * 1.7) * 10, y = o.y + 168 + hash2(i, 16) * 40 + Math.sin(t * 0.7 + i) * 5;
    const k = Math.max(0, Math.sin(t * (0.5 + hash2(i, 17) * 0.6) + i * 2.4)); if (k < 0.2) continue;
    g.globalAlpha = k * 0.8; v3R(x, y, 1, 1, '#f0e890'); g.globalAlpha = k * 0.25; v3R(x - 1, y, 3, 1, '#c8d060'); v3R(x, y - 1, 1, 3, '#c8d060');
  }
  g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
} });

// ================================================================== CT2 The Last Gate: the light beyond the gate, the causeway behind you
// A long room (cam.x 0..1088): the light sits at sky x 331, so it barely moves as you walk (it does not get nearer); seated,
// it stands behind the gate prop (82_forge.js gate2). The beyond stays vague: only a glow, rising rays, pale shapes in it.
const V3_CT2 = [
  { sheet: 'vista_ct2_sky', fac: 0.02, vfac: 0.04, dy: 14 },
  { sheet: 'vista_ct2_far', fac: 0.05, vfac: 0.05, dy: 17 },
  { sheet: 'vista_ct2_mid', fac: 0.1, vfac: 0.1, dy: 34 },
];
vistaRegister('CT2', { tint: '#2d3849', layers: V3_CT2, fx(t) {
  const c = v3At(V3_CT2[0], 331, 150); if (!c) return;
  // the light breathes in, slowly (the lore: "as if the world beyond were breathing in"). Seated, it opens up: the gate prop
  // stands in front of it then, so the glow is tall and wide enough to rise around and above the gate's silhouette.
  const V = SYS.vista, sk = V && V.p && V.p.room === 'CT2' ? sysEase(V.k) : 0, b = 0.5 + 0.5 * Math.sin(t * 0.45);
  g.globalCompositeOperation = 'lighter';
  g.save(); g.translate(c.x, c.y - 40); g.scale(1, 1.6);
  const gr = g.createRadialGradient(0, 0, 0, 0, 0, 120);
  gr.addColorStop(0, `rgba(246,244,240,${0.05 + 0.04 * b + (0.5 + 0.12 * b) * sk})`); gr.addColorStop(0.55, `rgba(232,236,242,${0.02 + (0.3 + 0.06 * b) * sk})`); gr.addColorStop(1, 'rgba(220,228,238,0)');
  g.fillStyle = gr; g.fillRect(-120, -120, 240, 240); g.restore();
  for (let i = 0; i < 7; i++) {   // rays fanning UP out of the horizon, each drifting a little
    const a = -Math.PI / 2 + (i - 3) * 0.2 + 0.03 * Math.sin(t * 0.2 + i * 1.3), L = 170, x0 = c.x + (i - 3) * 3, y0 = c.y + 4;
    const x1 = x0 + Math.cos(a) * L, y1 = y0 + Math.sin(a) * L, px = -Math.sin(a), py = Math.cos(a), w = 7 + (i % 3) * 3;
    const rg = g.createLinearGradient(x0, y0, x1, y1); rg.addColorStop(0, `rgba(244,239,230,${(0.02 + 0.14 * sk) * (0.6 + 0.4 * Math.sin(t * 0.3 + i * 2))})`); rg.addColorStop(1, 'rgba(244,239,230,0)');
    g.fillStyle = rg; g.beginPath(); g.moveTo(x0 - px, y0 - py); g.lineTo(x1 - px * w, y1 - py * w); g.lineTo(x1 + px * w, y1 + py * w); g.lineTo(x0 + px, y0 + py); g.fill();
  }
  g.globalCompositeOperation = 'source-over';
  // far ash rising toward the light, drawn in toward it as it climbs
  for (let i = 0; i < 26; i++) {
    const life = 9 + hash2(i, 21) * 6, k = ((t + hash2(i, 22) * 30) % life) / life, x0 = hash2(i, 23) * W;
    const x = x0 + (c.x - x0) * k * 0.35 + Math.sin(t * 0.6 + i) * 3, y = H + 4 - k * (H + 10);
    g.globalAlpha = Math.sin(k * Math.PI) * 0.5; v3R(x, y, 1, 1, i % 4 ? '#c4ccd5' : '#f4efe6');
  }
  g.globalAlpha = 1;
} });
