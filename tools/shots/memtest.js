// node memtest.js <html-or-url>: boots the game, visits rooms, reports total Chrome RSS (MB)
const puppeteer = require('puppeteer-core'); const { execSync } = require('child_process'); const path = require('path');
(async () => {
  const H = process.argv[2]; const url = /^https?:/.test(H) ? H : 'file://' + path.resolve(H);
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new', args: ['--mute-audio'] });
  const pid = browser.process().pid;
  const rss = () => { const out = execSync(`ps -A -o pid=,ppid=,rss=`).toString().trim().split('\n').map(l => l.trim().split(/\s+/).map(Number));
    const kids = new Set([pid]); let grew = true; while (grew) { grew = false; for (const [p, pp] of out) if (kids.has(pp) && !kids.has(p)) { kids.add(p); grew = true; } }
    return Math.round(out.filter(([p]) => kids.has(p)).reduce((a, [, , r]) => a + r, 0) / 1024); };
  const page = await browser.newPage(); await page.setViewport({ width: 1152, height: 648 });
  const t0 = Date.now(); await page.goto(url); await page.waitForFunction('window.__game && window.__game.state === "title"', { timeout: 60000 }); const tBoot = Date.now() - t0;
  await new Promise(r => setTimeout(r, 2000)); const mTitle = rss();
  await page.evaluate(async () => { const G = window.__game; G.newGame(); await new Promise(r => setTimeout(r, 800));
    for (let i = 0; i < 300 && G.state !== 'play'; i++) { if (G.state === 'cine' || G.state === 'cut') G.step(1, [], ['pause']); else G.step(10); }
    for (const [r, x, y] of [['R2', 5, 10], ['C5', 6, 10], ['K4', 6, 10], ['SP7', 46, 15], ['D8', 46, 14], ['X5', 6, 10], ['A6', 3, 14], ['HF7', 4, 13]]) { G.tp(r, x, y); for (let i = 0; i < 20; i++) { G.step(6, ['right']); if (G.state === 'cut') G.step(1, [], ['pause']); G.P.hp = 9999; } await new Promise(r => setTimeout(r, 300)); } });
  await new Promise(r => setTimeout(r, 2000)); const mPlay = rss();
  console.log(JSON.stringify({ bootMs: tBoot, rssTitleMB: mTitle, rssAfterRoomsMB: mPlay }));
  await browser.close();
})();
