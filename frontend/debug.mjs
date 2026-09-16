import puppeteer from 'puppeteer';

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
  
  try {
    await page.goto('http://localhost:3000/playground', { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 2000));
  } catch (err) {
    console.error('Error navigating:', err);
  }
  
  await browser.close();
})();
