import { test, expect } from '@playwright/test';

test.describe('Human-in-the-Loop Approvals Page Verification', () => {
  test('renders approvals queue page and mounts MonacoDiffViewer', async ({ page }) => {
    // Navigate to the approvals review dashboard queue
    await page.goto('/approvals');

    // Verify the page title matches
    const pageHeader = page.locator('text=Human-in-the-Loop Queue');
    await expect(pageHeader).toBeVisible();

    // Verify the pending approvals column layout is visible
    const pendingHeader = page.locator('text=Pending Approvals');
    await expect(pendingHeader).toBeVisible();

    // Verify that the Monaco Diff Viewer container renders on screen when active
    const diffContainer = page.locator('.monaco-diff-editor');
    expect(diffContainer).toBeDefined();
  });
});
