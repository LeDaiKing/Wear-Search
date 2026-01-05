"""
Rocchio Algorithm implementation for query refinement.
"""
import numpy as np
from typing import Optional

from app.config import settings


class RocchioAlgorithm:
    """
    Implementation of the Rocchio Algorithm for relevance feedback.
    
    The modified query vector is computed as:
    q_m = α * q + (β / |D_r|) * Σ d_j - (γ / |D_n|) * Σ d_k
    
    Where:
    - q: Original query vector
    - D_r: Set of relevant document vectors
    - D_n: Set of non-relevant document vectors
    - α, β, γ: Tunable weights
    """
    
    def __init__(
        self,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        gamma: Optional[float] = None
    ):
        """
        Initialize Rocchio with parameters.
        
        Args:
            alpha: Weight for original query (default from settings)
            beta: Weight for relevant documents (default from settings)
            gamma: Weight for non-relevant documents (default from settings)
        """
        self.alpha = alpha if alpha is not None else settings.ROCCHIO_ALPHA
        self.beta = beta if beta is not None else settings.ROCCHIO_BETA
        self.gamma = gamma if gamma is not None else settings.ROCCHIO_GAMMA
    
    def refine_query(
        self,
        query_vector: np.ndarray,
        relevant_vectors: Optional[np.ndarray] = None,
        non_relevant_vectors: Optional[np.ndarray] = None,
        text_modification_vector: Optional[np.ndarray] = None,
        text_weight: float = 0.3
    ) -> np.ndarray:
        """
        Refine query vector using Rocchio algorithm with optional text modification.
        
        Args:
            query_vector: Original query vector
            relevant_vectors: Array of relevant document vectors (N x D)
            non_relevant_vectors: Array of non-relevant document vectors (M x D)
            text_modification_vector: Optional text feedback vector
            text_weight: Weight for text modification
            
        Returns:
            Refined query vector (normalized)
        """
        # Start with weighted original query
        refined = self.alpha * query_vector.copy()
        
        # Add centroid of relevant documents
        if relevant_vectors is not None and len(relevant_vectors) > 0:
            relevant_centroid = np.mean(relevant_vectors, axis=0)
            refined += self.beta * relevant_centroid
        
        # Subtract centroid of non-relevant documents
        if non_relevant_vectors is not None and len(non_relevant_vectors) > 0:
            non_relevant_centroid = np.mean(non_relevant_vectors, axis=0)
            refined -= self.gamma * non_relevant_centroid
        
        # Apply text modification if provided
        if text_modification_vector is not None:
            refined = (1 - text_weight) * refined + text_weight * text_modification_vector
        
        # Normalize the result
        norm = np.linalg.norm(refined)
        if norm > 0:
            refined = refined / norm
        
        return refined.astype(np.float32)
    
    def pseudo_relevance_feedback(
        self,
        query_vector: np.ndarray,
        top_vectors: np.ndarray,
        top_m: Optional[int] = None
    ) -> np.ndarray:
        """
        Apply pseudo (blind) relevance feedback.
        
        Assumes top-m retrieved documents are relevant and uses them
        for query expansion without explicit user feedback.
        
        Args:
            query_vector: Original query vector
            top_vectors: Vectors of top retrieved documents
            top_m: Number of documents to assume relevant (default from settings)
            
        Returns:
            Refined query vector
        """
        top_m = top_m if top_m is not None else settings.PRF_TOP_K
        
        # Use top-m documents as "relevant"
        relevant_vectors = top_vectors[:top_m] if len(top_vectors) >= top_m else top_vectors
        
        # Apply Rocchio with only relevant feedback (no explicit negatives)
        return self.refine_query(
            query_vector=query_vector,
            relevant_vectors=relevant_vectors,
            non_relevant_vectors=None
        )
    
    def compute_query_shift(
        self,
        original_query: np.ndarray,
        refined_query: np.ndarray
    ) -> dict:
        """
        Compute metrics about query shift for visualization.
        
        Args:
            original_query: Original query vector
            refined_query: Refined query vector
            
        Returns:
            Dictionary with shift metrics
        """
        # Cosine similarity between original and refined
        similarity = float(np.dot(original_query, refined_query))
        
        # Euclidean distance
        distance = float(np.linalg.norm(refined_query - original_query))
        
        return {
            "similarity": similarity,
            "distance": distance,
            "shift_magnitude": distance
        }


# Global Rocchio instance
rocchio = RocchioAlgorithm()

