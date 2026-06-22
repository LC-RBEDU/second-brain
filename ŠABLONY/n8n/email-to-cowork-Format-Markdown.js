// Gmail Trigger: Simplify = OFF (simple: false).
// Drive fetch JE V DOWNSTREAM uzlech (Code node sandbox blokuje httpRequestWithAuthentication).
const TZ = 'Europe/Prague';
const MAX_LINKED_DOCS = 10;

/** Slug pro název souboru: NFC, zachová diakritiku (češtinu), odstraní jen znaky nebezpečné v názvech souborů. */
function filenameFriendlySlug(s, maxLen) {
  let t = String(s || '').normalize('NFC');
  t = t.replace(/<[^>]*>/g, ' ');
  t = t.split('<')[0].trim();
  t = t.replace(/^["'\s]+|["'\s]+$/g, '');
  t = t.replace(/[\u0000-\u001f\u007f\\/:?*|#"<>%]+/g, '-');
  t = t.replace(/\s+/g, '-');
  t = t.replace(/-+/g, '-').replace(/^-|-$/g, '');
  t = t.toLocaleLowerCase('cs-CZ');
  if (!t) t = 'unnamed';
  if (t.length > maxLen) t = t.substring(0, maxLen).replace(/-+$/g, '');
  return t;
}

function pragueFilenameTs(date) {
  const dtf = new Intl.DateTimeFormat('en-GB', {
    timeZone: TZ,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
  const parts = {};
  for (const { type, value } of dtf.formatToParts(date)) {
    if (type !== 'literal') parts[type] = value;
  }
  return `${parts.year}-${parts.month}-${parts.day}-${parts.hour}${parts.minute}`;
}

function addrToText(v) {
  if (!v) return '';
  if (typeof v === 'string') return v;
  if (typeof v === 'object') {
    if (v.text) return v.text;
    if (Array.isArray(v)) return v.map(addrToText).filter(Boolean).join(', ');
    if (Array.isArray(v.value)) {
      return v.value.map((x) => x && (x.address || x.name)).filter(Boolean).join(', ');
    }
  }
  return '';
}

function htmlToText(html) {
  if (html == null) return '';
  const s =
    typeof html === 'string'
      ? html
      : html && typeof html.toString === 'function'
        ? html.toString()
        : '';
  if (!s) return '';
  return s
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<head[\s\S]*?<\/head>/gi, ' ')
    .replace(/<br\s*\/?>(?=)/gi, '\n')
    .replace(/<\/(p|div|li|tr|h[1-6])>/gi, '\n')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/[ \t]{2,}/g, ' ')
    .trim();
}

function extractGoogleLinks(text) {
  if (!text) return [];
  const s = String(text);
  const patterns = [
    /https?:\/\/(?:docs|drive|sheets|slides|forms|sites|meet)\.google\.com\/[^\s"'<>\)\]]+/gi,
    /https?:\/\/drive\.google\.com\/open\?[^\s"'<>\)\]]+/gi,
  ];
  const all = [];
  for (const re of patterns) {
    const m = s.match(re) || [];
    all.push(...m);
  }
  return Array.from(new Set(all.map((u) => u.replace(/[).,;]+$/, ''))));
}

function extractHrefsFromHtml(html) {
  if (!html) return [];
  const s = String(html);
  const hrefs = [];
  const re = /href\s*=\s*["']([^"']+)["']/gi;
  let m;
  while ((m = re.exec(s)) !== null) {
    hrefs.push(m[1].replace(/&amp;/g, '&'));
  }
  return hrefs;
}

function extractSaferedirectUrls(html) {
  if (!html) return [];
  const s = String(html);
  const out = [];
  const re = /data-saferedirecturl\s*=\s*["']([^"']+)["']/gi;
  let m;
  while ((m = re.exec(s)) !== null) {
    out.push(m[1].replace(/&amp;/g, '&'));
  }
  return out;
}

function expandRedirectUrls(urls) {
  const seen = new Set();
  const out = [];
  for (const u of urls || []) {
    if (u && !seen.has(u)) {
      seen.add(u);
      out.push(u);
    }
    if (!u || typeof u !== 'string') continue;
    try {
      if (!/google\.(?:com|[a-z]{2,3})\/url\?/i.test(u)) continue;
      const parsed = new URL(u);
      for (const key of ['q', 'url']) {
        const inner = parsed.searchParams.get(key);
        if (!inner) continue;
        let dec = inner;
        try {
          dec = decodeURIComponent(inner);
        } catch (e) {
          dec = inner;
        }
        if (/^https?:\/\//i.test(dec) && !seen.has(dec)) {
          seen.add(dec);
          out.push(dec);
        }
      }
    } catch (e) {
      /* ignore */
    }
  }
  return out;
}

function extractDriveFileIds(urls) {
  const seen = new Set();
  const out = [];
  const patterns = [
    /\/document\/d\/([a-zA-Z0-9_-]+)/,
    /\/spreadsheets\/d\/([a-zA-Z0-9_-]+)/,
    /\/presentation\/d\/([a-zA-Z0-9_-]+)/,
    /\/forms\/d\/([a-zA-Z0-9_-]+)/,
    /\/file\/d\/([a-zA-Z0-9_-]+)/,
    /[?&]id=([a-zA-Z0-9_-]+)/,
  ];
  for (const url of urls || []) {
    for (const re of patterns) {
      const m = String(url).match(re);
      if (m && m[1] && !seen.has(m[1])) {
        seen.add(m[1]);
        out.push({ id: m[1], sourceUrl: url });
      }
    }
  }
  return out;
}

function binaryAttachmentList(binary) {
  if (!binary || typeof binary !== 'object') return [];
  return Object.keys(binary).map((k) => {
    const b = binary[k];
    const name = (b && b.fileName) || k;
    const mime = (b && b.mimeType) || '';
    return { key: k, name, mime };
  });
}

const items = [];
for (const item of $input.all()) {
  const e = item.json;

  const dateMs = e.internalDate
    ? parseInt(String(e.internalDate), 10)
    : e.date
      ? new Date(e.date).getTime()
      : Date.now();
  const date = new Date(dateMs);
  const ts = pragueFilenameTs(date);

  const fromText = addrToText(e.from) || addrToText(e.headers && e.headers.from) || 'unknown';
  const toText = addrToText(e.to) || addrToText(e.headers && e.headers.to) || '';
  const fromDisplay = String(fromText)
    .split('<')[0]
    .replace(/<[^>]+>/g, '')
    .trim()
    .replace(/^["']|["']$/g, '');
  const fromWords = fromDisplay.split(/\s+/).filter(Boolean).slice(0, 2).join(' ');
  const fromSlug = filenameFriendlySlug(fromWords || 'unknown', 40);
  const subject = (e.subject && String(e.subject).trim()) || 'no-subject';
  const subjectClean = subject.replace(/^(Re:|Fwd:|FW:|RE:|FWD:)\s*/gi, '').trim();
  const subjectSlug = filenameFriendlySlug(subjectClean, 80);
  const filename = `${ts}-${fromSlug}-${subjectSlug || 'no-subject'}.md`;

  const plain = e.text && String(e.text).trim();
  const htmlRaw = e.html != null ? e.html : e.textAsHtml || '';
  const htmlText = htmlToText(htmlRaw);
  const snippet = e.snippet && String(e.snippet).trim();
  let body = plain || htmlText;
  if (!body && snippet) {
    body =
      snippet +
      '\n\n_(jen Gmail snippet — máš zapnutý Simplify u Gmail triggeru? Vypni ho pro plné tělo.)_';
  }
  if (!body) body = '_(prázdné tělo — ověř Simplify=OFF)_';

  const hrefs = extractHrefsFromHtml(htmlRaw);
  const safeUrls = extractSaferedirectUrls(htmlRaw);
  const headerBlob =
    e.headers && typeof e.headers === 'object'
      ? JSON.stringify(e.headers).substring(0, 12000)
      : '';
  const haystackForLinks = `${plain || ''}\n${String(htmlRaw || '')}\n${hrefs.join('\n')}\n${safeUrls.join('\n')}\n${subject}\n${snippet || ''}\n${headerBlob}`;
  let links = extractGoogleLinks(haystackForLinks);
  links = expandRedirectUrls(links);
  const fileRefs = extractDriveFileIds(links).slice(0, MAX_LINKED_DOCS);

  const firstRef = fileRefs.length ? fileRefs[0] : null;

  const TOPIC_KEYWORDS = {
    'rb-universe': ['rb universe', 'rebel', 'pgvector', 'pipedrive', 'fio', 'fakturoid'],
    'ceo-reporting': ['ceo', 'reporting', 'dashboard', 'mixpanel', 'sales review'],
    'finance-procesy': ['fakturace', 'finance', 'účetní', 'allfred'],
    'interni-pravidla': ['cesťák', 'cesťáky', 'výdaje', 'platby kartou', 'evidence'],
  };
  const haystack = (subject + ' ' + body).toLowerCase();
  let suggestedTopic = null;
  for (const [topic, kws] of Object.entries(TOPIC_KEYWORDS)) {
    if (kws.some((k) => haystack.includes(k))) {
      suggestedTopic = topic;
      break;
    }
  }


  const lines = [
    `# Email: ${subject}`,
    '',
    `**From**: ${fromText}`,
    `**To**: ${toText}`,
    `**Date**: ${date.toLocaleString('cs-CZ', { timeZone: TZ })}`,
    `**Suggested topic**: ${suggestedTopic || '(nerozpoznáno)'}`,
    `**Gmail message ID**: ${e.id || ''}`,
    '',
  ];

  if (links.length) {
    lines.push('## Shared links (Google Drive / Docs)', '');
    for (const u of links) lines.push('- ' + u);
    lines.push('');
  }

  lines.push('## Tělo', '', body, '');

  const md = lines.join('\n');
  const binList = item.binary ? Object.keys(item.binary) : [];

  const row = {
    json: {
      filename,
      content: md,
      firstRefId: firstRef ? firstRef.id : '',
      firstRefUrl: firstRef ? firstRef.sourceUrl : '',
      _meta: {
        hasHtml: !!htmlRaw,
        hasText: !!plain,
        usedSnippetFallback: !plain && !htmlText && !!snippet,
        linkCount: links.length,
        binaryCount: binList.length,
        firstRefId: firstRef ? firstRef.id : '',
      },
    },
  };
  if (item.binary && Object.keys(item.binary).length) {
    row.binary = item.binary;
  }
  items.push(row);
}

return items;
