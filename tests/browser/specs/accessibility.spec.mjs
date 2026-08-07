import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const BLOCKING_IMPACTS = new Set(['serious', 'critical']);

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

function summarizeViolations(violations) {
  return violations.map((violation) => ({
    id: violation.id,
    impact: violation.impact,
    help: violation.help,
    helpUrl: violation.helpUrl,
    description: violation.description,
    nodes: violation.nodes.map((node) => ({
      target: node.target,
      html: node.html,
      failureSummary: node.failureSummary,
    })),
  }));
}

async function expectNoBlockingAxeViolations(page, label) {
  const results = await new AxeBuilder({ page }).analyze();
  const blocking = results.violations.filter((violation) =>
    BLOCKING_IMPACTS.has(violation.impact ?? ''),
  );

  expect(
    blocking,
    `${label} serious/critical axe violations:\n${JSON.stringify(
      summarizeViolations(blocking),
      null,
      2,
    )}`,
  ).toEqual([]);
}

async function assertCoreAccessibleControls(page) {
  await expect(page.getByRole('combobox', { name: /send a prompt to tau/i })).toHaveCount(1);
  await expect(page.getByRole('button', { name: /^run$/i })).toHaveCount(1);
  await expect(page.getByRole('complementary', { name: /session navigation/i })).toHaveCount(1);

  for (const tabName of ['Workspace', 'Search', 'Plan', 'Settings']) {
    await expect(page.getByRole('tab', { name: new RegExp(`^${tabName}$`, 'i') })).toHaveCount(1);
  }
}

async function openPhoneSurfaceForSecondScan(page) {
  const navToggle = page.locator('#mobile-nav-toggle');
  if (await navToggle.isVisible()) {
    if ((await navToggle.getAttribute('aria-expanded')) !== 'true') {
      await navToggle.click();
    }
    await expect(navToggle).toHaveAttribute('aria-expanded', 'true');
    return;
  }

  const dashboardToggle = page.locator('#dashboard-toggle');
  if (await dashboardToggle.isVisible()) {
    if ((await dashboardToggle.getAttribute('aria-expanded')) !== 'true') {
      await dashboardToggle.click();
    }
    await expect(dashboardToggle).toHaveAttribute('aria-expanded', 'true');
    return;
  }

  const panelToggle = page.locator('#mobile-panel-toggle');
  if (await panelToggle.isVisible()) {
    if ((await panelToggle.getAttribute('aria-expanded')) !== 'true') {
      await panelToggle.click();
    }
    await expect(panelToggle).toHaveAttribute('aria-expanded', 'true');
  }
}

async function assertComposeFocusIndicatorAfterGlobalShortcut(page) {
  const composeInput = page.locator('#compose-input');
  const modifier = (await page.evaluate(() => /Mac|iPhone|iPad/i.test(navigator.platform)))
    ? 'Meta'
    : 'Control';

  await page.locator('#timeline-main').focus();
  const before = await composeInput.evaluate((element) => {
    const style = getComputedStyle(element);
    return {
      outlineStyle: style.outlineStyle,
      outlineWidth: style.outlineWidth,
      outlineColor: style.outlineColor,
      boxShadow: style.boxShadow,
      borderColor: style.borderColor,
    };
  });

  await page.keyboard.press(`${modifier}+N`);

  await expect
    .poll(() => page.evaluate(() => document.activeElement?.id ?? ''), { timeout: 15_000 })
    .toBe('compose-input');

  const indicator = await composeInput.evaluate((element, previous) => {
    const style = getComputedStyle(element);
    const outlineStyle = (style.outlineStyle || '').toLowerCase();
    const outlineWidth = Number.parseFloat(style.outlineWidth || '0');
    const outlineColor = style.outlineColor || '';
    const boxShadow = style.boxShadow || '';

    const hasOutline =
      Number.isFinite(outlineWidth) &&
      outlineWidth > 0 &&
      !['none', 'hidden'].includes(outlineStyle) &&
      !/transparent|rgba?\(0,\s*0,\s*0,\s*0\)/i.test(outlineColor);
    const hasBoxShadow = boxShadow !== 'none' && !/rgba?\(0,\s*0,\s*0,\s*0\)/i.test(boxShadow);
    const borderChanged = previous?.borderColor && previous.borderColor !== style.borderColor;

    return {
      before: previous,
      after: {
        outlineStyle: style.outlineStyle,
        outlineWidth: style.outlineWidth,
        outlineColor,
        boxShadow,
        borderColor: style.borderColor,
      },
      hasOutline,
      hasBoxShadow,
      borderChanged,
      visible: hasOutline || hasBoxShadow || borderChanged,
    };
  }, before);

  expect(
    indicator.visible,
    `Expected a visible keyboard focus indicator on #compose-input after ${modifier}+N.\n${JSON.stringify(
      indicator,
      null,
      2,
    )}`,
  ).toBe(true);
}

test('baseline accessibility coverage and keyboard focus indicator', async ({ page }, testInfo) => {
  await waitForShell(page);
  await assertCoreAccessibleControls(page);
  await expectNoBlockingAxeViolations(page, `${testInfo.project.name} initial page`);

  if (/phone/i.test(testInfo.project.name)) {
    await openPhoneSurfaceForSecondScan(page);
    await expectNoBlockingAxeViolations(page, `${testInfo.project.name} phone nav/panel open`);
  }

  await assertComposeFocusIndicatorAfterGlobalShortcut(page);
});
