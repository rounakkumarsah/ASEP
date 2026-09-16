const puppeteer = require('puppeteer');

(async () => {
  console.log("Launching Puppeteer...");
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: "new"
    });
  } catch (err) {
    console.error("Launch failed:", err);
    process.exit(1);
  }

  const page = await browser.newPage();
  
  page.on('pageerror', err => {
    console.log('PAGE ERROR:', err.message);
  });
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('CONSOLE ERROR:', msg.text());
    }
  });

  console.log("Navigating to production site...");
  await page.goto('https://asep-ai.vercel.app/playground?projectId=b8412164-8477-44ad-9d3c-c529fc07490c&projectName=E-Commerce+Backend+Refactor', { waitUntil: 'networkidle0', timeout: 15000 });
  
  await page.waitForTimeout(3000);
  
  const content = await page.content();
  console.log("Checking if error boundary is visible...");
  
  if (content.includes("Playground Runtime Error") || content.includes("Global App Error")) {
    console.log("YES! The diagnostic error boundary was rendered.");
    
    // Extract the exact error text from the page
    const errorText = await page.evaluate(() => {
      const el = document.querySelector('.text-red-400') || document.querySelector('.text-red-500');
      const stack = document.querySelectorAll('pre');
      const details = document.querySelector('.text-red-400.font-bold') || document.querySelector('.text-sm.text-red-400.font-mono');
      
      return {
        header: el ? el.innerText : "Not found",
        details: details ? details.innerText : "No details",
        stack1: stack.length > 0 ? stack[0].innerText : "No stack",
        stack2: stack.length > 1 ? stack[1].innerText : "No component stack"
      };
    });
    
    console.log("=== EXACT ERROR EXTRACTED FROM PAGE ===");
    console.log("HEADER:", errorText.header);
    console.log("DETAILS:", errorText.details);
    console.log("STACK 1:", errorText.stack1);
    console.log("STACK 2:", errorText.stack2);
    console.log("=====================================");
  } else if (content.includes("Something went wrong!")) {
    console.log("STILL SHOWING OLD ERROR BOUNDARY.");
  } else {
    console.log("NO ERROR BOUNDARY FOUND! Page might be working.");
  }
  
  await browser.close();
})();
