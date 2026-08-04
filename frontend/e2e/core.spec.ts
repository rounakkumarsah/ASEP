import { test, expect } from '@playwright/test';
import { LoginPage } from './pom/login-page';
import { SignupPage } from './pom/signup-page';
import { DashboardPage } from './pom/dashboard-page';

// Bypassing global authenticated storageState for unauthenticated tests
test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Authentication and Core Flows', () => {

  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (window as any).__PLAYWRIGHT_TEST__ = true;
    });
  });

  const testEmail = `admin@example.com`;
  const testPass = 'SecurePass123!';

  test('Signup - successful registration', async ({ page }) => {
    const freshSignupEmail = `test_${Date.now()}@example.com`;
    const signupPage = new SignupPage(page);
    await signupPage.goto();
    await signupPage.signup('Test', 'User', freshSignupEmail, testPass);
    await page.waitForURL(/\/verify-email/, { timeout: 15000 });
    expect(page.url()).toMatch(/\/verify-email/);
  });

  test('Signup - username uniqueness', async ({ page }) => {
    // Try to signup with same username again
    const signupPage = new SignupPage(page);
    await signupPage.goto();
    await signupPage.signup('Test2', 'User2', 'admin@example.com', 'SecurePass123!');
    await expect(
      page.locator('text=Username already taken')
        .or(page.locator('text=User with this email or username already exists'))
        .or(page.locator('text=Email address already registered'))
    ).toBeVisible({ timeout: 15000 });
  });

  test('Login - successful login and Session Refresh', async ({ page }) => {
    const loginPage = new LoginPage(page);
    
    // Attempt login
    await loginPage.goto();
    await loginPage.login(testEmail, testPass);
    await page.waitForURL(/\/overview/, { timeout: 15000 });
    
    // Refresh Session
    await page.reload();
    await expect(page).toHaveURL(/\/overview/);
    await expect(page.getByRole('heading', { name: 'Overview', exact: false })).toBeVisible();
  });

  test('Zero-data Fresh Account & Dashboard Empty States', async ({ page }) => {
    const uniq = Date.now();
    const freshEmail = `fresh_${uniq}@example.com`;
    
    const signupPage = new SignupPage(page);
    await signupPage.goto();
    await signupPage.signup('Fresh', 'User', freshEmail, testPass);
    
    await page.waitForURL(/\/verify-email/, { timeout: 15000 });
    
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(freshEmail, testPass);
    await page.waitForURL(/\/overview/, { timeout: 15000 });
    
    // Verify Dashboard empty states
    await expect(page.locator('text=0').first()).toBeVisible();
    await expect(page.locator('text=No recent activity')).toBeVisible();
  });

  test('Logout and Route Validation', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(testEmail, testPass);
    await page.waitForURL(/\/overview/, { timeout: 15000 });

    const dashboardPage = new DashboardPage(page);
    await dashboardPage.logout();
    await expect(page).toHaveURL(/\/login/);

    // Route Validation: Try to access protected route after logout
    await page.goto('/overview');
    await expect(page).toHaveURL(/\/login/);
  });
});
