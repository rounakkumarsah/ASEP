import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.getByLabel('Email', { exact: true });
    this.passwordInput = page.getByLabel('Password', { exact: true });
    this.submitButton = page.getByRole('button', { name: 'Sign In' });
    this.errorMessage = page.locator('text=Invalid username or password');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectLoginError() {
    await expect(this.errorMessage).toBeVisible();
  }

  async expectValidationErrors() {
    await expect(this.page.locator('text=Username or email must be at least 3 characters')).toBeVisible();
    await expect(this.page.locator('text=Password must be at least 6 characters')).toBeVisible();
  }
}
