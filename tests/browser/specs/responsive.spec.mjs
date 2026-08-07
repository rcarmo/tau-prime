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
}

async function openNavDrawerIfAvailable(page) {
  const navToggle = page.locator('#mobile-nav-toggle');
  if (!(await navToggle.isVisible())) {
    return false;
  }

  await closeDrawersIfNeeded(page);
  await expect(navToggle).toHaveAttribute('aria-expanded', 'false');
  await navToggle.focus();
  await expect(navToggle).toBeFocused();
  await page.keyboard.press('Enter');

  await expect(navToggle).toHaveAttribute('aria-expanded', 'true');
  await expect.poll(() => drawerState(page)).toEqual({ nav: 'true', panel: 'false' });
  await expect(page.locator('#close-nav-drawer')).toBeVisible();

  await page.keyboard.press('Escape');
  await expect(navToggle).toHaveAttribute('aria-expanded', 'false');
  await expect.poll(() => drawerState(page)).toEqual({ nav: 'false', panel: 'false' });
  return true;
}

async function openWorkspacePanel(page) {
  const panelToggle = page.locator('#mobile-panel-toggle');
  if (await panelToggle.isVisible()) {
    await closeDrawersIfNeeded(page);
    await expect(panelToggle).toHaveAttribute('aria-expanded', 'false');
    await panelToggle.focus();
    await expect(panelToggle).toBeFocused();
    await page.keyboard.press('Enter');

    await expect(panelToggle).toHaveAttribute('aria-expanded', 'true');
    await expect.poll(() => drawerState(page)).toEqual({ nav: 'false', panel: 'true' });
  } else {
    await page.getByRole('button', { name: /^workspace$/i }).click();
    await expect(page.locator('#side-panel')).toBeVisible();
  }

  const workspaceTab = page.locator('#tab-workspace');
  if ((await workspaceTab.getAttribute('aria-selected')) !== 'true') {
    await workspaceTab.focus();
    await expect(workspaceTab).toBeFocused();
    await page.keyboard.press('Enter');
  }
  await expect(page.locator('#panel-workspace')).toBeVisible();
}

async function activateWorkspaceEntry(page, button) {
  await expect(button).toBeVisible();
  await button.scrollIntoViewIfNeeded();
  await button.focus();
  await expect(button).toBeFocused();
  await page.keyboard.press('Enter');
}

test('responsive shell, nav drawers, and UTF-8 workspace file rendering', async ({ page }) => {
  await waitForShell(page);

  const overflow = await page.evaluate(() => {
    const doc = document.documentElement;
    const body = document.body;
    return {
      doc: doc.scrollWidth - doc.clientWidth,
      body: body.scrollWidth - body.clientWidth,
    };
  });
  expect(overflow.doc).toBeLessThanOrEqual(1);
  expect(overflow.body).toBeLessThanOrEqual(1);

  await expect(page.locator('.app-layout__status-bar[aria-label="Tau status bar"]')).toHaveCount(1);
  await expect(page.getByRole('main')).toHaveCount(1);
  await expect(page.getByRole('navigation', { name: /activity bar/i })).toHaveCount(1);
  await expect(page.getByRole('button', { name: /^sessions$/i })).toHaveCount(1);
  await expect(page.getByRole('button', { name: /^run$/i })).toHaveCount(1);

  const usedDrawerLayout = await openNavDrawerIfAvailable(page);
  if (!usedDrawerLayout) {
    await expect(page.locator('#mobile-nav-toggle')).toBeHidden();
    await page.getByRole('button', { name: /^sessions$/i }).click();
    await expect(page.locator('#side-panel')).toBeVisible();
    await expect(page.getByRole('button', { name: /^new$/i })).toBeVisible();
  }

  await openWorkspacePanel(page);

  const readmeButton = page.getByRole('treeitem', { name: /README\.md/i });
  const notesButton = page.getByRole('treeitem', { name: /^notes\b/i });
  await expect(readmeButton).toBeVisible();
  await expect(notesButton).toBeVisible();

  await activateWorkspaceEntry(page, notesButton);
  await expect(page.locator('#workspace-path')).toContainText(/notes/);

  const welcomeButton = page.getByRole('treeitem', { name: /welcome\.txt/i });
  await activateWorkspaceEntry(page, welcomeButton);
  await expect(page.locator('#workspace-editor-path')).toContainText(/notes\/welcome\.txt/i);
  await expect(page.locator('#workspace-editor')).toHaveValue(/café/);
  await expect(page.locator('#workspace-editor')).toHaveValue(/日本語/);
});
