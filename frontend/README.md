# DovOS Frontend

Modern Svelte frontend for the conversation search application, built with TDD approach.

## Setup

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Run tests (TDD):**
```bash
npm test          # Run tests in watch mode
npm run test:ui   # Visual test interface
npm run test:coverage  # Coverage report
```

3. **Start development server:**
```bash
npm run dev       # Frontend on http://localhost:3000
```

4. **Make sure Flask backend is running:**
```bash
cd ..
python app.py     # Backend on http://localhost:5000
```

## TDD Workflow

1. **Write test first** (RED)
2. **Implement minimal code** to pass test (GREEN)  
3. **Refactor** while keeping tests green (REFACTOR)

## Current Components

### ✅ SearchBox
- [x] Renders search input with placeholder
- [x] Shows loading state during search
- [x] Dispatches search events with debouncing (300ms)
- [x] Has clear button functionality
- [x] Prevents empty query searches

### 🚧 Next Components (TDD)
- [ ] ConversationCard - Display single conversation preview
- [ ] ConversationList - List of conversation cards
- [ ] Sidebar - Navigation and search area
- [ ] MessageBubble - Individual message display

## Architecture

```
src/
├── components/         # Svelte components + tests
├── stores/            # Svelte stores for state
├── services/          # API communication
├── test/              # Test setup and mocks
└── main.js           # Entry point
```

## Testing Stack

- **Vitest** - Fast test runner
- **@testing-library/svelte** - Component testing
- **MSW** - API mocking
- **jsdom** - DOM simulation

## API Integration

Frontend proxies API calls to Flask backend:
- `/api/search?q=query` → Search conversations
- `/api/conversation/:id` → Get conversation details