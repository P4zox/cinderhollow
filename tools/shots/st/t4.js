await boot(); const o = [];
const settle = (n = 30) => { for (let i = 0; i < n; i++) G.step(1); };
const view = document.getElementById('game'), par = view.parentElement;
const S = G.SAVE; S.skills = ['keen_edge','heavy_hand','fourth_strike','quickstep']; S.shards = 8;
for (const [w, h, nm] of [[800, 450, 's2'], [640, 360, 's167']]) {
  par.style.width = w + 'px'; par.style.height = h + 'px'; window.dispatchEvent(new Event('resize')); await new Promise(r => setTimeout(r, 100));
  G.st.open(0); settle(); await snap('n_' + nm + '_mid'); G.st.zoom(-1); settle(); await snap('n_' + nm + '_over'); G.st.zoom(1); G.st.zoom(1); settle(); await snap('n_' + nm + '_close');
  o.push(nm + ' zooms ' + JSON.stringify(G.st.ST.cam));
}
return o;
