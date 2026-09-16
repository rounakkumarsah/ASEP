const { chromium } = require('playwright');

(async () => {
  console.log("Launching browser...");
  let browser;
  try {
    browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
    });
  } catch (err) {
    console.error("Failed to launch Playwright browser:", err.message);
    process.exit(1);
  }

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
  
  console.log("Navigating to production Playground...");
  try {
    await page.goto('https://asep-ai.vercel.app/playground?projectId=b8412164-8477-44ad-9d3c-c529fc07490c&projectName=E-Commerce+Backend+Refactor', { waitUntil: 'networkidle2', timeout: 15000 });
  } catch(e) {
    console.log("Navigation timeout or error:", e.message);
  }
  
  console.log("Waiting 3 seconds for React hydration...");
  await page.waitForTimeout(3000);
  
  const content = await page.content();
  console.log("Checking if error boundary is visible...");
  
  if (content.includes("Playground Runtime Error")) {
    console.log("YES! The diagnostic error boundary was rendered.");
    
    // Extract the exact error text from the page
    const errorText = await page.evaluate(() => {
      const el = document.querySelector('.text-red-400.font-mono');
      const stack = document.querySelectorAll('pre');
      return {
        message: el ? el.innerText : "Not found",
        stack1: stack.length > 0 ? stack[0].innerText : "No stack",
        stack2: stack.length > 1 ? stack[1].innerText : "No component stack"
      };
    });
    
    console.log("=== EXACT ERROR EXTRACTED FROM PAGE ===");
    console.log("MESSAGE:", errorText.message);
    console.log("STACK:", errorText.stack1);
    console.log("COMPONENT STACK:", errorText.stack2);
    console.log("=====================================");
  } else if (content.includes("Something went wrong!")) {
    console.log("STILL SHOWING OLD ERROR BOUNDARY.");
  } else {
    console.log("NO ERROR BOUNDARY FOUND! Page might be working.");
  }
  
  if (errors.length === 0) {
    console.log('No console errors captured.');
  }
  
  await browser.close();
})();
