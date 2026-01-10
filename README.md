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
- **Natural Language Feedback**: Provide text modifications like "similar but in blue" using Query Composition methods

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

### Data Preparation

**Important**: The source code repository does NOT include the dataset or pre-built index due to size constraints. You need to put the dataset in the `backend/data/images/` directory as follow structure:

```
backend/
└── data/
    ├── images.csv          # Required: CSV file with image metadata
    └── images/             # Required: Directory containing image files
        ├── 3238.jpg
        ├── 43044.jpg
        └── ...
```

#### CSV File Format

The `images.csv` file should have the following columns:
- `image`: Image filename (e.g., `3238.jpg`)
- `description`: Product description
- `display name`: Product display name
- `category`: Product category

Example:
```csv
image,description,display name,category
3238.jpg,"Round toed, black sports shoes...",Puma Men Black Sports Shoes,Sports Shoes
43044.jpg,"Style Note Built with the breathability...",Nike Men Grey Shorts,Shorts
```

#### Image Files

- Place all image files directly in `backend/data/images/` directory
- Supported formats: `.jpg`, `.jpeg`, `.png`, `.webp`
- Image filenames must match the `image` column values in the CSV

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify data files are in place
ls data/images.csv        # Should exist
ls data/images/           # Should contain image files

# Index images from CSV (IMPORTANT: Do this before starting the server)
python scripts/index_from_csv.py

# Optional: Test with a smaller subset first
python scripts/index_from_csv.py --limit 1000

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Note**: The indexing process will:
- Create `backend/data/index/` directory (not included in source)
- Generate `faiss.index` and `metadata.json` files
- Process all images from the CSV and create embeddings using CLIP
- This process may take 10-30 minutes depending on the number of images

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

### 3. Open the App

Navigate to [http://localhost:3000](http://localhost:3000)

### Troubleshooting

#### Index not found error
If you see an error about missing index, make sure you've run the indexing script:
```bash
cd backend
source venv/bin/activate
python scripts/index_from_csv.py
```

#### Images not found
Verify that:
- Image files are in `backend/data/images/` directory
- Image filenames in the directory match the `image` column in CSV
- You have read permissions for the images directory

#### CSV parsing errors
Check that your CSV:
- Has a header row with columns: `image`, `description`, `display name`, `category`
- Uses UTF-8 encoding
- Has proper quoting for text fields with commas

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

**Note**: For initial setup, use the indexing script instead:
```bash
python scripts/index_from_csv.py
```

### Visualization

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/visualization/vectors` | GET | Get 2D projections for visualization |

## Algorithms

### Rocchio Algorithm

Relevance feedback uses the Standard Rocchio Method for thumbs up/down feedback:

```
q_new = α·q + β·centroid(D_r) - γ·centroid(D_n)
```

Where:
- `q`: Original query vector
- `D_r, D_n`: Sets of relevant and non-relevant document vectors
- `α, β, γ`: Tunable weights (default: 1.0, 0.75, 0.15)

### Query Composition for Natural Language Feedback

Natural Language Feedback (NLF) uses Query Composition methods instead of Rocchio, as NLF operates differently from document-based feedback:

**Residual Composition** (default for NLF-only):
```
q_new = q + λ·(text_vector - proj(text_vector, q))
```

**Additive Composition** (for mixed feedback):
```
q_new = refined_query + λ·text_vector
```

**Attention Composition** (alternative):
Uses attention weights to combine query and text vector based on semantic similarity.

The system automatically selects the appropriate composition method based on the feedback type:
- NLF only → Residual Composition (stronger semantic shift)
- Mixed (thumbs + NLF) → Rocchio first, then Additive Composition

## Configuration

### Backend (`backend/app/config.py`)

| Variable | Default | Description |
|----------|---------|-------------|
| `CLIP_MODEL` | ViT-B-32 | CLIP model architecture |
| `ROCCHIO_ALPHA` | 1.0 | Weight for original query |
| `ROCCHIO_BETA` | 0.75 | Weight for relevant docs |
| `ROCCHIO_GAMMA` | 0.15 | Weight for non-relevant docs |
| `PRF_TOP_K` | 5 | Top-k for pseudo feedback |
| `DEFAULT_TOP_K` | 20 | Default number of search results |
| `MAX_TOP_K` | 500 | Maximum number of search results |

### Indexing Script Options

The indexing script (`scripts/index_from_csv.py`) supports the following options:

```bash
python scripts/index_from_csv.py [OPTIONS]

Options:
  --limit N       Limit number of images to index (useful for testing)
  --batch-size N  Batch size for processing images (default: 50)
```

Example usage:
```bash
# Index all images
python scripts/index_from_csv.py

# Test with first 1000 images
python scripts/index_from_csv.py --limit 1000

# Process in larger batches for faster indexing
python scripts/index_from_csv.py --batch-size 100
```

### Frontend

Set `NEXT_PUBLIC_API_URL` environment variable to point to your backend if not running on localhost:8000.

### Git Ignore Recommendations

The following should be in `.gitignore` to avoid committing large files:

```
# Data directories (provided separately)
backend/data/images/
backend/data/index/
backend/data/uploads/

# Python virtual environment
backend/venv/
backend/.venv/

# Node modules
frontend/node_modules/
frontend/.next/

# Environment files
.env
.env.local
.env*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

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

**Note**: The source code repository does NOT include:
- `backend/data/images/` - Image files directory (large size)
- `backend/data/index/` - Pre-built Faiss index (generated from images)
- `backend/venv/` - Python virtual environment (recreate locally)

These need to be provided separately or generated using the indexing script.


## Acknowledgments

- OpenAI CLIP for the vision-language model
- Facebook AI Research for Faiss
- The Rocchio algorithm from classic IR research
- Kaggle for the fashion product images and text dataset

