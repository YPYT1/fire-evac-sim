import { test, expect } from '@playwright/test';

test.describe('fire-evac-sim UI smoke', () => {
  test('home page renders control panel', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Fire Evacuation Simulation')).toBeVisible();
    await expect(page.getByRole('button', { name: '启动仿真' })).toBeVisible();
  });
});
