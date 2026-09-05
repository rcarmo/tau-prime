import { expect, test } from '@playwright/test';

test('Piclaw activity icons and external font assets render under Tau CSP', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeAttached();
  const results = await page.evaluate(async () => {
    const css = await (await fetch('/static/piclaw-reference.css')).text();
    const urls = [...new Set([...css.matchAll(/url\(\.\/([^)]*)\)/g)].map(match => match[1]))];
    const fonts = await Promise.all(urls.map(async (name, i) => {
      const response = await fetch(`/static/${name}`);
      const face = new FontFace(`tau-audit-${i}`, `url(/static/${name})`);
      await face.load();
      return { name, status: response.status, loaded: face.status };
    }));
    const icon = document.querySelector('.activity-bar__icon');
    const style = getComputedStyle(icon);
    const glyph = getComputedStyle(icon, '::before');
    const iconLoaded = await document.fonts.load(`${style.fontSize} ${style.fontFamily}`).then(() => true, () => false);
    return { iconLoaded, fonts, size: style.fontSize, family: style.fontFamily, glyph: glyph.content };
  });
  expect(results.fonts).toHaveLength(4);
  for (const font of results.fonts) {
    expect(font.status).toBe(200);
    expect(font.loaded).toBe('loaded');
  }
  expect(results.iconLoaded).toBe(true);
  expect(results.size).toBe('24px');
  expect(results.family).toContain('codicon');
  expect(results.glyph).not.toBe('none');
  expect(results.glyph).not.toBe('normal');
  expect(errors).toEqual([]);
});
