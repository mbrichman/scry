"""
API Compatibility Adapter

This module provides functions to map between internal data structures 
and the external API contract. This ensures that the frontend always 
receives data in the expected format, regardless of backend changes.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class CompatibilityAdapter:
    """Adapter class for mapping between internal and external data formats"""

    @staticmethod
    def map_conversation_summary(doc: str, meta: Dict[str, Any], index: int = 0) -> Dict[str, Any]:
        """
        Map internal conversation data to ConversationSummaryModel format
        
        Args:
            doc: Document content
            meta: Document metadata  
            index: Fallback index for ID generation
            
        Returns:
            Dict matching ConversationSummaryModel schema
        """
        # Extract preview content (max 200 chars)
        preview = CompatibilityAdapter._extract_preview_content(doc, max_length=200)
        
        # Ensure required fields have defaults
        conversation_id = meta.get("id") or meta.get("conversation_id") or f"conv-{index}"
        title = meta.get("title") or "Untitled Conversation"  # Handle None values
        date = meta.get("earliest_ts") or ""  # Empty string for missing dates or None
        source = meta.get("source") or "unknown"  # Handle None values
        
        return {
            "id": str(conversation_id),
            "title": str(title), 
            "preview": str(preview),
            "date": str(date),
            "source": str(source)
        }

    @staticmethod
    def map_conversations_list_response(docs: List[str], metadatas: List[Dict[str, Any]], 
                                      page: int, limit: int, total: int) -> Dict[str, Any]:
        """
        Map internal conversations data to ConversationsListResponse format
        
        Args:
            docs: List of document contents
            metadatas: List of document metadata
            page: Current page number
            limit: Items per page
            total: Total number of items
            
        Returns:
            Dict matching ConversationsListResponse schema
        """
        conversations = []
        
        for i, (doc, meta) in enumerate(zip(docs, metadatas)):
            conversation = CompatibilityAdapter.map_conversation_summary(doc, meta, i)
            conversations.append(conversation)
        
        # Calculate pagination
        has_next = (page * limit) < total
        has_prev = page > 1
        
        return {
            "conversations": conversations,
            "pagination": {
                "page": int(page),
                "limit": int(limit),
                "total": int(total),
                "has_next": bool(has_next),
                "has_prev": bool(has_prev)
            }
        }

    @staticmethod
    def map_message(message_id: str, role: str, content: str, timestamp: Optional[str] = None) -> Dict[str, Any]:
        """
        Map internal message data to MessageModel format
        
        Args:
            message_id: Message identifier
            role: Message role (user, assistant, system)
            content: Message content
            timestamp: Optional timestamp
            
        Returns:
            Dict matching MessageModel schema
        """
        return {
            "id": str(message_id),
            "role": str(role),
            "content": str(content),
            "timestamp": timestamp  # Can be None
        }

    @staticmethod
    def map_conversation_detail_response(conversation_id: str, document: str, metadata: Dict[str, Any],
                                       messages: List[Dict[str, Any]], assistant_name: str) -> Dict[str, Any]:
        """
        Map internal conversation detail data to ConversationDetailResponse format
        
        Args:
            conversation_id: Conversation ID
            document: Full document content
            metadata: Document metadata
            messages: Parsed messages list
            assistant_name: Name of the assistant
            
        Returns:
            Dict matching ConversationDetailResponse schema
        """
        title = metadata.get("title", "Untitled Conversation")
        source = metadata.get("source", "unknown")
        date = metadata.get("earliest_ts") or metadata.get("date")  # Can be None
        
        return {
            "id": str(conversation_id),
            "title": str(title),
            "source": str(source),
            "date": date,  # Can be None
            "assistant_name": str(assistant_name),
            "messages": messages  # Already formatted by map_message
        }

    @staticmethod
    def map_search_result(doc: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map internal search result to SearchResultModel format
        
        Args:
            doc: Document content
            meta: Document metadata
            
        Returns:
            Dict matching SearchResultModel schema
        """
        # Extract preview content (max 300 chars)
        content_preview = CompatibilityAdapter._extract_preview_content(doc, max_length=300)
        
        title = meta.get("title", "Untitled")
        date = meta.get("earliest_ts", "Unknown")
        
        return {
            "title": str(title),
            "date": str(date),
            "content": str(content_preview),
            "metadata": dict(meta)  # Ensure it's a dict
        }

    @staticmethod
    def map_search_response(query: str, docs: List[str], metadatas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Map internal search results to SearchResponse format
        
        Args:
            query: Original search query
            docs: List of document contents
            metadatas: List of document metadata
            
        Returns:
            Dict matching SearchResponse schema
        """
        results = []
        
        for doc, meta in zip(docs, metadatas):
            result = CompatibilityAdapter.map_search_result(doc, meta)
            results.append(result)
        
        return {
            "query": str(query),
            "results": results
        }

    @staticmethod
    def map_rag_result(doc: str, meta: Dict[str, Any], distance: float, index: int = 0) -> Dict[str, Any]:
        """
        Map internal RAG result to RAGResultModel format
        
        Args:
            doc: Document content
            meta: Document metadata
            distance: Distance score
            index: Fallback index for ID
            
        Returns:
            Dict matching RAGResultModel schema
        """
        # Extract preview content (max 500 chars)
        preview = doc[:500] + "..." if len(doc) > 500 else doc
        
        result_id = meta.get("id", f"result-{index}")
        title = meta.get("title", "Untitled")
        source = meta.get("source", "unknown")
        relevance = 1.0 - distance
        
        return {
            "id": str(result_id),
            "title": str(title),
            "content": str(doc),
            "preview": str(preview),
            "source": str(source),
            "distance": float(distance),
            "relevance": float(relevance),
            "metadata": dict(meta)
        }

    @staticmethod
    def map_rag_query_response(query: str, search_type: str, docs: List[str], 
                             metadatas: List[Dict[str, Any]], distances: List[float]) -> Dict[str, Any]:
        """
        Map internal RAG query results to RAGQueryResponse format
        
        Args:
            query: Original query
            search_type: Search type used
            docs: List of document contents
            metadatas: List of document metadata
            distances: List of distance scores
            
        Returns:
            Dict matching RAGQueryResponse schema
        """
        results = []
        
        for i, (doc, meta, distance) in enumerate(zip(docs, metadatas, distances)):
            result = CompatibilityAdapter.map_rag_result(doc, meta, distance, i)
            results.append(result)
        
        return {
            "query": str(query),
            "search_type": str(search_type),
            "results": results
        }

    @staticmethod
    def map_stats_response(doc_count: int, collection_name: str, embedding_model: str) -> Dict[str, Any]:
        """
        Map internal stats to StatsResponse format
        
        Args:
            doc_count: Document count
            collection_name: Collection name
            embedding_model: Embedding model name
            
        Returns:
            Dict matching StatsResponse schema
        """
        return {
            "status": "healthy",
            "collection_name": str(collection_name),
            "document_count": int(doc_count),
            "embedding_model": str(embedding_model)
        }

    @staticmethod
    def map_health_response(is_healthy: bool, doc_count: Optional[int] = None,
                           collection_name: Optional[str] = None,
                           embedding_model: Optional[str] = None,
                           error: Optional[str] = None) -> Dict[str, Any]:
        """
        Map internal health data to HealthResponse format
        
        Args:
            is_healthy: Health status
            doc_count: Optional document count
            collection_name: Optional collection name
            embedding_model: Optional embedding model
            error: Optional error message
            
        Returns:
            Dict matching HealthResponse schema
        """
        response = {
            "status": "healthy" if is_healthy else "unhealthy"
        }
        
        if is_healthy:
            if collection_name is not None:
                response["collection_name"] = str(collection_name)
            if doc_count is not None:
                response["document_count"] = int(doc_count)
            if embedding_model is not None:
                response["embedding_model"] = str(embedding_model)
        else:
            if error is not None:
                response["error"] = str(error)
        
        return response

    @staticmethod
    def map_export_response(success: bool, message: Optional[str] = None,
                          error: Optional[str] = None, detail: Optional[str] = None) -> Dict[str, Any]:
        """
        Map export result to ExportResponse format
        
        Args:
            success: Export success status
            message: Optional success message
            error: Optional error message
            detail: Optional detailed error
            
        Returns:
            Dict matching ExportResponse schema
        """
        response = {"success": bool(success)}
        
        if message is not None:
            response["message"] = str(message)
        if error is not None:
            response["error"] = str(error)
        if detail is not None:
            response["detail"] = str(detail)
        
        return response

    @staticmethod
    def map_clear_database_response(success: bool, message: str) -> Dict[str, Any]:
        """
        Map clear database result to ClearDatabaseResponse format
        
        Args:
            success: Operation success status
            message: Status message
            
        Returns:
            Dict matching ClearDatabaseResponse schema
        """
        return {
            "status": "success" if success else "error",
            "message": str(message)
        }

    @staticmethod
    def map_error_response(error_message: str) -> Dict[str, Any]:
        """
        Map error to ErrorResponse format
        
        Args:
            error_message: Error message
            
        Returns:
            Dict matching ErrorResponse schema
        """
        return {
            "error": str(error_message)
        }

    @staticmethod
    def _extract_preview_content(content: str, max_length: int = 200) -> str:
        """
        Extract clean preview content from document
        
        Args:
            content: Full document content
            max_length: Maximum preview length
            
        Returns:
            Clean preview string
        """
        if not content:
            return ""
        
        # Remove markdown formatting for preview
        preview = content.strip()
        
        # Remove common markdown patterns
        import re
        preview = re.sub(r'\*\*([^*]+)\*\*', r'\1', preview)  # Bold
        preview = re.sub(r'\*([^*]+)\*', r'\1', preview)      # Italic
        preview = re.sub(r'`([^`]+)`', r'\1', preview)        # Code
        preview = re.sub(r'\n+', ' ', preview)                # Multiple newlines
        preview = re.sub(r'\s+', ' ', preview)                # Multiple spaces
        
        # Truncate and add ellipsis if needed
        if len(preview) > max_length:
            preview = preview[:max_length].rsplit(' ', 1)[0] + "..."
        
        return preview.strip()