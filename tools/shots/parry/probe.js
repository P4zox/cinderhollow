// which boss hits are parryable today: every hurtPlayer call during each fight, split by opt.parryable
await new Promise(r => setTimeout(r, 300));
const T = G.trn, out = [], E = G.sk.ev;
T.start(); G.step(10);
E(`window.__ph = []; { const _h = hurtPlayer; hurtPlayer = function (dmg, dir, id, opt = {}) { if (boss && boss.active) window.__ph.push({ k: boss.kind, p: !!opt.parryable, id: String(id), src: opt.src ? (opt.src === boss ? 'boss' : (boss.parts && boss.parts.includes(opt.src)) ? 'part' : 'other') : 'none', st: boss.state, atk: boss.atk || boss.move || '' }); return _h.call(this, dmg, dir, id, opt); }; }`);
for (const k of T.bosses().map(b => b.kind)) {
  E('window.__ph.length = 0');
  if (!T.summon(k) || !G.boss) { out.push('NOBOSS ' + k); continue; }
  for (let i = 0; i < 700; i++) {
    const B = G.boss; if (!B) break;
    const tb = (B.parts && B.parts.find(q => q.alive !== false)) || B, d = tb.x - G.P.x;
    G.step(2, Math.abs(d) > 36 ? [d < 0 ? 'left' : 'right'] : [], []); G.P.face = d < 0 ? -1 : 1;
    G.P.hp = 99999; G.P.inv = 0; if (G.state !== 'play') G.step(1, [], ['pause']);
  }
  const L = E('window.__ph'), ids = {};
  for (const h of L) { const key = h.id.replace(/[0-9.]+$/, '#'); (ids[key] = ids[key] || { p: 0, n: 0, src: h.src, atk: new Set() }); ids[key].n++; if (h.p) ids[key].p++; }
  const par = L.filter(h => h.p).length, bySrc = {}; for (const h of L) bySrc[h.src] = (bySrc[h.src] || 0) + 1;
  const atks = [...new Set(L.map(h => (h.p ? '+' : '-') + h.atk))].slice(0, 14);
  out.push(`${k.padEnd(13)} hits=${L.length} parryable=${par} src=${JSON.stringify(bySrc)} atks=${atks.join(' ')}`);
  T.clear(); G.step(5);
}
return out;
