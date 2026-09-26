await boot(); G.give({ items: { talon: 1 } }); G.SAVE.flags['cut:warden'] = 1;
G.tp('TV8', 12, 10); G.step(5);
for (let i = 0; i < 200 && !(G.boss && G.boss.active); i++) G.step(2, ['right']);
const b = G.boss; G.step(200);
const out = {};
async function trial(m, dist, action) {
  b.x = 22 * 16; b.state = 'idle'; b.cool = 99; b.hidden = false; G.P.x = b.x + dist; G.P.y = 176; G.P.vx = 0; G.P.hp = 999; G.step(3);
  b.face = 1; b.begin(m); let hit = false, did = false, last = 999;
  for (let i = 0; i < 200; i++) {
    const tel = b.sh.meta.telegraph[b.anim.tag];
    let hold = [], tap = [];
    if (!did && ((tel && b.anim.tag === (m === 'sink' ? 'rise' : m) && b.anim.i >= tel.frame && (b.anim.i > tel.frame || b.anim.t > 90)) || (m === 'charge' && b.state === 'charge'))) { did = true; if (action === 'rollin') { tap = ['roll']; hold = ['left']; } if (action === 'rollout') { tap = ['roll']; hold = ['right']; } if (action === 'jump') { tap = ['jump']; hold = ['jump']; } }
    if (did && action === 'runback') hold = ['left'];
    if (did && action === 'runout') hold = ['right'];
    G.step(1, hold, tap);
    if (G.P.hp < last) hit = true; G.P.hp = 999; last = 999;
    if (b.state === 'idle' && i > 20) break;
  }
  out[`${m}@${dist}:${action}`] = hit ? 'HIT' : 'safe';
}
await trial('sweep', 60, 'none'); await trial('sweep', 60, 'rollin'); await trial('sweep', 60, 'rollout');
await trial('thrust', 90, 'none'); await trial('thrust', 90, 'rollout'); await trial('thrust', 90, 'rollin');
await trial('charge', 150, 'none'); await trial('charge', 150, 'rollin'); await trial('charge', 150, 'jump');
await trial('erupt', 110, 'none'); await trial('erupt', 110, 'rollout'); await trial('erupt', 110, 'runback'); await trial('erupt', 110, 'runout'); await trial('volley', 150, 'none'); await trial('volley', 150, 'rollin');
await trial('sink', 100, 'none'); await trial('sink', 100, 'rollout');
return out;
