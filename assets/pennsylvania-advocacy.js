/* Visitor-controlled PA drafts. No storage, sending or personal-data analytics. */
(function () {
  'use strict';
  const byId = id => document.getElementById(id);
  const builder = byId('pa-letter-builder');
  if (!builder) return;
  const topic = byId('pa-topic'), place = byId('pa-place'), reason = byId('pa-reason');
  const draft = byId('pa-draft'), status = byId('pa-letter-status'), build = byId('pa-build');
  const printText = byId('pa-letter-print');
  const questions = {
    market: 'What adult-use regulatory model would you support, and how would it provide workable opportunities for independent Pennsylvania businesses, patients, workers and local communities?',
    equity: 'What record-clearing, licensing-access and community-reinvestment provisions would you support alongside adult-use legalization, and how would their results be reported?',
    patients: 'How would you protect medical patient access, affordability and continuity of care in any adult-use legislation you support?',
    local: 'How would you address local authority, tax revenue, public health protections and community costs in adult-use legislation, and how would those results be measured and reported?'
  };
  function update() {
    const empty = !draft.value.trim();
    ['pa-copy', 'pa-download', 'pa-print'].forEach(id => { byId(id).disabled = empty; });
    printText.textContent = draft.value;
  }
  build.addEventListener('click', () => {
    const parts = ['Dear Pennsylvania legislator,'];
    if (place.value.trim()) parts.push('I live in ' + place.value.trim() + '.');
    parts.push('I am writing to ask about your position on Pennsylvania cannabis policy.', questions[topic.value]);
    if (reason.value.trim()) parts.push(reason.value.trim());
    parts.push('What specific bill, amendment or next step would you support, and how can I follow your action?', 'Thank you,\n[Your name]');
    draft.value = parts.join('\n\n');
    build.textContent = 'Rebuild and replace draft';
    status.textContent = 'Draft ready. Review and edit it before contacting your officials.';
    update();
  });
  [topic, place, reason].forEach(el => el.addEventListener('input', () => {
    if (draft.value) status.textContent = 'Choices changed. Your draft and edits are preserved. Rebuild to replace them; exports use the message shown below.';
  }));
  draft.addEventListener('input', () => { update(); status.textContent = 'Edits kept in the message shown here.'; });
  byId('pa-copy').addEventListener('click', async () => {
    const text = draft.value;
    try {
      await navigator.clipboard.writeText(text);
      status.textContent = 'Message copied. Paste it into your official’s contact form.';
    } catch (_) {
      draft.focus(); draft.select();
      status.textContent = 'Automatic copy is unavailable. Your message is selected; use your device’s Copy command.';
    }
  });
  byId('pa-download').addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([draft.value], {type: 'text/plain;charset=utf-8'}));
    const link = document.createElement('a');
    link.href = url; link.download = 'pennsylvania-cannabis-message.txt';
    document.body.appendChild(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    status.textContent = 'Downloaded the message shown here.';
  });
  function endPrint() { document.body.classList.remove('pa-print-letter'); }
  byId('pa-print').addEventListener('click', () => {
    update(); document.body.classList.add('pa-print-letter');
    try { window.print(); } finally { endPrint(); }
  });
  window.addEventListener('afterprint', endPrint);
  byId('pa-clear').addEventListener('click', () => {
    place.value = ''; reason.value = ''; draft.value = ''; topic.selectedIndex = 0;
    build.textContent = 'Build draft'; update();
    status.textContent = 'Message and personal details cleared from this page.';
  });
  builder.hidden = false;
  update();
})();
