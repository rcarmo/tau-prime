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

async function openWorkspacePanel(page) {
  const trigger=page.getByRole('button',{name:'Open sessions',exact:true});
  await trigger.focus();await page.keyboard.press('Enter');
  await expect(trigger).toHaveAttribute('aria-expanded','true');
  await page.keyboard.press('Escape');
  await expect.poll(()=>drawerState(page)).toEqual({nav:'false',panel:'false'});
  await trigger.focus();await page.keyboard.press('Enter');
  const tab=page.locator('#tab-workspace');await tab.focus();await page.keyboard.press('Enter');
  await expect(tab).toHaveAttribute('aria-pressed','true');
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

  await expect(page.locator('.app-layout__status-bar,.activity-bar')).toHaveCount(0);
  await expect(page.getByRole('main')).toHaveCount(1);
  await expect(page.getByRole('button',{name:'Open sessions',exact:true})).toHaveCount(1);
  await expect(page.getByRole('button',{name:'Send',exact:true})).toHaveCount(1);
  await expect(page.getByRole('button',{name:'Run',exact:true})).toHaveCount(0);

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
