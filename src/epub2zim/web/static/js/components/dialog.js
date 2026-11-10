// dialog.js: a friendly "are you sure?" box.
//   if (await confirmBox({ title, text, okLabel })) { ...do it... }
// Focus starts on Cancel, so pressing Enter by accident never deletes anything.

import { el, esc } from "../dom.js";

export function confirmBox({ title, text, okLabel = "Delete", danger = true }) {
  return new Promise((resolve) => {
    const dlg = el(`
      <dialog class="modal small">
        <form method="dialog">
          <div class="modal-head"><h2>${esc(title)}</h2></div>
          <div class="modal-body"><p class="confirm-text">${esc(text)}</p></div>
          <div class="modal-foot">
            <button type="button" class="pill-btn" data-act="cancel">Cancel</button>
            <button type="button" class="${danger ? "danger-btn" : "primary-btn"}" data-act="ok">${esc(okLabel)}</button>
          </div>
        </form>
      </dialog>`);
    const done = (answer) => { dlg.close(); dlg.remove(); resolve(answer); };
    dlg.querySelector('[data-act="cancel"]').onclick = () => done(false);
    dlg.querySelector('[data-act="ok"]').onclick = () => done(true);
    dlg.addEventListener("cancel", (e) => { e.preventDefault(); done(false); });   // Esc key
    dlg.addEventListener("click", (e) => { if (e.target === dlg) done(false); });   // backdrop
    document.body.append(dlg);
    dlg.showModal();
    dlg.querySelector('[data-act="cancel"]').focus();
  });
}
