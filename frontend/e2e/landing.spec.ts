import { test, expect } from '@playwright/test';

// Bypassing global authenticated storageState to test the public landing page
test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Public Landing Page', () => {
  test('renders marketing content and redirects to login', async ({ page }) => {
    await page.goto('/');
    
    // Check main branding logo is visible (it is a span, not a heading)
    await expect(page.getByText('ASEP').first()).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Autonomous Software Engineering at Enterprise Scale' })).toBeVisible();
    
    // Check CTA navigation to signup
    const ctaLink = page.getByRole('link', { name: 'Deploy Control Plane' });
    await expect(ctaLink).toBeVisible();
    await ctaLink.click();
    
    await expect(page).toHaveURL(/\/signup/);
  });
});
