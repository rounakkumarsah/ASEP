import { test, expect } from '@playwright/test';

test.describe('Specialized Workspaces E2E Tests', () => {
  test('verifies memory workspace tab switching and searching', async ({ page }) => {
    await page.goto('/memory');
    
    // Check initial memory title
    await expect(page.getByRole('heading', { name: 'Memory Workspace' })).toBeVisible();
    
    // Default tab should be Working Memory
    await expect(page.getByText('Working Memory').first()).toBeVisible();
    
    // Switch to Episodic Memory tab
    await page.getByRole('button', { name: 'Episodic Memory' }).click();
    await expect(page.getByText('Episodic Memory').first()).toBeVisible();
    
    // Try typing in filter query
    const searchInput = page.getByPlaceholder(/Search episodic memory/i);
    await expect(searchInput).toBeVisible();
    await searchInput.fill('JWT');
  });

  test('verifies governance approvals display', async ({ page }) => {
    await page.goto('/governance');
    
    // Check main title
    await expect(page.getByRole('heading', { name: 'Governance & Approval' })).toBeVisible();
    
    // Check tabs are available
    await expect(page.getByRole('button', { name: 'Approval Queue' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Policy Explorer' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Audit Summary' })).toBeVisible();
  });

  test('verifies live sessions lists', async ({ page }) => {
    await page.goto('/sessions');
    
    // Check main title
    await expect(page.getByRole('heading', { name: 'Active Sessions' })).toBeVisible();
  });
});
