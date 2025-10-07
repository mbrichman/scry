"""
API Contract Definition for Dovos Chat Archive System

This file defines the expected request/response schemas for all API endpoints.
These contracts MUST NOT change during the migration to ensure frontend compatibility.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


# ========== Response Models ==========

class PaginationModel(BaseModel):
    """Pagination metadata for paginated responses"""
    page: int = Field(..., description="Current page number (1-based)")
    limit: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of items")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class ConversationSummaryModel(BaseModel):
    """Summary of a conversation for list views"""
    id: str = Field(..., description="Unique conversation identifier")
    title: str = Field(..., description="Conversation title")
    preview: str = Field(..., description="Preview text (max 200 chars)")
    date: str = Field(..., description="ISO timestamp or empty string")
    source: str = Field(..., description="Source system (chatgpt, claude, etc.)")


class ConversationsListResponse(BaseModel):
    """Response for GET /api/conversations"""
    conversations: List[ConversationSummaryModel] = Field(..., description="List of conversations")
    pagination: PaginationModel = Field(..., description="Pagination metadata")


class MessageModel(BaseModel):
    """Individual message within a conversation"""
    id: str = Field(..., description="Message ID (e.g. 'user-1', 'assistant-1')")
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp or null")


class ConversationDetailResponse(BaseModel):
    """Response for GET /api/conversation/<id>"""
    id: str = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    source: str = Field(..., description="Source system")
    date: Optional[str] = Field(None, description="Conversation date or null")
    assistant_name: str = Field(..., description="Assistant name (ChatGPT, Claude, AI)")
    messages: List[MessageModel] = Field(..., description="List of messages")


class SearchResultModel(BaseModel):
    """Individual search result"""
    title: str = Field(..., description="Result title")
    date: str = Field(..., description="Result date or 'Unknown'")
    content: str = Field(..., description="Preview content (max 300 chars)")
    metadata: Dict[str, Any] = Field(..., description="Full metadata object")


class SearchResponse(BaseModel):
    """Response for GET /api/search"""
    query: str = Field(..., description="Original search query")
    results: List[SearchResultModel] = Field(..., description="Search results")


class RAGResultModel(BaseModel):
    """Individual RAG query result"""
    id: str = Field(..., description="Result ID")
    title: str = Field(..., description="Result title")
    content: str = Field(..., description="Full content")
    preview: str = Field(..., description="Preview content (max 500 chars)")
    source: str = Field(..., description="Source system")
    distance: float = Field(..., description="Distance score from query")
    relevance: float = Field(..., description="Relevance score (1.0 - distance)")
    metadata: Dict[str, Any] = Field(..., description="Full metadata object")


class RAGQueryResponse(BaseModel):
    """Response for POST /api/rag/query"""
    query: str = Field(..., description="Original query")
    search_type: str = Field(..., description="Search type used")
    results: List[RAGResultModel] = Field(..., description="RAG results")


class StatsResponse(BaseModel):
    """Response for GET /api/stats"""
    status: str = Field(..., description="Health status")
    collection_name: str = Field(..., description="Collection name")
    document_count: int = Field(..., description="Total document count")
    embedding_model: str = Field(..., description="Embedding model name")


class HealthResponse(BaseModel):
    """Response for GET /api/rag/health"""
    status: str = Field(..., description="Health status (healthy/unhealthy)")
    collection_name: Optional[str] = Field(None, description="Collection name if healthy")
    document_count: Optional[int] = Field(None, description="Document count if healthy")
    embedding_model: Optional[str] = Field(None, description="Embedding model if healthy")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class ExportResponse(BaseModel):
    """Response for POST /export_to_openwebui/<id>"""
    success: bool = Field(..., description="Export success status")
    message: Optional[str] = Field(None, description="Success message")
    error: Optional[str] = Field(None, description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class ClearDatabaseResponse(BaseModel):
    """Response for POST /clear_db"""
    status: str = Field(..., description="Operation status (success/error)")
    message: str = Field(..., description="Status message")


class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: str = Field(..., description="Error message")


# ========== Request Models ==========

class RAGQueryRequest(BaseModel):
    """Request for POST /api/rag/query"""
    query: str = Field(..., description="Search query text")
    n_results: Optional[int] = Field(5, description="Number of results to return")
    search_type: Optional[str] = Field("semantic", description="Search type (semantic/keyword)")


# ========== API Contract Registry ==========

class APIContract:
    """Registry of all API contracts that must be preserved"""
    
    # Non-negotiable HTTP routes and methods
    ROUTES = {
        "GET /": "Redirect to conversations view",
        "GET /conversations": "HTML conversations list page", 
        "POST /conversations": "HTML conversations list page with search",
        "GET /conversations/<page>": "HTML conversations list page (paginated)",
        "POST /conversations/<page>": "HTML conversations list page (paginated with search)",
        "GET /view/<doc_id>": "HTML conversation detail view",
        "GET /export/<doc_id>": "Export conversation as markdown",
        "POST /export_to_openwebui/<doc_id>": "Export to OpenWebUI",
        "GET /upload": "HTML upload form",
        "POST /upload": "File upload handler",
        "GET /stats": "HTML stats page",
        "GET /api/conversations": "JSON conversations list",
        "GET /api/conversation/<conversation_id>": "JSON conversation detail", 
        "GET /api/search": "JSON search results",
        "GET /api/stats": "JSON stats",
        "POST /api/rag/query": "RAG query endpoint",
        "GET /api/rag/health": "RAG health check",
        "POST /clear_db": "Clear database"
    }
    
    # Query parameters that must be preserved
    QUERY_PARAMS = {
        "/api/conversations": ["page", "limit"],
        "/api/search": ["q", "n", "keyword"],
        "/api/rag/query": [],  # POST body only
    }
    
    # Response schemas that must be preserved
    RESPONSE_SCHEMAS = {
        "GET /api/conversations": ConversationsListResponse,
        "GET /api/conversation/<id>": ConversationDetailResponse,
        "GET /api/search": SearchResponse,
        "POST /api/rag/query": RAGQueryResponse,
        "GET /api/stats": StatsResponse,
        "GET /api/rag/health": HealthResponse,
        "POST /export_to_openwebui/<id>": ExportResponse,
        "POST /clear_db": ClearDatabaseResponse,
        "ERROR": ErrorResponse
    }
    
    # Request schemas for POST/PUT endpoints
    REQUEST_SCHEMAS = {
        "POST /api/rag/query": RAGQueryRequest
    }
    
    # Status codes that must be preserved
    STATUS_CODES = {
        "GET /api/conversations": [200, 500],
        "GET /api/conversation/<id>": [200, 404, 500],
        "GET /api/search": [200, 400, 500],
        "POST /api/rag/query": [200, 400, 500],
        "GET /api/stats": [200, 500],
        "GET /api/rag/health": [200, 500],
        "POST /export_to_openwebui/<id>": [200, 404, 500],
        "POST /clear_db": [200, 500]
    }
    
    @classmethod
    def validate_response(cls, endpoint: str, response_data: dict, status_code: int = 200) -> bool:
        """Validate a response matches the contract"""
        if endpoint not in cls.RESPONSE_SCHEMAS:
            return True  # No schema defined, skip validation
            
        schema = cls.RESPONSE_SCHEMAS[endpoint]
        try:
            schema.model_validate(response_data)
            return True
        except Exception as e:
            print(f"Contract violation for {endpoint}: {e}")
            return False
    
    @classmethod
    def validate_request(cls, endpoint: str, request_data: dict) -> bool:
        """Validate a request matches the contract"""
        if endpoint not in cls.REQUEST_SCHEMAS:
            return True  # No schema defined, skip validation
            
        schema = cls.REQUEST_SCHEMAS[endpoint]
        try:
            schema.model_validate(request_data)
            return True
        except Exception as e:
            print(f"Request contract violation for {endpoint}: {e}")
            return False