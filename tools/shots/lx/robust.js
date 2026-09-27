// LX: map bake cost in the biggest rooms, title screen, dark phase readability, context loss -> plain blit fallback
await boot(); G.SETTINGS.god = 1; const o = [];
for (const [r, x, y] of [['SF4', 14, 48], ['T1', 4, 4], ['C2', 24, 10]]) { try { G.tp(r, x, y); G.step(2); o.push(`${r}: map bake ${G.lx.LX.mapMs && G.lx.LX.mapMs.toFixed(1)} ms, map ${G.lx.LX.map.w}x${G.lx.LX.map.h} tiles`); } catch (e) { o.push(r + ' ' + e.message); } }
G.lx.setDark(6); G.step(1); await snap('robust_dark'); o.push('dark n=' + G.lx.LX.n + ' amb=' + G.lx.LX.amb.map(v => v.toFixed(2)));
G.lx.setDark(0);
const ext = G.GFX.gl.getExtension('WEBGL_lose_context'); ext.loseContext(); G.step(2); await new Promise(r => setTimeout(r, 200)); G.step(2); await snap('robust_lost'); o.push('after context loss: GFX.ok=' + G.GFX.ok + ' LX.on=' + G.lx.LX.on);
return o;
