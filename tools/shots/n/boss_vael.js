window.__errs = []; console.error = (...a) => { if (window.__errs.length < 5) window.__errs.push(String(a[0] && a[0].stack || a[0]).slice(0, 400)); };
// King Vael: intro cutscene once, phase 1 moves, phase 2 court (scene + courtiers fighting), phase 3 absorb, death, rewards, fog.
await boot(); G.give({ stats: { vig: 60, mnd: 30, end: 40, str: 40, dex: 40, fth: 30, arc: 10 } });
const out = [], log = {};
for (const k of ['boss:vael', 'cut:vael', 'cutp2:vael', 'cutp3:vael']) delete G.SAVE.flags[k];
G.tp('NV7', 43, 12); G.P.hp = 99999;
const b = G.boss; if (!b) return ['NO BOSS'];
let cuts = 0;
for (let i = 0; i < 200 && !b.active; i++) { G.step(4, ['left']); if (G.state === 'cut') { cuts++; if (cuts % 4 === 1) await snap('v_cut_' + i); G.step(20); } }
for (let i = 0; i < 400 && G.state === 'cut'; i++) G.step(10);
out.push(`intro cutscene frames ${cuts}, active ${b.active}`);
let hurt = 0, minX = 1e9, maxX = -1e9, snaps = 0; const L = b.L, R = b.R;
const fight = async (n, tag) => {
  for (let i = 0; i < n; i++) {
    const live = b.parts || [b]; const tg = live[Math.floor(i / 60) % live.length] || b;
    const d = tg.x < G.P.x ? 'left' : 'right', far = Math.abs(tg.x - G.P.x) > 60;
    const prev = G.P.hp; G.step(3, far ? [d] : [], far ? [] : ['attack']);
    if (G.state === 'cut') { await snap(`v_${tag}_scene_${i}`); for (let k = 0; k < 400 && G.state === 'cut'; k++) G.step(6); }
    if (G.P.hp < prev) hurt++;
    G.P.hp = 99999; G.P.inv = 0;
    if (b.alive) { minX = Math.min(minX, b.x); maxX = Math.max(maxX, b.x); }
    const k = 'V' + b.phase + ':' + (b.state === 'attack' ? b.atk : b.state); log[k] = (log[k] || 0) + 1;
    for (const q of b.court || []) { const kk = q.kind + ':' + (q.state === 'attack' ? q.atk : q.state); log[kk] = (log[kk] || 0) + 1; }
    if (i % 150 === 75 && snaps < 12) { await snap(`v_${tag}_${i}`); snaps++; }
  }
};
await fight(500, 'p1');
b.hp = Math.floor(b.maxHp * 0.64);
await fight(900, 'p2');
out.push(`court after p2: ${(b.court || []).map(q => q.kind + ':' + q.state + ':' + q.hp).join(', ')}`);
b.hp = Math.floor(b.maxHp * 0.28);
await fight(700, 'p3');
out.push(`void during phase 3: ${!!G.NVR.void} biome ${G.room && G.NVR.void ? 'nv_void' : '-'}`);
out.push(`phase ${b.phase}, hits on player ${hurt}; x ${Math.round(minX)}..${Math.round(maxX)} in ${L}..${R}: ${minX >= L - 1 && maxX <= R + 1}`);
out.push('states ' + JSON.stringify(log));
for (let n = 0; n < 200 && b.alive; n++) { b.hit({ dmg: 300, poise: 0, dir: 1, kind: 'light', x: b.x, y: b.y - 20, melee: true }); G.step(3); G.P.hp = 99999; if (G.state === 'cut') G.step(1, [], ['pause']); }
for (let i = 0; i < 50; i++) { G.step(10); G.P.hp = 99999; }
await snap('v_dead');
await new Promise(r => setTimeout(r, 9000));
out.push(`void after death: ${!!G.NVR.void}`);
out.push(`dead ${!b.alive} flag ${!!G.SAVE.flags['boss:vael']} fogs ${JSON.stringify(G.props.filter(p => p.type === 'fog').map(p => p.on()))} spells ${JSON.stringify(G.SAVE.spellsOwned)} charms ${JSON.stringify(G.SAVE.charms)}`);
out.push(JSON.stringify(window.__errs)); return out;
