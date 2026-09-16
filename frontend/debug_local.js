const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: "new" });
  const page = await browser.newPage();
  
  page.on('pageerror', err => {
    console.log('PAGE ERROR (Uncaught Exception):', err.message);
  });
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('CONSOLE ERROR:', msg.text());
    }
  });

  try {
    await page.goto('http://localhost:3000/playground?projectId=b8412164-8477-44ad-9d3c-c529fc07490c&projectName=E-Commerce+Backend+Refactor', { waitUntil: 'networkidle2' });
  } catch (e) {
    console.log("Navigation error:", e.message);
  }
  
  await new Promise(r => setTimeout(r, 3000));
  
  const extract = await page.evaluate(() => {
      const el = document.querySelector('.text-red-400') || document.querySelector('.text-red-500') || document.querySelector('h1');
      const stack = document.querySelectorAll('pre');
      const p = document.querySelectorAll('p');
      return {
        header: el ? el.innerText : "No header",
        stack1: stack.length > 0 ? stack[0].innerText : "No stack",
        paragraphs: Array.from(p).map(p => p.innerText).join('\n')
      };
  });
  console.log("EXTRACTED:", extract);
  
  await browser.close();
})();
