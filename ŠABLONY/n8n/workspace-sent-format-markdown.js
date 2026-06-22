// SSOT for workspace-sent-to-inbox Format node (+ mirror in triage_commitments.py)
const TZ = 'Europe/Prague';

const SENT_INBOX_DROP_RULES = [
  { to: 'finance@redbutton.cz', subject: 'Fakturace dealu' },
];

function extractEmail(raw) {
  const s = String(raw || '').trim();
  const m = s.match(/<([^>]+)>/);
  if (m) return m[1].trim().toLowerCase();
  return s.split(',')[0].trim().toLowerCase();
}

function normalizeSubject(subject) {
  let t = String(subject || '').trim();
  while (/^(Re:|Fwd:|FW:|RE:|FWD:)\s*/i.test(t)) {
    t = t.replace(/^(Re:|Fwd:|FW:|RE:|FWD:)\s*/i, '').trim();
  }
  return t;
}

function shouldDropSentFromInbox(toText, subject) {
  const to = extractEmail(toText);
  const subj = normalizeSubject(subject).toLowerCase();
  return SENT_INBOX_DROP_RULES.some(
    (r) => to === r.to.toLowerCase() && subj === r.subject.toLowerCase(),
  );
}

function slug(s, maxLen) {
  let t = String(s || '')
    .normalize('NFC')
    .replace(/[\\/:?*|#"<>%]+/g, '-')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .toLocaleLowerCase('cs-CZ');
  if (!t) t = 'unnamed';
  return t.length > maxLen ? t.substring(0, maxLen).replace(/-+$/g, '') : t;
}

function tsPrague(d) {
  const p = Object.fromEntries(
    new Intl.DateTimeFormat('en-GB', {
      timeZone: TZ,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
      .formatToParts(d)
      .filter((x) => x.type !== 'literal')
      .map((x) => [x.type, x.value]),
  );
  return `${p.year}-${p.month}-${p.day}-${p.hour}${p.minute}`;
}

function addr(v) {
  if (!v) return '';
  if (typeof v === 'string') return v;
  if (v.text) return v.text;
  if (Array.isArray(v)) return v.map(addr).filter(Boolean).join(', ');
  if (Array.isArray(v.value))
    return v.value.map((x) => x && (x.address || x.name)).filter(Boolean).join(', ');
  return '';
}

function htmlToText(html) {
  if (!html) return '';
  return String(html)
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

const items = [];
for (const item of $input.all()) {
  const e = item.json;
  const messageId = String(e.id || e.messageId || '').trim();
  const date = new Date(
    e.internalDate
      ? parseInt(String(e.internalDate), 10)
      : e.date
        ? new Date(e.date).getTime()
        : Date.now(),
  );
  const fromText = addr(e.from) || 'lukas@redbuttonedu.cz';
  const toText = addr(e.to) || '';
  const subject = (e.subject && String(e.subject).trim()) || 'no-subject';
  const subjectClean = subject.replace(/^(Re:|Fwd:|FW:|RE:|FWD:)\s*/gi, '').trim();

  if (shouldDropSentFromInbox(toText, subject)) {
    continue;
  }

  const filename = `${tsPrague(date)}-sent-${slug(toText.split(',')[0] || 'recipient', 40)}-${slug(subjectClean, 60) || 'no-subject'}.md`;
  const plain = e.text && String(e.text).trim();
  const htmlText = htmlToText(e.html != null ? e.html : e.textAsHtml || '');
  const snippet = e.snippet && String(e.snippet).trim();
  let body =
    plain ||
    htmlText ||
    (snippet ? snippet + '\n\n_(snippet — vypni Simplify u triggeru)_' : '_(prázdné tělo)_');
  const fm = [
    '---',
    'source: sent',
    `messageId: ${messageId}`,
    `to: ${toText.replace(/\n/g, ' ')}`,
    `subject: ${subject.replace(/\n/g, ' ')}`,
    `date: ${date.toISOString()}`,
    `from: ${fromText.replace(/\n/g, ' ')}`,
    '---',
    '',
  ].join('\n');
  const md = [
    fm,
    `# Email: ${subject}`,
    '',
    '**Source**: sent',
    `**From**: ${fromText}`,
    `**To**: ${toText}`,
    `**Date**: ${date.toLocaleString('cs-CZ', { timeZone: TZ })}`,
    `**Gmail message ID**: ${messageId}`,
    '',
    '## Tělo',
    '',
    body,
    '',
  ].join('\n');
  const row = { json: { filename, content: md, messageId } };
  if (item.binary && Object.keys(item.binary).length) row.binary = item.binary;
  items.push(row);
}
return items;
