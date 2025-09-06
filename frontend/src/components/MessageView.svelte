<script>
  import { marked } from 'marked'
  
  export let conversation
  
  
  function formatTime(timestamp) {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    const now = new Date()
    const diffHours = Math.floor((now - date) / (1000 * 60 * 60))
    
    if (diffHours < 1) return 'now'
    if (diffHours === 1) return '1h ago'
    return `${diffHours}h ago`
  }
  
  function renderMarkdown(content) {
    return marked(content, {
      breaks: true,
      gfm: true
    })
  }
</script>

<!-- Conversation header -->
<div class="main__header">
  <div class="main__titles">
    <h2 class="main__name">{conversation?.title || 'Untitled Conversation'}</h2>
    <p class="main__sub">Last updated Sep 4</p>
  </div>
  <div class="main__actions">
    <span class="badge badge--amber">Claude</span>
    <button class="btn">Copy</button>
    <button class="btn">Refresh</button>
  </div>
</div>

<!-- Messages -->
<div class="messages">
  {#each conversation?.messages || [] as message}
    {#if message.role === 'user'}
      <!-- User message with bubble -->
      <article class="msg msg--me">
        <div class="bubble">
          <header class="bubble__hdr">
            <div class="bubble__meta">
              <strong>You</strong>
              <span class="bubble__time">{formatTime(message.timestamp)}</span>
            </div>
            <button class="btn btn--xs">Copy</button>
          </header>
          <p class="bubble__text">{message.content}</p>
        </div>
        <div class="avatar" role="img" aria-label="user avatar">Y</div>
      </article>
    {:else}
      <!-- AI message without bubble -->
      <article class="msg msg--ai">
        <div class="avatar" role="img" aria-label="ai avatar">A</div>
        <div class="ai">
          <div class="ai__meta">
            <strong>AI</strong>
            <span class="ai__time">{formatTime(message.timestamp)}</span>
          </div>
          <div class="ai__content">
            {@html renderMarkdown(message.content)}
          </div>
          <div class="ai__actions">
            <button class="btn btn--xs">Copy</button>
          </div>
        </div>
      </article>
    {/if}
  {/each}
</div>

<style>
  /* CSS variables matching the mockup */
  :root {
    --bg: #fafafa;
    --panel: #ffffff;
    --ink: #0b0b0c;
    --muted: #6b7280;
    --line: #e5e7eb;
    --line-strong: #d1d5db;
    --indigo: #4f46e5;
    --indigo-weak: #eef2ff;
    --amber: #f59e0b;
    --shadow: 0 1px 2px rgba(0,0,0,.06), 0 10px 30px rgba(0,0,0,.06);
  }

  /* Main header */
  .main__header {
    position: sticky;
    top: 0;
    z-index: 4;
    background: var(--panel);
    border-bottom: 1px solid var(--line);
    padding: 12px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
  }

  .main__name {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
  }

  .main__sub {
    margin: 2px 0 0;
    font-size: 12px;
    color: var(--muted);
  }

  .main__actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  /* Messages */
  .messages {
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .msg {
    display: flex;
    gap: 10px;
  }

  .msg--me {
    justify-content: flex-end;
  }

  /* Avatars */
  .avatar {
    width: 28px;
    height: 28px;
    border-radius: 999px;
    background: #e5e7eb;
    color: #111;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
  }

  @media (prefers-color-scheme: dark) {
    .avatar {
      background: #2b2e36;
      color: #e7e9ef;
    }
  }

  /* User bubble */
  .bubble {
    max-width: 75ch;
    border: 1px solid var(--line);
    background: var(--panel);
    border-radius: 18px;
    padding: 14px;
    box-shadow: var(--shadow);
  }

  .msg--me .bubble {
    background: var(--indigo-weak);
    border-color: color-mix(in oklab, var(--indigo) 30%, var(--line));
  }

  .bubble__hdr {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }

  .bubble__meta {
    font-size: 13px;
  }

  .bubble__time {
    margin-left: 6px;
    color: var(--muted);
    font-size: 12px;
  }

  .bubble__text {
    margin: 0;
    font-size: 15px;
    line-height: 1.55;
  }

  /* AI content (no bubble) */
  .msg--ai .avatar {
    margin-right: 2px;
  }

  .ai {
    max-width: 75ch;
  }

  .ai__meta {
    font-size: 13px;
    color: var(--muted);
    margin-bottom: 6px;
  }

  .ai__time {
    margin-left: 6px;
  }

  .ai__content {
    font-size: 15px;
    line-height: 1.6;
  }

  .ai__content :global(h1),
  .ai__content :global(h2),
  .ai__content :global(h3) {
    margin: 0.5rem 0 0.25rem;
    line-height: 1.25;
    font-weight: 700;
  }

  .ai__content :global(h3) {
    font-size: 16px;
  }

  .ai__content :global(p) {
    margin: 0.5rem 0;
  }

  .ai__content :global(ol),
  .ai__content :global(ul) {
    margin: 0.5rem 0 0.5rem 1.25rem;
  }

  .ai__content :global(li) {
    margin: 0.25rem 0;
  }

  .ai__content :global(code) {
    background: color-mix(in oklab, #ddd 35%, transparent);
    padding: 0 4px;
    border-radius: 6px;
  }

  @media (prefers-color-scheme: dark) {
    .ai__content :global(code) {
      background: #1c2030;
    }
  }

  .ai__content :global(pre) {
    margin: 0.6rem 0;
    padding: 12px;
    border-radius: 12px;
    border: 1px solid var(--line);
    background: var(--panel);
    overflow: auto;
    font-size: 13px;
  }

  .ai__content :global(blockquote) {
    margin: 0.6rem 0;
    padding: 10px 12px;
    border-left: 3px solid var(--indigo);
    background: var(--indigo-weak);
    border-radius: 10px;
  }

  .ai__actions {
    margin-top: 8px;
  }

  /* Buttons & badges */
  .btn {
    padding: 8px 12px;
    border: 1px solid var(--line-strong);
    border-radius: 10px;
    font-size: 13px;
    background: transparent;
    color: var(--ink);
    cursor: pointer;
  }

  .btn:hover {
    background: color-mix(in lab, var(--panel) 92%, transparent);
  }

  .btn--primary {
    background: var(--indigo);
    border-color: var(--indigo);
    color: #fff;
  }

  .btn--primary:hover {
    filter: brightness(1.05);
  }

  .btn--xs {
    padding: 4px 8px;
    font-size: 12px;
    border-radius: 8px;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    height: 22px;
    padding: 0 8px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    background: #eef2f7;
    color: #334155;
  }

  .badge--indigo {
    background: var(--indigo-weak);
    color: var(--indigo);
  }

  .badge--amber {
    background: color-mix(in oklab, var(--amber) 20%, transparent);
    color: var(--amber);
  }
</style>