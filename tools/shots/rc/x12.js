// Sovereign's Trial pilot: a search over the hook-swing timing, then dash through the veil, slam, updraft, glide home
await boot(); G.SETTINGS.god = 0; G.grantTechniques(); G.SAVE.items.talon = 1; delete G.SAVE.items.wings; const S = window.__sys, log = [];
G.SAVE.seenAreas = { crown: 1 };
const P = () => G.P, st = (h = [], t = []) => G.step(1, h, t);
const wait = n => { for (let i = 0; i < n; i++) st(); };
G.tp('X12', 4, 28); wait(30); G.step(1, [], ['interact']); wait(3);
const restart = () => { const sg = G.props.find(p => p.type === 'sys_sigil'); P().x = sg.x; P().y = sg.y; P().vx = P().vy = 0; wait(3); G.step(1, [], ['interact']); wait(3); };
const walkTo = (x, tol = 2) => { for (let i = 0; i < 200 && Math.abs(P().x - x) > tol; i++) st([P().x < x ? 'right' : 'left']); for (let i = 0; i < 4; i++) st(); };
let ok = false, tries = 0, att;
search: for (const ha of [14, 18, 22, 26]) for (const hp of [20, 30, 40, 50, 60, 70]) for (const hb of [4, 10, 16]) for (const hq of [20, 30, 40, 50, 60]) {
  tries++; if (tries > 1) restart(); att = S.SYS.trial.attempts;
  walkTo(6.3 * 16);
  st(['right', 'jump'], ['jump']);
  for (let i = 0; i < ha; i++) st(['right', 'jump']);
  st(['right'], ['hook']);
  for (let i = 0; i < 12 && P().state !== 'hook'; i++) st(['right']);
  if (P().state !== 'hook') continue;
  for (let i = 0; i < hp; i++) st(['right']);
  st(['right'], ['jump']);                          // release (boost)
  for (let i = 0; i < hb; i++) st(['right']);
  st(['right'], ['hook']);
  for (let i = 0; i < 12 && P().state !== 'hook'; i++) st(['right']);
  const h2 = P().state === 'hook';
  if (h2) { for (let i = 0; i < hq; i++) st(['right']); st(['right'], ['jump']); }
  for (let i = 0; i < 120 && !P().ground && S.SYS.trial.attempts === att; i++) st(['right']);
  if (tries <= 40 && tries % 3 === 1) log.push(`t${tries} ha${ha} hp${hp} hb${hb} hq${hq} h2 ${h2} -> ${(P().x/16).toFixed(1)},${(P().y/16).toFixed(1)} ${P().state} reset ${S.SYS.trial.attempts !== att}`);
  if (S.SYS.trial.attempts === att && P().ground && P().x > 23 * 16 && P().x < 28 * 16 && Math.abs(P().y - 23 * 16) < 3) { ok = true; log.push(`hooks ok ha${ha} hp${hp} hb${hb} hq${hq} after ${tries}`); break search; }
}
if (!ok) return log.concat(['hook phase failed after ' + tries]);
await snap('x12_1_landing');
// veil: run and roll through it
walkTo(24.5 * 16); for (let i = 0; i < 8; i++) st(['right']); st(['right'], ['roll']); for (let i = 0; i < 40; i++) st(['right']);
log.push('after veil ' + (P().x / 16).toFixed(1) + ',' + (P().y / 16).toFixed(1) + ' ' + P().state);
// slam through the cracked floor
walkTo(32.5 * 16, 3); st(['jump'], ['jump']); for (let i = 0; i < 14; i++) st(['jump']); st(['down'], ['heavy']); for (let i = 0; i < 60; i++) st(['down']);
log.push('after slam ' + (P().x / 16).toFixed(1) + ',' + (P().y / 16).toFixed(1) + ' ' + P().state);
await snap('x12_2_rootway');
// run into the updraft and glide up the east wall
walkTo(36 * 16, 3); st(['right', 'jump'], ['jump']); for (let i = 0; i < 200 && !(P().ground && P().y < 6 * 16); i++) st(['right', 'jump']);
log.push('top ' + (P().x / 16).toFixed(1) + ',' + (P().y / 16).toFixed(1) + ' ' + P().state);
await snap('x12_3_top');
// the long glide west home
st(['left', 'jump'], ['jump']); for (let i = 0; i < 400 && S.SYS.trial && !S.SYS.result; i++) st(['left', 'jump']);
wait(60);
log.push('result ' + JSON.stringify(S.SYS.result && { t: +S.SYS.result.time.toFixed(2), gold: S.SYS.result.gold }) + ' rec ' + JSON.stringify(S.x3().trials) + ' at ' + (P().x / 16).toFixed(1) + ',' + (P().y / 16).toFixed(1));
await snap('x12_4_end');
return log;
