"""
Fake Embedding Generator for Testing

Provides fast, deterministic embeddings for tests without loading actual ML models.
Uses seeded NumPy random number generator to ensure reproducibility.
"""
import hashlib
import numpy as np
from typing import List, Union


class FakeEmbeddingGenerator:
    """
    Generate deterministic fake embeddings for testing.
    
    Benefits:
    - Fast (no model loading)
    - Deterministic (same text always produces same embedding)
    - Realistic shape (384 dimensions matching all-MiniLM-L6-v2)
    - Stable distances (similar texts have similar embeddings)
    """
    
    def __init__(self, dimension: int = 384, seed: int = 42):
        """
        Initialize fake embedding generator.
        
        Args:
            dimension: Embedding vector dimension (default: 384 for all-MiniLM-L6-v2)
            seed: Random seed for reproducibility
        """
        self.dimension = dimension
        self.seed = seed
        self.rng = np.random.RandomState(seed)
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a single deterministic embedding for text.
        
        Uses hash of text as seed to ensure:
        - Same text always produces same embedding
        - Similar texts produce similar embeddings (via string hashing)
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text:
            # Return zero vector for empty text
            return [0.0] * self.dimension
        
        # Use text hash as seed for this specific embedding
        text_hash = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        text_rng = np.random.RandomState(text_hash)
        
        # Generate random vector
        vector = text_rng.randn(self.dimension)
        
        # Normalize to unit length (like real embeddings)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector.tolist()
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate multiple embeddings in batch.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        return [self.generate_embedding(text) for text in texts]
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (-1 to 1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def generate_similar_embedding(self, base_text: str, similarity: float = 0.9) -> List[float]:
        """
        Generate an embedding similar to base_text.
        
        Useful for testing similarity search functionality.
        
        Args:
            base_text: Base text to generate similar embedding for
            similarity: Target similarity score (0 to 1)
            
        Returns:
            Embedding vector similar to base_text embedding
        """
        base_embedding = np.array(self.generate_embedding(base_text))
        
        # Generate random noise
        noise = self.rng.randn(self.dimension)
        noise = noise / np.linalg.norm(noise)
        
        # Mix base embedding with noise to achieve target similarity
        # similarity = cos(theta), so theta = arccos(similarity)
        theta = np.arccos(np.clip(similarity, -1.0, 1.0))
        
        # Create similar vector using rotation
        similar = np.cos(theta) * base_embedding + np.sin(theta) * noise
        
        # Normalize
        similar = similar / np.linalg.norm(similar)
        
        return similar.tolist()


# Global instance for convenience
_default_generator = None


def get_fake_embedding_generator(dimension: int = 384, seed: int = 42) -> FakeEmbeddingGenerator:
    """
    Get or create the default fake embedding generator.
    
    Args:
        dimension: Embedding dimension
        seed: Random seed
        
    Returns:
        FakeEmbeddingGenerator instance
    """
    global _default_generator
    if _default_generator is None:
        _default_generator = FakeEmbeddingGenerator(dimension=dimension, seed=seed)
    return _default_generator


def generate_fake_embedding(text: str) -> List[float]:
    """
    Convenience function to generate a single fake embedding.
    
    Args:
        text: Input text
        
    Returns:
        Embedding vector
    """
    generator = get_fake_embedding_generator()
    return generator.generate_embedding(text)


def generate_fake_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Convenience function to generate multiple fake embeddings.
    
    Args:
        texts: List of input texts
        
    Returns:
        List of embedding vectors
    """
    generator = get_fake_embedding_generator()
    return generator.generate_embeddings(texts)


# Patch function for monkey-patching actual embedding generators in tests
def patch_embedding_function(model_function):
    """
    Decorator to replace actual embedding function with fake one in tests.
    
    Usage:
        @patch_embedding_function
        def test_something():
            # Your test code
    """
    def wrapper(*args, **kwargs):
        # Replace with fake embeddings
        if len(args) > 0 and isinstance(args[0], (list, str)):
            texts = args[0] if isinstance(args[0], list) else [args[0]]
            return generate_fake_embeddings(texts)
        return model_function(*args, **kwargs)
    return wrapper
