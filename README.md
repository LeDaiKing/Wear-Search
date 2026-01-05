# WearSearch 👗🔍

**Interactive Image Retrieval System with Relevance Feedback**

WearSearch is an AI-powered fashion image search system that uses CLIP embeddings and the Rocchio algorithm to enable iterative query refinement through user feedback.

## Features

### Multi-modal Query Initialization
- **Text-to-Image Search**: Describe what you're looking for in natural language
- **Image-to-Image Search**: Upload a reference image to find similar items

### Interactive Relevance Feedback
- **Positive/Negative Marking**: Click thumbs up/down on results to mark relevance
- **Query Refinement**: System uses Rocchio algorithm to shift the query vector toward relevant items
- **Natural Language Feedback**: Provide text modifications like "similar but in blue"

### Advanced Features
- **Pseudo (Blind) Feedback**: Automatic query expansion using top-k results
- **Vector Space Visualization**: Watch your query move through embedding space
- **Iteration Tracking**: View your search journey across refinement cycles

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│     Backend     │────▶│   Vector Store  │
│   (Next.js)     │◀────│    (FastAPI)    │◀────│    (Faiss)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌─────────────────┐
                        │  CLIP Encoder   │
                        │  (OpenCLIP)     │
                        └─────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- pnpm (or npm)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Seed Demo Images (Optional)

```bash
cd backend
python scripts/seed_demo.py
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

### 4. Open the App

Navigate to [http://localhost:3000](http://localhost:3000)

## API Reference

### Search Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/search/text` | POST | Text-to-image search |
| `/search/image` | POST | Image-to-image search |
| `/feedback/relevance` | POST | Submit relevance feedback |
| `/feedback/pseudo` | POST | Apply pseudo relevance feedback |

### Index Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/index/add` | POST | Add single image to index |
| `/index/bulk` | POST | Bulk index from directory |

### Visualization

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/visualization/vectors` | GET | Get 2D projections for visualization |

## Rocchio Algorithm

The query refinement uses the Standard Rocchio Method:

```
q_m = α·q + (β/|D_r|)·Σd_j - (γ/|D_n|)·Σd_k
```

Where:
- `q`: Original query vector
- `D_r, D_n`: Sets of relevant and non-relevant document vectors
- `α, β, γ`: Tunable weights (default: 1.0, 0.75, 0.15)

## Configuration

### Backend (`backend/app/config.py`)

| Variable | Default | Description |
|----------|---------|-------------|
| `CLIP_MODEL` | ViT-B-32 | CLIP model architecture |
| `ROCCHIO_ALPHA` | 1.0 | Weight for original query |
| `ROCCHIO_BETA` | 0.75 | Weight for relevant docs |
| `ROCCHIO_GAMMA` | 0.15 | Weight for non-relevant docs |
| `PRF_TOP_K` | 5 | Top-k for pseudo feedback |

### Frontend

Set `NEXT_PUBLIC_API_URL` environment variable to point to your backend if not running on localhost:8000.

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **OpenCLIP** - Vision-language model for embeddings
- **Faiss** - Efficient similarity search
- **scikit-learn** - PCA for visualization

### Frontend
- **Next.js 15** - React framework with App Router
- **Tailwind CSS 4** - Utility-first styling
- **Lucide React** - Beautiful icons
- **TypeScript** - Type safety

## Data Source
Fashion Product Images and Text Dataset, from [Kaggle](https://www.kaggle.com/datasets/nirmalsankalana/fashion-product-text-images-dataset/data).


## Acknowledgments

- OpenAI CLIP for the vision-language model
- Facebook AI Research for Faiss
- The Rocchio algorithm from classic IR research
- Kaggle for the fashion product images and text dataset

