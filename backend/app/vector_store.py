"""
Faiss-based vector store for image embeddings.
"""
import faiss
import numpy as np
import json
from pathlib import Path
from typing import Optional
import threading

from app.config import settings


class VectorStore:
    """
    Faiss-based vector store for efficient similarity search.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for vector store."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.dimension = settings.EMBEDDING_DIM
        self.index_path = settings.INDEX_DIR / "faiss.index"
        self.metadata_path = settings.INDEX_DIR / "metadata.json"
        
        # Initialize or load index
        self.index: Optional[faiss.IndexFlatIP] = None
        self.metadata: dict = {"images": [], "id_to_idx": {}}
        
        self._load_or_create_index()
        self._initialized = True
    
    def _load_or_create_index(self):
        """Load existing index or create new one."""
        if self.index_path.exists() and self.metadata_path.exists():
            print("📂 Loading existing Faiss index...")
            self.index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, "r") as f:
                self.metadata = json.load(f)
            print(f"✅ Loaded index with {self.index.ntotal} vectors")
        else:
            print("🆕 Creating new Faiss index...")
            # Use Inner Product (cosine similarity with normalized vectors)
            self.index = faiss.IndexFlatIP(self.dimension)
            print("✅ Created new empty index")
    
    def save(self):
        """Save index and metadata to disk."""
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2)
        print(f"💾 Saved index with {self.index.ntotal} vectors")
    
    def add_vectors(
        self,
        vectors: np.ndarray,
        image_ids: list[str],
        filenames: list[str],
        metadata_list: Optional[list[dict]] = None
    ):
        """
        Add vectors to the index.
        
        Args:
            vectors: Embedding vectors (N x D)
            image_ids: Unique image identifiers
            filenames: Image filenames
            metadata_list: Optional metadata for each image
        """
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)
        
        # Ensure vectors are normalized for cosine similarity
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / norms
        vectors = vectors.astype(np.float32)
        
        start_idx = self.index.ntotal
        self.index.add(vectors)
        
        for i, (img_id, filename) in enumerate(zip(image_ids, filenames)):
            idx = start_idx + i
            self.metadata["id_to_idx"][img_id] = idx
            self.metadata["images"].append({
                "image_id": img_id,
                "filename": filename,
                "idx": idx,
                "metadata": metadata_list[i] if metadata_list else {}
            })
    
    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 20
    ) -> tuple[list[str], list[float], list[dict]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            Tuple of (image_ids, scores, metadata_list)
        """
        if self.index.ntotal == 0:
            return [], [], []
        
        # Ensure query is normalized
        query_vector = query_vector.reshape(1, -1).astype(np.float32)
        query_vector = query_vector / np.linalg.norm(query_vector)
        
        # Search
        top_k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vector, top_k)
        
        image_ids = []
        similarities = []
        metadata_list = []
        
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.metadata["images"]):
                img_data = self.metadata["images"][idx]
                image_ids.append(img_data["image_id"])
                similarities.append(float(score))
                metadata_list.append(img_data)
        
        return image_ids, similarities, metadata_list
    
    def get_vector(self, image_id: str) -> Optional[np.ndarray]:
        """
        Get vector by image ID.
        
        Args:
            image_id: Image identifier
            
        Returns:
            Embedding vector or None if not found
        """
        if image_id not in self.metadata["id_to_idx"]:
            return None
        
        idx = self.metadata["id_to_idx"][image_id]
        vector = self.index.reconstruct(idx)
        return vector
    
    def get_vectors(self, image_ids: list[str]) -> np.ndarray:
        """
        Get multiple vectors by image IDs.
        
        Args:
            image_ids: List of image identifiers
            
        Returns:
            Array of embedding vectors
        """
        vectors = []
        for img_id in image_ids:
            vec = self.get_vector(img_id)
            if vec is not None:
                vectors.append(vec)
        return np.array(vectors) if vectors else np.array([])
    
    def get_all_vectors(self) -> np.ndarray:
        """Get all vectors in the index."""
        if self.index.ntotal == 0:
            return np.array([])
        return self.index.reconstruct_n(0, self.index.ntotal)
    
    @property
    def total_images(self) -> int:
        """Total number of images in index."""
        return self.index.ntotal if self.index else 0
    
    def clear(self):
        """Clear the index."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = {"images": [], "id_to_idx": {}}


# Global vector store instance
vector_store = VectorStore()

