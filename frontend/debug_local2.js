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
    await page.goto('http://localhost:3000/playground', { waitUntil: 'networkidle2' });
  } catch (e) {
    console.log("Navigation error:", e.message);
  }
  
  await new Promise(r => setTimeout(r, 2000));
  
  console.log("Current URL:", page.url());
  const html = await page.content();
  console.log("HTML length:", html.length);
  console.log("Includes 'Something went wrong':", html.includes("Something went wrong"));
  
  await browser.close();
})();
