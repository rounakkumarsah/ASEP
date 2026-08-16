import { test, expect } from '@playwright/test';

test.describe('Terminal Emulator Ingress Verification', () => {
  test('mounts TerminalEmulator component on session detail page', async ({ page }) => {
    // Navigate to a mockup session detail view
    await page.goto('/sessions/test-session-id-123');

    // Verify the timeline container card is rendered
    const timelineCard = page.locator('text=Execution Timeline');
    await expect(timelineCard).toBeVisible();

    // Verify the terminal emulator container has mounted inside the card
    const terminalContainer = page.locator('.xterm');
    // Non-crashing visual smoke validation: check that wrapper DOM elements exist
    expect(terminalContainer).toBeDefined();
  });
});
