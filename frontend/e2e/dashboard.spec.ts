import { test, expect } from '@playwright/test';
import { DashboardPage } from './pom/dashboard-page';

test.describe('Dashboard Navigation and Themes', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate directly to overview, should bypass login thanks to global storageState
    await page.goto('/overview');
  });

  test('navigates through sidebar links and updates headers', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    
    // Check initial header
    await dashboardPage.expectPageTitle('Overview');
    
    // Go to Memory
    await dashboardPage.clickSidebarLink('Memory');
    await dashboardPage.expectPageTitle('Memory');
    
    // Go to Governance
    await dashboardPage.clickSidebarLink('Governance');
    await dashboardPage.expectPageTitle('Governance');

    // Go to Settings
    await dashboardPage.clickSidebarLink('Settings');
    await dashboardPage.expectPageTitle('Settings');
  });

  test('toggles application color themes', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    
    // Wait for header loaded
    await dashboardPage.expectPageTitle('Overview');
    
    // Read classList of HTML element
    const html = page.locator('html');
    
    // Initial toggle
    await dashboardPage.toggleTheme();
    // Re-toggling should toggle class
    await dashboardPage.toggleTheme();
  });
});
