const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  const errors = [];
  page.on('pageerror', err => {
    console.log('PAGE ERROR:', err.message);
    errors.push(err.message);
  });
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('CONSOLE ERROR:', msg.text());
      errors.push(msg.text());
    }
  });
  
  try {
    await page.goto('http://localhost:3001/playground', { waitUntil: 'load', timeout: 5000 });
  } catch(e) {}
  
  await page.waitForTimeout(3000);
  
  if (errors.length === 0) {
    console.log('No errors captured.');
  }
  
  await browser.close();
})();
