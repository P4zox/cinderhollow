const puppeteer = require('puppeteer-core'); const path=require('path');
(async () => { const b = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new' });
 const p = await b.newPage(); const errs=[]; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type()==='error') errs.push(m.text()); });
 await p.goto('file://' + path.resolve(process.argv[2])); await new Promise(r=>setTimeout(r,8000)); console.log(errs.slice(0,8).join('\n')); await b.close(); })();
