import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import { searchConversations, getConversation } from './api.js'

// Mock fetch for testing
const originalFetch = global.fetch

const mockFetch = (url, options) => {
  const urlObj = new URL(url, 'http://localhost')
  
  if (url.includes('/api/search')) {
    const query = urlObj.searchParams.get('q')
    
    if (!query || query === 'nonexistent') {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ results: [] })
      })
    }
    
    const mockResults = [
      {
        title: 'Test Conversation 1',
        content: 'This is a test conversation about ' + query,
        date: '2024-01-01',
        metadata: {
          id: 'conv-1',
          source: 'chatgpt'
        }
      },
      {
        title: 'Another Test Chat',
        content: 'More content related to ' + query,
        date: '2024-01-02',
        metadata: {
          id: 'conv-2',
          source: 'claude'
        }
      }
    ]
    
    const filteredResults = mockResults.filter(result => 
      result.title.toLowerCase().includes(query.toLowerCase()) ||
      result.content.toLowerCase().includes(query.toLowerCase())
    )
    
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ results: filteredResults })
    })
  }
  
  if (url.includes('/api/conversation/')) {
    const id = url.split('/').pop()
    
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        id: id,
        title: 'Mock Conversation',
        messages: [
          { role: 'user', content: 'Hello', timestamp: '2024-01-01T10:00:00Z' },
          { role: 'assistant', content: 'Hi there!', timestamp: '2024-01-01T10:00:01Z' }
        ],
        metadata: {
          source: 'chatgpt',
          date: '2024-01-01T10:00:00Z'
        }
      })
    })
  }
  
  return Promise.reject(new Error('Unhandled request: ' + url))
}

describe('API Service', () => {
  beforeAll(() => {
    global.fetch = mockFetch
  })

  afterAll(() => {
    global.fetch = originalFetch
  })

  describe('searchConversations', () => {
    test('returns search results for valid query', async () => {
      const results = await searchConversations('react')
      
      expect(results.results).toHaveLength(2)
      expect(results.results[0].title).toBe('Test Conversation 1')
      expect(results.results[0].preview).toContain('react')
    })

    test('returns empty results for query with no matches', async () => {
      const results = await searchConversations('nonexistent')
      
      expect(results.results).toEqual([])
    })

    test('handles empty or null query', async () => {
      const emptyResults = await searchConversations('')
      const nullResults = await searchConversations(null)
      
      expect(emptyResults.results).toEqual([])
      expect(nullResults.results).toEqual([])
    })
  })

  describe('getConversation', () => {
    test('returns conversation details for valid ID', async () => {
      const conversation = await getConversation('conv-123')
      
      expect(conversation.id).toBe('conv-123')
      expect(conversation.title).toBe('Mock Conversation')
      expect(conversation.messages).toHaveLength(2)
    })
  })
})