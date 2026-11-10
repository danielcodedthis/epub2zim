// toast.js: show a short message at the bottom of the screen.
//   toast("Saved", "ok")   kinds: "" (neutral ✦), "ok" (✓), "err" (!)

let current = null;

export function toast(message, kind = "", ms = 3200) {
  if (current) current.remove();
  const box = document.createElement("div");
  box.className = `toast ${kind}`;
  box.setAttribute("role", kind === "err" ? "alert" : "status");
  box.textContent = message;
  document.body.append(box);
  current = box;
  setTimeout(() => { if (current === box) { box.remove(); current = null; } }, kind === "err" ? ms * 2 : ms);
}
