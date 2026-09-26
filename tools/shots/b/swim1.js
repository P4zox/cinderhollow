await boot();
G.give({ items: { hook: 1, talon: 1 } });
const out = [];
const S = () => { const p = G.P; return { x: Math.round(p.x), y: Math.round(p.y), s: p.state, a: p.anim.tag, vx: Math.round(p.vx), vy: Math.round(p.vy), br: +window.__db.DBS.breath.toFixed(1), hp: Math.round(p.hp) }; };
G.tp('DB2', 32, 9); G.step(30);
out.push(['start', S()]);
await snap('s01_db2_start');
// walk west into the water
G.step(40, ['left']); out.push(['walked', S()]);
G.step(60); out.push(['floating', S()]);
await snap('s02_floating');
G.step(60, ['left']); out.push(['paddle west vs tide', S()]);
G.step(60, ['down']); out.push(['try dive', S()]);
await snap('s03_nodive');
// jump out by the wall
G.step(1, [], ['jump']); G.step(30, ['right']); out.push(['jumped out', S()]);
await snap('s04_out');
// tidebreath: dive
G.give({ items: { hook: 1, talon: 1, tidebreath: 1 } });
G.tp('DB2', 32, 9); G.step(20);
G.step(40, ['left']); G.step(30);
G.step(50, ['down', 'left']); out.push(['diving', S()]);
await snap('s05_dive');
G.step(200, ['left']); out.push(['swim west deep', S()]);
await snap('s06_deep');
G.step(500, ['down']); out.push(['drain', S()]);
await snap('s07_drown');
G.step(200, ['up']); out.push(['surface', S()]);
await snap('s08_surface');
return out;
