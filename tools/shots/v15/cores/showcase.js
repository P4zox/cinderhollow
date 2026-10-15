// v15 cores showcase (snapshots in a real, dark arena): the effigy, the Rekindle prompt, an enchanted finisher on the
// rekindled boss (slash light, ribbon and sparks in the Core's colour) and the idle blade ember.
// Run: SHOT_HTML=web/dist/v15_cores.html node tools/shots/shot.js tools/shots/v15/cores/showcase.js <out>
await boot();
const C = G.cores, E = C.ev, step = (n = 1, tap = [], hold = []) => G.step(n, hold, tap);
const R = [], T = (name, pass, detail = '') => R.push(`${pass ? 'OK ' : 'BAD'} ${name}${detail ? '  [' + detail + ']' : ''}`);
E(`SETTINGS.god = 1; SAVE.flags['boss:hound'] = 1; for (const f of ['cut:', 'cutp2:', 'cutp3:']) SAVE.flags[f + 'hound'] = 1;
   SAVE.cores = { hound: 1, overseer: 1, cindervane: 1 }; SAVE.enchants = { longsword: 'overseer' }; SAVE.stats.str = 30; refreshDerived(false); P.hp = D.maxHp`);
G.tp('C5', 6, 10); step(90);
const eff = E(`(() => { const p = props.find(p => p.type === 'cr_effigy'); return p ? [p.x, p.y] : null; })()`);
T('the effigy stands in Gravetusk’s den', !!eff);
E(`P.x = ${eff[0]} - 30; P.face = 1; setP('idle', 'idle', true)`); step(40); await snap('show_effigy');
E(`P.x = ${eff[0]} + 4`); step(4);
T('its prompt reads "Rekindle Gravetusk"', E('nearbyPrompt()') === 'Rekindle Gravetusk', E('nearbyPrompt()'));
await snap('show_prompt');
// an enchanted finisher in the dark den (Forgefire: the slash light, ribbon and sparks burn orange)
let shot = 0;
const finisher = async (tag) => { E(`P.x = ${eff[0]} - 80; P.face = 1; P.st = D.maxSt; setP('idle', 'idle', true)`); step(10);
  for (const k of ['attack', 'attack', 'attack', 'attack']) { step(1, [k]); for (let i = 0; i < 13; i++) { step(1); if (shot < 6 && E("P.state === 'attack4' && fx.some(f => f.tint)")) { await snap(`show_finisher_${tag}_${shot++}`); step(2); } } }
  for (let i = 0; i < 40; i++) { step(1); if (shot < 6 && E("P.state === 'attack4' && fx.some(f => f.tint)")) { await snap(`show_finisher_${tag}_${shot++}`); step(2); } } };
await finisher('overseer'); E("SAVE.enchants.longsword = 'cindervane'"); await finisher('cindervane'); E("SAVE.enchants.longsword = 'overseer'");
T('caught the tinted finisher in the dark', shot > 0, `${shot} frames`);
E(`P.x = ${eff[0]} + 4; setP('idle', 'idle', true)`); step(4);
step(1, ['interact']); step(30); await snap('show_dialog');
for (let i = 0; i < 6 && !E('!!(dialog && dialog.steps[dialog.i] && dialog.steps[dialog.i].choice)'); i++) step(1, ['confirm']);
step(1, ['confirm']); step(40); await snap('show_rekindled');
// the blade at rest, in the dark
E(`SAVE.enchants.longsword = 'cindervane'; boss = null; enemies = []; P.x = ${eff[0]} - 60; setP('idle', 'idle', true)`); step(120); await snap('show_idle_cindervane');
E(`SAVE.enchants.longsword = 'overseer'`); step(120); await snap('show_idle_overseer');
return R;
