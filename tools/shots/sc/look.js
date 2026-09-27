await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.items.moonstep = 1; G.SAVE.items.wings = 1; G.SAVE.items.talon = 1; G.SAVE.items.tidebreath = 1;
const spots = window.__spots || [];
const out = [];
for (const [r, x, y, tag] of SPOTS) {
  try { G.tp(r, x, y); G.step(90); G.xs.clean(); G.step(2); await snap((tag || r)); out.push(r + ' ok lights=' + G.xs.lights); }
  catch (e) { out.push(r + ' ERR ' + e.message); }
}
return out;
