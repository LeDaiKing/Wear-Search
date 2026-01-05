"""
Session management for tracking search iterations and query history.
"""
import uuid
from datetime import datetime
from typing import Optional
import numpy as np
from dataclasses import dataclass, field
from sklearn.decomposition import PCA
import threading


@dataclass
class SearchIteration:
    """Represents a single search iteration."""
    iteration: int
    query_vector: np.ndarray
    query_type: str  # "text", "image", "feedback"
    results: list[str]  # List of image IDs
    positive_feedback: list[str] = field(default_factory=list)
    negative_feedback: list[str] = field(default_factory=list)
    text_feedback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Session:
    """Represents a user search session."""
    session_id: str
    created_at: datetime
    iterations: list[SearchIteration] = field(default_factory=list)
    
    @property
    def current_iteration(self) -> int:
        return len(self.iterations)
    
    @property
    def current_query_vector(self) -> Optional[np.ndarray]:
        if self.iterations:
            return self.iterations[-1].query_vector
        return None
    
    def get_all_query_vectors(self) -> list[np.ndarray]:
        return [it.query_vector for it in self.iterations]
    
    def get_feedback_counts(self) -> dict:
        total_positive = sum(len(it.positive_feedback) for it in self.iterations)
        total_negative = sum(len(it.negative_feedback) for it in self.iterations)
        return {"positive": total_positive, "negative": total_negative}


class SessionManager:
    """
    Manages search sessions for tracking iterations and enabling visualization.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.sessions: dict[str, Session] = {}
        self.pca: Optional[PCA] = None
        self._initialized = True
    
    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = Session(
            session_id=session_id,
            created_at=datetime.now()
        )
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> tuple[str, Session]:
        """Get existing session or create new one."""
        if session_id and session_id in self.sessions:
            return session_id, self.sessions[session_id]
        
        new_id = self.create_session()
        return new_id, self.sessions[new_id]
    
    def add_iteration(
        self,
        session_id: str,
        query_vector: np.ndarray,
        query_type: str,
        results: list[str],
        positive_feedback: Optional[list[str]] = None,
        negative_feedback: Optional[list[str]] = None,
        text_feedback: Optional[str] = None
    ) -> int:
        """
        Add a new iteration to a session.
        
        Returns:
            The iteration number
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        iteration = SearchIteration(
            iteration=session.current_iteration + 1,
            query_vector=query_vector.copy(),
            query_type=query_type,
            results=results,
            positive_feedback=positive_feedback or [],
            negative_feedback=negative_feedback or [],
            text_feedback=text_feedback
        )
        session.iterations.append(iteration)
        return iteration.iteration
    
    def update_last_iteration_feedback(
        self,
        session_id: str,
        positive_ids: list[str],
        negative_ids: list[str],
        text_feedback: Optional[str] = None
    ):
        """Update feedback for the last iteration."""
        session = self.sessions.get(session_id)
        if session and session.iterations:
            last = session.iterations[-1]
            last.positive_feedback = positive_ids
            last.negative_feedback = negative_ids
            last.text_feedback = text_feedback
    
    def get_query_vectors_2d(
        self,
        session_id: str,
        reference_vectors: Optional[np.ndarray] = None
    ) -> list[dict]:
        """
        Get 2D projections of query vectors for visualization.
        
        Args:
            session_id: Session ID
            reference_vectors: Optional corpus vectors for PCA fitting
            
        Returns:
            List of {x, y, iteration} dicts
        """
        session = self.sessions.get(session_id)
        if not session or not session.iterations:
            return []
        
        query_vectors = np.array(session.get_all_query_vectors())
        
        if len(query_vectors) < 2:
            # For single vector, place at origin
            return [{"x": 0.0, "y": 0.0, "iteration": 1}]
        
        # Fit PCA on query vectors (or include reference vectors)
        if reference_vectors is not None and len(reference_vectors) > 0:
            all_vectors = np.vstack([query_vectors, reference_vectors])
        else:
            all_vectors = query_vectors
        
        pca = PCA(n_components=2)
        pca.fit(all_vectors)
        
        projected = pca.transform(query_vectors)
        
        result = []
        for i, (x, y) in enumerate(projected):
            result.append({
                "x": float(x),
                "y": float(y),
                "iteration": i + 1
            })
        
        return result
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove sessions older than max_age_hours."""
        now = datetime.now()
        to_remove = []
        for sid, session in self.sessions.items():
            age = (now - session.created_at).total_seconds() / 3600
            if age > max_age_hours:
                to_remove.append(sid)
        
        for sid in to_remove:
            del self.sessions[sid]


# Global session manager
session_manager = SessionManager()

