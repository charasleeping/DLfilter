const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
    testDir: './tests/browser', timeout: 60000, workers: 1,
    use: { baseURL: 'http://127.0.0.1:8765', headless: true, screenshot: 'only-on-failure', trace: 'retain-on-failure' },
    webServer: { command: '.venv/bin/python tests/browser_server.py', url: 'http://127.0.0.1:8765', reuseExistingServer: false },
});
