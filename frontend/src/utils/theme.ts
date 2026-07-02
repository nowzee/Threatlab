/**
 * Theme preference management (light / dark / system).
 *
 * The resolved theme is applied as `data-theme` on <html>. Dark is the app
 * default; the light "paper" palette lives in assets/css/variable.css under
 * [data-theme="light"]. Preference is persisted client-side (localStorage,
 * mirroring the i18n `tl_locale` key) and defaults to the OS theme.
 *
 * An inline bootstrap in index.html sets the attribute before the app mounts to
 * avoid a flash; initTheme() re-applies it and binds the system-change listener.
 */
export type ThemePref = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

const STORAGE_KEY = 'tl_theme'

export function getThemePref(): ThemePref {
  const v = localStorage.getItem(STORAGE_KEY)
  return v === 'light' || v === 'dark' ? v : 'system'
}

function systemPrefersDark(): boolean {
  return typeof window !== 'undefined' && !!window.matchMedia
    ? window.matchMedia('(prefers-color-scheme: dark)').matches
    : true
}

export function resolveTheme(pref: ThemePref = getThemePref()): ResolvedTheme {
  return pref === 'system' ? (systemPrefersDark() ? 'dark' : 'light') : pref
}

export function applyTheme(pref: ThemePref = getThemePref()): void {
  document.documentElement.setAttribute('data-theme', resolveTheme(pref))
}

export function setThemePref(pref: ThemePref): void {
  if (pref === 'system') localStorage.removeItem(STORAGE_KEY)
  else localStorage.setItem(STORAGE_KEY, pref)
  applyTheme(pref)
}

let _mediaBound = false

export function initTheme(): void {
  applyTheme()
  if (!_mediaBound && typeof window !== 'undefined' && window.matchMedia) {
    _mediaBound = true
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (getThemePref() === 'system') applyTheme('system')
    })
  }
}
