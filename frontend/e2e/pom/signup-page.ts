import { Page, Locator, expect } from '@playwright/test';

export class SignupPage {
  readonly page: Page;
  readonly workspaceNameInput: Locator;
  readonly fullNameInput: Locator;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly confirmPasswordInput: Locator;
  readonly termsCheckbox: Locator;
  readonly submitButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.workspaceNameInput = page.getByLabel('Workspace Name', { exact: true });
    this.fullNameInput = page.getByLabel('Full Name', { exact: true });
    this.emailInput = page.getByLabel('Work Email', { exact: true });
    this.passwordInput = page.getByLabel('Password', { exact: true });
    this.confirmPasswordInput = page.getByLabel('Confirm Password', { exact: true });
    this.termsCheckbox = page.locator('#acceptTerms');
    this.submitButton = page.getByRole('button', { name: 'Register Account' });
  }

  async goto() {
    await this.page.goto('/signup');
  }

  async signup(firstName: string, lastName: string, email: string, pass: string) {
    await this.workspaceNameInput.fill('Acme Corp');
    await this.fullNameInput.fill(`${firstName} ${lastName}`);
    await this.emailInput.fill(email);
    await this.passwordInput.fill(pass);
    await this.confirmPasswordInput.fill(pass);
    
    await this.termsCheckbox.check();
    await this.page.waitForTimeout(1000);
    
    await this.submitButton.click();
  }
}
