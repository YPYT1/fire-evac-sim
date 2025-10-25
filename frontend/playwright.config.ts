import { defineConfig, devices } from '@playwright/test';

const PORT = process.env.E2E_PORT || '5173';
const BASE_URL = process.env.E2E_BASE_URL || `http://127.0.0.1:${PORT}`;

export default defineConfig({
  testDir: 'tests/e2e',
  retries: process.env.CI ? 2 : 0,
  timeout: 60_000,
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
  },
  webServer: {
    command: `bun run dev -- --host 0.0.0.0 --port ${PORT}`,
    url: BASE_URL,
    timeout: 120_000,
    reuseExistingServer: !process.env.CI,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
