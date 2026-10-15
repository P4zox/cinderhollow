// the soul wisps / Reap / charge in a dark room (the boss arena C5, boss parked): snapshots + screen positions
const out = [];
W().reset('scythe', 1); delete G.SAVE.flags['boss:hound']; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'hound'] = 1;
G.tp('C5', 6, 10); W().frame(30); E('if (boss) { boss.active = false; } enemies = []');
const sh = async (name) => { E('hitstop = 0'); G.step(0); await snap(name); out.push({ name, st: G.P.state, t: Math.round(E('P.mvT') || 0), sc: E('[(P.x - cam.x) * scale + ox, (P.y - cam.y) * scale + oy, scale, P.face]') }); };
W().reset('scythe', 1); E('P.scySouls = 1'); W().frame(20); await sh('dark_souls1');
E('P.scySouls = 3'); W().frame(37); await sh('dark_souls3');
W().down('heavy'); W().frame(4); for (let i = 0; i < 40 && G.P.state !== 'scy_reap'; i++) W().frame(1); W().frame(6); await sh('dark_reap_windup');
for (let i = 0; i < 40 && E('P.mvT') < 330; i++) W().frame(1); W().up('heavy'); await sh('dark_reap'); W().frame(60);
W().reset('scythe', 1); E('P.scySouls = 0'); W().down('heavy'); W().frame(50); await sh('dark_charge'); W().up('heavy'); for (let i = 0; i < 40 && E('P.mvT') < 260; i++) W().frame(1); await sh('dark_charged'); W().frame(60);
W().reset('scythe', 1); E('P.scySouls = 2'); W().tap('attack', 2); for (let i = 0; i < 40 && E('P.mvT') < 175; i++) W().frame(1); await sh('dark_scy1');
return out;
