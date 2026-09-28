await boot();
const S = G.sk.SKILLS, by = G.sk.SKILL_BY, bad = [];
for (const s of S) { for (const r of s.req) if (!by[r]) bad.push(s.id + ' req ' + r); for (const r of s.excl) if (!by[r] || !by[r].excl.includes(s.id)) bad.push(s.id + ' excl ' + r); }
const ids = new Set(); for (const s of S) { if (ids.has(s.id)) bad.push('dup ' + s.id); ids.add(s.id); }
// min distance between nodes on the constellation
let md = 99, mp = ''; const main = S.filter(s => s.br !== 'arsenal');
for (let i = 0; i < main.length; i++) for (let j = i + 1; j < main.length; j++) { const d = Math.hypot(main[i].x - main[j].x, main[i].y - main[j].y); if (d < md) { md = d; mp = main[i].id + '/' + main[j].id; } }
const cost = {}; for (const s of S) cost[s.br] = (cost[s.br] || 0) + s.cost;
const learnable = {}; for (const s of S) { if (s.excl.length && s.excl[0] < s.id) continue; learnable[s.br] = (learnable[s.br] || 0) + s.cost; }
// economy: shards in the world, cinders from bosses and foes
const eco = G.sk.ev(`(() => { let sh = 0, ch = 0, sc = 0; for (const r of ROOMS) { for (const k of ['items','chests']) for (const it of r[k] || []) if (it === 'shard') sh++; for (const s of r.spawns || []) if (s.kind === 'shard' || s.item === 'shard') ch++; }
  let bc = 0, bs = 0; for (const [k, b] of Object.entries(BOSS_INFO)) { bc += b.cinders || 0; if ((b.reward || []).includes('shard')) bs++; }
  let ec = 0, en = 0; for (const r of ROOMS) { for (const row of r.map) for (const c of row) if (ENEMY_CHARS[c] && ENEMY[ENEMY_CHARS[c]]) { ec += ENEMY[ENEMY_CHARS[c]].cinders; en++; } for (const s of r.spawns || []) if (s.t === 'enemy' && ENEMY[s.type]) { ec += ENEMY[s.type].cinders; en++; } }
  return { roomShards: sh, spawnShards: ch, bossShards: bs, bosses: Object.keys(BOSS_INFO).length, bossCinders: bc, foeCinders: ec, foes: en }; })()`);
return { n: S.length, bad, md: md.toFixed(2) + ' ' + mp, cost, learnable, eco };
