import { render, screen } from '@testing-library/svelte'
import { describe, it, expect } from 'vitest'
import MessageView from '../components/MessageView.svelte'

describe('MessageView', () => {
  const mockUserMessage = {
    id: '1',
    role: 'user',
    content: 'How do I enable SSH without monitor/keyboard?',
    timestamp: '2025-09-04T21:58:00Z'
  }

  const mockAIMessage = {
    id: '2', 
    role: 'assistant',
    content: `# Enable SSH + Wi-Fi headless

On the boot volume of your microSD card:

1. Add an empty file named \`ssh\`
2. Add \`wpa_supplicant.conf\` with your Wi-Fi credentials:

\`\`\`
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
  ssid="YourSSID"
  psk="YourPassword"
}
\`\`\`

> Tip: stick to 2.4 GHz networks for first boot.`,
    timestamp: '2025-09-04T22:12:00Z'
  }

  const mockConversation = {
    id: 'conv-1',
    title: 'SSH and VNC on Raspberry Pi 5',
    assistant_name: 'Claude',
    messages: [mockUserMessage, mockAIMessage]
  }

  it('renders conversation header with title and metadata', () => {
    render(MessageView, { props: { conversation: mockConversation } })
    
    expect(screen.getByText('SSH and VNC on Raspberry Pi 5')).toBeInTheDocument()
    expect(screen.getByText(/Last updated/)).toBeInTheDocument()
    expect(screen.getAllByText('Copy').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Refresh')).toBeInTheDocument()
  })

  it('renders user messages with bubble styling', () => {
    render(MessageView, { props: { conversation: mockConversation } })
    
    const userBubble = screen.getByText('How do I enable SSH without monitor/keyboard?').closest('.bubble')
    expect(userBubble).toBeInTheDocument()
    
    const userMsg = userBubble.closest('.msg--me')
    expect(userMsg).toBeInTheDocument()
    
    expect(screen.getByText('You')).toBeInTheDocument()
    // Check that timestamp appears in bubble context
    expect(userBubble.textContent).toMatch(/\d+[mhdw] ago|\d+[dw] \d+[hd] ago|now|\w{3} \d+, \d+/)
  })

  it('renders AI messages with content styling (no bubble)', () => {
    render(MessageView, { props: { conversation: mockConversation } })
    
    const aiContent = screen.getByText('Enable SSH + Wi-Fi headless').closest('.ai__content')
    expect(aiContent).toBeInTheDocument()
    
    const aiMsg = aiContent.closest('.msg--ai')
    expect(aiMsg).toBeInTheDocument()
    
    // Check for Claude text in the AI message meta specifically
    const aiMeta = aiContent.closest('.ai').querySelector('.ai__meta strong')
    expect(aiMeta).toHaveTextContent('Claude')
    // Check that timestamp appears in AI content context  
    const aiContainer = aiContent.closest('.ai')
    expect(aiContainer.textContent).toMatch(/\d+[mhdw] ago|\d+[dw] \d+[hd] ago|now|\w{3} \d+, \d+/)
  })

  it('renders formatted AI content with headers, lists, and code blocks', () => {
    render(MessageView, { props: { conversation: mockConversation } })
    
    // Check for header
    expect(screen.getByRole('heading', { name: 'Enable SSH + Wi-Fi headless' })).toBeInTheDocument()
    
    // Check for list items
    expect(screen.getByText(/Add an empty file named/)).toBeInTheDocument()
    expect(screen.getByText('wpa_supplicant.conf')).toBeInTheDocument()
    expect(screen.getByText(/with your Wi-Fi credentials/)).toBeInTheDocument()
    
    // Check for code block
    expect(screen.getByText(/country=US/)).toBeInTheDocument()
    
    // Check for blockquote
    expect(screen.getByText(/Tip: stick to 2.4 GHz networks/)).toBeInTheDocument()
  })

  it('displays avatar for both user and AI messages', () => {
    render(MessageView, { props: { conversation: mockConversation } })
    
    const avatars = screen.getAllByRole('img', { name: /avatar/i })
    expect(avatars).toHaveLength(2)
    
    // User avatar shows "Y", AI avatar shows "A"
    expect(screen.getByText('Y')).toBeInTheDocument()
    expect(screen.getByText('A')).toBeInTheDocument()
  })

  it('shows copy buttons for each message', () => {
    render(MessageView, { props: { conversation: mockConversation } })
    
    const copyButtons = screen.getAllByText('Copy')
    // Header Copy + 2 message copy buttons = 3 total
    expect(copyButtons.length).toBe(3)
  })

  it('handles empty conversation gracefully', () => {
    const emptyConversation = {
      id: 'empty',
      title: 'Empty Chat',
      messages: []
    }
    
    render(MessageView, { props: { conversation: emptyConversation } })
    
    expect(screen.getByText('Empty Chat')).toBeInTheDocument()
    // Should not crash with no messages
  })

  it('displays Claude as assistant name when specified', () => {
    const claudeConversation = {
      id: 'conv-claude',
      title: 'Claude Chat',
      assistant_name: 'Claude',
      messages: [mockUserMessage, mockAIMessage]
    }
    
    render(MessageView, { props: { conversation: claudeConversation } })
    
    // Check header badge specifically
    const headerBadge = document.querySelector('.badge')
    expect(headerBadge).toHaveTextContent('Claude')
    // Check message meta specifically
    const aiMeta = document.querySelector('.ai__meta strong')
    expect(aiMeta).toHaveTextContent('Claude')
    // Ensure no other assistant names appear
    expect(screen.queryByText('AI')).not.toBeInTheDocument()
    expect(screen.queryByText('ChatGPT')).not.toBeInTheDocument()
  })

  it('displays ChatGPT as assistant name when specified', () => {
    const chatgptConversation = {
      id: 'conv-chatgpt',
      title: 'ChatGPT Chat',
      assistant_name: 'ChatGPT',
      messages: [mockUserMessage, mockAIMessage]
    }
    
    render(MessageView, { props: { conversation: chatgptConversation } })
    
    // Check header badge specifically
    const headerBadge = document.querySelector('.badge')
    expect(headerBadge).toHaveTextContent('ChatGPT')
    // Check message meta specifically
    const aiMeta = document.querySelector('.ai__meta strong')
    expect(aiMeta).toHaveTextContent('ChatGPT')
    // Ensure no other assistant names appear
    expect(screen.queryByText('Claude')).not.toBeInTheDocument()
    expect(screen.queryByText('AI')).not.toBeInTheDocument()
  })

  it('falls back to AI when assistant_name is not provided', () => {
    const genericConversation = {
      id: 'conv-generic',
      title: 'Generic Chat',
      messages: [mockUserMessage, mockAIMessage]
    }
    
    render(MessageView, { props: { conversation: genericConversation } })
    
    // Check header badge specifically
    const headerBadge = document.querySelector('.badge')
    expect(headerBadge).toHaveTextContent('AI')
    // Check message meta specifically
    const aiMeta = document.querySelector('.ai__meta strong')
    expect(aiMeta).toHaveTextContent('AI')
    // Ensure no other assistant names appear
    expect(screen.queryByText('Claude')).not.toBeInTheDocument()
    expect(screen.queryByText('ChatGPT')).not.toBeInTheDocument()
  })

  it('falls back to AI when assistant_name is empty', () => {
    const emptyAssistantConversation = {
      id: 'conv-empty-assistant',
      title: 'Empty Assistant Chat',
      assistant_name: '',
      messages: [mockUserMessage, mockAIMessage]
    }
    
    render(MessageView, { props: { conversation: emptyAssistantConversation } })
    
    // Check header badge specifically
    const headerBadge = document.querySelector('.badge')
    expect(headerBadge).toHaveTextContent('AI')
    // Check message meta specifically
    const aiMeta = document.querySelector('.ai__meta strong')
    expect(aiMeta).toHaveTextContent('AI')
  })

  it('formats time correctly for different durations', () => {
    const now = new Date()
    
    // Test minutes ago
    const fiveMinutesAgo = new Date(now - 5 * 60 * 1000)
    const minuteConversation = {
      ...mockConversation,
      messages: [{
        ...mockUserMessage,
        timestamp: fiveMinutesAgo.toISOString()
      }]
    }
    
    render(MessageView, { props: { conversation: minuteConversation } })
    expect(document.body.textContent).toMatch(/5m ago/)
    
    // The component is rendered once, so we need to clear and test other scenarios separately
  })
  
  it('formats time correctly for hours ago', () => {
    const now = new Date()
    const threeHoursAgo = new Date(now - 3 * 60 * 60 * 1000)
    const hourConversation = {
      ...mockConversation,
      messages: [{
        ...mockUserMessage,
        timestamp: threeHoursAgo.toISOString()
      }]
    }
    
    render(MessageView, { props: { conversation: hourConversation } })
    expect(document.body.textContent).toMatch(/3h ago/)
  })
  
  it('formats time correctly for days ago', () => {
    const now = new Date()
    const twoDaysAgo = new Date(now - 2 * 24 * 60 * 60 * 1000)
    const dayConversation = {
      ...mockConversation,
      messages: [{
        ...mockUserMessage,
        timestamp: twoDaysAgo.toISOString()
      }]
    }
    
    render(MessageView, { props: { conversation: dayConversation } })
    expect(document.body.textContent).toMatch(/2d ago/)
  })
  
  it('formats time correctly for weeks ago', () => {
    const now = new Date()
    const twoWeeksAgo = new Date(now - 2 * 7 * 24 * 60 * 60 * 1000)
    const weekConversation = {
      ...mockConversation,
      messages: [{
        ...mockUserMessage,
        timestamp: twoWeeksAgo.toISOString()
      }]
    }
    
    render(MessageView, { props: { conversation: weekConversation } })
    expect(document.body.textContent).toMatch(/2w ago/)
  })
})