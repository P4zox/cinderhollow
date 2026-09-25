const puppeteer = require('puppeteer-core'); const { execSync } = require('child_process'); const path = require('path');
(async () => {
  const H = process.argv[2]; const url = H === 'blank' ? 'about:blank' : /^https?:/.test(H) ? H : 'file://' + path.resolve(H);
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new', args: ['--mute-audio'] });
  const pid = browser.process().pid;
  const page = await browser.newPage(); await page.setViewport({ width: 1152, height: 648 });
  await page.goto(url); if (H !== 'blank') await page.waitForFunction('window.__game && window.__game.state === "title"', { timeout: 60000 });
  await new Promise(r => setTimeout(r, 2500));
  const out = execSync(`ps -A -o pid=,ppid=,rss=,command=`).toString().trim().split('\n').map(l => { const m = l.trim().match(/^(\d+)\s+(\d+)\s+(\d+)\s+(.*)$/); return m && [+m[1], +m[2], +m[3], m[4]]; }).filter(Boolean);
  const kids = new Set([pid]); let grew = true; while (grew) { grew = false; for (const [p, pp] of out) if (kids.has(pp) && !kids.has(p)) { kids.add(p); grew = true; } }
  const rows = out.filter(([p]) => kids.has(p)).map(([p, , r, c]) => [Math.round(r / 1024), (c.match(/--type=([\w-]+)/) || [, 'browser'])[1]]);
  const heap = H === 'blank' ? 0 : await page.evaluate(() => Math.round(performance.memory.usedJSHeapSize / 1e6));
  console.log(H.slice(-30), JSON.stringify(rows), 'jsHeapMB', heap);
  await browser.close();
})();
