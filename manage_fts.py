#!/usr/bin/env python3
"""
FTS5 Management Utility
"""

import sys
import os
import argparse

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.conversation_model import ConversationModel
from models.fts_model import FTSModel


def migrate_from_chromadb():
    """Migrate all conversations from ChromaDB to FTS5"""
    print("🚀 Migrating conversations from ChromaDB to FTS5...")
    
    conversation_model = ConversationModel()
    fts_model = FTSModel()
    
    # Get all documents from ChromaDB
    docs = conversation_model.get_documents(include=["documents", "metadatas"], limit=9999)
    
    if not docs or not docs.get("documents"):
        print("❌ No documents found in ChromaDB")
        return False
    
    documents = docs["documents"]
    metadatas = docs.get("metadatas", [])
    ids = docs.get("ids", [])
    
    print(f"📄 Found {len(documents)} documents to migrate")
    
    # Prepare documents for FTS indexing
    fts_documents = []
    
    for i, doc in enumerate(documents):
        meta = metadatas[i] if i < len(metadatas) else {}
        doc_id = ids[i] if i < len(ids) else f"doc_{i}"
        
        title = meta.get('title', 'Untitled')
        source = meta.get('source', 'unknown')
        conversation_id = meta.get('conversation_id') or meta.get('id', '')
        
        # Get date string
        date_str = "Unknown"
        for date_field in ['latest_ts', 'earliest_ts', 'created', 'modified']:
            if meta.get(date_field):
                date_str = str(meta[date_field])
                break
        
        content = doc.strip() if doc else ""
        
        fts_doc = {
            'doc_id': doc_id,
            'title': title,
            'content': content,
            'source': source,
            'date_str': date_str,
            'conversation_id': conversation_id
        }
        
        fts_documents.append(fts_doc)
    
    # Batch insert into FTS
    print("💾 Indexing documents in FTS5...")
    fts_model.add_documents(fts_documents)
    
    # Verify
    fts_count = fts_model.get_document_count()
    print(f"✅ Migration complete! Indexed {fts_count} documents")
    
    return True


def show_stats():
    """Show FTS5 database statistics"""
    fts_model = FTSModel()
    stats = fts_model.get_stats()
    
    print("📊 FTS5 Database Statistics:")
    print(f"   • Total documents: {stats['total_documents']}")
    print(f"   • Database size: {stats['db_size_mb']} MB")
    print(f"   • Database location: {stats['db_path']}")
    print("   • Source breakdown:")
    for source, count in stats['sources'].items():
        print(f"     - {source}: {count} documents")


def test_search():
    """Test FTS5 search functionality"""
    fts_model = FTSModel()
    
    test_queries = ["python", "react", "API", "database"]
    
    print("🔍 Testing FTS5 search...")
    for query in test_queries:
        print(f"\n🔎 Searching for: '{query}'")
        results = fts_model.search(query, limit=2)
        
        if results:
            print(f"   Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                title = result['title'][:50] + "..." if len(result['title']) > 50 else result['title']
                print(f"   {i}. {title}")
                print(f"      [Source: {result['source']}, Rank: {result['rank']:.2f}]")
        else:
            print("   No results found")


def clear_index():
    """Clear the FTS5 index"""
    fts_model = FTSModel()
    
    confirm = input("⚠️  This will delete all FTS5 data. Continue? (y/N): ")
    if confirm.lower() == 'y':
        fts_model.clear_index()
        print("🗑️  FTS5 index cleared")
    else:
        print("❌ Operation cancelled")


def rebuild_index():
    """Rebuild/optimize the FTS5 index"""
    fts_model = FTSModel()
    
    print("🔧 Rebuilding FTS5 index...")
    fts_model.rebuild_index()
    print("✅ FTS5 index rebuilt and optimized")


def vacuum_database():
    """Reclaim unused database space"""
    fts_model = FTSModel()
    
    stats_before = fts_model.get_stats()
    print(f"🗜️  Database size before vacuum: {stats_before['db_size_mb']} MB")
    
    print("🔧 Vacuuming database...")
    fts_model.vacuum_database()
    
    stats_after = fts_model.get_stats()
    print(f"✅ Database size after vacuum: {stats_after['db_size_mb']} MB")
    saved = stats_before['db_size_mb'] - stats_after['db_size_mb']
    print(f"💾 Space reclaimed: {saved:.2f} MB")


def main():
    parser = argparse.ArgumentParser(description="FTS5 Management Utility")
    parser.add_argument('action', choices=['migrate', 'stats', 'test', 'clear', 'rebuild', 'vacuum'], 
                       help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'migrate':
        migrate_from_chromadb()
    elif args.action == 'stats':
        show_stats()
    elif args.action == 'test':
        test_search()
    elif args.action == 'clear':
        clear_index()
    elif args.action == 'rebuild':
        rebuild_index()
    elif args.action == 'vacuum':
        vacuum_database()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("FTS5 Management Utility")
        print("\nUsage: python manage_fts.py <action>")
        print("\nActions:")
        print("  migrate  - Migrate conversations from ChromaDB to FTS5")
        print("  stats    - Show FTS5 database statistics")  
        print("  test     - Test FTS5 search functionality")
        print("  clear    - Clear FTS5 index (dangerous!)")
        print("  rebuild  - Rebuild/optimize FTS5 index")
        print("  vacuum   - Reclaim unused database space")
        print("\nExample: python manage_fts.py migrate")
    else:
        main()