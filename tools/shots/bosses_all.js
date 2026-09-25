await boot(); G.give({ stats: { vig: 60, mnd: 30, end: 40, str: 40, dex: 40, fth: 30, arc: 10 } });
const cases = [['C5','hound',6,10,1],['M5','kalden',6,10,1],['M6','vessel',6,10,1],['A3','librarian',20,10,-1],['A6','unwritten',3,14,1],['HF4','ice_warden',31,10,-1],['HF7','twins',4,13,1],['SP5','bellringer',3,10,1],['SP7','cindervane',46,15,-1],['D5','overseer',40,10,-1],['D8','colossus',46,14,-1],['H1','oswin',30,10,-1],['X3','sentinels',3,8,1],['E3','first_ember',10,10,1]];
G.SAVE.flags['sc:seal'] = 1;
const out = [];
for (const [r, k, tx, ty, dir] of cases) {
  try {
    delete G.SAVE.flags['boss:' + k]; G.SAVE.flags['cut:' + k] = 1; G.SAVE.flags['cutp2:' + k] = 1;
    G.tp(r, tx, ty); G.P.hp = 99999;
    let b = G.boss;
    if (!b) { out.push(`${k}: NO BOSS in ${G.room}`); continue; }
    for (let i = 0; i < 150 && !b.active; i++) { const d = b.x < G.P.x ? 'left' : 'right'; G.step(4, Math.abs(b.x - G.P.x) > 60 ? [d] : []); G.P.hp = 99999; if (G.state === 'cut') G.step(1, [], ['pause']); }
    if (!b.active) { out.push(`${k}: never activated (state ${b.state}) px ${Math.round(G.P.x)} bx ${Math.round(b.x)}`); continue; }
    let hurt = 0, dealt = 0, hp0 = b.hp;
    for (let i = 0; i < 500; i++) {
      const tg = (b.parts || [b]).filter(q => q.alive !== false)[0] || b;
      const d = tg.x < G.P.x ? 'left' : 'right', far = Math.abs(tg.x - G.P.x) > 40;
      const prev = G.P.hp; G.step(3, far ? [d] : [], far ? [] : ['attack']); if (G.state === 'cut') G.step(1, [], ['pause']);
      if (G.P.hp < prev) hurt++; G.P.hp = 99999; G.P.inv = 0;
    }
    dealt = hp0 - b.hp;
    // force a kill: hammer every target part
    for (let n = 0; n < 400 && b.alive; n++) { for (const t of (b.parts || [b])) if (t.alive !== false && t.hit) t.hit({ dmg: 400, poise: 0, dir: 1, kind: 'light', x: t.x, y: t.y - 20, melee: true }); G.step(2); G.P.hp = 99999; if (G.state === 'cut') G.step(1, [], ['pause']); }
    for (let i = 0; i < 60; i++) { G.step(10); G.P.hp = 99999; if (G.state === 'cut' || G.state === 'cine') G.step(1, [], ['pause']); }
    out.push(`${k}: hitsOnPlayer ${hurt} dmgDealt ${Math.round(dealt)} ph ${b.phase} alive ${b.alive} flag ${!!G.SAVE.flags['boss:' + k]} state ${G.state}`);
  } catch (e) { out.push(`${k}: EXC ${e.message}`); }
}
return out;
