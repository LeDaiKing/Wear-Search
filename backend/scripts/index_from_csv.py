#!/usr/bin/env python3
"""
Script to index images from CSV with metadata.
Reads images.csv and creates a new Faiss index with full metadata.
"""

import sys
import os
import csv
import json
import shutil
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.encoder import encoder
from app.vector_store import VectorStore
import numpy as np
from PIL import Image
import faiss
import json

def main():
    parser = argparse.ArgumentParser(description="Index images from CSV with metadata")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of images to index (for testing)")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    args = parser.parse_args()
    
    # Paths
    csv_path = Path(settings.DATA_DIR) / "images.csv"
    images_dir = Path(settings.DATA_DIR) / "images"
    index_dir = Path(settings.DATA_DIR) / "index"
    
    print(f"📂 CSV Path: {csv_path}")
    print(f"📂 Images Dir: {images_dir}")
    print(f"📂 Index Dir: {index_dir}")
    if args.limit:
        print(f"🔢 Limiting to {args.limit} images")
    
    # Check if files exist
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    if not images_dir.exists():
        print(f"❌ Images directory not found: {images_dir}")
        return
    
    # Remove old index
    if index_dir.exists():
        print(f"🗑️  Removing old index at {index_dir}...")
        shutil.rmtree(index_dir)
    
    # Create new index directory
    index_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize encoder (uses the global encoder instance)
    print("🔧 CLIP model already loaded...")
    
    # Create a fresh Faiss index directly (bypassing singleton)
    print("🔧 Creating fresh Faiss index...")
    dimension = settings.EMBEDDING_DIM
    faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
    metadata = {"images": [], "id_to_idx": {}}
    
    # Read CSV and create lookup dictionary
    print("📖 Reading CSV file...")
    csv_data = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            image_name = row['image'].strip()
            csv_data[image_name] = {
                'description': row.get('description', '').strip(),
                'display_name': row.get('display name', '').strip(),
                'category': row.get('category', '').strip(),
            }
    
    print(f"📊 Found {len(csv_data)} entries in CSV")
    
    # Get list of actual images in directory that have CSV entries
    all_image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.jpeg")) + \
                      list(images_dir.glob("*.png")) + list(images_dir.glob("*.webp"))
    
    # Filter to only images that exist in CSV
    image_files = [f for f in all_image_files if f.name in csv_data]
    
    print(f"🖼️  Found {len(all_image_files)} image files, {len(image_files)} with CSV metadata")
    
    # Apply limit if specified
    if args.limit:
        image_files = image_files[:args.limit]
        print(f"📌 Limited to {len(image_files)} images")
    
    # Process images in batches
    batch_size = args.batch_size
    indexed_count = 0
    failed_count = 0
    
    for i in range(0, len(image_files), batch_size):
        batch_files = image_files[i:i + batch_size]
        batch_embeddings = []
        batch_image_ids = []
        batch_filenames = []
        batch_metadata = []
        
        for img_path in batch_files:
            try:
                # Open and encode image
                img = Image.open(img_path).convert('RGB')
                embedding = encoder.encode_image(img)
                
                # Get metadata from CSV
                image_name = img_path.name
                csv_info = csv_data.get(image_name, {})
                
                # Generate unique ID
                image_id = f"img_{img_path.stem}"
                
                # Create custom metadata
                custom_metadata = {
                    'display_name': csv_info.get('display_name', image_name),
                    'description': csv_info.get('description', ''),
                    'category': csv_info.get('category', 'Unknown'),
                }
                
                batch_embeddings.append(embedding)
                batch_image_ids.append(image_id)
                batch_filenames.append(image_name)
                batch_metadata.append(custom_metadata)
                indexed_count += 1
                
            except Exception as e:
                print(f"⚠️  Failed to process {img_path.name}: {e}")
                failed_count += 1
                continue
        
        # Add batch to index directly
        if batch_embeddings:
            embeddings_array = np.vstack(batch_embeddings).astype(np.float32)
            # Normalize for cosine similarity
            norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
            embeddings_array = embeddings_array / norms
            
            start_idx = faiss_index.ntotal
            faiss_index.add(embeddings_array)
            
            for j, (img_id, filename, meta) in enumerate(zip(batch_image_ids, batch_filenames, batch_metadata)):
                idx = start_idx + j
                metadata["id_to_idx"][img_id] = idx
                metadata["images"].append({
                    "image_id": img_id,
                    "filename": filename,
                    "idx": idx,
                    "metadata": meta
                })
        
        progress_pct = (i + len(batch_files)) / len(image_files) * 100
        print(f"📈 Progress: {indexed_count}/{len(image_files)} images indexed ({progress_pct:.1f}%)...")
    
    # Save the index
    print("💾 Saving index...")
    index_path = index_dir / "faiss.index"
    metadata_path = index_dir / "metadata.json"
    faiss.write_index(faiss_index, str(index_path))
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"""
✅ Indexing Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Total images in CSV: {len(csv_data)}
🖼️  Total image files: {len(all_image_files)}
📌 Images with metadata: {len(image_files) if not args.limit else args.limit}
✅ Successfully indexed: {indexed_count}
❌ Failed to index: {failed_count}
💾 Index saved to: {index_dir}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

if __name__ == "__main__":
    main()
