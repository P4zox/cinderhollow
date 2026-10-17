// ------------------------------------------------------------------ v17 vistas, agent V1 (docs/v17/vista_v1.md)
// R11 Watcher's Perch, K11 The Rose Window, M14 Fisherman's Rest, A14 The Reading Nook, HF14 Frostbitten Overlook,
// SP15 Lighthouse Balcony. Art: art/gen_vista_<room>.py -> assets/vista_<room>_<layer>.png. Engine: 85_vistas.js.
window.__v1 = { get cam() { return { x: cam.x, y: cam.y }; }, view: () => (typeof sysVistaView === 'function' ? sysVistaView() : null), get rm() { return room && { pw: room.pw, ph: room.ph, id: room.id }; },
  skyFlash: () => typeof spSkyFlash === 'function' && spSkyFlash() };   // debug handles for tools/shots/v17/vista (dropped in release builds)

// where a painting's pixel (px, py) of layer L lands on screen right now (as vistaLayer places it)
function v1At(L, px, py) {
  const sh = sheet(L.sheet), f = sh && sh.ok ? sh.frames[0] : { w: W, h: H };
  const oy = Math.round(clamp(-cam.y * (L.vfac || 0), -(f.h - H) - 20, 20)) + (H - f.h) + (L.dy || 0);
  return { x: Math.round((L.x || 0) - cam.x * (L.fac || 0)) + px, y: oy + py };
}
const v1Ready = id => { const V = VISTA_BG[id]; return !!(V && V.layers.every(L => { const s = sheet(L.sheet); return s && s.ok; })); };
// light-shaft source per vista room (40_gfx.js keys GFX_SUN by biome; a painting's light sits elsewhere): the biome entry is
// swapped for this frame only, so nothing else changes. fn() -> [uv x, uv y, strength, colour, indoors, threshold]
const V1_SUN = {};
{ const _rs = gfxRaySources;
  gfxRaySources = function (dt) {   // eslint-disable-line no-func-assign
    const f = room && V1_SUN[room.id]; if (!f || !v1Ready(room.id)) return _rs.apply(this, arguments);
    const b = room.def.biome, keep = GFX_SUN[b]; GFX_SUN[b] = f();
    try { return _rs.apply(this, arguments); } finally { if (keep === undefined) delete GFX_SUN[b]; else GFX_SUN[b] = keep; }
  }; }
// drifting motes / ash / snow in screen space with a little parallax (n flakes, seeded, wrapping)
function v1Flakes(n, seed, o) {
  const t = time, Wp = W + 40, Hp = H + 30;
  for (let i = 0; i < n; i++) {
    const r1 = hash2(i, seed), r2 = hash2(i, seed + 1), r3 = hash2(i, seed + 2), sp = o.speed * (0.6 + 0.8 * r3);
    let x = r1 * Wp + Math.sin(t * o.sway + i) * o.swayA + t * o.wind * (0.5 + r3) - cam.x * o.par;
    let y = r2 * Hp + t * sp - cam.y * o.par;
    x = ((x % Wp) + Wp) % Wp - 20; y = ((y % Hp) + Hp) % Hp - 15;
    g.globalAlpha = o.a * (0.4 + 0.6 * r3); g.fillStyle = o.col; g.fillRect(Math.round(x), Math.round(y), r3 > 0.85 ? 2 : 1, 1);
  }
  g.globalAlpha = 1;
}

// R11 Watcher's Perch: the Hallow at last light, the Pale Root on the horizon (art/gen_vista_r11.py)
{ const FAR = { sheet: 'vista_r11_far', fac: 0.02, vfac: 0.3, wrap: false, x: -4, dy: 12 };
  vistaRegister('R11', { tint: '#120f20', layers: [FAR,
    { sheet: 'vista_r11_mid', fac: 0.12, vfac: 0.3, wrap: false, x: -4, dy: 12 }],
    fx(t) {
      // long cloud wisps drifting across the dusk, lit from below (as the old Perch band had them)
      g.globalCompositeOperation = 'lighter';
      for (let i = 0; i < 5; i++) {
        const y = v1At(FAR, 0, 70 + i * 11 + Math.sin(i * 7) * 5).y, x = ((t * (2 + i * 0.7) + i * 131 - cam.x * 0.04) % (W + 220) + W + 220) % (W + 220) - 140;
        g.fillStyle = `rgba(255,150,120,${0.035 + 0.015 * (i % 2)})`; g.fillRect(Math.round(x), y, 80 + i * 19, 1); g.fillRect(Math.round(x) + 24, y + 1, 40 + i * 9, 1);
      }
      // the light that did not set breathes, very slowly
      const r = v1At(FAR, 300, 120), k = 0.05 + 0.025 * Math.sin(t * 0.4);
      const gr = g.createRadialGradient(r.x, r.y, 2, r.x, r.y, 60); gr.addColorStop(0, `rgba(255,236,200,${k})`); gr.addColorStop(1, 'rgba(255,236,200,0)');
      g.fillStyle = gr; g.fillRect(r.x - 60, r.y - 60, 120, 120);
      // the signal fires along the wall, still burning (the painting's beacon posts)
      [[40, 154], [80, 162], [120, 150], [150, 145], [182, 140], [205, 136], [232, 133], [126, 189]].forEach(([x, y], i) => {
        const p = v1At(FAR, x, y), k = 0.18 + 0.12 * Math.sin(t * (5 + i) + i * 1.3) * Math.sin(t * 2.3 + i);
        const gr2 = g.createRadialGradient(p.x, p.y, 0, p.x, p.y, 5); gr2.addColorStop(0, `rgba(255,170,90,${k})`); gr2.addColorStop(1, 'rgba(255,170,90,0)');
        g.fillStyle = gr2; g.fillRect(p.x - 5, p.y - 5, 10, 10);
      });
      // mist rolling slowly over the valley, catching the Root's light toward the middle
      for (let i = 0; i < 4; i++) {
        const y = v1At(FAR, 0, 146 + i * 16).y, x = ((t * (1.2 + i * 0.5) + i * 173 - cam.x * (0.03 + i * 0.02)) % (W + 300) + W + 300) % (W + 300) - 250;
        const lg = g.createLinearGradient(x, 0, x + 260, 0); const c = i < 2 ? '220,170,170' : '150,110,150';
        lg.addColorStop(0, `rgba(${c},0)`); lg.addColorStop(0.5, `rgba(${c},${0.05 - i * 0.008})`); lg.addColorStop(1, `rgba(${c},0)`);
        g.fillStyle = lg; g.fillRect(Math.round(x), y, 260, 3 + i); g.fillRect(Math.round(x) + 40, y + 3 + i, 180, 2);
      }
      g.globalCompositeOperation = 'source-over';
      // the ash, soft as snow and warm
      v1Flakes(46, 11, { speed: 6, wind: 2.5, sway: 0.5, swayA: 6, par: 0.2, a: 0.55, col: '#d8c4bc' });
    } });
  V1_SUN.R11 = () => { const p = v1At(FAR, 300, 116); return [p.x / W, 1 - p.y / H, 0.42, '255,226,196', 0, 0.45]; }; }

// HF14 Frostbitten Overlook: the aurora over the frozen reservoir, no moon (art/gen_vista_hf14.py). Replaces the procedural
// aurora / reservoir band of 51_rb.js in this room (it is drawn inside the biome parallax, which the vista replaces).
{ const FAR = { sheet: 'vista_hf14_far', fac: 0.03, vfac: 0.05, wrap: false, x: -4, dy: 12 };
  vistaRegister('HF14', { tint: '#070a16', layers: [FAR,
    { sheet: 'vista_hf14_mid', fac: 0.1, vfac: 0.05, wrap: false, x: -4, dy: 12 }],
    fx(t) {
      // the curtains breathe: two ray states of the painted aurora, crossfaded and added, drifting a pixel or two
      const sh = sheet('vista_hf14_aur');
      if (sh.ok && sh.frames.length > 1) {
        const p = v1At(FAR, 0, 0); g.globalCompositeOperation = 'lighter';
        for (let i = 0; i < 2; i++) {
          const f = sh.frames[i], k = 0.5 + 0.5 * Math.sin(t * 0.45 + i * Math.PI);
          g.globalAlpha = 0.1 + 0.32 * k * (0.75 + 0.25 * Math.sin(t * 0.13 + i));
          g.drawImage(sh.img, f.x, f.y, f.w, f.h, p.x + Math.round(Math.sin(t * 0.07 + i * 2) * 2), p.y, f.w, f.h);
        }
        g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
      }
      // a few stars twinkle
      for (let i = 0; i < 24; i++) {
        const s = Math.sin(t * (0.8 + hash2(i, 5)) + i * 3.1); if (s < 0.55) continue;
        const q = v1At(FAR, Math.floor(hash2(i, 6) * 420), Math.floor(hash2(i, 7) * 92));
        g.fillStyle = `rgba(230,240,255,${(s - 0.55) * 1.6})`; g.fillRect(q.x, q.y, 1, 1);
      }
      v1Flakes(30, 23, { speed: 9, wind: -3, sway: 0.7, swayA: 5, par: 0.25, a: 0.5, col: '#dfeaf4' });
    } }); }

// the zoom the parallax is drawn under: 1, or the bench view's while sysDrawVista draws it (it moves cam to the view origin)
function v1Zoom() {
  if (!SYS.vista || typeof sysVistaView !== 'function') return { z: 1, x0: cam.x, y0: cam.y };
  const v = sysVistaView(); return v && Math.abs(cam.x - v.x0) < 0.01 && Math.abs(cam.y - v.y0) < 0.01 ? { z: v.z, x0: v.x0, y0: v.y0 } : { z: 1, x0: cam.x, y0: cam.y };
}

// SP15 Lighthouse Balcony: the storm over the open sea, the moon's road on the swells (art/gen_vista_sp15.py). The storm front
// lights up from inside with the Spire's own sky flashes (22_spire.js SPR.flash, so it keeps time with the thunder), and the
// lamp's beam turns over the water from the lantern room (replaces 52_rc.js's seaview band + beam in this room).
{ const v1SpFlash = () => typeof SPR !== 'undefined' ? clamp(SPR.flash / 0.5, 0, 1) * (0.75 + 0.25 * Math.sin(time * 47)) : 0;
  const FAR = { sheet: 'vista_sp15_far', fac: 0.03, vfac: 0.1, wrap: false, x: -4, dy: 4 };
  vistaRegister('SP15', { tint: '#0a0d16', layers: [FAR,
    { sheet: 'vista_sp15_flash', fac: 0.03, vfac: 0.1, wrap: false, x: -4, dy: 4, get alpha() { return v1SpFlash(); } },
    { sheet: 'vista_sp15_mid', fac: 0.12, vfac: 0.1, wrap: false, x: -4, dy: 4 }],
    fx(t) {
      // the moon keeps its light under the storm's dark ambient: an unlit halo (glow layer; open sky in both views)
      const m = v1At(FAR, 124, 40);
      drawGlow(() => { const gr = g.createRadialGradient(m.x, m.y, 6, m.x, m.y, 46); gr.addColorStop(0, 'rgba(220,230,255,0.22)'); gr.addColorStop(1, 'rgba(220,230,255,0)');
        g.fillStyle = gr; g.fillRect(m.x - 46, m.y - 46, 92, 92); g.fillStyle = 'rgba(240,244,250,0.85)'; g.beginPath(); g.arc(m.x + 0.5, m.y + 0.5, 8.6, 0, 7); g.fill(); });
      const Z = v1Zoom(), ox = (408 - Z.x0) * Z.z, oy = (60 - Z.y0) * Z.z;   // the lamp: lantern_room prop at tile (25, 6), light 52 px up
      const a = Math.PI - 0.16 + Math.sin(t * 0.42) * 0.42;
      g.globalCompositeOperation = 'lighter';
      for (const [w, al] of [[0.11, 0.035], [0.06, 0.05], [0.025, 0.07]]) {
        const gr = g.createRadialGradient(ox, oy, 4, ox, oy, 520); gr.addColorStop(0, `rgba(255,228,176,${al * 2})`); gr.addColorStop(1, 'rgba(255,228,176,0)');
        g.fillStyle = gr; g.beginPath(); g.moveTo(ox, oy);
        g.lineTo(ox + Math.cos(a - w) * 600, oy + Math.sin(a - w) * 600); g.lineTo(ox + Math.cos(a + w) * 600, oy + Math.sin(a + w) * 600); g.closePath(); g.fill();
      }
      g.globalCompositeOperation = 'source-over';
    } });
  V1_SUN.SP15 = () => { const p = v1At(FAR, 124, 40); return [p.x / W, 1 - p.y / H, 0.3, '214,226,255', 0, 0.5]; }; }

// M14 / A14 paint a night into the room's back canvas (51_rb.js xrbBackdrop) that covers the parallax. With the vista's art
// present, M14 only clears the back wall in the open part of the room (the painting shows there instead); A14 keeps its wall
// and opens only the window (see A14 below). Anything else, or the art missing: the original backdrop.
const V1_BACKDROP = {};
if (typeof xrbBackdrop === 'function') {
  const _bd = xrbBackdrop;
  xrbBackdrop = function (ctx, R, s) {   // eslint-disable-line no-func-assign
    const f = V1_BACKDROP[R.def.id]; if (!f || !v1Ready(R.def.id)) return _bd.apply(this, arguments);
    return f(ctx, R, s);
  };
}
function v1ClearOpen(ctx, R) {   // xrbBackdrop's clearing: the back wall goes where the room is open, it keeps hugging the terrain
  for (let y = 0; y < R.h; y++) for (let x = 0; x < R.w; x++) {
    if (isSolidT(R.grid[y * R.w + x])) continue;
    let near = false; for (let yy = -1; yy <= 1 && !near; yy++) for (let xx = -1; xx <= 1; xx++) if (isSolidT(tileAtR(R, x + xx, y + yy))) { near = true; break; }
    if (!near) ctx.clearRect(x * TILE, y * TILE, TILE, TILE);
  }
}

// M14 Fisherman's Rest: dusk on the still marsh, the lights on the water (art/gen_vista_m14.py)
{ const FAR = { sheet: 'vista_m14_far', fac: 0.04, vfac: 0.1, wrap: false, x: -4, dy: 4 };
  const LIGHTS = [[211, 103], [263, 105], [277, 105], [321, 105], [213, 143], [213, 152], [384, 164], [110, 167], [383, 175]];   // lights.json
  V1_BACKDROP.M14 = (ctx, R) => v1ClearOpen(ctx, R);
  vistaRegister('M14', { tint: '#0a1210', layers: [FAR],
    fx(t) {
      g.globalCompositeOperation = 'lighter';
      LIGHTS.forEach(([x, y], i) => {   // windows and lanterns breathe
        const p = v1At(FAR, x, y), k = 0.16 + 0.1 * Math.sin(t * (1.3 + hash2(i, 3)) + i * 2.1) + (Math.sin(t * 9 + i) > 0.97 ? 0.1 : 0);
        const gr = g.createRadialGradient(p.x + 0.5, p.y + 0.5, 0, p.x + 0.5, p.y + 0.5, 7); gr.addColorStop(0, `rgba(255,190,110,${k})`); gr.addColorStop(1, 'rgba(255,190,110,0)');
        g.fillStyle = gr; g.fillRect(p.x - 7, p.y - 7, 15, 15);
      });
      // and a few more lights than there are lanterns: pale, drifting, never quite where you looked
      for (let i = 0; i < 4; i++) {
        const ph = t * 0.05 + i * 1.7, life = (Math.sin(ph * 2.3 + i) + 1) / 2; if (life < 0.35) continue;
        const a = (life - 0.35) / 0.65 * 0.5, x = 60 + ((hash2(i, 9) * 300 + t * (1.5 + i * 0.4)) % 320), y = 122 + hash2(i, 4) * 46 + Math.sin(t * 0.7 + i) * 2;
        const p = v1At(FAR, x, y);
        g.fillStyle = `rgba(190,245,215,${a})`; g.fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
        g.fillStyle = `rgba(150,230,190,${a * 0.35})`; g.fillRect(Math.round(p.x), Math.round(p.y) + 3, 1, Math.round(4 + (y - 112) * 0.2));
        const gr = g.createRadialGradient(p.x, p.y, 0, p.x, p.y, 6); gr.addColorStop(0, `rgba(150,230,190,${a * 0.4})`); gr.addColorStop(1, 'rgba(150,230,190,0)');
        g.fillStyle = gr; g.fillRect(p.x - 6, p.y - 6, 12, 12);
      }
      g.globalCompositeOperation = 'source-over';
    } }); }

// A14 The Reading Nook: rain on the glass, the Pale Root rising through the broken east wing (art/gen_vista_a14.py). The nook
// keeps its wall (solid back-wall tiles, darkened) and opens only the tall window's glass (xrb_awin, interior x 8..87, y 13..116
// of the 96x128 frame drawn at room (232, 18); the hole runs 3 px under the frame). The painting is room-locked: A14 is one
// screen wide, so fac 0 and vfac 1 keep it behind the window at every camera position.
const V1_THUNDER = { c: -1 };
{ const v1Bolt = () => {   // a slow storm: a flash every 9-16 s, a double flicker
    const P = 12.5, c = Math.floor(time / P), t0 = c * P + hash2(c, 77) * 6, d = time - t0;
    if (d < 0) return 0;
    const e = x => x > 0 ? Math.exp(-x * 9) : 0;
    return clamp(e(d) + 0.7 * e(d - 0.16) + (hash2(c, 78) > 0.5 ? 0.5 * e(d - 0.42) : 0), 0, 1);
  };
  V1_BACKDROP.A14 = (ctx, R) => {
    const sh = tileSheet(R.def.biome);
    for (let y = 0; y < R.h; y++) for (let x = 0; x < R.w; x++) if (!isSolidT(R.grid[y * R.w + x])) drawTile(ctx, sh, 38 + Math.floor(hash2(x, y) * 4), x * TILE, y * TILE, 1);
    ctx.save();
    const gr = ctx.createLinearGradient(0, 0, 0, R.ph); gr.addColorStop(0, 'rgba(8,6,14,0.62)'); gr.addColorStop(1, 'rgba(8,6,14,0.4)');
    ctx.fillStyle = gr; ctx.fillRect(0, 0, R.pw, R.ph);
    // the window: an arch (centre 279.5, spring 71, radius 43) over a rect down to the sill
    ctx.globalCompositeOperation = 'destination-out'; ctx.beginPath();
    ctx.moveTo(236.5, 137); ctx.lineTo(236.5, 71); ctx.arc(279.5, 71, 43, Math.PI, 0); ctx.lineTo(322.5, 137); ctx.closePath(); ctx.fill();
    ctx.restore();
  };
  vistaRegister('A14', { tint: '#0c0a12', layers: [
    { sheet: 'vista_a14_far', fac: 0, vfac: 1, wrap: false, x: 0, dy: 8 },
    { sheet: 'vista_a14_flash', fac: 0, vfac: 1, wrap: false, x: 0, dy: 8, get alpha() { return v1Bolt(); } }],
    fx(t) {
      if (typeof XRB !== 'undefined') XRB.flash = 0;   // the rain area's random full-box flash would light the wall; the window flashes instead
      { const c = Math.floor(time / 12.5), t0 = c * 12.5 + hash2(c, 77) * 6; if (time >= t0 && V1_THUNDER.c !== c) { V1_THUNDER.c = c; setTimeout(() => tone(55, 1.2, 0.05, 'sine', 0.9), 600); } }   // thunder after the window's flash (v1Bolt's schedule)
      // slanting rain beyond the glass (the room's own rain area draws the drops on the pane)
      const Z = v1Zoom(), ox = -Z.x0 * Z.z, oy = -Z.y0 * Z.z, s = Z.z;
      g.fillStyle = 'rgba(176,170,220,0.32)';
      for (let i = 0; i < 70; i++) {
        const x = 236 + hash2(i, 1) * 90, yy = 28 + ((t * 150 * (0.8 + 0.4 * hash2(i, 2)) + hash2(i, 3) * 112) % 112);
        g.fillRect(Math.round(ox + (x + (yy - 28) * 0.22) * s), Math.round(oy + yy * s), 1, Math.max(1, Math.round(4 * s)));
      }
    } }); }

// K11 The Rose Window: the great rose window at dawn in the east wall of the upper nave (art/gen_vista_k11.py). The painting
// holds the window itself, so the room's old rose prop (50_ra.js SPAWNS.ra_rose: a flat-colour wheel) keeps only its lights and
// motes while the painting is loaded; its light shafts are drawn here instead, from the painted window, so they stay on it.
{ const FAR = { sheet: 'vista_k11_far', fac: 0.08, vfac: 0.15, wrap: false, x: -4, dy: 16 }, RX = 296, RY = 84, RR = 64;
  if (SPAWNS.ra_rose) {
    const _rose = SPAWNS.ra_rose;
    SPAWNS.ra_rose = function (s, c) {
      const n = props.length; _rose.apply(this, arguments);
      const p = props.slice(n).find(q => q.type === 'ra_rose'); if (!p) return;
      if (c.id === 'K11' && v1Ready('K11') && typeof RA !== 'undefined' && RA.lights.length >= 3) {
        // the painted window is already lit: its three lights at the glass (dynamic lighting multiplies the parallax too)
        // blew it to white, so they move down to where the shafts reach the floor, softer
        const Ls = RA.lights.splice(RA.lights.length - 3, 3);
        RA.lights.push([Ls[0][0] - 60, Ls[0][1] + 110, 170, '255,214,180', 0.6, 0], [Ls[1][0] - 80, Ls[1][1] + 150, 80, '255,150,170', 0.3, 0], [Ls[2][0] - 40, Ls[2][1] + 150, 80, '150,170,255', 0.3, 0]);
      }
      const draw = p.draw;
      p.draw = () => {
        if (!(room && room.id === 'K11' && v1Ready('K11'))) return draw();
        if (Math.random() < 0.2) particles.push({ x: p.x + rand(-70, 90), y: p.y + rand(60, 200), vx: rand(2, 6), vy: rand(-3, 3), life: rand(2, 4), kind: 'gold' });
      };
    };
  }
  // the back-wall veil (cathedral: 0.28 in open space) laid its small arch tiles across the painted window; in K11 it is
  // thinned in the open middle of the room (a blurred mask of the cells 3+ tiles from any wall), so the window reads clean
  { const _rrl = renderRoomLayers;
    renderRoomLayers = function (R) {   // eslint-disable-line no-func-assign
      _rrl.apply(this, arguments);
      if (!R || R.def.id !== 'K11' || !R.back || !v1Ready('K11')) return;
      const m = document.createElement('canvas'); m.width = R.pw; m.height = R.ph; const mx = m.getContext('2d'); mx.fillStyle = '#000';
      for (let y = 0; y < R.h; y++) for (let x = 0; x < R.w; x++) {
        let d = 9; for (let yy = -3; yy <= 3; yy++) for (let xx = -3; xx <= 3; xx++) if (isSolidT(tileAtR(R, x + xx, y + yy))) d = Math.min(d, Math.max(Math.abs(xx), Math.abs(yy)));
        if (d >= 3) mx.fillRect(x * TILE, y * TILE, TILE, TILE);
      }
      const bx = R.back.getContext('2d'); bx.save(); bx.globalCompositeOperation = 'destination-out'; bx.globalAlpha = 0.6; bx.filter = 'blur(10px)';
      bx.drawImage(m, 0, 0); bx.restore();
    }; }
  vistaRegister('K11', { tint: '#0e0c14', layers: [FAR],
    fx(t) {
      const r = v1At(FAR, RX, RY), Z = v1Zoom(), floor = (304 - Z.y0) * Z.z;
      g.globalCompositeOperation = 'lighter';
      // the window breathes with the dawn
      const k = 0.07 + 0.03 * Math.sin(t * 0.35);
      let gr = g.createRadialGradient(r.x, r.y, RR * 0.2, r.x, r.y, RR * 1.3); gr.addColorStop(0, `rgba(255,214,160,${k})`); gr.addColorStop(1, 'rgba(255,214,160,0)');
      g.fillStyle = gr; g.fillRect(r.x - RR * 1.3, r.y - RR * 1.3, RR * 2.6, RR * 2.6);
      // shafts of coloured dawn falling from the glass down and to the left, to the floor
      const cols = ['255,190,140', '160,170,255', '255,214,150', '230,150,170'];
      for (let i = 0; i < 4; i++) {
        const a = 0.035 + 0.02 * Math.sin(t * 0.6 + i * 1.7), x0 = r.x - 40 + i * 22, y0 = r.y + 10 + Math.abs(i - 1.5) * 10, w = 16;
        const lg = g.createLinearGradient(x0, y0, x0 - 120, floor); lg.addColorStop(0, `rgba(${cols[i]},${a})`); lg.addColorStop(1, `rgba(${cols[i]},0)`);
        g.fillStyle = lg; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x0 + w, y0); g.lineTo(x0 + w - 150, floor); g.lineTo(x0 - 150 - 20, floor); g.closePath(); g.fill();
      }
      g.globalCompositeOperation = 'source-over';
      // dust turning in the light
      for (let i = 0; i < 40; i++) {
        const u = (hash2(i, 31) + t * 0.004 * (0.5 + hash2(i, 32))) % 1, x = r.x - 30 + hash2(i, 33) * 60 - u * 150 + Math.sin(t * 0.5 + i) * 3, y = r.y + 20 + u * (floor - r.y - 20);
        const a = 0.5 * Math.sin(u * Math.PI) * (0.5 + 0.5 * Math.sin(t * 2 + i * 3));
        if (a > 0.05) { g.fillStyle = `rgba(255,230,190,${a})`; g.fillRect(Math.round(x), Math.round(y), 1, 1); }
      }
    } });
  V1_SUN.K11 = () => { const p = v1At(FAR, RX, RY); return [p.x / W, 1 - p.y / H, 0.22, '255,214,170', 1, 0.45]; }; }
