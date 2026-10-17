// ------------------------------------------------------------------ v17 painted vistas, agent V2 (docs/v17/vista_v2.md)
// X11 The Crown Overlook, TV14 Mossbed Glade, DB15 Pearl Lagoon, CM16 Moonlit Conservatory, DU15 The Last Oasis,
// LF1 The Long Evening. Art: art/gen_vista_<room>.py -> assets/vista_<room>_<layer>.png (+ .json, tag 'loop').
const V2 = { rooms: ['X11', 'TV14', 'DB15', 'CM16', 'DU15', 'LF1'] };
// screen position of a point painted at (px, py) in a layer (same placement as vistaLayer in 85_vistas.js)
function v2At(L, px, py, fh) {
  const s = clamp(-cam.y * (L.vfac || 0), -(fh - H) - 20, 20);
  return [px + (L.x || 0) - cam.x * (L.fac || 0), py + Math.round(s) + (H - fh) + (L.dy || 0)];
}
// soft fields of 1-2 px marks (mist, caustics, cloud veils) in a few alpha steps: one fillStyle per step, no per-pixel strings
function v2Field(col, steps, amax, fn) {
  const buckets = Array.from({ length: steps }, () => []);
  fn((x, y, w, h, a) => { const i = Math.min(steps - 1, Math.floor(a / amax * steps)); if (i >= 0) buckets[i].push(x, y, w, h); });
  g.fillStyle = col;
  for (let i = 0; i < steps; i++) { const b = buckets[i]; if (!b.length) continue; g.globalAlpha = (i + 0.5) / steps * amax;
    for (let j = 0; j < b.length; j += 4) g.fillRect(b[j], b[j + 1], b[j + 2], b[j + 3]); }
  g.globalAlpha = 1;
}
const v2Ok = id => { const V = VISTA_BG[id]; return !!V && V.layers.every(L => { const s = sheet(L.sheet); return s && s.ok; }); };

// ================================================================== CM16 The Moonlit Conservatory
{
  // vfac 0.29 + dy 21: standing (cam.y 72) the moon rides high in the glass; seated (the view pulls back to cam.y -36) the
  // painting sinks 31 px so the moon clears the roof's arches. Above the painting the tint is its own zenith colour.
  const FAR = { sheet: 'vista_cm16_far', fac: 0.04, vfac: 0.29, dy: 21, wrap: false, x: 0 };
  vistaRegister('CM16', { tint: '#14162a', sun: [0.61, 0.75, 0.22, '214,218,255'], layers: [
    FAR, { sheet: 'vista_cm16_glint', fac: 0.04, vfac: 0.29, dy: 21, wrap: false, x: 0, fps: 4 },
    { sheet: 'vista_cm16_mid', fac: 0.14, vfac: 0.35, dy: 25, wrap: false, x: 0 }],
  fx(t) {
    const [mx, my] = v2At(FAR, 238, 62, 224), [, wy] = v2At(FAR, 0, 172, 224);
    g.globalCompositeOperation = 'lighter';
    const k = 0.05 + 0.015 * Math.sin(t * 0.7);   // the moon breathes a little
    const gr = g.createRadialGradient(mx, my, 20, mx, my, 90); gr.addColorStop(0, `rgba(200,200,255,${k})`); gr.addColorStop(1, 'rgba(200,200,255,0)');
    g.fillStyle = gr; g.fillRect(mx - 90, my - 90, 180, 180);
    g.globalCompositeOperation = 'source-over';
    v2Field('rgb(170,172,215)', 6, 0.07, put => {   // low mist drifting over the canal (alpha up to 0.07)
      for (let i = 0; i < 3; i++) {
        const y = Math.round(wy - 4 + i * 5), off = (t * (3 + i) + i * 140) % 520 - 120;
        for (let x = 0; x < W; x += 2) {
          const a = Math.max(0, Math.sin((x + off) / 46 + i)) * (1 - i * 0.25);
          if (a > 0.15) put(x, y + Math.round(Math.sin(x / 31 + t * 0.3) * 1.5), 2, 2, a * 0.07);
        }
      }
    });
  } });
}

// ================================================================== X11 The Crown Overlook
// The whole Hallow under a sea of cloud at golden hour (lore rc_10). `far`: sky, sun, the cloud sea and the Spire's thunderhead;
// `land`: the Ramparts on their crag, the drowned Cathedral's spires, the Spire's lighthouse (by hand, 1x). Live: the Deep's
// red breath through a rift in the clouds, lightning in the thunderhead, a veil of cloud drifting over the sea, the sun's bloom.
{
  const FAR = { sheet: 'vista_x11_far', fac: 0.02, vfac: 0.03, wrap: false, x: 0 }, FH = 240;
  const flash = t => { const p = (t + 2.1) % 7.7; return p < 0.09 ? 1 : p > 0.17 && p < 0.24 ? 0.6 : p > 3.1 && p < 3.16 ? 0.35 : 0; };
  vistaRegister('X11', { tint: '#2a2450', sun: null, layers: [
    FAR, { sheet: 'vista_x11_land', fac: 0.035, vfac: 0.03, wrap: false, x: 0 }],
  fx(t) {
    const [sx, sy] = v2At(FAR, 146, 133, FH), [rx, ry] = v2At(FAR, 262, 158, FH), [hx, hy] = v2At(FAR, 338, 100, FH), [, zy] = v2At(FAR, 0, 140, FH);
    g.globalCompositeOperation = 'lighter';
    let gr = g.createRadialGradient(sx, sy, 6, sx, sy, 70); const k = 0.05 + 0.015 * Math.sin(t * 0.5);
    gr.addColorStop(0, `rgba(255,220,160,${k})`); gr.addColorStop(1, 'rgba(255,200,140,0)'); g.fillStyle = gr; g.fillRect(sx - 70, sy - 70, 140, 140);
    const b = 0.5 + 0.5 * Math.sin(t * 0.9) * Math.sin(t * 0.37 + 1);   // the Deep breathes
    gr = g.createRadialGradient(rx, ry, 1, rx, ry, 30); gr.addColorStop(0, `rgba(255,90,40,${0.28 + 0.2 * b})`); gr.addColorStop(0.5, `rgba(200,50,30,${0.1 + 0.08 * b})`); gr.addColorStop(1, 'rgba(160,30,20,0)');
    g.save(); g.translate(rx, ry); g.scale(1, 0.3); g.translate(-rx, -ry); g.fillStyle = gr; g.fillRect(rx - 30, ry - 30, 60, 60); g.restore();
    g.fillStyle = `rgba(255,150,80,${0.35 + 0.25 * b})`; g.fillRect(Math.round(rx - 7), Math.round(ry), 14, 1); g.fillRect(Math.round(rx - 3), Math.round(ry) + 1, 6, 1);
    const f = flash(t);
    if (f) {   // lightning inside the thunderhead, now and then a bolt to the sea
      gr = g.createRadialGradient(hx, hy, 4, hx, hy, 44); gr.addColorStop(0, `rgba(220,215,255,${0.4 * f})`); gr.addColorStop(1, 'rgba(200,200,255,0)');
      g.fillStyle = gr; g.fillRect(hx - 44, hy - 44, 88, 88);
      if (f === 1) { g.fillStyle = 'rgba(240,236,255,0.8)'; let x = hx + 6, y = hy + 22; while (y < zy) { const nx = x + (hash2(Math.floor(t / 7.7), y) - 0.5) * 6; g.fillRect(Math.round(Math.min(x, nx)), Math.round(y), Math.max(1, Math.round(Math.abs(nx - x))), 3); x = nx; y += 3; } }
    }
    g.globalCompositeOperation = 'source-over';
    v2Field('rgb(255,216,196)', 6, 0.11, put => {   // a veil of cloud drifting over the sea, in front of the landmarks' feet (alpha up to ~0.11)
      for (let i = 0; i < 4; i++) {
        const y = Math.round(zy - 2 + i * 6 + i * i), sp = 2 + i * 1.5, off = t * sp + i * 97;
        for (let x = 0; x < W; x += 2) {
          const a = (0.05 + 0.02 * i) * Math.max(0, Math.sin((x + off) / (38 + i * 10)) * Math.sin((x + off * 0.6) / 23 + i));
          if (a > 0.015) put(x, y, 2, 1 + (i >> 1), a);
        }
      }
    });
  } });
}

// ================================================================== LF1 The Long Evening
// Kept: the evening that never ends over her field, the god-rays breathing from the low sun, the warm light. Raised: her storm
// stands over the field as a cloud deck whose underside burns crimson and gold, the sun sunk in a bank of gold cloud; the drake
// stones on the far hill, the Stormspire in the east, harvested fields and hedgerows in long light. Live: god-rays, the deck's
// slow lightning, the sun's warm light on the field (the room's own seeds and embers still drift on the wind, 52_rc.js).
{
  const SKY = { sheet: 'vista_lf1_sky', fac: 0.015, vfac: 0.03, wrap: false, x: 0 }, FH = 256;
  vistaRegister('LF1', { tint: '#2a1830', sun: null, layers: [
    SKY, { sheet: 'vista_lf1_far', fac: 0.05, vfac: 0.05, wrap: false, x: 0 }, { sheet: 'vista_lf1_mid', fac: 0.12, vfac: 0.09, wrap: false, x: 0 }],
  fx(t) {
    const [sx, sy] = v2At(SKY, 191, 168, FH);
    g.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 7; i++) {   // god-rays from the sunken sun, breathing slowly (as the old sky did)
      const a = -Math.PI * 0.5 + (i - 3) * 0.3 + Math.sin(t * 0.15 + i) * 0.04, len = 240, w = 0.045 + 0.02 * Math.sin(t * 0.4 + i * 1.7);
      g.fillStyle = `rgba(255,206,140,${(0.016 + 0.01 * Math.sin(t * 0.3 + i)).toFixed(3)})`;
      g.beginPath(); g.moveTo(sx, sy); g.lineTo(sx + Math.cos(a - w) * len, sy + Math.sin(a - w) * len); g.lineTo(sx + Math.cos(a + w) * len, sy + Math.sin(a + w) * len); g.closePath(); g.fill();
    }
    const p = (t + 1.3) % 9.1, f = p < 0.08 ? 1 : p > 0.16 && p < 0.22 ? 0.5 : p > 4.4 && p < 4.47 ? 0.4 : 0;
    if (f) {   // lightning moving inside her storm, far over the field
      const lx = ((Math.floor((t + 1.3) / 9.1) * 137) % 300) + 40, [, ly] = v2At(SKY, 0, 70, FH);
      const gr = g.createRadialGradient(lx, ly, 4, lx, ly, 70); gr.addColorStop(0, `rgba(255,200,220,${0.22 * f})`); gr.addColorStop(1, 'rgba(255,180,200,0)');
      g.fillStyle = gr; g.fillRect(lx - 70, ly - 70, 140, 140);
    }
    g.globalCompositeOperation = 'source-over';
    addLight(cam.x + sx, cam.y + sy + 30, 200, '255,190,120', 0.22, { shadow: false });
  } });
}

// ================================================================== DU15 The Last Oasis
// Kept: the sun-kings' evening (the old xsb_sky sunset and its pyramid). Raised: a still lake runs from the pool to the
// horizon and holds the sunset upside down; pyramids and two obelisks in the haze, the sun on the dunes' rim. Live: the sun's
// reflection breaks and re-forms (glint frames), heat shimmer along the horizon, the first stars.
{
  const FAR = { sheet: 'vista_du15_far', fac: 0.04, vfac: 0.05, wrap: false, x: 0 }, FH = 232;
  vistaRegister('DU15', { tint: '#2a1030', sun: [0.55, 0.52, 0.18, '255,200,140', 1], layers: [
    FAR, { sheet: 'vista_du15_glint', fac: 0.04, vfac: 0.05, wrap: false, x: 0, fps: 5 }],
  fx(t) {
    const [sx, sy] = v2At(FAR, 210, 111, FH), [, hz] = v2At(FAR, 0, 127, FH);
    g.globalCompositeOperation = 'lighter';
    const gr = g.createRadialGradient(sx, sy, 6, sx, sy, 60); gr.addColorStop(0, `rgba(255,190,120,${(0.07 + 0.02 * Math.sin(t * 0.6)).toFixed(3)})`); gr.addColorStop(1, 'rgba(255,160,100,0)');
    g.fillStyle = gr; g.fillRect(sx - 60, sy - 60, 120, 120);
    g.globalCompositeOperation = 'source-over';
    const sh = sheet(FAR.sheet), f0 = sh.frames[0], oy = sy - 111;   // heat shimmer: the horizon rows of the painting waver
    for (let y = Math.round(hz) - 5; y < hz + 2; y++) {
      const dx = Math.round(Math.sin(t * 2.2 + y * 1.7) * 1.2), py = y - Math.round(oy);
      if (dx && py >= 0 && py < f0.h) g.drawImage(sh.img, f0.x, f0.y + py, f0.w, 1, Math.round(FAR.x - cam.x * FAR.fac) + dx, y, f0.w, 1);
    }
    for (let i = 0; i < 6; i++) {   // the first stars come and go
      const x = (i * 71 + 23) % W, y = 6 + (i * 37) % 30, a = Math.max(0, Math.sin(t * 0.5 + i * 2.3)) * 0.7;
      if (a > 0.05) { g.fillStyle = `rgba(255,236,240,${a.toFixed(2)})`; g.fillRect(x, y, 1, 1); }
    }
  } });
}

// ================================================================== TV14 Mossbed Glade
// Past the Mother Oak the old wood opens onto a sunlit glade far off: the one place in the Thornveil where the morning gets in,
// and the oak stands black against it. Live: slanted shafts breathing, motes drifting in the light. The room's back-wall veil
// is smoothed here (see V2_VEIL) so the view is not cut into 16 px boxes.
{
  const FAR = { sheet: 'vista_tv14_far', fac: 0.03, vfac: 0.04, wrap: false, x: 0 }, FH = 232;
  const motes = Array.from({ length: 26 }, (_, i) => ({ x: hash2(i, 3) * 400, y: 40 + hash2(i, 7) * 110, s: 0.3 + hash2(i, 11) * 0.7, p: hash2(i, 5) * 6.3 }));
  vistaRegister('TV14', { tint: '#0c1a12', layers: [FAR],
  fx(t) {
    const [gx, gy] = v2At(FAR, 203, 133, FH);
    g.globalCompositeOperation = 'lighter';
    for (let k = 0; k < 4; k++) {   // shafts from the high canopy, leaning toward the glade
      const x0 = gx - 120 + k * 52 + Math.sin(t * 0.07 + k) * 4, a = 0.035 + 0.02 * Math.sin(t * 0.35 + k * 1.9), w = 6 + k * 2;
      g.fillStyle = `rgba(220,240,170,${a.toFixed(3)})`;
      g.beginPath(); g.moveTo(x0, 0); g.lineTo(x0 + w, 0); g.lineTo(x0 + w + 70, gy + 30); g.lineTo(x0 + 70 - w, gy + 30); g.closePath(); g.fill();
    }
    const gr = g.createRadialGradient(gx, gy, 4, gx, gy, 70); gr.addColorStop(0, `rgba(240,255,190,${(0.06 + 0.02 * Math.sin(t * 0.4)).toFixed(3)})`); gr.addColorStop(1, 'rgba(200,240,160,0)');
    g.fillStyle = gr; g.fillRect(gx - 70, gy - 70, 140, 140);
    for (const m of motes) {   // pollen in the light
      const x = ((m.x + t * 4 * m.s - cam.x * 0.03) % 400 + 400) % 400 - 8, y = m.y + Math.sin(t * 0.6 + m.p) * 6, a = 0.25 + 0.25 * Math.sin(t * 1.3 + m.p);
      g.fillStyle = `rgba(240,255,200,${a.toFixed(2)})`; g.fillRect(Math.round(x), Math.round(y), 1, 1);
    }
    g.globalCompositeOperation = 'source-over';
  } });
}

// ================================================================== DB15 Pearl Lagoon
// "Light comes down here from somewhere no one has found": past the grotto shelf a drowned sea-cave whose far wall opens in an
// arch full of pale light with no source, mirrored in still water. Live: the reflection ripples (glint frames), shafts from
// the opening breathe, caustic light wavers on the cave roof, motes drift in the light.
{
  const FAR = { sheet: 'vista_db15_far', fac: 0.03, vfac: 0.1, wrap: false, x: 0 }, FH = 240;
  vistaRegister('DB15', { tint: '#061416', layers: [FAR, { sheet: 'vista_db15_glint', fac: 0.03, vfac: 0.1, wrap: false, x: 0, fps: 4 }],
  fx(t) {
    const [ax, ay] = v2At(FAR, 240, 108, FH), [, wl] = v2At(FAR, 0, 150, FH);
    g.globalCompositeOperation = 'lighter';
    const gr = g.createRadialGradient(ax, ay, 8, ax, ay, 110); gr.addColorStop(0, `rgba(190,250,240,${(0.035 + 0.015 * Math.sin(t * 0.5)).toFixed(3)})`); gr.addColorStop(1, 'rgba(150,230,220,0)');
    g.fillStyle = gr; g.fillRect(ax - 110, ay - 110, 220, 220);
    for (let k = 0; k < 3; k++) {   // god-rays out of the mouth, slanting down and toward us into the cave (not over the opening)
      const x0 = ax - 36 - k * 4, y0 = ay - 40 + k * 22, a = 0.03 + 0.016 * Math.sin(t * 0.33 + k * 2.1), w = 5 + k * 2;
      g.fillStyle = `rgba(190,250,240,${a.toFixed(3)})`;
      g.beginPath(); g.moveTo(x0, y0); g.lineTo(x0, y0 + w); g.lineTo(x0 - 110, wl + 10); g.lineTo(x0 - 110 - w * 3, wl - 4); g.closePath(); g.fill();
    }
    v2Field('rgb(170,240,230)', 5, 0.054, put => {   // caustics: the water's light wavering on the cave roof (alpha up to ~0.05)
      for (let y = 8; y < ay - 30; y += 3) {
        const sy = Math.sin(y * 0.2 + t * 0.7) * 2;
        for (let x = 0; x < W; x += 3) {
          const v = Math.sin(x * 0.11 + t * 1.3 + sy) * Math.sin(y * 0.17 - t * 0.9 + x * 0.03), a = (v - 0.55) * 0.12 * Math.exp(-Math.abs(x - ax) / 140);
          if (a > 0.004) put(x, y, 2, 1, a);
        }
      }
    });
    g.globalCompositeOperation = 'source-over';
  } });
}

// ================================================================== the light shafts follow each painting's own sun / moon
// GFX_SUN (40_gfx.js) is keyed per biome; while one of these rooms is current its biome entry is swapped for the vista's
// `sun` (and put back on leaving), so no engine file changes. A vista with sun: null switches the biome's rays off there.
{
  const orig = {};
  HOOKS.enter.push(def => {
    for (const b in orig) { if (orig[b] === undefined) delete GFX_SUN[b]; else GFX_SUN[b] = orig[b]; delete orig[b]; }
    const V = VISTA_BG[def.id];
    if (!V || !V2.rooms.includes(def.id) || !('sun' in V) || !v2Ok(def.id)) return;
    orig[def.biome] = GFX_SUN[def.biome];
    if (V.sun) GFX_SUN[def.biome] = V.sun; else delete GFX_SUN[def.biome];
  });
}

// per-room smooth back-wall veil (03_world.js drawSmoothVeil, opted in per biome by AREAS[b].veil / AREA_VEIL): an indoor vista
// room whose view shows through the back wall gets the smooth falloff for itself, set only while its layers are rendered.
const V2_VEIL = { TV14: [1, 0.72, 0.4, 0.16], DB15: [1, 0.7, 0.36, 0.1] };
{
  const rrl = renderRoomLayers;
  renderRoomLayers = function (R) {   // eslint-disable-line no-func-assign
    const v = R && R.def && V2_VEIL[R.def.id], A = v && AREAS[R.def.biome];
    if (!v || !A || !v2Ok(R.def.id)) return rrl.apply(this, arguments);
    const had = 'veil' in A, old = A.veil; A.veil = v;
    try { return rrl.apply(this, arguments); } finally { if (had) A.veil = old; else delete A.veil; }
  };
}

// DB15: the room's own flat lagoon backdrop (xsa_lagoon 'lagoonback', painted opaque into the back layer by 53_sa.js) is left
// out once the vista's art is there, so the painted grotto shows through the smoothed back wall instead.
HOOKS.enter.push(def => {
  if (def.id !== 'DB15' || !v2Ok('DB15') || typeof SA === 'undefined' || !SA.back) return;
  const n = SA.back.length; SA.back = SA.back.filter(t => t.tag !== 'lagoonback');
  if (SA.back.length !== n) renderRoomLayers(room);
});

// debug probe for headless tests: window.__v2probe = '#fff' fills the backdrop flat (measures what shows through the room)
{
  const _dpV2 = drawParallax;
  drawParallax = function () {   // eslint-disable-line no-func-assign
    if (window.__v2probe && room && V2.rooms.includes(room.id)) { g.fillStyle = window.__v2probe; g.fillRect(0, 0, W, H); return; }
    return _dpV2.apply(this, arguments);
  };
}
