// progression costs: points every 3 levels, skill prices rise every 15 learned, paid prices stick, level costs ramp
await boot(); const E = G.sk.ev, out = [];
const st = lv => { const b = E('({...BASE_STATS})'), o = ['vig','str','dex','end']; for (let i = 0; i < lv - E('levelOf(BASE_STATS)'); i++) b[o[i % 4]]++; return b; };
for (const [lv, sh] of [[40, 20], [83, 45], [83, 71], [120, 71]]) {
  G.give({ stats: st(lv), skills: [] }); G.SAVE.shards = sh;
  let n = 0; for (let guard = 0; guard < 200; guard++) {   // buy the cheapest learnable skill until nothing is affordable
    const c = E("SKILLS.filter(s => skillLearnable(s.id).ok).sort((a, b) => a.cost - b.cost)[0]"); if (!c) break;
    E(`learnSkill('${c.id}')`); n++;
  }
  out.push(`L${lv} + ${sh} shards: ${E('skillBudget()')} points -> ${n}/${E('skillMaxLearnable()')} skills, left ${E('skillPoints()')}, next price +${Math.floor(n / 15)}`);
}
const s0 = E('SAVE.skills[0]'), s20 = E('SAVE.skills[20]');
out.push(`paid prices kept: 1st ${E(`SKILL_BY['${s0}']._base`)}->${E(`SKILL_BY['${s0}'].cost`)}, 21st ${E(`SKILL_BY['${s20}']._base`)}->${E(`SKILL_BY['${s20}'].cost`)}`);
out.push('level costs L5/L20/L40/L80: ' + [5, 20, 40, 80].map(L => E(`levelCost(${L})`)).join(' / '));
G.SAVE.skills = []; E("menu = { screen: 'tree', br: 0, t: 0, prev: null }; state = 'menu'; stOpen(menu)"); G.step(3); await snap('tree');
return out;
