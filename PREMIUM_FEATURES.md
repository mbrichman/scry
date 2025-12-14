# Premium Features

Dovos offers premium importers available with Pro and Enterprise licenses.

## Free Features (Open Source)

✅ **Claude Importer** - Import conversations from Claude AI  
✅ **OpenWebUI Importer** - Import conversations from Open WebUI  
✅ **Full-text Search** - Fast PostgreSQL-based full-text search  
✅ **Vector Search** - Semantic search with pgvector embeddings  
✅ **Hybrid Search** - Combined FTS and vector similarity ranking  
✅ **Web UI** - Modern Flask-based interface  
✅ **REST API** - Full API access for integration  

## Premium Features (Pro/Enterprise)

🔒 **ChatGPT Importer** - Import conversations from ChatGPT exports  
🔒 **DOCX Importer** - Import conversations from Word documents  

### Why Premium?

The ChatGPT and DOCX importers require significant ongoing maintenance due to:
- Frequent format changes from OpenAI
- Complex parsing logic for ChatGPT's node-based structure
- DOCX format variations and compatibility requirements
- Attachment handling and extraction
- Edge case handling and testing

Premium licenses help support this development and maintenance.

## Getting a License

Interested in premium features? Contact us at:  
📧 **[your-email@example.com]**

We offer:
- **Pro License**: Individual/small team use
- **Enterprise License**: Organizational use with support

## Using Premium Features

If you have a license key:

1. **Set environment variable:**
   ```bash
   export DOVOS_LICENSE_KEY=DOVOS-PRO-your-key-here
   ```

2. **Or configure in settings:**
   - Navigate to `/settings` in the web UI
   - Enter your license key
   - Save settings

3. **Copy importer files (provided with license):**
   ```
   db/importers/chatgpt.py
   db/importers/docx.py
   utils/docx_parser.py
   ```

4. **Restart the application**

The premium importers will be automatically discovered and enabled.

## Questions?

- **License inquiries**: [your-email@example.com]
- **Support**: [support-email@example.com]
- **Issues**: https://github.com/your-username/dovos/issues

## License Validation

License validation is performed server-side using the `db/licensing/` module:
- Validates format: `DOVOS-PRO-*` or `DOVOS-ENT-*`
- Checks feature availability before import
- Shows user-friendly upgrade prompts
- No external API calls (offline validation)
