import { expect, test } from '@playwright/test';

async function waitForShell(page) {
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeAttached();
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
  const cancelOnboarding = page.getByRole('button', { name: 'Cancel' });
  await cancelOnboarding.waitFor({ state: 'visible', timeout: 2000 }).catch(() => {});
  if (await cancelOnboarding.isVisible()) await cancelOnboarding.click();
}

async function drawerState(page) {
  return page.evaluate(() => ({
    nav: document.body.dataset.navOpen ?? 'false',
    panel: document.body.dataset.panelOpen ?? 'false',
  }));
}

async function closeDrawersIfNeeded(page) {
  await page.keyboard.press('Escape');
  await expect.poll(() => drawerState(page)).toEqual({nav:'false',panel:'false'});
}

async function openNavIfNeeded(page) {
  if ((await drawerState(page)).nav === 'true') return;
  await closeDrawersIfNeeded(page);
  const trigger=page.getByRole('button',{name:'Open sessions',exact:true});
  await trigger.focus();await page.keyboard.press('Enter');
  await expect(trigger).toHaveAttribute('aria-expanded','true');
  await expect(page.locator('#panel-sessions')).toBeVisible();
}

async function openSidePanelIfNeeded(page) {
  await openNavIfNeeded(page);
  await page.getByRole('group',{name:'Navigation',exact:true}).getByRole('button',{name:'Workspace',exact:true}).click();
}

async function ensureSessionSelected(page) {
  const sessionButtons = page.locator('#session-list .sessions-panel__session');
  if ((await sessionButtons.count()) === 0) {
    await openNavIfNeeded(page);
    await page.locator('#new-session-button').click();
    await expect.poll(() => sessionButtons.count()).toBeGreaterThan(0);
  }

  await openNavIfNeeded(page);
  await sessionButtons.first().click();
  await expect
    .poll(() => page.locator('#session-list .sessions-panel__session[data-active="true"]').count())
    .toBeGreaterThan(0);
}

test('keyboard shortcuts, completion behavior, and focus traversal', async ({ page }) => {
  await waitForShell(page);
  await ensureSessionSelected(page);

  const modifier = (await page.evaluate(() => /Mac|iPhone|iPad/i.test(navigator.platform)))
    ? 'Meta'
    : 'Control';

  await page.keyboard.press(`${modifier}+K`);
  const focusedAfterPalette = await page.evaluate(() => document.activeElement?.id ?? '');
  expect(['search-input', 'compose-input']).toContain(focusedAfterPalette);
  if (focusedAfterPalette === 'search-input') {
    await expect(page.locator('#tab-search')).toHaveAttribute('aria-pressed', 'true');
  }

  await page.evaluate((activeModifier) => {
    const event = new KeyboardEvent('keydown', {
      key: 'n',
      ctrlKey: activeModifier === 'Control',
      metaKey: activeModifier === 'Meta',
      bubbles: true,
    });
    window.dispatchEvent(event);
  }, modifier);
  await expect(page.locator('#compose-input')).toBeFocused();

  const composeInput = page.locator('#compose-input');
  await composeInput.fill('/');
  await expect(page.locator('#compose-completion-popup')).toBeVisible();
  await expect
    .poll(() => page.locator('#compose-completion-listbox [role="option"]').count())
    .toBeGreaterThan(0);
  await expect(composeInput).toHaveAttribute('aria-expanded', 'true');

  await page.keyboard.press('Escape');
  await expect(page.locator('#compose-completion-popup')).toBeHidden();
  await expect(composeInput).toHaveAttribute('aria-expanded', 'false');

  await composeInput.fill('keyboard flow');
  await composeInput.focus();
  await page.keyboard.press('Tab');
  await expect
    .poll(() =>
      page.evaluate(() =>
        Boolean(
          document.activeElement?.matches(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
          ),
        ),
      ),
    )
    .toBe(true);
  await page.keyboard.press('Shift+Tab');
  await expect(composeInput).toBeFocused();

  await openSidePanelIfNeeded(page);
  await expect(page.locator('#panel-workspace')).toBeVisible();

  const reloadButton = page.locator('#workspace-reload-button');
  await expect(reloadButton).toBeEnabled();
  await reloadButton.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('#app-status')).toContainText('Workspace reloaded.');

  await closeDrawersIfNeeded(page);
  await openNavIfNeeded(page);
  await page.keyboard.press('Escape');
  await expect.poll(() => drawerState(page)).toEqual({nav:'false',panel:'false'});

});
