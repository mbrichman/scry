"""
Synonym and acronym mappings for query expansion in search.

This module provides bidirectional synonym mappings to improve search results
by expanding queries with related terms and acronyms.
"""

# Acronym/synonym mapping (bidirectional)
SEARCH_SYNONYMS = {
    # Tech acronyms
    'zk': ['zero knowledge', 'zero-knowledge'],
    'zero knowledge': ['zk'],
    'zero-knowledge': ['zk'],
    
    'api': ['application programming interface'],
    'application programming interface': ['api'],
    
    'ml': ['machine learning'],
    'machine learning': ['ml'],
    
    'ai': ['artificial intelligence'],
    'artificial intelligence': ['ai'],
    
    'nlp': ['natural language processing'],
    'natural language processing': ['nlp'],
    
    'rag': ['retrieval augmented generation', 'retrieval-augmented generation'],
    'retrieval augmented generation': ['rag'],
    'retrieval-augmented generation': ['rag'],
    
    'llm': ['large language model'],
    'large language model': ['llm'],
    
    'ui': ['user interface'],
    'user interface': ['ui'],
    
    'ux': ['user experience'],
    'user experience': ['ux'],
    
    'sql': ['structured query language'],
    'structured query language': ['sql'],
    
    # App-specific terms
    'search': ['find', 'lookup', 'query'],
    'find': ['search', 'lookup'],
    'lookup': ['search', 'find'],
    
    'message': ['text', 'content', 'chat'],
    'text': ['message', 'content'],
    
    'conversation': ['chat', 'discussion', 'dialogue'],
    'chat': ['conversation', 'discussion'],
    'discussion': ['conversation', 'chat'],
    
    'database': ['db', 'storage', 'data'],
    'db': ['database'],
    
    'postgresql': ['postgres', 'pg', 'psql'],
    'postgres': ['postgresql', 'pg'],
    'pg': ['postgresql', 'postgres'],
    
    'embedding': ['vector', 'similarity', 'semantic'],
    'vector': ['embedding', 'similarity'],
    'semantic': ['embedding', 'similarity'],
}


def get_synonyms(term: str) -> list[str]:
    """
    Get synonyms for a given term.
    
    Args:
        term: The term to get synonyms for
        
    Returns:
        List of synonyms (empty list if no synonyms found)
    """
    return SEARCH_SYNONYMS.get(term.lower(), [])


def add_synonym_mapping(term: str, synonyms: list[str], bidirectional: bool = True):
    """
    Add a new synonym mapping dynamically.
    
    Args:
        term: The term to add synonyms for
        synonyms: List of synonym terms
        bidirectional: If True, also map synonyms back to the original term
    """
    SEARCH_SYNONYMS[term.lower()] = synonyms
    
    if bidirectional:
        for syn in synonyms:
            if syn.lower() not in SEARCH_SYNONYMS:
                SEARCH_SYNONYMS[syn.lower()] = [term]
            elif term not in SEARCH_SYNONYMS[syn.lower()]:
                SEARCH_SYNONYMS[syn.lower()].append(term)
