import { describe, test, expect } from 'vitest'
import { transformSearchResult } from './api.js'

describe('API Data Transformation', () => {
  describe('transformSearchResult', () => {
    test('transforms complete API result to frontend format', () => {
      const apiResult = {
        title: 'Test Conversation Title',
        content: 'This is the full content of the conversation that should be truncated for preview',
        date: '2024-01-15T10:30:00Z',
        metadata: {
          id: 'chatgpt-chat-123',
          source: 'chatgpt',
          earliest_ts: '2024-01-15T10:30:00Z'
        }
      }

      const result = transformSearchResult(apiResult)

      expect(result).toEqual({
        id: 'chatgpt-chat-123',
        title: 'Test Conversation Title',
        preview: 'This is the full content of the conversation that should be truncated for preview',
        date: '2024-01-15T10:30:00Z',
        source: 'chatgpt'
      })
    })

    test('handles missing title with fallback', () => {
      const apiResult = {
        content: 'Content without title',
        metadata: { id: 'test-123', source: 'claude' }
      }

      const result = transformSearchResult(apiResult)

      expect(result.title).toBe('Untitled Conversation')
      expect(result.id).toBe('test-123')
      expect(result.source).toBe('claude')
    })

    test('truncates long content for preview', () => {
      const longContent = 'A'.repeat(300) // 300 character string
      const apiResult = {
        title: 'Long Content Test',
        content: longContent,
        metadata: { id: 'long-test', source: 'chatgpt' }
      }

      const result = transformSearchResult(apiResult)

      expect(result.preview).toHaveLength(203) // 200 chars + '...'
      expect(result.preview.endsWith('...')).toBe(true)
      expect(result.preview.substring(0, 200)).toBe('A'.repeat(200))
    })

    test('does not truncate short content', () => {
      const shortContent = 'Short content'
      const apiResult = {
        title: 'Short Content Test',
        content: shortContent,
        metadata: { id: 'short-test', source: 'claude' }
      }

      const result = transformSearchResult(apiResult)

      expect(result.preview).toBe(shortContent)
      expect(result.preview.endsWith('...')).toBe(false)
    })

    test('handles missing content', () => {
      const apiResult = {
        title: 'No Content Test',
        metadata: { id: 'no-content', source: 'chatgpt' }
      }

      const result = transformSearchResult(apiResult)

      expect(result.preview).toBe('')
    })

    test('generates fallback ID when metadata.id is missing', () => {
      const apiResult = {
        title: 'Missing ID Test',
        content: 'Content',
        metadata: { source: 'claude' }
      }

      const result = transformSearchResult(apiResult)

      expect(result.id).toMatch(/^result-[a-z0-9]{9}$/)
      expect(result.id).not.toBeUndefined()
      expect(result.id).not.toBe('')
    })

    test('handles completely missing metadata', () => {
      const apiResult = {
        title: 'No Metadata Test',
        content: 'Content without metadata'
      }

      const result = transformSearchResult(apiResult)

      expect(result.id).toMatch(/^result-[a-z0-9]{9}$/)
      expect(result.source).toBe('unknown')
      expect(result.date).toBeUndefined()
    })

    test('prefers date over metadata.earliest_ts', () => {
      const apiResult = {
        title: 'Date Priority Test',
        content: 'Content',
        date: '2024-01-15T10:30:00Z',
        metadata: {
          id: 'date-test',
          source: 'chatgpt',
          earliest_ts: '2024-01-10T10:30:00Z'
        }
      }

      const result = transformSearchResult(apiResult)

      expect(result.date).toBe('2024-01-15T10:30:00Z')
    })

    test('falls back to metadata.earliest_ts when date is missing', () => {
      const apiResult = {
        title: 'Fallback Date Test',
        content: 'Content',
        metadata: {
          id: 'fallback-test',
          source: 'claude',
          earliest_ts: '2024-01-10T10:30:00Z'
        }
      }

      const result = transformSearchResult(apiResult)

      expect(result.date).toBe('2024-01-10T10:30:00Z')
    })

    test('handles different source types', () => {
      const sources = ['chatgpt', 'claude', 'docx', 'unknown_source']

      sources.forEach(sourceType => {
        const apiResult = {
          title: `Source Test - ${sourceType}`,
          content: 'Content',
          metadata: {
            id: `source-test-${sourceType}`,
            source: sourceType
          }
        }

        const result = transformSearchResult(apiResult)

        expect(result.source).toBe(sourceType)
      })
    })

    test('handles empty string values gracefully', () => {
      const apiResult = {
        title: '',
        content: '',
        date: '',
        metadata: {
          id: '',
          source: ''
        }
      }

      const result = transformSearchResult(apiResult)

      expect(result.title).toBe('Untitled Conversation') // Falls back to default
      expect(result.preview).toBe('')
      expect(result.date).toBe('')
      expect(result.source).toBe('')
      expect(result.id).toMatch(/^result-[a-z0-9]{9}$/) // Generates fallback ID
    })

    test('ensures all required properties are present', () => {
      const apiResult = {
        title: 'Complete Properties Test',
        content: 'Some content',
        metadata: {
          id: 'complete-test',
          source: 'chatgpt'
        }
      }

      const result = transformSearchResult(apiResult)

      // Check that all expected properties exist
      expect(result).toHaveProperty('id')
      expect(result).toHaveProperty('title')
      expect(result).toHaveProperty('preview')
      expect(result).toHaveProperty('date')
      expect(result).toHaveProperty('source')

      // Check that no unexpected properties exist
      const expectedKeys = ['id', 'title', 'preview', 'date', 'source']
      expect(Object.keys(result)).toEqual(expectedKeys)
    })
  })
})