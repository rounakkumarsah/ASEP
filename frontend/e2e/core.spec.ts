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

  // Use same E2E user seeded in auth.setup.ts
  const testEmail = 'e2e_admin@playwright.test';
  const testPass = 'Playwright$Test123!';


  test('Signup - terms validation error when unchecked and clears on check', async ({ page }) => {
    const signupPage = new SignupPage(page);
    await signupPage.goto();
    await signupPage.workspaceNameInput.fill('Acme Corp');
    await signupPage.fullNameInput.fill('Terms Tester');
    await signupPage.emailInput.fill(`terms_${Date.now()}@example.com`);
    await signupPage.passwordInput.fill('SecurePass123!');
    await signupPage.confirmPasswordInput.fill('SecurePass123!');
    await page.waitForTimeout(500);

    // Do NOT check terms, click Register Account
    await signupPage.submitButton.click();

    // Verify error message is displayed and checkbox is aria-invalid
    const errorMessage = page.locator('text=You must accept the Terms of Service and Privacy Policy before creating an account.');
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
    await expect(signupPage.termsCheckbox).toHaveAttribute('aria-invalid', 'true');

    // Check the checkbox -> error message disappears immediately
    await signupPage.termsCheckbox.check();
    await expect(errorMessage).not.toBeVisible();
  });

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
      page.locator('text=already registered')
        .or(page.locator('text=already exists'))
        .or(page.locator('text=taken'))
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
    await page.waitForURL(/\/overview/, { timeout: 15000 });
    await expect(page.locator('header').getByText('Overview', { exact: true })).toBeVisible();
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
    
    // Verify Dashboard welcome checklist is visible
    await expect(page.locator('text=Developer Workspace').first()).toBeVisible();
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
