# DOCX Parsing Strategy

## Overview

The DOCX parser uses a **hybrid strategy** that automatically selects the optimal parsing approach based on document structure analysis.

## How It Works

### 1. Document Analysis Phase

Before parsing, the system analyzes the document to detect:

- **Role markers**: "You said:", "ChatGPT said:", "User:", "Assistant:", etc.
- **Marker coverage**: Percentage of paragraphs that contain role markers
- **Alternation pattern**: Whether markers alternate between user ↔ assistant
- **False positives**: Filters out list items (A., 1.), "Note:", code blocks, etc.

### 2. Strategy Selection

Based on analysis, one of two strategies is chosen:

#### **Structured Parsing** (High Confidence)
- **Used when**: Clear role markers present with good alternation
- **Threshold**: ≥40% confidence score
- **Confidence formula**: 
  ```
  confidence = (min(coverage * 2, 1.0) * 0.3) + (alternation_ratio * 0.7)
  ```
- **Best for**: ChatGPT/Claude exports, formatted conversations
- **Handles**: 
  - Multi-paragraph messages (low coverage is expected)
  - Missing first marker (accumulates pre-role content)
  - Perfect user ↔ assistant alternation

#### **Semantic Chunking** (Low/No Confidence)
- **Used when**: No markers or inconsistent structure
- **Threshold**: <40% confidence score
- **Best for**: Raw conversation transcripts, manual notes
- **Strategy**:
  - Splits on empty paragraphs to create chunks
  - Uses heuristics (questions vs statements)
  - Assumes alternating user/assistant pattern
  - Falls back gracefully for unstructured content

### 3. Metadata Tracking

Each parsed document includes metadata about parsing:

```python
{
    'parsing_strategy': 'structured',  # or 'semantic'
    'parsing_confidence': 0.813,
    'marker_coverage': 0.189
}
```

## Test Results

Results from sample documents in `sampe_word_docs/`:

| Document | Strategy | Confidence | Messages | Notes |
|----------|----------|------------|----------|-------|
| 70's pop culture.docx | STRUCTURED | 75.3% | 570 | 8.8% coverage, 100% alternation |
| Canadian Snax.docx | SEMANTIC | 0.0% | 157 | No markers detected |
| Chappell Roan & Feelings.docx | STRUCTURED | 80.1% | 618 | 16.9% coverage, 100% alternation |
| Difficult Truths...docx | STRUCTURED | 74.9% | 645 | 8.2% coverage, 100% alternation |
| Join Therapy Session...docx | STRUCTURED | 75.2% | 251 | 8.6% coverage, 100% alternation |
| Mark and Politics.docx | STRUCTURED | 81.3% | 266 | 18.9% coverage, 100% alternation |

**Success rate**: 100% - All documents correctly classified and parsed without errors.

## Key Features

### ✅ Robust Role Marker Detection

Supports multiple formats:
- **User markers**: "You:", "You said:", "User:", "Me:", "Human:", "[You]", "**You**"
- **Assistant markers**: "ChatGPT:", "ChatGPT said:", "Assistant:", "AI:", "Claude:", "GPT:", "[Assistant]", "**ChatGPT**"
- **System markers**: "System:", "[System]", "**System**"

### ✅ False Positive Filtering

Automatically excludes:
- List items: "A.", "1.", "Step 1:"
- Section markers: "Note:", "Example:"
- Code blocks and indented content

### ✅ Graceful Degradation

- Structured parsing falls back to semantic if markers are inconsistent
- Semantic parsing falls back to paragraph-level if chunking fails
- Always produces valid output, never crashes

### ✅ Multi-Paragraph Message Support

Correctly handles messages that span multiple paragraphs:
```
You said:
[Paragraph 1 of user message]
[Paragraph 2 of user message]
[Paragraph 3 of user message]

ChatGPT said:
[Assistant response paragraph 1]
[Assistant response paragraph 2]
```

### ✅ Pre-Role Content Handling

Accumulates content before first marker and assigns it to the appropriate role:
```
[Some content without marker at start]
[More content]

You said:
[Explicit user message]
```
→ Pre-role content becomes a user message

## RAG Compatibility

The parser is optimized for **semantic search and RAG retrieval**:

1. **Clean text extraction**: Removes formatting artifacts, normalizes whitespace
2. **Reasonable chunk sizes**: Averages 500-1500 characters per message
3. **Preserves context**: Multi-paragraph messages stay together
4. **Metadata tracking**: Strategy and confidence available for debugging
5. **Consistent output**: Always produces valid message format for vector embedding

## Usage

```python
from utils.docx_parser import parse_docx_file

messages, timestamps, title = parse_docx_file('conversation.docx')

# Each message has:
# - role: 'user' | 'assistant' | 'system'
# - content: str (cleaned text content)
# - metadata: dict (optional, includes parsing info)

# First message contains parsing metadata
if messages:
    metadata = messages[0].get('metadata', {})
    print(f"Strategy: {metadata['parsing_strategy']}")
    print(f"Confidence: {metadata['parsing_confidence']:.1%}")
```

## Analysis Tool

Use the probe script to analyze documents before importing:

```bash
# Analyze all Word documents
python scripts/utils/docx_probe.py sampe_word_docs/*.docx

# Output as JSON
python scripts/utils/docx_probe.py sampe_word_docs/*.docx --json
```

## Future Enhancements

Potential improvements:
- [ ] Language-specific marker detection (non-English conversations)
- [ ] Table extraction (currently skipped)
- [ ] Image/attachment metadata extraction
- [ ] Custom marker pattern configuration
- [ ] Confidence threshold tuning per document type

## Related Files

- **Implementation**: `utils/docx_parser.py`
- **Analysis Tool**: `scripts/utils/docx_probe.py`
- **Test Samples**: `sampe_word_docs/*.docx`
- **Database Import**: `controllers/postgres_controller.py` (uses parser via `_import_docx_file`)
