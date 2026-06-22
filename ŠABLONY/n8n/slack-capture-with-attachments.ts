import { workflow, node, trigger, ifElse, newCredential, expr } from '@n8n/workflow-sdk';

const slackTrigger = trigger({
  type: 'n8n-nodes-base.slackTrigger',
  version: 1,
  config: {
    name: 'Slack: nová zpráva',
    parameters: {
      trigger: ['message'],
      watchWorkspace: false,
      channelId: { __rl: true, mode: 'id', value: 'REPLACE_WITH_PRIVATE_CAPTURE_CHANNEL_ID' },
      options: {},
    },
    credentials: { slackApi: newCredential('Slack App (Socket Mode)') },
    position: [200, 300],
  },
  output: [{ event: { type: 'message', channel: 'C123', user: 'U123', ts: '1748169000.000100', text: 'demo', files: [] } }],
});

const filterMessages = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Filtrovat zprávy',
    parameters: {
      jsCode: "const raw = $input.first().json;\nconst ev = raw.event || raw;\nif (!ev || (ev.type && ev.type !== 'message')) return [];\nconst skip = new Set(['channel_join','channel_leave','group_join','message_changed','message_deleted','channel_topic','channel_purpose','channel_archive','channel_unarchive','pinned_item','unpinned_item','file_comment']);\nif (ev.subtype && skip.has(ev.subtype)) return [];\nif (ev.subtype === 'bot_message') return [];\nif (!ev.channel) return [];\nconst directFiles = Array.isArray(ev.files) ? ev.files : [];\nconst unfurlFiles = (Array.isArray(ev.attachments) ? ev.attachments : []).flatMap((a) => (Array.isArray(a?.files) ? a.files : []));\nconst seen = new Set();\nconst files = [];\nfor (const f of [...directFiles, ...unfurlFiles]) {\n  const key = f?.id || f?.url_private_download;\n  if (!key || seen.has(key)) continue;\n  seen.add(key);\n  files.push(f);\n}\nconst hasText = ev.text && String(ev.text).trim().length > 0;\nconst hasFiles = files.length > 0;\nconst hasAttachments = Array.isArray(ev.attachments) && ev.attachments.length > 0;\nif (!hasText && !hasFiles && !hasAttachments) return [];\nreturn [{ json: { channelId: ev.channel, slackEvent: ev, files } }];",
    },
    position: [420, 300],
  },
  output: [{ channelId: 'C123', slackEvent: { ts: '1748169000.000100', user: 'U123', text: 'demo', files: [] }, files: [] }],
});

const channelInfo = node({
  type: 'n8n-nodes-base.slack',
  version: 2.4,
  config: {
    name: 'Slack: Channel info',
    parameters: {
      resource: 'channel',
      operation: 'get',
      channelId: { __rl: true, mode: 'id', value: expr('{{ $json.channelId }}') },
      options: {},
    },
    credentials: { slackApi: newCredential('Slack App (Socket Mode)') },
    position: [640, 300],
  },
  output: [{ id: 'C123', name: 'capture' }],
});

const hasFilesCheck = ifElse({
  version: 2.3,
  config: {
    name: 'Má přílohy?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose', version: 2 },
        conditions: [
          {
            id: 'has-files',
            leftValue: expr("{{ ($('Filtrovat zprávy').first().json.files || []).length }}"),
            rightValue: 0,
            operator: { type: 'number', operation: 'gt' },
          },
        ],
        combinator: 'and',
      },
      options: {},
    },
    position: [860, 300],
  },
});

const prepareAttachments = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Připrav přílohy',
    parameters: {
      jsCode: "const pack = $('Filtrovat zprávy').first().json;\nconst e = pack.slackEvent;\nconst files = pack.files || [];\nconst date = new Date(parseFloat(e.ts) * 1000);\nconst ts = `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}-${String(date.getHours()).padStart(2,'0')}${String(date.getMinutes()).padStart(2,'0')}`;\nreturn files.map((f, i) => {\n  const safeName = String(f.name || 'unnamed').replace(/[\\\\/]/g, '_');\n  const fileTag = f.id || `f${i}`;\n  return { json: { file: f, ts, targetName: `${ts}-${fileTag}-${safeName}`.substring(0, 200) } };\n});",
    },
    position: [1080, 480],
  },
  output: [{ file: { id: 'F123', name: 'demo.pdf', url_private_download: 'https://files.slack.com/demo' }, ts: '2026-05-25-2333', targetName: '2026-05-25-2333-F123-demo.pdf' }],
});

const httpDownload = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Stáhni přílohu (Slack auth)',
    parameters: {
      method: 'GET',
      url: expr('{{ $json.file.url_private_download }}'),
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'slackApi',
      options: {
        response: { response: { responseFormat: 'file', outputPropertyName: 'data' } },
        timeout: 120000,
      },
    },
    credentials: { slackApi: newCredential('Slack App (Socket Mode)') },
    position: [1300, 480],
  },
  output: [{ data: '<binary>', file: { id: 'F123', name: 'demo.pdf', url_private_download: 'https://files.slack.com/demo' }, ts: '2026-05-25-2333', targetName: '2026-05-25-2333-F123-demo.pdf' }],
});

const driveUploadAttachment = node({
  type: 'n8n-nodes-base.googleDrive',
  version: 3,
  config: {
    name: 'Drive: Upload přílohy',
    parameters: {
      resource: 'file',
      operation: 'upload',
      inputDataFieldName: 'data',
      name: expr('{{ $json.targetName }}'),
      driveId: { __rl: true, mode: 'list', value: 'My Drive' },
      folderId: { __rl: true, mode: 'id', value: '1bHjE9pEjKh3HOwVwjCH3V8t74-8FTNIm' },
      options: {},
    },
    credentials: { googleDriveOAuth2Api: newCredential('Google Drive account 2') },
    position: [1520, 480],
  },
  output: [{ id: 'driveFileId', name: '2026-05-25-2333-F123-demo.pdf', webViewLink: 'https://drive.google.com/file/d/x/view', mimeType: 'application/pdf', size: '12345' }],
});

const aggregateAttachments = node({
  type: 'n8n-nodes-base.aggregate',
  version: 1,
  config: {
    name: 'Aggregate přílohy',
    parameters: {
      aggregate: 'aggregateAllItemData',
      destinationFieldName: 'uploadedAttachments',
      include: 'allFields',
      options: {},
    },
    position: [1740, 480],
  },
  output: [{ uploadedAttachments: [{ id: 'x', name: 'demo.pdf', webViewLink: '...', mimeType: 'application/pdf', size: '12345' }] }],
});

const formatMarkdown = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Format → Markdown',
    parameters: {
      jsCode: "const pack = $('Filtrovat zprávy').first().json;\nconst e = pack.slackEvent;\nconst channelId = pack.channelId;\nconst ch = $('Slack: Channel info').first().json;\nconst channelName = ch.name || channelId || 'unknown';\nlet uploadedAttachments = [];\ntry {\n  const agg = $('Aggregate přílohy').first();\n  if (agg && agg.json && Array.isArray(agg.json.uploadedAttachments)) {\n    uploadedAttachments = agg.json.uploadedAttachments;\n  }\n} catch (_) {}\nconst date = new Date(parseFloat(e.ts) * 1000);\nconst ts = `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}-${String(date.getHours()).padStart(2,'0')}${String(date.getMinutes()).padStart(2,'0')}`;\nconst ownText = (e.text && String(e.text).trim()) ? String(e.text) : '';\nconst attachments = Array.isArray(e.attachments) ? e.attachments : [];\nconst forwards = attachments.filter(a => a && (a.is_msg_unfurl || a.from_url || a.text || a.fallback));\nconst slugSrc = ownText || (forwards[0] && (forwards[0].text || forwards[0].fallback)) || 'zprava';\nconst textSlug = String(slugSrc).replace(/[^a-z0-9 ]/gi,'').trim().replace(/\\s+/g,'-').toLowerCase().substring(0, 50);\nconst filename = `${ts}-${channelName}-${textSlug || 'slack'}.md`.substring(0, 120);\nconst permalink = `https://slack.com/archives/${channelId}/p${String(e.ts).replace('.','')}`;\nconst threadNote = e.thread_ts && e.thread_ts !== e.ts ? `**Odpověď ve vlákně** (thread_ts: ${e.thread_ts})` : '';\nconst lines = [`# #${channelName}`, '', `**Čas:** ${date.toLocaleString('cs-CZ')}`, `**Uživatel (Slack ID):** ${e.user || '—'}`, threadNote, `**Odkaz:** ${permalink}`, ''];\nif (ownText) { lines.push('## Komentář', '', ownText, ''); }\nif (forwards.length) {\n  lines.push(`## Forwardovaný obsah${forwards.length > 1 ? ` (${forwards.length})` : ''}`, '');\n  for (const a of forwards) {\n    const author = a.author_name || a.author_subname || '—';\n    const srcChannel = a.channel_name ? `#${a.channel_name}` : (a.channel_id || '');\n    const srcLink = a.from_url || '';\n    const srcTs = a.ts ? new Date(parseFloat(a.ts) * 1000).toLocaleString('cs-CZ') : '';\n    const body = String(a.text || a.fallback || '').replace(/^\\u200B+/, '').trim();\n    lines.push(`### ${author}${srcChannel ? ` v ${srcChannel}` : ''}${srcTs ? ` (${srcTs})` : ''}`);\n    if (srcLink) lines.push(`**Zdroj:** ${srcLink}`);\n    lines.push('');\n    lines.push(body || '_(prázdná příloha)_');\n    lines.push('');\n  }\n}\nif (uploadedAttachments.length) {\n  lines.push(`## Přílohy${uploadedAttachments.length > 1 ? ` (${uploadedAttachments.length})` : ''}`, '');\n  for (const a of uploadedAttachments) {\n    const link = a.webViewLink || '';\n    const name = a.name || '(bez jména)';\n    const mime = a.mimeType || '';\n    const sizeBytes = a.size ? parseInt(a.size, 10) : 0;\n    const sizeStr = sizeBytes ? (sizeBytes >= 1024*1024 ? `${(sizeBytes/1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(sizeBytes/1024))} kB`) : '';\n    const meta = [mime, sizeStr].filter(Boolean).join(', ');\n    lines.push(`- [${name}](${link})${meta ? ` — ${meta}` : ''}`);\n  }\n  lines.push('');\n}\nif (!ownText && !forwards.length && !uploadedAttachments.length) {\n  lines.push('## Text', '', '_(bez textu — v původní zprávě mohou být jen přílohy)_', '');\n}\nconst md = lines.join('\\n');\nreturn [{ json: { filename, content: md } }];",
    },
    position: [1960, 300],
  },
  output: [{ filename: '2026-05-25-2333-capture-demo.md', content: '# #capture\n\n...' }],
});

const driveSaveMd = node({
  type: 'n8n-nodes-base.googleDrive',
  version: 3,
  config: {
    name: 'Drive: Save .md to INBOX/slack/',
    parameters: {
      resource: 'file',
      operation: 'createFromText',
      content: expr('{{ $json.content }}'),
      name: expr('{{ $json.filename }}'),
      driveId: { __rl: true, mode: 'list', value: 'My Drive' },
      folderId: { __rl: true, mode: 'id', value: '1bHjE9pEjKh3HOwVwjCH3V8t74-8FTNIm' },
      options: {},
    },
    credentials: { googleDriveOAuth2Api: newCredential('Google Drive account 2') },
    position: [2180, 300],
  },
  output: [{ id: 'mdFileId', name: '2026-05-25-2333-capture-demo.md' }],
});

const slackReactSaved = node({
  type: 'n8n-nodes-base.slack',
  version: 2.4,
  config: {
    name: 'Slack: ✅ reakce po uložení',
    parameters: {
      resource: 'reaction',
      operation: 'add',
      channelId: { __rl: true, mode: 'id', value: expr("{{ $('Filtrovat zprávy').first().json.channelId }}") },
      timestamp: expr("{{ $('Filtrovat zprávy').first().json.slackEvent.ts }}"),
      name: 'white_check_mark',
    },
    credentials: { slackApi: newCredential('Slack App (Socket Mode)') },
    position: [2400, 300],
  },
  output: [{ ok: true }],
});

export default workflow('slack-capture-attachments', 'Slack capture kanál → Cowork INBOX (with attachments)')
  .add(slackTrigger)
  .to(filterMessages)
  .to(channelInfo)
  .to(hasFilesCheck
    .onTrue(prepareAttachments.to(httpDownload.to(driveUploadAttachment.to(aggregateAttachments.to(formatMarkdown.to(driveSaveMd.to(slackReactSaved)))))))
    .onFalse(formatMarkdown)
  );
