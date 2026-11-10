// theme.js: switch between the "blush" (light) and "midnight" (dark) themes.
// The choice is saved in this browser only (localStorage).

const KEY = "epub2zim.theme";

export function currentTheme() {
  return document.documentElement.dataset.theme || "blush";
}

export function setTheme(name) {
  if (name === "blush") delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = name;
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.content = name === "midnight" ? "#17121d" : "#fff6fa";
  try { localStorage.setItem(KEY, name); } catch (e) { /* private mode: not saved */ }
}
