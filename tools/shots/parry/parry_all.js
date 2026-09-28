// every boss: auto-parry each parryable hit; count parries / broken combos / staggers; the boss must keep fighting after
await new Promise(r => setTimeout(r, 300));
const T = G.trn, out = [], E = G.sk.ev, only = (window.__only || '').split(',').filter(Boolean);
const errs = []; const ce = console.error; console.error = (...a) => { errs.push(String(a[0] && a[0].stack || a[0]).slice(0, 200)); ce(...a); };
window.addEventListener('error', e => errs.push(String(e.message)));
T.start(); G.step(10);
E(`window.__pp = { par: 0, hits: 0 }; { const _h = hurtPlayer; hurtPlayer = function (dmg, dir, id, opt = {}) {
    const src = opt && opt.src, own = src && boss && (src === boss || (boss.parts && boss.parts.includes(src)));
    if (own && window.__autoParry) { P.state = 'parry'; P.parryWin = 0.1; P.face = -dir; }
    const hp = P.hp, r = _h.call(this, dmg, dir, id, opt);
    if (own && window.__autoParry) { if (P.hp === hp && P.parried) window.__pp.par++; P.state = 'idle'; P.parried = false; }
    return r; }; }
  HOOKS.parry.push(() => {});`);
for (const k of T.bosses().map(b => b.kind).filter(k => !only.length || only.includes(k))) {
  errs.length = 0;
  if (!T.summon(k) || !G.boss) { out.push('NOBOSS ' + k); continue; }
  E('window.__pp = { par: 0 }; window.__autoParry = true');
  let staggers = 0, broken = 0, lastSt = null, statesAfter = new Set(), lastBreakI = -1, stuck = 0, prevX = null, sameFor = 0;
  const popsSeen = new Set();
  for (let i = 0; i < 900; i++) {
    const B = G.boss; if (!B) break;
    const tb = (B.parts && B.parts.find(q => q.alive !== false)) || B, d = tb.x - G.P.x;
    G.step(2, Math.abs(d) > 30 ? [d < 0 ? 'left' : 'right'] : [], []);
    G.P.hp = 99999; G.P.inv = 0; if (G.state !== 'play') G.step(1, [], ['pause']);
    const bodies = B.parts ? B.parts : [B];
    for (const b of bodies) { if (b.state === 'stagger' && b._lastSt !== 'stagger') staggers++; b._lastSt = b.state; }
    const pops = E("popups.filter(p => p.v === 'BROKEN').length");
    if (pops && i - lastBreakI > 10) { broken++; lastBreakI = i; }
    if (lastBreakI >= 0 && i - lastBreakI > 40 && i - lastBreakI < 400) statesAfter.add(B.state);
    if (B.hp <= 1) B.hp = B.maxHp * 0.6;   // keep it alive
  }
  const B = G.boss;
  const ok = !errs.length && (broken === 0 || statesAfter.size > 1 || [...statesAfter].some(s => s !== 'idle'));
  out.push(`${ok ? 'OK ' : 'BAD'} ${k.padEnd(13)} parries=${E('window.__pp.par')} broken=${broken} staggers=${staggers} after=${[...statesAfter].slice(0, 6).join(',')}${errs.length ? ' ERR ' + [...new Set(errs)].slice(0, 2).join(' || ') : ''}`);
  E('window.__autoParry = false');
  T.clear(); G.step(5);
}
return out;
