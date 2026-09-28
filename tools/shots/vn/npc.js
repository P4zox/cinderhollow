// Sister Venn NPC in her shrine rooms (agent VN).  SHOT_HTML=web/dist/vn.html node tools/shots/shot.js tools/shots/vn/npc.js <out>
await boot();
const out = [];
const shotAt = async (rid, name, flags) => {
  Object.assign(G.SAVE.flags, flags || {});
  G.tp(rid, 5, 10); G.step(20);
  const v = G.props.find(p => p.type === 'npc' && p.id === 'venn');
  if (!v) { out.push(rid + ': no venn'); return; }
  G.tp(rid, Math.round((v.x - 72) / 16), Math.round(v.y / 16) - 1);
  G.step(240); G.step(6, ['right']); G.step(30);          // let the region card fade, face her
  out.push(`${rid}: venn at ${Math.round(v.x)},${Math.round(v.y)} player ${Math.round(G.P.x)},${Math.round(G.P.y)} anim=${v.anim && v.anim.tag}`);
  await snap(name + '_idle');
};
await shotAt('R1', 'npc_r1');
await shotAt('C4', 'npc_c4', { 'boss:hound': 1 });
await shotAt('X4', 'npc_x4', { 'boss:hound': 1, 'boss:omen': 1 });
return out;
