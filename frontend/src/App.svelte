<script>
  import { onMount } from 'svelte'
  import SearchBox from './components/SearchBox.svelte'
  import ConversationList from './components/ConversationList.svelte'
  import { searchConversations, getConversation } from './services/api.js'
  
  // App state
  let conversations = []
  let isLoading = false
  let searchQuery = ''
  let selectedConversation = null
  let errorMessage = ''
  
  // Handle search from SearchBox component
  async function handleSearch(event) {
    const query = event.detail.query
    searchQuery = query
    
    if (!query.trim()) {
      conversations = []
      return
    }
    
    try {
      isLoading = true
      errorMessage = ''
      
      console.log('🔍 Searching for:', query)
      const results = await searchConversations(query)
      
      conversations = results.results
      console.log('✅ Found', conversations.length, 'results')
      
    } catch (error) {
      console.error('❌ Search error:', error)
      errorMessage = 'Search failed. Please try again.'
      conversations = []
    } finally {
      isLoading = false
    }
  }
  
  // Handle conversation selection
  async function handleConversationSelect(event) {
    const conversation = event.detail.conversation
    console.log('📄 Selected conversation:', conversation.title)
    
    try {
      // For now, just log the selection
      // Later we could navigate to a detail view or show in a modal
      selectedConversation = conversation
      
      // Optional: fetch full conversation details
      // const fullConversation = await getConversation(conversation.id)
      // console.log('Full conversation:', fullConversation)
      
    } catch (error) {
      console.error('❌ Error loading conversation:', error)
    }
  }
  
  // Clear search results
  function clearSearch() {
    searchQuery = ''
    conversations = []
    selectedConversation = null
    errorMessage = ''
  }
</script>

<main>
  <div class="app-container">
    <!-- Header -->
    <header class="app-header">
      <div class="header-content">
        <h1 class="app-title">DovOS - Conversation Search</h1>
        <div class="header-actions">
          {#if searchQuery}
            <button class="clear-button" on:click={clearSearch}>
              Clear Search
            </button>
          {/if}
        </div>
      </div>
    </header>
    
    <!-- Main Content -->
    <div class="main-content">
      <!-- Search Section -->
      <section class="search-section">
        <SearchBox on:search={handleSearch} />
      </section>
      
      <!-- Error Message -->
      {#if errorMessage}
        <div class="error-message">
          <p>{errorMessage}</p>
        </div>
      {/if}
      
      <!-- Results Section -->
      <section class="results-section">
        {#if searchQuery}
          <ConversationList 
            {conversations}
            {isLoading}
            {searchQuery}
            on:conversationSelect={handleConversationSelect}
          />
        {:else}
          <!-- Welcome State -->
          <div class="welcome-state">
            <div class="welcome-icon">🔍</div>
            <h2>Search Your Conversations</h2>
            <p>Enter a search term above to find relevant conversations from your ChatGPT and Claude exports.</p>
            <div class="search-tips">
              <h3>Search Tips:</h3>
              <ul>
                <li>Try keywords like "python", "react", or "api"</li>
                <li>Use quotes for exact phrases: "machine learning"</li>
                <li>Search works across titles and conversation content</li>
              </ul>
            </div>
          </div>
        {/if}
      </section>
      
      <!-- Selected Conversation (Optional) -->
      {#if selectedConversation}
        <aside class="selection-info">
          <p><strong>Selected:</strong> {selectedConversation.title}</p>
          <p class="text-sm text-gray-600">Click to view full conversation (feature coming soon)</p>
        </aside>
      {/if}
    </div>
  </div>
</main>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    background-color: #f9fafb;
  }
  
  .app-container {
    min-height: 100vh;
    max-width: 1200px;
    margin: 0 auto;
  }
  
  .app-header {
    background: white;
    border-bottom: 1px solid #e5e7eb;
    padding: 1rem 2rem;
    position: sticky;
    top: 0;
    z-index: 10;
  }
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .app-title {
    color: #111827;
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
  }
  
  .clear-button {
    padding: 0.5rem 1rem;
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    color: #374151;
    cursor: pointer;
    font-size: 0.875rem;
    transition: all 0.2s;
  }
  
  .clear-button:hover {
    background: #e5e7eb;
    border-color: #9ca3af;
  }
  
  .main-content {
    padding: 2rem;
  }
  
  .search-section {
    margin-bottom: 2rem;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
  }
  
  .error-message {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 2rem;
    color: #dc2626;
    text-align: center;
  }
  
  .results-section {
    max-width: 800px;
    margin: 0 auto;
  }
  
  .welcome-state {
    text-align: center;
    padding: 4rem 2rem;
    background: white;
    border-radius: 0.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .welcome-icon {
    font-size: 4rem;
    margin-bottom: 1.5rem;
    opacity: 0.7;
  }
  
  .welcome-state h2 {
    color: #111827;
    margin-bottom: 1rem;
    font-size: 1.5rem;
  }
  
  .welcome-state p {
    color: #6b7280;
    margin-bottom: 2rem;
    font-size: 1.1rem;
  }
  
  .search-tips {
    background: #f9fafb;
    border-radius: 0.5rem;
    padding: 1.5rem;
    text-align: left;
    max-width: 400px;
    margin: 0 auto;
  }
  
  .search-tips h3 {
    color: #374151;
    margin: 0 0 1rem 0;
    font-size: 1rem;
  }
  
  .search-tips ul {
    margin: 0;
    padding-left: 1.5rem;
  }
  
  .search-tips li {
    color: #6b7280;
    margin-bottom: 0.5rem;
    line-height: 1.5;
  }
  
  .selection-info {
    margin-top: 2rem;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 0.5rem;
    padding: 1rem;
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
  }
  
  .selection-info p {
    margin: 0;
    color: #1e40af;
  }
  
  .text-sm {
    font-size: 0.875rem;
  }
  
  .text-gray-600 {
    color: #4b5563;
  }
  
  /* Responsive Design */
  @media (max-width: 768px) {
    .app-header {
      padding: 1rem;
    }
    
    .header-content {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }
    
    .main-content {
      padding: 1rem;
    }
    
    .welcome-state {
      padding: 2rem 1rem;
    }
    
    .search-tips {
      max-width: none;
    }
  }
</style>