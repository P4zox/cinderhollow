window.__arena='flat'; window.__snap='hound,omen,kalden,bellringer,orrery,enforcer,oswin,scarab';
// every boss: summon into the arena, confirm it activates, hurts the player, takes damage, changes phase; no errors
await new Promise(r=>setTimeout(r,300));
const T = G.trn, out = [], only = (window.__only || '').split(',').filter(Boolean);
const errs = []; const ce = console.error; console.error = (...a) => { errs.push(String(a[0] && a[0].stack || a[0]).split('\n').slice(0,2).join(' | ').slice(0, 240)); ce(...a); };
T.start(); G.step(10); if (window.__arena) T.TRN.arena = window.__arena;
const kinds = T.bosses().map(b => b.kind).filter(k => !only.length || only.includes(k));
const hpOf = b => b.hp;
const SNAP = (window.__snap || 'hound,cindervane,sanguine,colossus,unwritten,saint0,twins,pharaoh').split(',');
for (const k of kinds) {
  errs.length = 0; let res = { k };
  try {
    const ok = T.summon(k); const b = G.boss;
    if (!ok || !b) { out.push(`NOBOSS ${k}`); continue; }
    G.SETTINGS.god = 0;
    let seen = new Set(), hurt = 0, phases = new Set([b.phase]), act = false, t0hp = null, dealt = 0, firstAct = -1;
    let byPlayer = 0;
    for (let i = 0; i < 800; i++) {
      const prev = G.P.hp; const B = G.boss; if (!B) break;
      const tx = B.parts && B.parts.find(q => q.alive !== false) ? B.parts.find(q => q.alive !== false).x : B.x;
      const d = tx - G.P.x, far = Math.abs(d) > 40;
      const tb = (B.parts && B.parts.find(q => q.alive !== false)) || B; let hb = null; try { hb = tb.hurtbox && tb.hurtbox(); } catch (e) {}
      const high = hb && hb.y1 < G.P.y - 34;
      const hold = far ? [d < 0 ? 'left' : 'right'] : high ? ['up'] : [];
      const tap = (!far && i >= 200 && i % 6 === 0) ? (high && i % 12 === 0 ? ['jump'] : ['attack']) : [];
      if (!far) G.P.face = d < 0 ? -1 : 1;
      G.step(2, hold, tap);
      if (G.P.hp < prev) hurt++;
      G.P.hp = 99999; G.P.inv = 0;
      if (G.state !== 'play') { G.step(1, [], ['pause']); if (G.state === 'menu') G.step(1, [], ['pause']); }
      if (B.active && !act) { act = true; firstAct = i; t0hp = hpOf(B); }
      seen.add(B.state); phases.add(B.phase);
      if (act && t0hp !== null) dealt = Math.max(dealt, t0hp - hpOf(B));
      if (i === 399) byPlayer = dealt - (B._pre || 0); if (i === 199) B._pre = dealt;
      if (i === 250 && SNAP.includes(k)) await snap('boss_' + k);
      if ((i === 400 || i === 600) && B.alive) {   // push it toward its next phase
        const tg = G.trn.targets.filter(t => t.boss || t === B || (B.parts && B.parts.includes(t)));
        for (const t of tg) try { t.hit({ dmg: Math.round(B.hp * (i === 400 ? 0.5 : 0.7)), poise: 0, dir: 1, kind: 'light', x: t.x, y: t.y - 30 }); } catch (e) { errs.push('hit ' + e.message); }
      }
      if (G.P.state === 'dead') { G.P.state = 'idle'; }
    }
    const B = G.boss;
    res = `${(act && hurt && byPlayer > 0 && !errs.length) ? 'OK  ' : 'BAD '}${k.padEnd(13)} act=${act}@${firstAct} hurt=${hurt} byPlayer=${Math.round(byPlayer)} dealt=${Math.round(dealt)} phases=${[...phases].join('/')} alive=${B ? B.alive : '-'} biome=${G.sk.ev('room.def.biome')} arena=${G.sk.ev('trnFlat()') ? 'flat' : 'home'} states=${[...seen].slice(0, 9).join(',')}${errs.length ? ' ERR ' + [...new Set(errs)].slice(0, 2).join(' || ') : ''}`;
  } catch (e) { res = `EXC  ${k} ${e.message} ${String(e.stack).split('\n')[1]}`; }
  out.push(res);
  T.clear(); G.step(5);
}
G.SETTINGS.god = 0;
return out;
