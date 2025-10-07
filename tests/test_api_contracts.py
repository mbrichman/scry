"""
API Contract Tests

These tests ensure that the API responses always match the expected contract,
regardless of backend changes. All tests in this file MUST pass before deployment.
"""

import json
from typing import Dict, Any
from unittest.mock import Mock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.contracts.api_contract import APIContract
from api.compat import CompatibilityAdapter


class TestAPIContracts:
    """Test that all API responses conform to the contract"""
    
    def test_conversation_summary_mapping(self):
        """Test conversation summary mapping follows contract"""
        # Mock data
        doc = "This is a test conversation with some content that should be previewed"
        meta = {
            "id": "test-123",
            "title": "Test Conversation", 
            "earliest_ts": "2025-01-01T10:00:00Z",
            "source": "chatgpt"
        }
        
        # Map using adapter
        result = CompatibilityAdapter.map_conversation_summary(doc, meta, 0)
        
        # Validate contract
        assert APIContract.validate_response("GET /api/conversations", {"conversations": [result], "pagination": {"page": 1, "limit": 10, "total": 1, "has_next": False, "has_prev": False}})
        
        # Check required fields
        assert "id" in result
        assert "title" in result
        assert "preview" in result
        assert "date" in result
        assert "source" in result
        
        # Check data types
        assert isinstance(result["id"], str)
        assert isinstance(result["title"], str)
        assert isinstance(result["preview"], str)
        assert isinstance(result["date"], str)
        assert isinstance(result["source"], str)

    def test_conversations_list_response_mapping(self):
        """Test conversations list response follows contract"""
        # Mock data
        docs = ["Test doc 1", "Test doc 2"]
        metadatas = [
            {"id": "conv-1", "title": "Conv 1", "earliest_ts": "2025-01-01T10:00:00Z", "source": "chatgpt"},
            {"id": "conv-2", "title": "Conv 2", "earliest_ts": "2025-01-02T10:00:00Z", "source": "claude"}
        ]
        
        # Map using adapter
        result = CompatibilityAdapter.map_conversations_list_response(docs, metadatas, 1, 10, 2)
        
        # Validate contract
        assert APIContract.validate_response("GET /api/conversations", result)
        
        # Check structure
        assert "conversations" in result
        assert "pagination" in result
        assert len(result["conversations"]) == 2
        
        # Check pagination
        pagination = result["pagination"]
        assert pagination["page"] == 1
        assert pagination["limit"] == 10
        assert pagination["total"] == 2
        assert pagination["has_next"] is False
        assert pagination["has_prev"] is False

    def test_message_mapping(self):
        """Test message mapping follows contract"""
        result = CompatibilityAdapter.map_message("user-1", "user", "Hello world", "2025-01-01T10:00:00Z")
        
        # Check required fields
        assert "id" in result
        assert "role" in result
        assert "content" in result
        assert "timestamp" in result
        
        # Check values
        assert result["id"] == "user-1"
        assert result["role"] == "user"
        assert result["content"] == "Hello world"
        assert result["timestamp"] == "2025-01-01T10:00:00Z"
        
        # Test with null timestamp
        result_null = CompatibilityAdapter.map_message("user-2", "user", "Hello", None)
        assert result_null["timestamp"] is None

    def test_conversation_detail_response_mapping(self):
        """Test conversation detail response follows contract"""
        # Mock data
        messages = [
            {"id": "user-1", "role": "user", "content": "Hello", "timestamp": None},
            {"id": "assistant-1", "role": "assistant", "content": "Hi there!", "timestamp": None}
        ]
        metadata = {"title": "Test Chat", "source": "chatgpt", "earliest_ts": "2025-01-01T10:00:00Z"}
        
        # Map using adapter
        result = CompatibilityAdapter.map_conversation_detail_response(
            "test-123", "doc content", metadata, messages, "ChatGPT"
        )
        
        # Validate contract
        assert APIContract.validate_response("GET /api/conversation/<id>", result)
        
        # Check structure
        assert "id" in result
        assert "title" in result
        assert "source" in result
        assert "date" in result
        assert "assistant_name" in result
        assert "messages" in result
        assert len(result["messages"]) == 2

    def test_search_response_mapping(self):
        """Test search response follows contract"""
        # Mock data
        docs = ["Search result 1 content", "Search result 2 content"]
        metadatas = [
            {"title": "Result 1", "earliest_ts": "2025-01-01T10:00:00Z", "extra": "data"},
            {"title": "Result 2", "earliest_ts": "2025-01-02T10:00:00Z", "other": "info"}
        ]
        
        # Map using adapter
        result = CompatibilityAdapter.map_search_response("test query", docs, metadatas)
        
        # Validate contract
        assert APIContract.validate_response("GET /api/search", result)
        
        # Check structure
        assert "query" in result
        assert "results" in result
        assert result["query"] == "test query"
        assert len(result["results"]) == 2
        
        # Check result structure
        for search_result in result["results"]:
            assert "title" in search_result
            assert "date" in search_result
            assert "content" in search_result
            assert "metadata" in search_result

    def test_rag_query_response_mapping(self):
        """Test RAG query response follows contract"""
        # Mock data
        docs = ["RAG result content here"]
        metadatas = [{"id": "rag-1", "title": "RAG Result", "source": "chatgpt"}]
        distances = [0.25]
        
        # Map using adapter
        result = CompatibilityAdapter.map_rag_query_response(
            "rag query", "semantic", docs, metadatas, distances
        )
        
        # Validate contract
        assert APIContract.validate_response("POST /api/rag/query", result)
        
        # Check structure
        assert "query" in result
        assert "search_type" in result
        assert "results" in result
        assert len(result["results"]) == 1
        
        # Check result structure
        rag_result = result["results"][0]
        assert "id" in rag_result
        assert "title" in rag_result
        assert "content" in rag_result
        assert "preview" in rag_result
        assert "source" in rag_result
        assert "distance" in rag_result
        assert "relevance" in rag_result
        assert "metadata" in rag_result
        
        # Check relevance calculation
        assert rag_result["relevance"] == 0.75  # 1.0 - 0.25

    def test_stats_response_mapping(self):
        """Test stats response follows contract"""
        result = CompatibilityAdapter.map_stats_response(150, "chat_history", "all-MiniLM-L6-v2")
        
        # Validate contract  
        assert APIContract.validate_response("GET /api/stats", result)
        
        # Check structure
        assert "status" in result
        assert "collection_name" in result
        assert "document_count" in result
        assert "embedding_model" in result
        assert result["status"] == "healthy"

    def test_health_response_mapping(self):
        """Test health response follows contract"""
        # Test healthy response
        result_healthy = CompatibilityAdapter.map_health_response(
            True, doc_count=100, collection_name="test", embedding_model="model"
        )
        
        assert APIContract.validate_response("GET /api/rag/health", result_healthy)
        assert result_healthy["status"] == "healthy"
        assert "error" not in result_healthy or result_healthy.get("error") is None
        
        # Test unhealthy response
        result_unhealthy = CompatibilityAdapter.map_health_response(False, error="Connection failed")
        
        assert APIContract.validate_response("GET /api/rag/health", result_unhealthy)
        assert result_unhealthy["status"] == "unhealthy"
        assert result_unhealthy["error"] == "Connection failed"

    def test_export_response_mapping(self):
        """Test export response follows contract"""
        # Test success response
        result_success = CompatibilityAdapter.map_export_response(True, message="Export successful")
        
        assert APIContract.validate_response("POST /export_to_openwebui/<id>", result_success)
        assert result_success["success"] is True
        assert result_success["message"] == "Export successful"
        
        # Test error response
        result_error = CompatibilityAdapter.map_export_response(
            False, error="Export failed", detail="Connection timeout"
        )
        
        assert APIContract.validate_response("POST /export_to_openwebui/<id>", result_error)
        assert result_error["success"] is False
        assert result_error["error"] == "Export failed"
        assert result_error["detail"] == "Connection timeout"

    def test_error_response_mapping(self):
        """Test error response follows contract"""
        result = CompatibilityAdapter.map_error_response("Something went wrong")
        
        assert APIContract.validate_response("ERROR", result)
        assert "error" in result
        assert result["error"] == "Something went wrong"

    def test_preview_content_extraction(self):
        """Test preview content extraction logic"""
        # Test normal content
        content = "This is a test conversation with **bold** and *italic* text."
        preview = CompatibilityAdapter._extract_preview_content(content, 50)
        
        # Should remove markdown
        assert "**" not in preview
        assert "*" not in preview
        assert len(preview) <= 53  # 50 + "..."
        
        # Test long content
        long_content = "A" * 300
        preview = CompatibilityAdapter._extract_preview_content(long_content, 100)
        assert len(preview) <= 103  # 100 + "..."
        assert preview.endswith("...")
        
        # Test empty content
        empty_preview = CompatibilityAdapter._extract_preview_content("", 100)
        assert empty_preview == ""

    def test_fallback_values(self):
        """Test that mapping functions provide appropriate fallbacks"""
        # Test with minimal metadata
        minimal_meta = {}
        result = CompatibilityAdapter.map_conversation_summary("content", minimal_meta, 5)
        
        assert result["id"] == "conv-5"  # Fallback ID
        assert result["title"] == "Untitled Conversation"  # Default title
        assert result["date"] == ""  # Empty string for missing date
        assert result["source"] == "unknown"  # Default source
        
        # Test with None/empty values
        none_meta = {"id": None, "title": None, "earliest_ts": None, "source": None}
        result = CompatibilityAdapter.map_conversation_summary("content", none_meta, 10)
        
        assert result["id"] == "conv-10"  # Fallback when None
        assert result["title"] == "Untitled Conversation"


class TestContractValidation:
    """Test the contract validation system itself"""
    
    def test_valid_response_passes_validation(self):
        """Test that valid responses pass validation"""
        valid_response = {
            "conversations": [
                {"id": "1", "title": "Test", "preview": "Preview", "date": "2025-01-01", "source": "test"}
            ],
            "pagination": {"page": 1, "limit": 10, "total": 1, "has_next": False, "has_prev": False}
        }
        
        assert APIContract.validate_response("GET /api/conversations", valid_response)

    def test_invalid_response_fails_validation(self):
        """Test that invalid responses fail validation"""
        invalid_response = {
            "conversations": [
                {"id": 123, "title": "Test"}  # Missing fields, wrong types
            ]
        }
        
        assert not APIContract.validate_response("GET /api/conversations", invalid_response)

    def test_unknown_endpoint_passes_validation(self):
        """Test that unknown endpoints pass validation (no schema defined)"""
        assert APIContract.validate_response("GET /unknown", {"anything": "goes"})

    def test_request_validation(self):
        """Test request validation"""
        valid_request = {"query": "test", "n_results": 5, "search_type": "semantic"}
        assert APIContract.validate_request("POST /api/rag/query", valid_request)
        
        invalid_request = {"n_results": "invalid"}  # Missing query, wrong type
        assert not APIContract.validate_request("POST /api/rag/query", invalid_request)


if __name__ == "__main__":
    # Run tests directly for development
    import unittest
    unittest.main()