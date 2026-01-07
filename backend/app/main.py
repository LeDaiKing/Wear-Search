"""
WearSearch - Interactive Image Retrieval System
FastAPI Backend
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import numpy as np
from pathlib import Path
import uuid
import shutil

from app.config import settings
from app.models import (
    TextSearchRequest,
    RelevanceFeedbackRequest,
    PseudoFeedbackRequest,
    SearchResponse,
    ImageResult,
    QueryVector,
    HealthResponse,
    SessionInfo,
    FeedbackType
)
from app.encoder import encoder
from app.vector_store import vector_store
from app.rocchio import rocchio
from app.query_composer import query_composer, CompositionMethod
from app.session_manager import session_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🚀 Starting WearSearch Backend...")
    print(f"📊 Index contains {vector_store.total_images} images")
    yield
    # Shutdown
    print("👋 Shutting down WearSearch Backend...")


app = FastAPI(
    title="WearSearch API",
    description="Interactive Image Retrieval System with Relevance Feedback",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded/indexed images
app.mount("/images", StaticFiles(directory=str(settings.IMAGES_DIR)), name="images")
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")


def create_search_response(
    session_id: str,
    iteration: int,
    image_ids: list[str],
    scores: list[float],
    metadata_list: list[dict]
) -> SearchResponse:
    """Create SearchResponse from search results."""
    results = []
    for img_id, score, meta in zip(image_ids, scores, metadata_list):
        results.append(ImageResult(
            image_id=img_id,
            filename=meta.get("filename", ""),
            url=f"/images/{meta.get('filename', '')}",
            similarity_score=score,
            metadata=meta.get("metadata", {})
        ))
    
    # Get query vectors for visualization
    query_vectors = session_manager.get_query_vectors_2d(session_id)
    
    return SearchResponse(
        session_id=session_id,
        iteration=iteration,
        results=results,
        query_vectors=[QueryVector(**qv) for qv in query_vectors],
        total_images=vector_store.total_images
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        index_loaded=vector_store.index is not None,
        total_images=vector_store.total_images
    )


@app.post("/search/text", response_model=SearchResponse)
async def search_by_text(request: TextSearchRequest):
    """
    Text-to-image search.
    
    Encode the text query and find similar images in the corpus.
    """
    # Get or create session
    session_id, session = session_manager.get_or_create_session(request.session_id)
    
    # Encode text query
    query_vector = encoder.encode_text(request.query)
    
    # Search
    image_ids, scores, metadata_list = vector_store.search(query_vector, request.top_k)
    
    # Record iteration
    iteration = session_manager.add_iteration(
        session_id=session_id,
        query_vector=query_vector,
        query_type="text",
        results=image_ids
    )
    
    return create_search_response(session_id, iteration, image_ids, scores, metadata_list)


@app.post("/search/image", response_model=SearchResponse)
async def search_by_image(
    image: UploadFile = File(...),
    top_k: int = Form(default=20),
    session_id: str = Form(default=None)
):
    """
    Image-to-image search.
    
    Encode the uploaded image and find similar images in the corpus.
    """
    # Validate file type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Get or create session
    sid, session = session_manager.get_or_create_session(session_id)
    
    # Read and encode image
    image_bytes = await image.read()
    query_vector = encoder.encode_image(image_bytes)
    
    # Search
    image_ids, scores, metadata_list = vector_store.search(query_vector, top_k)
    
    # Record iteration
    iteration = session_manager.add_iteration(
        session_id=sid,
        query_vector=query_vector,
        query_type="image",
        results=image_ids
    )
    
    return create_search_response(sid, iteration, image_ids, scores, metadata_list)


@app.post("/feedback/relevance", response_model=SearchResponse)
async def relevance_feedback(request: RelevanceFeedbackRequest):
    """
    Apply relevance feedback using Rocchio algorithm and/or Natural Language Feedback.
    
    - Rocchio: Used for positive/negative image feedback (document-based)
    - QueryComposer: Used for natural language feedback (semantic modification)
    
    These are applied separately as they work on different principles.
    """
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.current_query_vector is None:
        raise HTTPException(status_code=400, detail="No previous query in session")
    
    # Validate that at least some feedback is provided
    if not request.feedback_items and not request.text_feedback:
        raise HTTPException(status_code=400, detail="At least one type of feedback is required")
    
    # Separate positive and negative feedback
    positive_ids = [f.image_id for f in request.feedback_items if f.feedback == FeedbackType.POSITIVE]
    negative_ids = [f.image_id for f in request.feedback_items if f.feedback == FeedbackType.NEGATIVE]
    
    # Get vectors for feedback images
    positive_vectors = vector_store.get_vectors(positive_ids) if positive_ids else None
    negative_vectors = vector_store.get_vectors(negative_ids) if negative_ids else None
    
    current_query = session.current_query_vector
    refined_query = current_query.copy()
    
    # Step 1: Apply Rocchio for image-based relevance feedback
    has_image_feedback = (positive_vectors is not None and len(positive_vectors) > 0) or \
                         (negative_vectors is not None and len(negative_vectors) > 0)
    
    if has_image_feedback:
        refined_query = rocchio.refine_query(
            query_vector=refined_query,
            relevant_vectors=positive_vectors if positive_vectors is not None and len(positive_vectors) > 0 else None,
            non_relevant_vectors=negative_vectors if negative_vectors is not None and len(negative_vectors) > 0 else None
        )
    
    # Step 2: Apply QueryComposer for natural language feedback (separate mechanism)
    if request.text_feedback:
        text_vector = encoder.encode_text(request.text_feedback)
        
        # Use different composition method based on whether there's also image feedback
        if has_image_feedback:
            # Mixed feedback: use additive to layer NLF on top of Rocchio result
            refined_query = query_composer.compose(
                query_vector=refined_query,
                text_vector=text_vector,
                method=CompositionMethod.ADDITIVE
            )
        else:
            # Pure NLF: use residual composition for stronger semantic modification
            # This allows text like "navy color" to more strongly influence the query
            refined_query = query_composer.compose(
                query_vector=refined_query,
                text_vector=text_vector,
                method=CompositionMethod.RESIDUAL
            )
    
    # Search with refined query
    image_ids, scores, metadata_list = vector_store.search(refined_query, request.top_k)
    
    # Update feedback on previous iteration
    session_manager.update_last_iteration_feedback(
        request.session_id,
        positive_ids,
        negative_ids,
        request.text_feedback
    )
    
    # Record new iteration
    iteration = session_manager.add_iteration(
        session_id=request.session_id,
        query_vector=refined_query,
        query_type="feedback",
        results=image_ids,
        positive_feedback=positive_ids,
        negative_feedback=negative_ids,
        text_feedback=request.text_feedback
    )
    
    return create_search_response(request.session_id, iteration, image_ids, scores, metadata_list)


@app.post("/feedback/pseudo", response_model=SearchResponse)
async def pseudo_relevance_feedback(request: PseudoFeedbackRequest):
    """
    Apply pseudo (blind) relevance feedback.
    
    Automatically assumes top-m results are relevant and refines query.
    """
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.current_query_vector is None:
        raise HTTPException(status_code=400, detail="No previous query in session")
    
    # Get last results
    if not session.iterations:
        raise HTTPException(status_code=400, detail="No previous search in session")
    
    last_results = session.iterations[-1].results[:request.top_m]
    
    # Get vectors for top results
    top_vectors = vector_store.get_vectors(last_results)
    
    if len(top_vectors) == 0:
        raise HTTPException(status_code=400, detail="Could not find vectors for top results")
    
    # Apply pseudo relevance feedback
    current_query = session.current_query_vector
    refined_query = rocchio.pseudo_relevance_feedback(
        query_vector=current_query,
        top_vectors=top_vectors,
        top_m=request.top_m
    )
    
    # Search with refined query
    image_ids, scores, metadata_list = vector_store.search(refined_query, request.top_k)
    
    # Record new iteration
    iteration = session_manager.add_iteration(
        session_id=request.session_id,
        query_vector=refined_query,
        query_type="pseudo_feedback",
        results=image_ids
    )
    
    return create_search_response(request.session_id, iteration, image_ids, scores, metadata_list)


@app.get("/session/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """Get information about a search session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    query_type = "none"
    if session.iterations:
        query_type = session.iterations[-1].query_type
    
    return SessionInfo(
        session_id=session_id,
        iterations=session.current_iteration,
        current_query_type=query_type,
        feedback_counts=session.get_feedback_counts()
    )


@app.post("/index/add")
async def add_image_to_index(
    image: UploadFile = File(...),
    image_id: str = Form(default=None),
    metadata: str = Form(default="{}")
):
    """
    Add a new image to the search index.
    
    This endpoint allows building the image corpus.
    """
    import json
    
    # Validate file type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate image ID if not provided
    if not image_id:
        image_id = str(uuid.uuid4())
    
    # Parse metadata
    try:
        meta_dict = json.loads(metadata)
    except json.JSONDecodeError:
        meta_dict = {}
    
    # Save image
    filename = f"{image_id}_{image.filename}"
    save_path = settings.IMAGES_DIR / filename
    
    with open(save_path, "wb") as f:
        content = await image.read()
        f.write(content)
    
    # Encode and add to index
    vector = encoder.encode_image(save_path)
    vector_store.add_vectors(
        vectors=vector.reshape(1, -1),
        image_ids=[image_id],
        filenames=[filename],
        metadata_list=[meta_dict]
    )
    
    # Save index
    vector_store.save()
    
    return {
        "status": "success",
        "image_id": image_id,
        "filename": filename,
        "total_images": vector_store.total_images
    }


@app.post("/index/bulk")
async def bulk_index_images(images_dir: str = Form(...)):
    """
    Bulk index images from a directory.
    
    Scans the provided directory for images and adds them to the index.
    """
    from pathlib import Path
    import os
    
    source_dir = Path(images_dir)
    if not source_dir.exists():
        raise HTTPException(status_code=400, detail=f"Directory not found: {images_dir}")
    
    # Find all images
    extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    image_files = [
        f for f in source_dir.iterdir()
        if f.is_file() and f.suffix.lower() in extensions
    ]
    
    if not image_files:
        raise HTTPException(status_code=400, detail="No images found in directory")
    
    added = 0
    errors = []
    
    for img_path in image_files:
        try:
            image_id = str(uuid.uuid4())
            filename = f"{image_id}_{img_path.name}"
            
            # Copy to images directory
            dest_path = settings.IMAGES_DIR / filename
            shutil.copy2(img_path, dest_path)
            
            # Encode and add
            vector = encoder.encode_image(dest_path)
            vector_store.add_vectors(
                vectors=vector.reshape(1, -1),
                image_ids=[image_id],
                filenames=[filename],
                metadata_list=[{"original_name": img_path.name}]
            )
            added += 1
            
        except Exception as e:
            errors.append({"file": str(img_path), "error": str(e)})
    
    # Save index
    vector_store.save()
    
    return {
        "status": "success",
        "added": added,
        "errors": errors,
        "total_images": vector_store.total_images
    }


@app.get("/visualization/vectors")
async def get_visualization_data(
    session_id: str = Query(...),
    include_corpus: bool = Query(default=False),
    sample_size: int = Query(default=100)
):
    """
    Get vector visualization data for the session.
    
    Returns 2D projections of query vectors across iterations,
    optionally including sample corpus vectors for context.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get reference vectors for better PCA fitting
    reference_vectors = None
    corpus_points = []
    
    if include_corpus and vector_store.total_images > 0:
        all_vectors = vector_store.get_all_vectors()
        # Sample if too many
        if len(all_vectors) > sample_size:
            indices = np.random.choice(len(all_vectors), sample_size, replace=False)
            reference_vectors = all_vectors[indices]
        else:
            reference_vectors = all_vectors
    
    query_points = session_manager.get_query_vectors_2d(session_id, reference_vectors)
    
    # Project corpus vectors too if included
    if reference_vectors is not None and len(query_points) > 0:
        from sklearn.decomposition import PCA
        
        query_vectors = np.array(session.get_all_query_vectors())
        all_for_pca = np.vstack([query_vectors, reference_vectors])
        
        pca = PCA(n_components=2)
        pca.fit(all_for_pca)
        
        corpus_projected = pca.transform(reference_vectors)
        corpus_points = [{"x": float(x), "y": float(y)} for x, y in corpus_projected]
    
    return {
        "query_vectors": query_points,
        "corpus_vectors": corpus_points,
        "iterations": session.current_iteration
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

