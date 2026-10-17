// Hero ledger: optional "follow a source" interaction. The page is complete without it.
// The three source rows are plain markup; here they are upgraded to native buttons.
(() => {
  const trace = document.querySelector('[data-trace]');
  if (!trace) return;

  const caption = trace.querySelector('[data-caption]');
  const hint = trace.querySelector('[data-hint]');
  const tokens = trace.querySelectorAll('[data-for]');
  const defaultText = caption.textContent;

  const messages = {
    terms: 'The approved $65 hourly rate applies to these service dates.',
    work: '40 approved hours × $65 gives $2,600 expected under the approved terms.',
    invoice: '$2,400 invoiced is $200 below the expected amount. Human review is required.'
  };

  const buttons = [...trace.querySelectorAll('[data-source]')].map((row) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = row.className;
    button.dataset.source = row.dataset.source;
    button.setAttribute('aria-pressed', 'false');
    button.append(...row.childNodes);
    row.replaceWith(button);
    return button;
  });

  function show(key) {
    const index = buttons.findIndex((b) => b.dataset.source === key);
    buttons.forEach((b, i) => {
      const active = b.dataset.source === key;
      b.classList.toggle('is-active', active);
      b.setAttribute('aria-pressed', String(active));
      b.parentElement.classList.toggle('is-traced', index !== -1 && i >= index);
    });
    tokens.forEach((t) => t.classList.toggle('is-linked', t.dataset.for === key));
    caption.textContent = messages[key] || defaultText;
  }

  let current = null;
  buttons.forEach((b) => {
    b.addEventListener('click', () => {
      current = current === b.dataset.source ? null : b.dataset.source;
      show(current);
    });
  });

  hint.hidden = false;
})();
