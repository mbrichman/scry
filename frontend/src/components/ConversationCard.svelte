<script>
  import { createEventDispatcher } from 'svelte'
  
  export let conversation
  
  const dispatch = createEventDispatcher()
  
  function handleClick() {
    dispatch('select', { conversation })
  }
  
  function formatDate(dateString) {
    if (!dateString) return ''
    
    try {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      
      const now = new Date()
      const isThisYear = date.getFullYear() === now.getFullYear()
      
      const options = {
        month: 'short',
        day: 'numeric'
      }
      
      if (!isThisYear) {
        options.year = 'numeric'
      }
      
      return date.toLocaleDateString(undefined, options)
    } catch (e) {
      return dateString
    }
  }
  
  function getSourceDisplayName(source) {
    switch (source?.toLowerCase()) {
      case 'chatgpt':
        return 'ChatGPT'
      case 'claude':
        return 'Claude'
      case 'docx':
        return 'Word Doc'
      default:
        return source || 'Unknown'
    }
  }
  
  function getSourceBadgeColor(source) {
    switch (source?.toLowerCase()) {
      case 'chatgpt':
        return 'bg-green-100 text-green-800'
      case 'claude':
        return 'bg-blue-100 text-blue-800'
      case 'docx':
        return 'bg-purple-100 text-purple-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }
</script>

<button 
  class="conversation-card w-full text-left p-4 rounded-lg border border-gray-200 hover:border-gray-300 hover:shadow-sm transition-all duration-200 bg-white"
  on:click={handleClick}
  role="button"
  tabindex="0"
>
  <div class="flex items-start justify-between gap-3 mb-2">
    <h3 class="font-medium text-gray-900 line-clamp-2 flex-1">
      {conversation.title || 'Untitled Conversation'}
    </h3>
    <div class="flex items-center gap-2 flex-shrink-0">
      <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium {getSourceBadgeColor(conversation.source)}">
        {getSourceDisplayName(conversation.source)}
      </span>
      {#if conversation.date}
        <span class="text-xs text-gray-500 whitespace-nowrap">
          {formatDate(conversation.date)}
        </span>
      {/if}
    </div>
  </div>
  
  {#if conversation.preview}
    <p class="text-sm text-gray-600 line-clamp-2 leading-relaxed">
      {conversation.preview}
    </p>
  {/if}
</button>

<style>
  .conversation-card:hover {
    transform: translateY(-1px);
  }
  
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  .conversation-card:focus {
    outline: 2px solid #6366f1;
    outline-offset: 2px;
  }
</style>