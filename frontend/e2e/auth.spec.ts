import { test, expect } from '@playwright/test';
import { LoginPage } from './pom/login-page';
import { DashboardPage } from './pom/dashboard-page';

// Bypassing global authenticated storageState to test authentication mechanics
test.use({ storageState: { cookies: [], origins: [] } });

// Use the same E2E user that auth.setup.ts seeds
const E2E_EMAIL = 'e2e_admin@playwright.test';
const E2E_PASSWORD = 'Playwright$Test123!';

test.describe('Authentication Flow', () => {
  test('redirects unauthenticated users visiting protected pages', async ({ page }) => {
    await page.goto('/overview');
    // Should redirect to login page with redirect URL param
    await expect(page).toHaveURL(/\/login\?redirect=%2Foverview/);
  });

  test('validates minimum input requirements', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    
    // Attempt login with empty credentials to trigger react-hook-form validation
    await loginPage.login('ab', '12345');
    await loginPage.expectValidationErrors();
  });

  test('handles invalid login credentials', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    
    await loginPage.login('wrong-admin', 'wrong-password');
    await loginPage.expectLoginError();
  });

  test('signs in successfully with valid credentials and logs out', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);
    
    await loginPage.goto();
    await loginPage.login(E2E_EMAIL, E2E_PASSWORD);
    await expect(page).toHaveURL(/\/overview/, { timeout: 15000 });
    
    // Verify user can log out
    await dashboardPage.logout();
    await expect(page).toHaveURL(/\/login/, { timeout: 15000 });
  });
});

