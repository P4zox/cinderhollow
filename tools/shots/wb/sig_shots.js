// screenshots of every signature's finisher / charged-heavy flourish on a held boss (agent WB)
// SHOT_HTML=web/dist/wb.html node tools/shots/shot.js tools/shots/wb/sig_shots.js tools/shots/wb/shots
// then: python3 tools/shots/wb/crop.py tools/shots/wb/shots <result json>  (crops around the player, builds sig_montage.png)
await boot(); G.giveArmory(); G.grantTechniques();
const E = G.sk.ev;
const ids = (typeof ONLY !== 'undefined' && ONLY) || E('Object.keys(SIGS)');
const out = {};
for (const id of ids) {
  G.SAVE.weapon = id; G.SAVE.weapons[id] = 5; G.SAVE.lastCls = 'sword';
  G.give({ stats: { vig: 35, mnd: 25, end: 25, str: 30, dex: 30, fth: 25 }, charmsEq: [], skills: [] });
  delete G.SAVE.flags['boss:hound']; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'hound'] = 1;
  G.tp('C5', 6, 10); const b = G.boss;
  for (let i = 0; i < 200 && !b.active; i++) { G.step(4, ['right']); G.P.hp = 99999; if (G.state !== 'play') G.step(1, [], ['pause']); }
  const bx = b.x, by0 = b.y; b.update = function (dt) { this.x = bx; this.y = by0; this.commonUpdate(dt); };
  b.state = 'idle'; b.hp = 1e7;
  E('refreshDerived(false); P.cds = {}; P.sigCd = {}; clearBuffer(); P.sigCharge = 2');
  const place = () => { const hb = E('hbOf(boss)'); G.P.x = hb.x0 - G.wb.sigReach() + 6; G.P.face = 1; };   // the boss at the edge of reach: the flourish shows in the gap
  place(); G.step(10); place();
  const pos = () => E('[Math.round((P.x - cam.x) * 3), Math.round((P.y - cam.y) * 3)]');
  // a charged heavy (the staff's spin), snapped on the flourish
  G.P.st = 999; G.step(1, ['heavy'], ['heavy']);
  let n = 0; for (let f = 0; f < 90; f++) { G.P.st = 999; const A = E('ATK[P.state]'); const act = A && G.P.anim.i >= A.active[0]; G.step(1, !G.P.charged && !act ? ['heavy'] : []); if (act && n < 1 && G.P.anim.i >= A.active[0] + 1) { await snap(`${id}_heavy`); out[id + '_heavy'] = pos(); n++; } }
  G.step(40); E('P.sigCd = {}'); place();
  // the combo up to its finisher
  const ms = E('moveset().combo'); let shot = false;
  for (let f = 0; f < 140 && !shot; f++) { G.P.st = 999; G.step(1, [], f % 6 === 0 ? ['attack'] : []); if (G.P.state === ms[ms.length - 1] && G.P.anim.i >= E('ATK[P.state].active[0]') + 1) { G.step(3); await snap(`${id}_fin`); out[id + '_fin'] = pos(); shot = true; } }
}
return out;
