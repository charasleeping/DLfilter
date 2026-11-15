const { test, expect } = require('@playwright/test');
async function open(page) {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('#copy-tags-btn')).toBeEnabled();
}
async function copy(page, id) {
    if (await page.locator('#copy-tags-btn').getAttribute('aria-expanded') !== 'true') await page.locator('#copy-tags-btn').click();
    await expect(page.locator('#copy-tags-btn')).toHaveAttribute('aria-expanded', 'true');
    await expect(page.locator('#rjid')).toBeFocused();
    await page.locator('#rjid').fill(id);
    await page.locator('#rjid').press('Enter');
}
async function closePopup(page) { await page.keyboard.press('Escape'); await expect(page.locator('#copy-tags-btn')).toHaveAttribute('aria-expanded', 'false'); }

test('one Search, defaults, additive popup copying and all genres', async ({ page }) => {
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await open(page);
    await expect(page.locator('#search-tabs')).toHaveCount(0);
    await expect(page.locator('#age-checkbox-1')).toBeChecked();
    await expect(page.locator('#age-checkbox-3')).not.toBeChecked();
    await expect(page.locator('#popularity-weight-enabled')).toBeDisabled();
    await copy(page, 'ｖｊ０１２３４５６７');
    await expect(page.locator('#genre-add-container button')).toHaveCount(2);
    await expect(page.locator('#reference-work')).toContainText('Test Game');
    await expect(page.locator('#workformat-add-container button')).toHaveCount(0);
    await copy(page, 'bj123456');
    await expect(page.locator('#genre-add-container button')).toHaveCount(14);
    await expect(page.locator('#reference-work')).toContainText('Test Book');
    await expect(page.locator('#copy-tags-content')).toBeVisible();
    await expect(page.locator('.copy-tags-popover')).toHaveCount(1);
    const anchor = await page.locator('#copy-tags-btn').boundingBox(), popup = await page.locator('.copy-tags-popover').boundingBox();
    expect(Math.abs(anchor.y - popup.y)).toBeLessThan(250);
    await copy(page, 'BJ654321');
    await expect(page.locator('#rjid-work-name')).toContainText('no available genres');
    await expect(page.locator('#genre-add-container button')).toHaveCount(14);
    await expect(page.locator('#reference-work')).toContainText('Test Book');
    await closePopup(page);
    await expect(page.locator('#copy-tags-btn')).toBeFocused();
    await page.locator('#catalog-query').fill('Test');
    const response = page.waitForResponse(r => r.url().includes('/api/search?'));
    await page.locator('#search-btn').click();
    const data = await (await response).json();
    expect(data.results.map(w => w.index)).toEqual(['VJ01234567']);
    expect(data.results[0].score).toBeDefined();
    await expect(page.locator('#catalog-card-container .catalog-card')).toHaveCount(1);
    expect(errors).toEqual([]);
});

test('preferences, language, theme and reset survive reload', async ({ page }) => {
    await open(page);
    await page.locator('#catalog-query').fill('Test');
    await page.locator('#catalog-field').selectOption('title');
    await copy(page, 'VJ01234567'); await expect(page.locator('#genre-add-container button')).toHaveCount(2); await closePopup(page);
    await page.locator('#advanced-panel-toggle').click();
    await page.locator('#date-range-enabled').check();
    await page.locator('#date-range').fill('40');
    await page.locator('#dark-toggle').click();
    await page.locator('#lang-toggle').click();
    await expect(page.locator('html')).toHaveAttribute('lang', 'ja-JP');
    await page.reload(); await expect(page.locator('#copy-tags-btn')).toBeEnabled();
    await expect(page.locator('#catalog-query')).toHaveValue('Test');
    await expect(page.locator('#catalog-field')).toHaveValue('title');
    await expect(page.locator('#genre-add-container button')).toHaveCount(2);
    await expect(page.locator('#date-range-enabled')).toBeChecked();
    await expect(page.locator('#date-range')).toHaveValue('40');
    await expect(page.locator('html')).toHaveAttribute('data-bs-theme', 'dark');
    await expect(page.locator('html')).toHaveAttribute('lang', 'ja-JP');
    await expect(page.locator('#catalog-results-section')).toBeHidden();
    await page.locator('#similar-reset-btn').click();
    await expect(page.locator('#catalog-query')).toHaveValue('');
    await expect(page.locator('#genre-add-container button')).toHaveCount(0);
    await page.reload(); await expect(page.locator('#copy-tags-btn')).toBeEnabled();
    await expect(page.locator('#genre-add-container button')).toHaveCount(0);
    await expect(page.locator('#age-checkbox-1')).toBeChecked();
});

test('malformed storage and legacy presets restore safely', async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('dlfilter.search.v1', '{invalid'));
    await open(page);
    await page.locator('#preset-load-btn').click();
    await page.locator('#preset-file-input').setInputFiles({ name: 'legacy.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify({ genres: ['001', '999'], rj_id: 'BJ123456', categories: ['SOU', 'XXX'] })) });
    await expect(page.locator('#genre-add-container button')).toHaveCount(1);
    await expect(page.locator('#workformat-add-container button')).toHaveCount(1);
    await expect(page.locator('#catalog-query')).toHaveValue('');
    await expect(page.locator('#preset-load-modal')).toBeHidden();
    await page.locator('#preset-save-btn').click();
    await page.locator('#preset-name').fill('Browser preset');
    await page.locator('#preset-save-submit').click();
    await expect(page.locator('#preset-save-modal')).toBeHidden();
    await page.locator('#similar-reset-btn').click();
    await page.locator('#preset-load-btn').click();
    await page.getByRole('button', { name: 'Browser preset', exact: true }).click();
    await expect(page.locator('#genre-add-container button')).toHaveCount(1);
    await expect(page.locator('#reference-work')).toContainText('BJ123456');
});

test('stale responses and errors clear loading state', async ({ page }) => {
    await open(page);
    await page.route('**/api/search?**', async route => {
        await new Promise(r => setTimeout(r, 250));
        await route.fulfill({ json: { state: 'success', results: [{ index: 'RJ999999', name: 'Stale' }], total: 1, page: 1 } });
    });
    await page.locator('#search-btn').click();
    await page.locator('#similar-reset-btn').click();
    await page.waitForTimeout(400);
    await expect(page.locator('#catalog-results-section')).toBeHidden();
    await expect(page.locator('#catalog-card-container')).toBeEmpty();
    await page.unroute('**/api/search?**');
    await page.route('**/api/search?**', route => route.fulfill({ status: 500, json: { state: 'error' } }));
    await page.locator('#search-btn').click();
    await expect(page.locator('#catalog-status')).toContainText('failed');
    await expect(page.locator('#catalog-spinner')).toBeHidden();
});

test('all languages and themes fit desktop and narrow viewports', async ({ page }) => {
    await open(page);
    for (const width of [1280, 390]) {
        await page.setViewportSize({ width, height: 900 });
        for (let i = 0; i < 4; i++) {
            await page.locator('#lang-toggle').click();
            await page.locator('#dark-toggle').click();
            await page.locator('#copy-tags-btn').click();
            await expect(page.locator('.copy-tags-popover')).toBeVisible();
            const box = await page.locator('.copy-tags-popover').boundingBox();
            expect(box.x).toBeGreaterThanOrEqual(0); expect(box.x + box.width).toBeLessThanOrEqual(width + 1);
            await closePopup(page);
            expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
        }
    }
    await page.screenshot({ path: '/tmp/dlfilter-mobile.png', fullPage: true });
});

test('result copying preserves filters and never starts a search automatically', async ({ page }) => {
    await open(page);
    await page.locator('#catalog-query').fill('Test');
    await page.locator('#catalog-field').selectOption('title');
    await page.locator('#advanced-panel-toggle').click();
    await page.locator('#misc-checkbox-4').uncheck();
    let searches = 0; page.on('request', r => { if (r.url().includes('/api/search?')) searches++; });
    await page.locator('#search-btn').click();
    await expect(page.locator('#catalog-card-container .catalog-card')).toHaveCount(2);
    await page.locator('#catalog-card-container .catalog-card').filter({ hasText: 'Test Book' }).locator('.catalog-find-similar').click();
    await expect(page.locator('#reference-work')).toContainText('Test Book');
    await expect(page.locator('.copy-tags-popover')).toBeVisible();
    await expect(page.locator('#genre-add-container button')).toHaveCount(12);
    await expect(page.locator('#catalog-query')).toHaveValue('Test');
    await expect(page.locator('#catalog-field')).toHaveValue('title');
    await expect(page.locator('#misc-checkbox-4')).not.toBeChecked();
    expect(searches).toBe(1);
    await copy(page, 'RJ999999');
    await expect(page.locator('#rjid-work-name')).toContainText('not in the local catalogue');
    await expect(page.locator('#reference-work')).toContainText('Test Book');
    // Popper can place the popup over the heading on shorter Linux layouts.
    // Click the empty top margin, verifying it is actually outside the popup.
    const outside = { x: Math.floor(page.viewportSize().width / 2), y: 8 };
    expect(await page.evaluate(({ x, y }) => !document.elementFromPoint(x, y)?.closest('.copy-tags-popover'), outside)).toBe(true);
    await page.mouse.click(outside.x, outside.y);
    await expect(page.locator('.copy-tags-popover')).toHaveCount(0);
});

test('storage denial does not prevent searching and images use the right prefix', async ({ page }) => {
    await page.addInitScript(() => {
        Storage.prototype.getItem = () => { throw new Error('denied'); };
        Storage.prototype.setItem = () => { throw new Error('denied'); };
    });
    await open(page);
    const images = await page.evaluate(() => [getImgUrl('BJ123456'), getImgUrl('VJ01234567'), getImgUrl('RJ123456'), getImgUrl('BJ123456', '//img.dlsite.jp/sample.jpg'), getImgUrl('BJ123456', 'javascript:alert(1)')]);
    expect(images[0]).toContain('/books/BJ124000/BJ123456_');
    expect(images[1]).toContain('/professional/VJ01235000/VJ01234567_');
    expect(images[2]).toContain('/doujin/RJ124000/RJ123456_');
    expect(images[3]).toBe('https://img.dlsite.jp/sample.jpg');
    expect(images[4]).toBe(images[0]);
    await page.locator('#catalog-query').fill('Tagless Book');
    await page.locator('#search-btn').click();
    await expect(page.locator('#catalog-card-container .catalog-card')).toHaveCount(1);
    await expect(page.locator('#catalog-card-container')).toContainText('Tagless Book');
});

test('language strip, theme graphics and welcome section highlights', async ({ page }) => {
    await open(page);
    await expect(page.locator('#lang-toggle .lang-strip-glyph')).toHaveCount(4);
    await expect(page.locator('#lang-toggle .active')).toHaveText('A');
    expect(await page.locator('#lang-toggle .active').evaluate(e => parseFloat(getComputedStyle(e).fontSize))).toBeGreaterThan(18);
    await expect(page.locator('#dark-toggle svg circle')).toHaveCount(1);
    await page.locator('#dark-toggle').click();
    await expect(page.locator('#dark-toggle svg circle')).toHaveCount(0);
    await expect(page.locator('#dark-toggle svg path')).toHaveCount(1);
    const targets = { keywords: 'catalog-search-form', genres: 'genre-selection-section', formats: 'format-selection-section' };
    for (const [term, id] of Object.entries(targets)) {
        const link = page.locator(`.welcome-hint-link[data-term=${term}]`);
        expect(await link.evaluate(e => getComputedStyle(e).textDecorationLine)).toContain('underline');
        const before = await page.locator('#'+id).boundingBox();
        await link.hover(); await expect(page.locator('#'+id)).toHaveClass(/welcome-section-highlight/);
        expect(await page.locator('#'+id).boundingBox()).toEqual(before);
        await page.locator('#search-title').hover();
        await link.focus(); await expect(page.locator('#'+id)).toHaveClass(/welcome-section-highlight/);
        await page.locator('#catalog-query').focus(); await expect(page.locator('#'+id)).not.toHaveClass(/welcome-section-highlight/);
    }
    await page.locator('.welcome-hint-link[data-term=keywords]').click();
    await expect(page.locator('#catalog-query')).toBeFocused();
    await page.locator('#lang-toggle').click();
    await expect(page.locator('#lang-toggle .active')).toHaveText('あ');
    expect(await page.locator('#lang-toggle .active').evaluate(e => getComputedStyle(e).transitionDuration)).toContain('0.32');
    for (let i=0;i<3;i++) await page.locator('#lang-toggle').click();
    await expect(page.locator('#lang-toggle .active')).toHaveText('A');
    await expect(page.locator('.welcome-hint-link')).toHaveCount(3);
    await page.emulateMedia({ reducedMotion: 'reduce' });
    expect(await page.locator('#lang-toggle .active').evaluate(e => getComputedStyle(e).transitionDuration)).toBe('0s');
});

test('theme spreads from its button in both directions and respects reduced motion', async ({ page }) => {
    await open(page);
    await page.evaluate(() => {
        window.themeSpreads = [];
        const animate = Element.prototype.animate;
        Element.prototype.animate = function (frames, options) {
            if (options?.pseudoElement === '::view-transition-new(root)') window.themeSpreads.push({ frames, options });
            return animate.call(this, frames, options);
        };
    });
    expect(await page.locator('#lang-toggle .active').evaluate(e => getComputedStyle(e).fontWeight)).toBe('400');
    for (const theme of ['dark', 'light']) {
        const button = await page.locator('#dark-toggle').boundingBox();
        await page.locator('#dark-toggle').click();
        await expect(page.locator('html')).toHaveAttribute('data-bs-theme', theme);
        await expect.poll(() => page.evaluate(() => window.themeSpreads.length)).toBe(theme === 'dark' ? 1 : 2);
        const spread = await page.evaluate(() => window.themeSpreads.at(-1));
        expect(spread.frames.clipPath[0]).toBe(`circle(0px at ${button.x + button.width / 2}px ${button.y + button.height / 2}px)`);
        expect(spread.options.duration).toBe(600);
        await page.waitForFunction(() => !document.getAnimations().some(a => a.effect?.pseudoElement === '::view-transition-new(root)'));
        if (theme === 'dark') await page.screenshot({ path: '/tmp/dlfilter-theme-icons.png' });
    }
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.locator('#dark-toggle').click();
    await expect(page.locator('html')).toHaveAttribute('data-bs-theme', 'dark');
    expect(await page.evaluate(() => window.themeSpreads.length)).toBe(2);
});
