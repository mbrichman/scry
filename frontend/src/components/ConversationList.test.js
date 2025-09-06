import { render, screen, fireEvent } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import ConversationList from './ConversationList.svelte'

describe('ConversationList', () => {
  const mockConversations = [
    {
      id: 'conv-1',
      title: 'React Component State',
      preview: 'Discussion about React state management and hooks.',
      date: '2024-01-15T10:30:00Z',
      source: 'chatgpt'
    },
    {
      id: 'conv-2',
      title: 'Python Data Analysis',
      preview: 'Working with pandas and data visualization.',
      date: '2024-01-14T14:20:00Z',
      source: 'claude'
    },
    {
      id: 'conv-3',
      title: 'API Design Patterns',
      preview: 'Best practices for REST API development.',
      date: '2024-01-13T09:15:00Z',
      source: 'chatgpt'
    }
  ]

  test('renders list of conversation cards', () => {
    render(ConversationList, { conversations: mockConversations })
    
    expect(screen.getByText('React Component State')).toBeInTheDocument()
    expect(screen.getByText('Python Data Analysis')).toBeInTheDocument()
    expect(screen.getByText('API Design Patterns')).toBeInTheDocument()
  })

  test('displays loading state', () => {
    render(ConversationList, { conversations: [], isLoading: true })
    
    expect(screen.getByText('Loading conversations...')).toBeInTheDocument()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  test('displays empty state when no conversations', () => {
    render(ConversationList, { conversations: [], isLoading: false })
    
    expect(screen.getByText('No conversations found')).toBeInTheDocument()
    expect(screen.getByText(/Upload some conversation files to get started/)).toBeInTheDocument()
  })

  test('displays search results count', () => {
    render(ConversationList, { conversations: mockConversations, searchQuery: 'react' })
    
    expect(screen.getByText('3 results for "react"')).toBeInTheDocument()
  })

  test('does not show results count without search query', () => {
    render(ConversationList, { conversations: mockConversations })
    
    expect(screen.queryByText(/results for/)).not.toBeInTheDocument()
  })

  test('forwards conversation selection events', async () => {
    const user = userEvent.setup()
    const mockSelectHandler = vi.fn()
    
    const { component } = render(ConversationList, { conversations: mockConversations })
    component.$on('conversationSelect', mockSelectHandler)
    
    // Click on the first conversation card
    const firstCard = screen.getByText('React Component State').closest('button')
    await user.click(firstCard)
    
    expect(mockSelectHandler).toHaveBeenCalledWith(
      expect.objectContaining({
        detail: { conversation: mockConversations[0] }
      })
    )
  })

  test('displays conversations in correct order', () => {
    render(ConversationList, { conversations: mockConversations })
    
    const titles = screen.getAllByRole('button').map(button => 
      button.querySelector('h3').textContent
    )
    
    expect(titles).toEqual([
      'React Component State',
      'Python Data Analysis', 
      'API Design Patterns'
    ])
  })

  test('handles empty search results with query', () => {
    render(ConversationList, { 
      conversations: [], 
      isLoading: false, 
      searchQuery: 'nonexistent' 
    })
    
    expect(screen.getByText('0 results for "nonexistent"')).toBeInTheDocument()
    expect(screen.getByText('No conversations found')).toBeInTheDocument()
    expect(screen.getByText(/Try a different search term/)).toBeInTheDocument()
  })

  test('shows loading state overrides empty state', () => {
    render(ConversationList, { 
      conversations: [], 
      isLoading: true,
      searchQuery: 'test'
    })
    
    expect(screen.getByText('Loading conversations...')).toBeInTheDocument()
    expect(screen.queryByText('No conversations found')).not.toBeInTheDocument()
  })

  test('handles single conversation correctly', () => {
    render(ConversationList, { 
      conversations: [mockConversations[0]], 
      searchQuery: 'react' 
    })
    
    expect(screen.getByText('1 result for "react"')).toBeInTheDocument()
    expect(screen.getByText('React Component State')).toBeInTheDocument()
  })

  test('applies proper accessibility attributes', () => {
    render(ConversationList, { conversations: mockConversations })
    
    const list = screen.getByRole('list', { name: /conversations/i })
    expect(list).toBeInTheDocument()
    
    const listItems = screen.getAllByRole('listitem')
    expect(listItems).toHaveLength(3)
  })

  test('renders with custom CSS classes', () => {
    render(ConversationList, { conversations: mockConversations })
    
    const container = screen.getByRole('list')
    expect(container).toHaveClass('conversation-list-inner')
  })
})