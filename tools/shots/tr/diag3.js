await new Promise(r=>setTimeout(r,300));
const T = G.trn, out = []; T.start(); G.step(5);
for (const k of ['hound','champion']) {
T.summon(k); G.step(30); const B = G.boss;
out.push(`${k} active=${B.active} state=${B.state} hp=${B.hp} tg=${T.targets.map(t=>t.kind||t.type).join(',')} Px=${G.P.x}`);
for (let i = 0; i < 5; i++) { for (const t of T.targets) t.hit({ dmg: 999999, poise: 0, dir: 1, kind: 'light', x: t.x, y: t.y - 20 }); G.step(10); out.push(` hp=${B.hp} state=${B.state} alive=${B.alive} ph=${B.phase} pend=${B.pendingPhase}`); }
}
return out;
