import { expect, test } from '@playwright/test';

async function waitForShell(page) {
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeVisible();
  await expect
    .poll(async () => (await page.locator('#app-status').textContent())?.trim() ?? '')
    .not.toMatch(/Loading Tau shell/i);
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
  const navToggle = page.locator('#mobile-nav-toggle');
  const panelToggle = page.locator('#mobile-panel-toggle');
  if (!(await navToggle.isVisible()) && !(await panelToggle.isVisible())) {
    return;
  }

  await page.keyboard.press('Escape');
  await expect.poll(() => drawerState(page)).toEqual({ nav: 'false', panel: 'false' });

  const drawerBackdrop = page.locator('#drawer-backdrop');
  if (await drawerBackdrop.isVisible()) {
    await drawerBackdrop.focus();
    await expect(drawerBackdrop).toBeFocused();
    await page.keyboard.press('Enter');
    await expect.poll(() => drawerState(page)).toEqual({ nav: 'false', panel: 'false' });
  }

  if (await navToggle.isVisible()) {
    await expect(navToggle).toHaveAttribute('aria-expanded', 'false');
  }
  if (await panelToggle.isVisible()) {
    await expect(panelToggle).toHaveAttribute('aria-expanded', 'false');
  }
}

async function openNavIfNeeded(page) {
  if ((await drawerState(page)).nav === 'true') return;

  const navToggle = page.locator('#mobile-nav-toggle');
  const trigger = (await navToggle.isVisible())
    ? navToggle
    : page.getByRole('button', { name: 'Sessions', exact: true }).first();

  await closeDrawersIfNeeded(page);
  await trigger.focus();
  await expect(trigger).toBeFocused();
  await page.keyboard.press('Enter');

  await expect(navToggle).toHaveAttribute('aria-expanded', 'true');
  await expect.poll(() => drawerState(page)).toEqual({ nav: 'true', panel: 'false' });
}

async function openSidePanelIfNeeded(page) {
  const panelToggle = page.locator('#mobile-panel-toggle');
  if (!(await panelToggle.isVisible())) {
    return;
  }

  await closeDrawersIfNeeded(page);
  await panelToggle.focus();
  await expect(panelToggle).toBeFocused();
  await page.keyboard.press('Enter');

  await expect(panelToggle).toHaveAttribute('aria-expanded', 'true');
  await expect.poll(() => drawerState(page)).toEqual({ nav: 'false', panel: 'true' });
}

async function ensureSessionSelected(page) {
  const sessionButtons = page.locator('#session-list .session-button');
  if ((await sessionButtons.count()) === 0) {
    await openNavIfNeeded(page);
    await page.locator('#new-session-button').click();
    await expect.poll(() => sessionButtons.count()).toBeGreaterThan(0);
  }

  await openNavIfNeeded(page);
  await sessionButtons.first().click();
  await expect
    .poll(() => page.locator('#session-list .session-button[data-active="true"]').count())
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
    await expect(page.locator('#tab-search')).toHaveAttribute('aria-selected', 'true');
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
  const workspacePanelButton = page.locator('.activity-bar__button[aria-label="Workspace"]');
  if (await workspacePanelButton.isVisible()) await workspacePanelButton.click();
  await expect(page.locator('#panel-workspace')).toBeVisible();

  const reloadButton = page.locator('#workspace-reload-button');
  await expect(reloadButton).toBeEnabled();
  await reloadButton.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('#app-status')).toContainText('Workspace reloaded.');

  const navToggle = page.locator('#mobile-nav-toggle');
  if (await navToggle.isVisible()) {
    await closeDrawersIfNeeded(page);
    await navToggle.focus();
    await expect(navToggle).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(navToggle).toHaveAttribute('aria-expanded', 'true');
    await expect.poll(() => drawerState(page)).toEqual({ nav: 'true', panel: 'false' });

    await page.keyboard.press('Escape');
    await expect(navToggle).toHaveAttribute('aria-expanded', 'false');
    await expect.poll(() => drawerState(page)).toEqual({ nav: 'false', panel: 'false' });
  }
});
