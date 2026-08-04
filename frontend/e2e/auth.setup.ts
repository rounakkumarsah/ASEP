import { test as setup, expect } from '@playwright/test';
import { LoginPage } from './pom/login-page';
import { STORAGE_STATE } from '../playwright.config';

import { SignupPage } from './pom/signup-page';

setup('authenticate user and save storage state', async ({ page, request }) => {
  await page.addInitScript(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).__PLAYWRIGHT_TEST__ = true;
  });

  // Ensure user exists via API
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  await request.post(`${API_URL}/api/v1/auth/signup`, {
    data: {
      firstName: 'Admin',
      lastName: 'User',
      email: 'admin@example.com',
      password: 'SecurePass123!',
      acceptTerms: true,
      captchaToken: 'mock-turnstile-token'
    }
  });

  // Now login via UI
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('admin@example.com', 'SecurePass123!');
  await page.waitForURL(/\/overview/);
  
  // Save credentials state to local filesystem
  await page.context().storageState({ path: STORAGE_STATE });
});
