import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from config import PERSIST_DIR
from models import BaseModel


class FTSModel(BaseModel):
    """Full-Text Search model using SQLite FTS5"""
    
    def __init__(self):
        self.db_path = None
        self.initialize()
    
    def initialize(self):
        """Initialize SQLite FTS5 database"""
        # Create FTS database in the same directory as ChromaDB
        fts_dir = Path(PERSIST_DIR)
        fts_dir.mkdir(exist_ok=True)
        self.db_path = fts_dir / "conversations_fts.db"
        
        # Create FTS5 table if it doesn't exist
        self._create_fts_table()
    
    def _create_fts_table(self):
        """Create the FTS5 virtual table"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS conversations_fts USING fts5(
                    doc_id UNINDEXED,
                    title,
                    content,
                    source,
                    date_str UNINDEXED,
                    conversation_id UNINDEXED,
                    content='conversations_content',
                    tokenize='porter unicode61'
                );
            """)
            
            # Create the content table for external content storage
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations_content(
                    rowid INTEGER PRIMARY KEY,
                    doc_id TEXT UNIQUE,
                    title TEXT,
                    content TEXT,
                    source TEXT,
                    date_str TEXT,
                    conversation_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create index on doc_id for faster lookups
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_doc_id 
                ON conversations_content(doc_id);
            """)
            
            conn.commit()
    
    def add_document(self, doc_id: str, title: str, content: str, 
                    source: str, date_str: str, conversation_id: str = None):
        """Add a single document to the FTS index"""
        with sqlite3.connect(self.db_path) as conn:
            # Insert into content table (handles duplicates with REPLACE)
            conn.execute("""
                INSERT OR REPLACE INTO conversations_content
                (doc_id, title, content, source, date_str, conversation_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (doc_id, title, content, source, date_str, conversation_id))
            
            # Insert into FTS table
            conn.execute("""
                INSERT OR REPLACE INTO conversations_fts
                (doc_id, title, content, source, date_str, conversation_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (doc_id, title, content, source, date_str, conversation_id))
            
            conn.commit()
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add multiple documents to the FTS index"""
        with sqlite3.connect(self.db_path) as conn:
            content_data = []
            fts_data = []
            
            for doc in documents:
                doc_data = (
                    doc['doc_id'],
                    doc['title'],
                    doc['content'],
                    doc['source'],
                    doc['date_str'],
                    doc.get('conversation_id', '')
                )
                content_data.append(doc_data)
                fts_data.append(doc_data)
            
            # Batch insert into content table
            conn.executemany("""
                INSERT OR REPLACE INTO conversations_content
                (doc_id, title, content, source, date_str, conversation_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, content_data)
            
            # Batch insert into FTS table
            conn.executemany("""
                INSERT OR REPLACE INTO conversations_fts
                (doc_id, title, content, source, date_str, conversation_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, fts_data)
            
            conn.commit()
    
    def search(self, query: str, limit: int = 20, source_filter: str = None) -> List[Dict[str, Any]]:
        """Search documents using FTS5"""
        if not query or not query.strip():
            return []
        
        # Build the FTS query
        fts_query = self._build_fts_query(query)
        
        # Build the base SQL query
        sql = """
            SELECT doc_id, title, content, source, date_str, conversation_id,
                   bm25(conversations_fts) as rank,
                   snippet(conversations_fts, 1, '<mark>', '</mark>', '...', 32) as title_snippet,
                   snippet(conversations_fts, 2, '<mark>', '</mark>', '...', 64) as content_snippet
            FROM conversations_fts 
            WHERE conversations_fts MATCH ?
        """
        
        params = [fts_query]
        
        # Add source filter if specified
        if source_filter and source_filter != 'all':
            sql += " AND source = ?"
            params.append(source_filter)
        
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql, params)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'doc_id': row['doc_id'],
                    'title': row['title'],
                    'content': row['content'],
                    'source': row['source'],
                    'date_str': row['date_str'],
                    'conversation_id': row['conversation_id'],
                    'rank': row['rank'],
                    'title_snippet': row['title_snippet'],
                    'content_snippet': row['content_snippet']
                })
            
            return results
    
    def _build_fts_query(self, query: str) -> str:
        """Build an FTS5 query from user input"""
        # Clean and prepare the query
        query = query.strip()
        
        # Handle quoted phrases
        if '"' in query:
            return query  # Let FTS5 handle quoted phrases directly
        
        # Split into terms and create an OR query for better results
        terms = query.split()
        if len(terms) == 1:
            return query
        
        # Create a query that searches for the full phrase first, then individual terms
        phrase_query = f'"{query}"'
        terms_query = ' OR '.join(terms)
        
        return f"({phrase_query}) OR ({terms_query})"
    
    def get_document_count(self) -> int:
        """Get the total number of documents in the FTS index"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM conversations_content")
            return cursor.fetchone()[0]
    
    def clear_index(self):
        """Clear all documents from the FTS index and reclaim disk space"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM conversations_fts")
            conn.execute("DELETE FROM conversations_content") 
            conn.commit()
            # Reclaim disk space
            conn.execute("VACUUM")
            conn.commit()
    
    def rebuild_index(self):
        """Rebuild the FTS index (useful for optimization)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO conversations_fts(conversations_fts) VALUES('rebuild')")
            conn.commit()
    
    def vacuum_database(self):
        """Reclaim unused database space"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("VACUUM")
            conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the FTS index"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get basic stats
            total_docs = conn.execute("SELECT COUNT(*) as count FROM conversations_content").fetchone()['count']
            
            # Get source breakdown
            source_stats = {}
            cursor = conn.execute("SELECT source, COUNT(*) as count FROM conversations_content GROUP BY source")
            for row in cursor.fetchall():
                source_stats[row['source']] = row['count']
            
            # Get database file size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            return {
                'total_documents': total_docs,
                'sources': source_stats,
                'db_size_mb': round(db_size / (1024 * 1024), 2),
                'db_path': str(self.db_path)
            }