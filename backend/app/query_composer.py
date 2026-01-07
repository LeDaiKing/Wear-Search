"""
Query Composer for Natural Language Feedback.

Implements various composition strategies for combining 
image queries with text modifications, separate from Rocchio.
"""
import numpy as np
from typing import Optional, Literal
from enum import Enum

from app.config import settings


class CompositionMethod(str, Enum):
    """Available composition methods for NLF."""
    ADDITIVE = "additive"           # q_new = q + λ * text
    INTERPOLATION = "interpolation" # q_new = (1-α) * q + α * text
    RESIDUAL = "residual"           # q_new = q + (text - projection)
    ATTENTION = "attention"         # Feature-wise attention weighting


class QueryComposer:
    """
    Composes query vectors with natural language modifications.
    
    Unlike Rocchio which shifts toward/away from documents,
    this class modifies the semantic content of queries using
    text embeddings as modifiers.
    """
    
    def __init__(
        self,
        default_method: CompositionMethod = CompositionMethod.RESIDUAL,
        additive_lambda: float = 0.5,
        interpolation_alpha: float = 0.6,
        residual_strength: float = 0.8,
        attention_temperature: float = 1.0
    ):
        """
        Initialize QueryComposer with composition parameters.
        
        Args:
            default_method: Default composition method
            additive_lambda: Strength of additive modification
            interpolation_alpha: Weight for text in interpolation (higher = more text influence)
            residual_strength: Strength of residual modification
            attention_temperature: Temperature for attention softmax
        """
        self.default_method = default_method
        self.additive_lambda = additive_lambda
        self.interpolation_alpha = interpolation_alpha
        self.residual_strength = residual_strength
        self.attention_temperature = attention_temperature
    
    def compose(
        self,
        query_vector: np.ndarray,
        text_vector: np.ndarray,
        method: Optional[CompositionMethod] = None
    ) -> np.ndarray:
        """
        Compose query with text modification using specified method.
        
        Args:
            query_vector: Original query embedding (from image or text)
            text_vector: Text modification embedding (e.g., "navy color")
            method: Composition method (uses default if None)
            
        Returns:
            Modified query vector (normalized)
        """
        method = method or self.default_method
        
        # Normalize inputs
        query_vector = self._normalize(query_vector)
        text_vector = self._normalize(text_vector)
        
        if method == CompositionMethod.ADDITIVE:
            result = self._additive_compose(query_vector, text_vector)
        elif method == CompositionMethod.INTERPOLATION:
            result = self._interpolation_compose(query_vector, text_vector)
        elif method == CompositionMethod.RESIDUAL:
            result = self._residual_compose(query_vector, text_vector)
        elif method == CompositionMethod.ATTENTION:
            result = self._attention_compose(query_vector, text_vector)
        else:
            raise ValueError(f"Unknown composition method: {method}")
        
        return self._normalize(result).astype(np.float32)
    
    def _normalize(self, vector: np.ndarray) -> np.ndarray:
        """Normalize vector to unit length."""
        norm = np.linalg.norm(vector)
        if norm > 0:
            return vector / norm
        return vector
    
    def _additive_compose(
        self,
        query: np.ndarray,
        text: np.ndarray
    ) -> np.ndarray:
        """
        Additive composition: q_new = q + λ * text
        
        Treats text as a direction to shift the query.
        Good for modifications like "add stripes" or "make darker".
        """
        return query + self.additive_lambda * text
    
    def _interpolation_compose(
        self,
        query: np.ndarray,
        text: np.ndarray
    ) -> np.ndarray:
        """
        Interpolation composition: q_new = (1-α) * q + α * text
        
        Linear blend between query and text.
        Good for strong modifications like changing color entirely.
        """
        return (1 - self.interpolation_alpha) * query + self.interpolation_alpha * text
    
    def _residual_compose(
        self,
        query: np.ndarray,
        text: np.ndarray
    ) -> np.ndarray:
        """
        Residual composition: q_new = q + strength * (text - proj(text, q))
        
        Adds the component of text that is orthogonal to query.
        This preserves the original query's main features while
        adding new information from the text.
        
        Good for refinements like "similar but in blue" - keeps
        the "similar" part and adds the "blue" modification.
        """
        # Project text onto query direction
        projection = np.dot(text, query) * query
        
        # Get the residual (orthogonal component)
        residual = text - projection
        
        # Add scaled residual to query
        return query + self.residual_strength * residual
    
    def _attention_compose(
        self,
        query: np.ndarray,
        text: np.ndarray
    ) -> np.ndarray:
        """
        Attention-based composition: Feature-wise weighted combination.
        
        Uses text vector to compute attention weights for each feature,
        then applies weighted combination. This allows text to selectively
        modify certain features while preserving others.
        
        Good for nuanced modifications where only certain aspects
        should change (e.g., color but not style).
        """
        # Compute attention weights based on text magnitude per feature
        # Higher absolute values in text = more modification
        text_importance = np.abs(text)
        
        # Apply temperature-scaled softmax-like transformation
        attention_weights = np.exp(text_importance / self.attention_temperature)
        attention_weights = attention_weights / np.sum(attention_weights) * len(attention_weights)
        
        # Clamp weights to reasonable range [0.5, 2.0]
        attention_weights = np.clip(attention_weights, 0.5, 2.0)
        
        # Feature-wise combination with attention
        # High attention = more text influence, low attention = more query influence
        text_influence = (attention_weights - 1.0) / 2.0 + 0.5  # Map to [0.25, 0.75]
        
        composed = (1 - text_influence) * query + text_influence * text
        
        return composed
    
    def compose_multiple(
        self,
        query_vector: np.ndarray,
        text_vectors: list[np.ndarray],
        method: Optional[CompositionMethod] = None,
        aggregation: Literal["sequential", "average"] = "sequential"
    ) -> np.ndarray:
        """
        Compose query with multiple text modifications.
        
        Args:
            query_vector: Original query embedding
            text_vectors: List of text modification embeddings
            method: Composition method
            aggregation: How to combine multiple texts:
                - "sequential": Apply each modification in sequence
                - "average": Average all text vectors first, then compose
                
        Returns:
            Modified query vector (normalized)
        """
        if not text_vectors:
            return self._normalize(query_vector).astype(np.float32)
        
        if aggregation == "average":
            # Average all text vectors
            avg_text = np.mean(text_vectors, axis=0)
            return self.compose(query_vector, avg_text, method)
        
        else:  # sequential
            result = query_vector.copy()
            for text_vec in text_vectors:
                result = self.compose(result, text_vec, method)
            return result


# Global composer instance with good defaults for color/style modifications
query_composer = QueryComposer(
    default_method=CompositionMethod.RESIDUAL,
    interpolation_alpha=0.6,  # Strong text influence for color changes
    residual_strength=0.8,    # Strong residual for adding new features
)

