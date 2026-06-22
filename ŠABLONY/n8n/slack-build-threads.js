// Node: Sestav thready k načtení
// Jen vlákna v capture kanálu — bot nemá přístup do cizích kanálů/DM (conversations.replies → channel_not_found).
// Forwardovaný obsah je už v message attachments (## Forwardovaný obsah v Format → Markdown).

const pack = $input.first().json;
const ev = pack.slackEvent;
const threads = [];
const seen = new Set();

function addThread(channelId, threadTs, label) {
  if (!channelId || !threadTs) return;
  const key = `${channelId}:${threadTs}`;
  if (seen.has(key)) return;
  seen.add(key);
  threads.push({ channelId, threadTs, label });
}

if (ev.thread_ts) {
  addThread(ev.channel, ev.thread_ts, 'capture');
}

return [{ json: { ...pack, threadsToFetch: threads } }];
