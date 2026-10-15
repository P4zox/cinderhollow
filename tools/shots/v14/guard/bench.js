// v14 guard bench: dmg/s (x light AR) of each SnS / Spear route, looped from real inputs for ~10 s against a dummy that
// follows (infinite stamina, as tools/shots/wm/bench.js), plus stamina per second with real stamina and a real-boss pass.
// run: SHOT_HTML=web/dist/v14_guard.html sh tools/shots/wm/run.sh tools/shots/v14/guard/bench.js <outdir>
const st = () => G.P.state;
const toLate = (ms = 110) => { for (let i = 0; i < 70 && E('!!ATK[P.state] && ATK[P.state].mv.total - P.mvT > ' + ms); i++) W().frame(1); };
const nextLate = (id, ms = 110) => { for (let i = 0; i < 70 && st() !== id; i++) W().frame(1); toLate(ms); };
const idle = () => { for (let i = 0; i < 150 && !['idle', 'run', 'land', 'guard', 'block'].includes(st()); i++) W().frame(1); };
const free = () => { for (let i = 0; i < 150 && (E('!!ATK[P.state]') || st() === 'roll'); i++) W().frame(1); };
const J = () => W().tap('attack'), K = () => W().tap('heavy'), L = () => W().tap('roll');
const R = {
  'sns|1|J J J J': () => { free(); J(); nextLate('sh_1'); J(); nextLate('sh_2'); J(); nextLate('sh_3'); J(); nextLate('sh_4'); },
  'sns|1|J K J J (jab)': () => { free(); J(); nextLate('sh_1'); K(); nextLate('sh_jab'); J(); nextLate('sh_3'); J(); nextLate('sh_4'); },
  'sns|1|J J J K (rim upper)': () => { free(); J(); nextLate('sh_1'); J(); nextLate('sh_2'); J(); nextLate('sh_3'); K(); nextLate('sh_rim'); },
  'sns|2|J J . J (wheel)': () => { free(); J(); nextLate('sh_1'); J(); nextLate('sh_2', 0); for (let i = 0; i < 20 && st() === 'sh_2'; i++) W().frame(1); W().frame(8); J(); nextLate('sh_wheel'); },
  'sns|2|perfect rush J J K': () => { free(); J(); nextLate('sh_1'); J(); nextLate('sh_2'); K(); nextLate('sh_prush'); },
  'sns|1|L -> J (leap)': () => { idle(); L(); W().frame(9); J(); nextLate('sh_leap'); },
  'sns|1|L -> K (shield charge)': () => { idle(); L(); W().frame(9); K(); nextLate('sh_charge'); },
  'spear|1|J J J': () => { free(); J(); nextLate('sp_1'); J(); nextLate('sp_2'); J(); nextLate('sp_3'); },
  'spear|1|J J J K (drive)': () => { free(); J(); nextLate('sp_1'); J(); nextLate('sp_2'); J(); nextLate('sp_3'); K(); nextLate('sp_drive'); },
  'spear|2|J J . J (wheel)': () => { free(); J(); nextLate('sp_1'); J(); nextLate('sp_2', 0); for (let i = 0; i < 25 && st() === 'sp_2'; i++) W().frame(1); W().frame(8); J(); nextLate('sp_wheel'); },
  'spear|1|L -> K (hop lunge)': () => { idle(); L(); W().frame(10); K(); nextLate('sp_hoplunge'); },
  'spear|1|guard poke loop (I + J)': () => { if (!E('held.has("parry")')) { W().down('parry'); W().frame(6); } J(); W().frame(5); for (let i = 0; i < 40 && st() === 'sp_gpoke'; i++) W().frame(1); },
  'spear|1|charge dash, quick release': () => { idle(); W().down('right'); W().down('heavy'); W().frame(26); W().up('heavy'); W().up('right'); idle(); },
  'spear|1|charge dash, 0.4 s run': () => { idle(); W().down('right'); W().down('heavy'); W().frame(51); W().up('heavy'); W().up('right'); idle(); },
};
const out = [];
for (const [key, fn] of Object.entries(R)) {
  const [type, rank, name] = key.split('|');
  for (const real of [false, true]) {
    W().reset(type, +rank); arena(); W().reset(type, +rank); const far = type === 'spear' ? 44 : 26;
    if (!real) E('D.maxSt = 1e6; P.st = 1e6'); W().dummy(far); E('window.__wm.follow = ' + far);
    W().log = []; const t0 = W().ms; let used = 0, n = 0;
    while (W().ms - t0 < (real ? 6000 : 10000) && n < 60) { const s0 = G.P.st; fn(); n++; if (!real) E('P.st = 1e6; if (P.x > 330) P.x -= 200'); else { used += Math.max(0, s0 - G.P.st); E('if (P.x > 330) P.x -= 200'); if (G.P.st <= 5) break; } }
    W().up('parry'); idle();
    const secs = (W().ms - t0) / 1000, dmg = W().log.filter(h => h.melee || !real).reduce((a, h) => a + h.dmg / h.light, 0);
    if (!real) out.push({ route: `${type} ${name}`, rank: +rank, dps: +(dmg / secs).toFixed(2), loops: n, perLoop: +(dmg / n).toFixed(2), poisePerS: +(W().log.reduce((a, h) => a + h.poise, 0) / secs).toFixed(0) });
    else Object.assign(out[out.length - 1], { realStamSecs: +secs.toFixed(1), stamPerS: +(used / secs).toFixed(1) });
  }
}
// ---- the same against a real boss in the Training Grounds (Gravetusk, held in place; god mode): does each new move connect?
const boss = [];
G.trn.start(); W().frame(10);
for (const [type, rank, ids, play] of [
  ['sns', 2, ['sh_jab', 'sh_rim', 'sh_wheel', 'sh_charge'], () => { J(); toLate(); K(); nextLate('sh_jab'); J(); nextLate('sh_3'); K(); nextLate('sh_rim'); idle(); J(); toLate(); J(); nextLate('sh_2', 0); for (let i = 0; i < 20 && st() === 'sh_2'; i++) W().frame(1); W().frame(8); J(); nextLate('sh_wheel'); idle(); L(); W().frame(9); K(); nextLate('sh_charge'); idle(); }],
  ['spear', 3, ['sp_drive', 'sp_wheel', 'sp_hoplunge'], () => { J(); toLate(); J(); nextLate('sp_2'); J(); nextLate('sp_3'); K(); nextLate('sp_drive'); idle(); J(); toLate(); J(); nextLate('sp_2', 0); for (let i = 0; i < 25 && st() === 'sp_2'; i++) W().frame(1); W().frame(8); J(); nextLate('sp_wheel'); idle(); L(); W().frame(10); K(); nextLate('sp_hoplunge'); idle(); }],
]) {
  W().reset(type, rank); G.SETTINGS.god = 1; G.trn.summon('hound'); W().frame(5); W().reset(type, rank); E('D.maxSt = 1e6; P.st = 1e6'); const b = G.boss;
  for (let i = 0; i < 200 && !b.active; i++) W().frame(1);
  b.active = true; const bx = b.x; b.update = function (dt) { this.x = bx; this.state = 'idle'; if (this.commonUpdate) this.commonUpdate(dt); };
  const got = {}; const oh = b.hit; b.hit = function (info) { got[G.P.state] = (got[G.P.state] || 0) + 1; return oh.call(this, info); };
  E(`P.x = ${bx} - ${type === 'spear' ? 50 : 30}; P.face = 1; P.vx = 0`); W().frame(2);
  play();
  boss.push({ type, hits: got, missing: ids.filter(i => !got[i]) });
  b.hit = oh; G.SETTINGS.god = 0;
}
return { routes: out, boss };
