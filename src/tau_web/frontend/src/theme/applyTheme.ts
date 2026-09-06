// Piclaw 2.15.3 ThemeProvider root mapping (MIT; see PICLAW-LICENSE.md).
import { DARK_THEME, LIGHT_THEME, getSystemTheme } from './theme';

export function installSystemTheme() {
  const apply = () => {
    const mode = getSystemTheme();
    const theme = mode === 'dark' ? DARK_THEME : LIGHT_THEME;
    const root = document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(mode);
    const variables = {
      '--bg': theme.bg, '--bg-sidebar': theme.bgSidebar,
      '--bg-terminal': theme.bgTerminal, '--bg-status': theme.bgStatus,
      '--border': theme.border, '--text': theme.text, '--text-muted': theme.textMuted,
      '--accent': theme.accent, '--success': theme.success, '--error': theme.error,
      '--handle-hover': theme.handleHover, '--handle': theme.handle,
      '--input-bg': theme.inputBg, '--input-border': theme.inputBorder,
    };
    for (const [key, value] of Object.entries(variables)) root.style.setProperty(key, value);
  };
  apply();
  const media = window.matchMedia('(prefers-color-scheme: dark)');
  media.addEventListener('change', apply);
  return () => media.removeEventListener('change', apply);
}
