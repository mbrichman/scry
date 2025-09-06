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
    expect(userBubble.textContent).toMatch(/\d+h ago|now/)
  })

  it('renders AI messages with content styling (no bubble)', () => {
    render(MessageView, { props: { conversation: mockConversation } })
    
    const aiContent = screen.getByText('Enable SSH + Wi-Fi headless').closest('.ai__content')
    expect(aiContent).toBeInTheDocument()
    
    const aiMsg = aiContent.closest('.msg--ai')
    expect(aiMsg).toBeInTheDocument()
    
    expect(screen.getByText('AI')).toBeInTheDocument()
    // Check that timestamp appears in AI content context  
    const aiContainer = aiContent.closest('.ai')
    expect(aiContainer.textContent).toMatch(/\d+h ago|now/)
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
})