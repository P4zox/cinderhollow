await boot(); G.SAVE.items.wings = 1; G.SAVE.items.tidebreath = 1;
const out = [], K = G.KIT, P = () => G.P;
const byKind = k => K.objs.filter(q => q.kind === k);
const put = (x, y) => { const p = P(); p.x = x; p.y = y; p.vx = p.vy = 0; };
const god = () => { G.SETTINGS.god = true; };
god();
// ---- phase
G.tp('T1', 2, 36); G.step(3);
{ const ph = byKind('phase')[0]; let log = [], was = null, fellAt = -1;
  put((ph.d.x0 + ph.d.x1) / 2, ph.d.y0 - 20); G.step(1);
  for (let i = 0; i < 300; i++) { G.step(1); if (ph.solidNow !== was) { log.push(i + ':' + (ph.solidNow ? 'on' : 'off') + ':py' + Math.round(P().y)); was = ph.solidNow; } if (fellAt < 0 && P().y > ph.d.y0 + 20) fellAt = i; if (P().y > ph.d.y0 + 20) put((ph.d.x0 + ph.d.x1) / 2, ph.d.y0 - 30); }
  out.push('phase ' + log.slice(0, 8).join(' ') + ' fellAt=' + fellAt); }
// ---- crumble
G.tp('T1', 62, 16); G.step(3);
{ const c = byKind('crumble')[0]; put(c.d.x0 + 16, c.d.y0); G.step(1); let st = [];
  for (let i = 0; i < 300; i++) { G.step(1); if (!st.length || st[st.length - 1].split(':')[1] !== c.st) st.push(i + ':' + c.st); }
  out.push('crumble ' + st.join(' ') + ' Py=' + Math.round(P().y)); }
// ---- swing
G.tp('T1', 27, 32); G.step(3);
{ const r = byKind('swing')[0]; const ax = r.anchor.x, ay = r.anchor.y; put(ax, ay + r.len + 10); P().vy = 30; G.step(1, [], []);
  let s = [];
  for (let i = 0; i < 12; i++) G.step(1);
  s.push('state=' + P().state + ' held=' + r.held);
  let maxA = 0; for (let i = 0; i < 120; i++) { G.step(1, [i % 60 < 30 ? 'right' : 'left']); maxA = Math.max(maxA, Math.abs(r.ang)); }
  s.push('maxAng=' + maxA.toFixed(2));
  let ang0 = r.ang; G.step(1, [], ['jump']); s.push('after jump state=' + P().state + ' vx=' + Math.round(P().vx) + ' vy=' + Math.round(P().vy) + ' ang=' + ang0.toFixed(2));
  G.step(10); s.push('regrab? ' + r.held);
  out.push('swing ' + s.join(' | ')); }
// ---- pendulum
G.tp('T1', 72, 36); G.step(3);
{ let hurt = 0, hp = []; G.SETTINGS.god = false; const h0 = P().hp; for (let i = 0; i < 200; i++) { const b = P().hp; G.step(1); if (P().hp < b) hurt++; P().hp = Math.max(P().hp, 60); } out.push('pendulum hits in 200f: ' + hurt); G.SETTINGS.god = true; }
// ---- spring
G.tp('T1', 27, 56); G.step(3);
{ const sp = byKind('spring')[0]; put(sp.x, sp.d.y0); G.step(1); let minY = 1e9; for (let i = 0; i < 90; i++) { G.step(1); minY = Math.min(minY, P().y); } out.push('spring rise px=' + Math.round(sp.d.y0 - minY)); }
// ---- wind gust
G.tp('T1', 12, 56); G.step(3);
{ let xs = []; for (let i = 0; i < 180; i++) { G.step(1); if (i % 30 == 0) xs.push(Math.round(P().x)); } out.push('wind x drift ' + xs.join(',')); }
// ---- updraft
G.tp('T1', 19, 56); G.step(3);
{ let minY = 1e9; G.step(1, [], ['jump']); for (let i = 0; i < 150; i++) { G.step(1, ['jump']); minY = Math.min(minY, P().y); } out.push('updraft minY row=' + (minY / 16).toFixed(1) + ' state=' + P().state); }
// ---- crate onto plate
G.tp('T1', 38, 56); G.step(3);
{ const cr = byKind('crate')[0], g1 = K.byId.g1, x0 = cr.body.x; for (let i = 0; i < 240; i++) G.step(1, ['right']); out.push('crate moved ' + Math.round(cr.body.x - x0) + ' plate=' + K.byId.pl1.active + ' g1.k=' + g1.k.toFixed(2)); }
// ---- levers
G.tp('T1', 56, 56); G.step(3);
{ const L1 = K.byId.L1; L1.interact(); G.step(90); out.push('L1 ' + L1.active + ' g2.k=' + K.byId.g2.k.toFixed(2));
  const L2 = K.byId.L2; L2.onHit({ kind: 'light' }); G.step(60); const k1 = K.byId.g3.k; G.step(240); out.push('timed L2 g3 open=' + k1.toFixed(2) + ' then=' + K.byId.g3.k.toFixed(2) + ' L2=' + L2.active);
  K.byId.W1.interact(); G.step(30); const kw = K.byId.g5.k; K.byId.W2.interact(); G.step(60); out.push('winch one=' + kw.toFixed(2) + ' both=' + K.byId.g5.k.toFixed(2));
  K.byId.S1.interact(); G.step(90); out.push('switch g4=' + K.byId.g4.k.toFixed(2) + ' flag=' + G.SAVE.flags['x3:T1:g4']); }
// ---- seq bells
G.tp('T1', 12, 76); G.step(3);
{ const b = id => K.byId[id]; const hit = id => { b(id).onHit({ kind: 'light' }); G.step(20); };
  hit('b3'); hit('b2'); const p1 = K.byId.sq1.prog; hit('b3'); hit('b1'); hit('b4'); hit('b2'); G.step(90);
  out.push('seq wrongReset prog=' + p1 + ' solved=' + K.byId.sq1.active + ' g6.k=' + K.byId.g6.k.toFixed(2)); }
// ---- braziers seq + glyphs
{ for (const id of ['f2', 'f3', 'f1']) { K.byId[id].onHit({ kind: 'light' }); G.step(20); } G.step(90); out.push('brazier seq ' + K.byId.sq3.active + ' g8.k=' + K.byId.g8.k.toFixed(2));
  for (const id of ['gC', 'gA', 'gD', 'gB']) { K.byId[id].onHit({ kind: 'light' }); G.step(20); } G.step(90); out.push('glyph seq ' + K.byId.sq2.active); }
// ---- beam
G.tp('T1', 80, 76); G.step(3);
{ const b = byKind('beam')[0]; out.push('beam path0 ' + b.path.length); for (let i = 0; i < 3; i++) { K.byId.M1.onHit({}); G.step(20); } G.step(2); out.push('after M1 ' + JSON.stringify(b.path.map(p => p.map(v => Math.round(v / 16))))); for (let i = 0; i < 2; i++) { K.byId.M2.onHit({}); G.step(20); } G.step(60); out.push('after M2 ' + JSON.stringify(b.path.map(p => p.map(v => Math.round(v / 16)))) + ' socket=' + K.byId.so1.active + ' g9.k=' + K.byId.g9.k.toFixed(2)); await snap('beam_solved'); }
// ---- level
G.tp('T1', 3, 96); G.step(3);
{ const lv = K.byId.lvl, lvs = byKind('lever').filter(l => l.targets.includes('lvl')); const y0 = lv.sy; lvs[0].interact(); G.step(200); const y1 = lv.sy; lvs[1].interact(); G.step(200);
  out.push('level sy ' + y0 / 16 + ' -> ' + y1 / 16 + ' -> ' + (lv.sy / 16).toFixed(2)); await snap('level_up'); }
// ---- rising
G.tp('T1', 45, 96); G.step(3);
{ const r = K.byId.rise1; let st = []; for (let i = 0; i < 700; i++) { G.step(1); if (!st.length || st[st.length - 1].split(':')[1] !== r.st) st.push(i + ':' + r.st + ':' + Math.round(r.sy / 16)); if (i == 200) await snap('rising'); }
  out.push('rising ' + st.join(' ') + ' P=' + Math.round(P().x / 16) + ',' + Math.round(P().y / 16)); }
return out;
