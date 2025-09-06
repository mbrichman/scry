<script>
  import { createEventDispatcher } from 'svelte'
  import ConversationCard from './ConversationCard.svelte'
  
  export let conversations = []
  export let isLoading = false
  export let searchQuery = ''
  
  const dispatch = createEventDispatcher()
  
  function handleConversationSelect(event) {
    dispatch('conversationSelect', event.detail)
  }
  
  function getResultsText() {
    if (!searchQuery) return ''
    
    const count = conversations.length
    const plural = count === 1 ? 'result' : 'results'
    return `${count} ${plural} for "${searchQuery}"`
  }
</script>

<div class="conversation-list">
  {#if isLoading}
    <div class="loading-state" role="status" aria-live="polite">
      <div class="flex items-center justify-center py-8">
        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mr-3"></div>
        <span class="text-gray-600">Loading conversations...</span>
      </div>
    </div>
  {:else if conversations.length === 0}
    <div class="empty-state py-12 text-center">
      {#if searchQuery}
        <p class="text-sm text-gray-500 mb-2">{getResultsText()}</p>
      {/if}
      <div class="text-gray-400 text-4xl mb-4">💬</div>
      <h3 class="text-lg font-medium text-gray-900 mb-2">No conversations found</h3>
      <p class="text-gray-500">
        {#if searchQuery}
          Try a different search term or browse all conversations.
        {:else}
          Upload some conversation files to get started.
        {/if}
      </p>
    </div>
  {:else}
    {#if searchQuery}
      <div class="results-header mb-4">
        <p class="text-sm text-gray-600">{getResultsText()}</p>
      </div>
    {/if}
    
    <ul class="conversation-list-inner" role="list" aria-label="Conversations list">
      {#each conversations as conversation (conversation.id)}
        <li role="listitem">
          <ConversationCard 
            {conversation} 
            on:select={handleConversationSelect}
          />
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .conversation-list {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem;
    min-height: 0;
  }
  
  .conversation-list-inner {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .loading-state {
    min-height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .empty-state {
    min-height: 200px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  
  .results-header {
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e5e7eb;
  }
  
  ul.conversation-list-inner {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  ul.conversation-list-inner li {
    padding: 0 0.25rem;
  }
  
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
  
  .animate-spin {
    animation: spin 1s linear infinite;
  }
</style>