import { Page, Locator, expect } from '@playwright/test';

export class SignupPage {
  readonly page: Page;
  readonly firstNameInput: Locator;
  readonly lastNameInput: Locator;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly confirmPasswordInput: Locator;
  readonly termsCheckbox: Locator;
  readonly submitButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.firstNameInput = page.getByLabel('First Name', { exact: true });
    this.lastNameInput = page.getByLabel('Last Name', { exact: true });
    this.emailInput = page.getByLabel('Email Address', { exact: true });
    this.passwordInput = page.getByLabel('Password', { exact: true });
    this.confirmPasswordInput = page.getByLabel('Confirm Password', { exact: true });
    // Handle the custom checkbox component which might hide the actual input
    this.termsCheckbox = page.getByRole('button', { name: /accept terms/i });
    if (this.termsCheckbox === undefined) {
      this.termsCheckbox = page.locator('button[role="checkbox"]');
    }
    this.submitButton = page.getByRole('button', { name: 'Register Account' });
  }

  async goto() {
    await this.page.goto('/signup');
  }

  async signup(firstName: string, lastName: string, email: string, pass: string) {
    await this.firstNameInput.fill(firstName);
    await this.lastNameInput.fill(lastName);
    await this.emailInput.fill(email);
    await this.passwordInput.fill(pass);
    await this.confirmPasswordInput.fill(pass);
    
    await this.page.locator('#acceptTerms').check();
    
    // Fallback if there is a turnstile checkbox, wait for it or assume auto-resolve in tests
    // Some tests wait a bit for Turnstile to automatically resolve in dev mode
    await this.page.waitForTimeout(1000);
    
    await this.submitButton.click();
  }
}
