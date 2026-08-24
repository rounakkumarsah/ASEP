import { test as setup, expect } from '@playwright/test';
import { LoginPage } from './pom/login-page';
import { STORAGE_STATE } from '../playwright.config';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
const E2E_EMAIL = 'e2e_admin@playwright.test';
const E2E_PASSWORD = 'Playwright$Test123!';

setup('authenticate user and save storage state', async ({ page, request }) => {
  await page.addInitScript(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).__PLAYWRIGHT_TEST__ = true;
  });

  // Seed or refresh the E2E test user (email already verified, rate limit cleared)
  // This endpoint is only active in development/test environments
  const seedRes = await request.post(`${API_URL}/api/v1/auth/e2e/seed-user`, {
    data: {
      email: E2E_EMAIL,
      password: E2E_PASSWORD,
      firstName: 'E2E',
      lastName: 'Admin',
    },
  });

  // Accept 200 (created/updated) or 409 (already exists — still ok)
  expect(
    seedRes.status() === 200 || seedRes.status() === 201 || seedRes.status() === 204,
    `Seed user failed with status ${seedRes.status()}: ${await seedRes.text()}`,
  ).toBeTruthy();

  // Login via UI
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login(E2E_EMAIL, E2E_PASSWORD);
  await page.waitForURL(/\/overview/, { timeout: 20000 });

  // Persist cookies/localStorage for authenticated tests
  await page.context().storageState({ path: STORAGE_STATE });
});

