// v15 run lean in game: the knight running right with each of the 9 weapon overlays (snap + player screen box)
await boot(); G.SETTINGS.god = 1; G.giveArmory();
Object.assign(G.SETTINGS, { shaders: 0 });
const E = G.sk.ev, o = [];
for (const w of ['longsword', 'katana', 'greatsword', 'maul', 'knight_shield', 'twinfangs', 'spear', 'quarterstaff', 'headsman_chain']) {
  G.tp('R2', 6, 10); G.step(40); E('regionCard = null; enemies.length = 0');
  G.SAVE.weapon = w; E(`(() => { try { if (typeof wsEquip === 'function') wsEquip('${w}'); } catch (e) {} })()`);
  for (let i = 0; i < 4; i++) {
    G.step(i ? 3 : 20, ['right']);
    const s = E('[Math.round((P.x - cam.x) * scale + ox), Math.round((P.y - cam.y) * scale + oy), scale, P.anim.tag, P.anim.frame]');
    await snap(`run_${w}_${i}`); o.push(`${w} ${i} ${JSON.stringify(s)}`);
  }
}
return o;
