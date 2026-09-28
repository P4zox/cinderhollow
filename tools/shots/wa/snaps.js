// WA: in-game frames of every class's up / air / down (and the air one mid-air), cropped around the player by snaps_sheet.py
await boot(); G.giveArmory(); G.grantTechniques(); G.SETTINGS.god = 1;
const X = G.sk.ev('({ ATK, refreshDerived, setP, get cam() { return cam; } })');
const WPN = window.__wpn || { sword: 'longsword', dagger: 'carving_knife', great: 'colossus_hammer', spear: 'saint_lance', katana: 'katana', staff: 'lantern_staff',
  shield: 'overseer_bulwark', twin: 'twinfangs', scythe: 'last_kindling', whip: 'orrery_whip' };
const A = () => X.ATK[G.P.state];
const until = (fn, n = 90) => { for (let i = 0; i < n && !fn(); i++) G.step(1); };
const pos = {};
const shot = async n => { await snap(n); pos[n] = [Math.round((G.P.x - X.cam.x) * 3), Math.round((G.P.y - X.cam.y) * 3), G.P.state + ':' + G.P.anim.tag + ':' + G.P.anim.i]; };
G.tp('R1', 38, 10); G.step(260);
for (const [cls, id] of Object.entries(WPN)) {
  G.SAVE.weapon = id; X.refreshDerived(); await G.sk.ev("sheet('wpn_' + SAVE.weapon).img.decode()").catch(() => {}); G.tp('R1', 38, 10); G.step(40); G.P.face = 1;
  // up (ground), at the first active frame + 1 step
  G.step(1, ['up'], ['attack']); until(() => A() && G.P.anim.i >= A().active[0], 40); G.step(1); await shot(`${cls}_1up`);
  until(() => !A(), 90); G.step(15);
  // air: jump, attack near the apex
  G.step(1, [], ['jump']); G.step(14, ['jump']); G.step(1, [], ['attack']); until(() => A() && G.P.anim.i >= A().active[0], 40); G.step(1); await shot(`${cls}_2air`);
  until(() => G.P.ground, 120); G.step(20);
  // down: jump, then down + attack on the way up
  G.step(1, [], ['jump']); G.step(16, ['jump']); G.step(1, ['down'], ['attack']); until(() => A() && G.P.anim.i >= A().active[0] + 1, 40); await shot(`${cls}_3down`);
  until(() => G.P.ground, 120); G.step(20);
}
return pos;
