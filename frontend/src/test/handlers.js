import { rest } from 'msw'

// Mock API handlers for testing
export const handlers = [
  // Mock search endpoint
  rest.get('/api/search', (req, res, ctx) => {
    const query = req.url.searchParams.get('q')
    
    if (!query) {
      return res(ctx.json({ results: [] }))
    }
    
    // Mock search results
    const mockResults = [
      {
        id: 'conv-1',
        title: 'Test Conversation 1',
        preview: 'This is a test conversation about ' + query,
        date: '2024-01-01',
        source: 'chatgpt'
      },
      {
        id: 'conv-2', 
        title: 'Another Test Chat',
        preview: 'More content related to ' + query,
        date: '2024-01-02',
        source: 'claude'
      }
    ]
    
    // Filter results based on query
    const filteredResults = mockResults.filter(result => 
      result.title.toLowerCase().includes(query.toLowerCase()) ||
      result.preview.toLowerCase().includes(query.toLowerCase())
    )
    
    return res(ctx.json({ results: filteredResults }))
  }),
  
  // Mock conversation detail endpoint
  rest.get('/api/conversation/:id', (req, res, ctx) => {
    return res(ctx.json({
      id: req.params.id,
      title: 'Mock Conversation',
      messages: [
        { role: 'user', content: 'Hello', timestamp: '2024-01-01T10:00:00Z' },
        { role: 'assistant', content: 'Hi there!', timestamp: '2024-01-01T10:00:01Z' }
      ],
      metadata: {
        source: 'chatgpt',
        date: '2024-01-01T10:00:00Z'
      }
    }))
  })
]