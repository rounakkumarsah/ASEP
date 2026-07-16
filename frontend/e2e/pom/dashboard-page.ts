import { Page, Locator, expect } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly mobileMenuButton: Locator;
  readonly themeToggle: Locator;
  readonly profileMenuButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.mobileMenuButton = page.getByRole('button', { name: 'Open sidebar' });
    this.themeToggle = page.getByRole('button', { name: 'Toggle theme' });
    this.profileMenuButton = page.getByRole('button', { name: 'User profile / Logout' });
  }

  async clickSidebarLink(name: string) {
    // Select sidebar links using role or text. In desktop, sidebar links are visible.
    // In mobile, we might need to open the sidebar first if it is hidden.
    const isMobile = await this.mobileMenuButton.isVisible();
    if (isMobile) {
      await this.mobileMenuButton.click();
      // Wait for navigation links to be visible inside the sheet/dialog
      const menuTitle = this.page.getByRole('heading', { name: 'Navigation Menu' });
      await expect(menuTitle).toBeAttached();
    }
    
    // Locate the link inside nav structure and click it
    const link = this.page.getByRole('link', { name }).first();
    await link.click();
  }

  async logout() {
    this.page.once('dialog', async (dialog) => {
      await dialog.accept();
    });
    await this.profileMenuButton.click();
  }

  async toggleTheme() {
    await this.themeToggle.click();
  }

  async expectPageTitle(title: string) {
    const heading = this.page.locator('header').getByRole('heading', { name: title, exact: true });
    await expect(heading).toBeVisible();
  }
}
