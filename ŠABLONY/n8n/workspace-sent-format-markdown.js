// SSOT mirror: ŠABLONY/n8n/workspace-sent-format-markdown.js
const TZ = 'Europe/Prague';

const SENT_INBOX_DROP_RULES = [
  { to: 'finance@redbutton.cz', subject: 'Fakturace dealu', dropReplies: true },
  { to: '*', subjectContains: 'Narozeniny a výročí' },
  { to: '*', subjectContains: '[Audits]' },
  { to: '*', subject: 'Podklady pro fakturaci' },
  { to: '*', subjectContains: 'out of office' },
  { to: '*', subjectContains: 'automatická odpověď' },
  { to: '*', subjectContains: 'automatic reply' },
  { to: '*', subjectContains: 'mimo kancelář' },
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
function shouldDropSentFromInbox(toText, subject, fromText) {
  const to = extractEmail(toText);
  const from = String(fromText || '').toLowerCase();
  const subj = normalizeSubject(subject).toLowerCase();
  const rawSub = String(subject || '').toLowerCase();
  const isReply = /^(Re:|Fwd:|FW:|RE:|FWD:)\s*/i.test(String(subject || '').trim());
  if (from.includes('calendar-noreply') || from.includes('calendar-notification@google.com')) return true;
  if (/^(accepted|declined|tentatively accepted|invitation|updated invitation):/i.test(rawSub)) return true;
  if (/out of office|automatick[aá] odpov|automatic reply|mimo kancel/i.test(rawSub)) return true;
  return SENT_INBOX_DROP_RULES.some((r) => {
    if (r.to !== '*' && to !== r.to.toLowerCase()) return false;
    if (r.subjectContains) {
      if (!subj.includes(r.subjectContains.toLowerCase())) return false;
    } else if (subj !== r.subject.toLowerCase()) return false;
    return !isReply || !!r.dropReplies;
  });
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
function yamlQuote(s) {
  return JSON.stringify(String(s || '').replace(/\n/g, ' '));
}
function headerValue(e, name) {
  const want = String(name || '').toLowerCase();
  const h = (e && e.headers) || (e && e.payload && e.payload.headers);
  if (!h) return '';
  if (Array.isArray(h)) {
    const row = h.find((x) => String((x && x.name) || '').toLowerCase() === want);
    return row ? String(row.value || '') : '';
  }
  if (typeof h === 'object') {
    for (const [k, v] of Object.entries(h)) {
      if (String(k).toLowerCase() === want) return typeof v === 'string' ? v : String((v && v.value) || v || '');
    }
  }
  return '';
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
  const inReplyTo = headerValue(e, 'in-reply-to');
  const gmailThreadId = String(e.threadId || e.thread_id || '');

  // New originated mail only — not a reply in someone else's thread.
  if (inReplyTo && String(inReplyTo).trim()) {
    continue;
  }
  if (/^(Re:|Fwd:|FW:|RE:|FWD:)\s*/i.test(subject)) {
    continue;
  }
  if (shouldDropSentFromInbox(toText, subject, fromText)) {
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
  const rfcMessageId = headerValue(e, 'message-id');
  const fm = [
    '---',
    'source: sent',
    'mailbox: workspace',
    `gmail_thread_id: ${yamlQuote(gmailThreadId)}`,
    `message_id: ${yamlQuote(rfcMessageId || messageId)}`,
    `in_reply_to: ${yamlQuote(inReplyTo)}`,
    `gmail_id: ${yamlQuote(messageId)}`,
    `to: ${yamlQuote(toText)}`,
    `subject: ${yamlQuote(subject)}`,
    `date: ${yamlQuote(date.toISOString())}`,
    `from: ${yamlQuote(fromText)}`,
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
  const row = { json: { filename, content: md, messageId, threadId: gmailThreadId } };
  if (item.binary && Object.keys(item.binary).length) row.binary = item.binary;
  items.push(row);
}
return items;
