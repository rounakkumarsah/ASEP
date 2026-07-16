import { test, expect } from '@playwright/test';
import { LoginPage } from './pom/login-page';
import { DashboardPage } from './pom/dashboard-page';

// Bypassing global authenticated storageState to test authentication mechanics
test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Authentication Flow', () => {
  test('redirects unauthenticated users visiting protected pages', async ({ page }) => {
    await page.goto('/overview');
    // Shoud redirect to login page with redirect URL param
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
    await loginPage.login('admin', 'password');
    await expect(page).toHaveURL(/\/overview/);
    
    // Verify user can log out
    await dashboardPage.logout();
    await expect(page).toHaveURL(/\/login/);
  });
});
