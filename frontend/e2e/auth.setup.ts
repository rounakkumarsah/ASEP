import { test as setup, expect } from '@playwright/test';
import { LoginPage } from './pom/login-page';
import { STORAGE_STATE } from '../playwright.config';

setup('authenticate user and save storage state', async ({ page }) => {
  const loginPage = new LoginPage(page);
  
  await loginPage.goto();
  await loginPage.login('admin', 'password');
  
  // Wait for redirect to overview page
  await expect(page).toHaveURL(/\/overview/);
  
  // Save credentials state to local filesystem
  await page.context().storageState({ path: STORAGE_STATE });
});
