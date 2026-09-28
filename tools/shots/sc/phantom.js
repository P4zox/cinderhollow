// phantom-damage check: in every SC room, stand 3 s on every standable cell (foes removed, god mode off) and report any
// HP loss or respawn jump. Rooms are entered once (by tp from the previous room, so leftover region state would show);
// inside a room the player is moved by position only.
await boot(); G.grantTechniques(); Object.assign(G.SAVE.items, { moonstep: 1, wings: 1, talon: 1, tidebreath: 1 });
for (const f of ['boss:astrel', 'boss:first_ember', 'boss:oswin', 'sc:seal', 'sf:stair']) G.SAVE.flags[f] = 1;
G.SETTINGS.god = 0;
const ROOMS_SC = __ROOMS__, PART = __PART__, NPARTS = __NPARTS__;
const SOLIDISH = '#?=B$Y12%';   // '%' veils are solid until phased
const out = [], hits = [];
let spots = 0;
for (const rid of ROOMS_SC) {
  G.tp(rid, 1, 1); G.step(2);
  const d = window.__sys.roomObj.def;
  const home = () => { for (let y = 1; y < d.h - 1; y++) for (let x = 1; x < d.w - 1; x++) if (d.map[y][x] === '.' && d.map[y - 1][x] === '.' && '#='.includes(d.map[y + 1][x])) { G.tp(rid, x, y); G.step(90); return; } };
  home();   // a safe floor cell first (tp into (1,1) can land in ceiling spikes and the hit carries over)
  for (let y = 1; y < d.h - 1; y++) for (let x = 1; x < d.w - 1; x++) {
    const c = d.map[y][x], below = d.map[y + 1][x], above = d.map[y - 1][x];
    if (SOLIDISH.includes(c) || '^v*'.includes(c) || !SOLIDISH.includes(below) || below === '1' || below === '2' || SOLIDISH.includes(above)) continue;
    if ((x + y) % NPARTS !== PART) continue;   // this run's share of the spots   // every other column in the wide rooms
    const P = G.P; P.x = x * 16 + 8; P.y = (y + 1) * 16; P.vx = P.vy = 0; P.hp = G.D.maxHp; P.inv = 0;
    let lost = 0, jumped = false;
    for (let f = 0; f < 180; f++) { G.enemies.length = 0; const h0 = P.hp; G.step(1); if (P.hp < h0) lost += h0 - P.hp; if (Math.abs(P.x - (x * 16 + 8)) > 40 || Math.abs(P.y - (y + 1) * 16) > 60) jumped = true; if (G.room !== rid) break; }
    spots++;
    if (lost > 0 || jumped) hits.push(`${rid} (${x},${y}) lost ${Math.round(lost)}${jumped ? ' moved' : ''} ${G.room !== rid ? 'left to ' + G.room : ''}`);
    if (G.room !== rid) home();
  }
}
return { spots, hits: hits.slice(0, 200), n: hits.length };
