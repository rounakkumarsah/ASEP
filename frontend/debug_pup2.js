const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: "new" });
  const page = await browser.newPage();
  
  page.on('response', response => {
    if (!response.ok() && response.status() >= 400) {
      console.log(`FAILED RESPONSE [${response.status()}]: ${response.url()}`);
    }
  });

  page.on('requestfailed', request => {
    console.log(`REQUEST FAILED: ${request.url()} - ${request.failure()?.errorText}`);
  });

  page.on('pageerror', err => {
    console.log('PAGE ERROR (Uncaught Exception):', err.message);
  });
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('CONSOLE ERROR:', msg.text());
    }
  });

  try {
    await page.goto('https://asep-ai.vercel.app/playground?projectId=b8412164-8477-44ad-9d3c-c529fc07490c&projectName=E-Commerce+Backend+Refactor', { waitUntil: 'networkidle2', timeout: 15000 });
  } catch (e) {
    console.log("Navigation error:", e.message);
  }
  
  await page.waitForTimeout(3000);
  const content = await page.content();
  
  const extract = await page.evaluate(() => {
      const el = document.querySelector('.text-red-400') || document.querySelector('.text-red-500') || document.querySelector('h1');
      const stack = document.querySelectorAll('pre');
      return {
        header: el ? el.innerText : "No header",
        stack1: stack.length > 0 ? stack[0].innerText : "No stack"
      };
  });
  console.log("EXTRACTED:", extract);
  
  await browser.close();
})();
