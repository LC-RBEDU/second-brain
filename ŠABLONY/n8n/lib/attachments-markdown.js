/**
 * SSOT helper — canonical ## Přílohy block for n8n Code nodes.
 * Copy into workflow jsCode or require inline (n8n has no module imports).
 *
 * Format:
 *   ## Přílohy
 *   - [filename.pdf](webViewLink) — application/pdf, 1.2 MB
 */

function formatFileSize(bytes) {
  const n = Number(bytes);
  if (!n || n <= 0) return '';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} kB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * @param {Array<{name?: string, webViewLink?: string, mimeType?: string, size?: number}>} attachments
 * @returns {string[]} markdown lines (empty when no attachments)
 */
function buildAttachmentsSectionLines(attachments) {
  const list = Array.isArray(attachments) ? attachments : [];
  if (!list.length) return [];
  const heading =
    list.length === 1 ? '## Přílohy' : `## Přílohy (${list.length})`;
  const lines = [heading, ''];
  for (const a of list) {
    const name = String(a.name || a.fileName || 'attachment').trim();
    const link = a.webViewLink || a.webContentLink || a.url || '';
    const mime = a.mimeType || a.mime || '';
    const size = formatFileSize(a.size);
    const meta = [mime, size].filter(Boolean).join(', ');
    if (link) {
      lines.push(`- [${name}](${link})${meta ? ` — ${meta}` : ''}`);
    } else {
      lines.push(`- ${name}${meta ? ` — ${meta}` : ''}`);
    }
  }
  lines.push('');
  return lines;
}

/**
 * Replace legacy attachment sections or append canonical block.
 * @param {string} content
 * @param {Array} attachments
 */
function injectAttachmentsSection(content, attachments) {
  let md = String(content || '');
  const legacyRe =
    /\n## Přílohy(?: \(stažené v n8n\)| \(\d+\))?\s*\n[\s\S]*?(?=\n## |\n*$)/i;
  md = md.replace(legacyRe, '\n');
  const section = buildAttachmentsSectionLines(attachments);
  if (!section.length) return md.trimEnd() + '\n';
  return md.trimEnd() + '\n\n' + section.join('\n');
}

module.exports = {
  buildAttachmentsSectionLines,
  formatFileSize,
  injectAttachmentsSection,
};
