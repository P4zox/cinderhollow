await boot();
// ENEMY is inside the IIFE; spawn each type through the room lists and read cfg
const out = {};
const rooms = ['R1','R2','R3','R4','C1','C2','C3','C4','C6','K1','K2','K3','M1','M2','M3','M4','X1','X2','X3','X4','A1','A2','A4','A5','HF1','HF2','HF3','HF5','HF6','SP1','SP2','SP3','SP4','SP6','D1','D2','D3','D4','D6','D7','E1','E2'];
for (const r of rooms) { try { G.tp(r, 3, 3); } catch (e) { continue; } for (const e of G.enemies) { const c = e.cfg || {}; out[e.type] = out[e.type] || { hp: c.hp, cinders: c.cinders, dmg: JSON.stringify(c.dmg || c.contact || ''), rooms: [] }; if (!out[e.type].rooms.includes(r)) out[e.type].rooms.push(r); } }
return out;
