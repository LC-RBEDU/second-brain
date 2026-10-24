/** Match http(s), www., and bare domains with a short TLD list (cz/com/…). */
const URL_RE =
  /https?:\/\/[^\s<>"']+|www\.[^\s<>"']+|\b(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+(?:cz|com|io|org|net|ai|app|dev|edu|cloud|info|me|co)(?:\/[^\s<>"']*)?/gi;

const TRAIL_PUNCT = /[.,;:!?)\]}'"]+$/;

/**
 * Split plain text into { text, href? } parts. href is a safe http(s) URL or null for plain.
 * @param {string} text
 * @returns {{ text: string, href: string | null }[]}
 */
export function linkifyParts(text) {
  const source = String(text || "");
  if (!source) return [];
  const parts = [];
  let last = 0;
  URL_RE.lastIndex = 0;
  let match;
  while ((match = URL_RE.exec(source)) !== null) {
    let raw = match[0];
    let trail = "";
    const punct = raw.match(TRAIL_PUNCT);
    if (punct) {
      trail = punct[0];
      raw = raw.slice(0, -trail.length);
    }
    if (match.index > last) {
      parts.push({ text: source.slice(last, match.index), href: null });
    }
    const href = toHref(raw);
    if (href) {
      parts.push({ text: raw, href });
    } else {
      parts.push({ text: raw, href: null });
    }
    if (trail) parts.push({ text: trail, href: null });
    last = match.index + match[0].length;
  }
  if (last < source.length) {
    parts.push({ text: source.slice(last), href: null });
  }
  return parts;
}

/** @param {string} raw */
export function toHref(raw) {
  const trimmed = String(raw || "").trim();
  if (!trimmed) return null;
  let candidate = trimmed;
  if (/^www\./i.test(candidate)) candidate = `https://${candidate}`;
  else if (!/^https?:\/\//i.test(candidate)) candidate = `https://${candidate}`;
  try {
    const parsed = new URL(candidate);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return null;
    return parsed.href;
  } catch {
    return null;
  }
}
