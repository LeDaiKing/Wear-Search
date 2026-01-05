#!/usr/bin/env python3
"""
Seed script to add demo images to the WearSearch index.
Downloads sample fashion images for testing.
"""
import asyncio
import httpx
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Sample fashion image URLs (Unsplash - free to use)
DEMO_IMAGES = [
    # Dresses
    ("https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400", "red_dress_1.jpg", {"category": "dress", "color": "red"}),
    ("https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=400", "blue_dress_1.jpg", {"category": "dress", "color": "blue"}),
    ("https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=400", "floral_dress_1.jpg", {"category": "dress", "pattern": "floral"}),
    ("https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=400", "white_dress_1.jpg", {"category": "dress", "color": "white"}),
    ("https://images.unsplash.com/photo-1539008835657-9e8e9680c956?w=400", "black_dress_1.jpg", {"category": "dress", "color": "black"}),
    
    # Shirts & Tops
    ("https://images.unsplash.com/photo-1598033129183-c4f50c736f10?w=400", "casual_shirt_1.jpg", {"category": "shirt", "style": "casual"}),
    ("https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=400", "white_shirt_1.jpg", {"category": "shirt", "color": "white"}),
    ("https://images.unsplash.com/photo-1603252109303-2751441dd157?w=400", "striped_shirt_1.jpg", {"category": "shirt", "pattern": "striped"}),
    ("https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400", "blouse_1.jpg", {"category": "blouse", "style": "elegant"}),
    ("https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400", "tshirt_1.jpg", {"category": "tshirt", "style": "casual"}),
    
    # Jackets
    ("https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400", "denim_jacket_1.jpg", {"category": "jacket", "material": "denim"}),
    ("https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400", "leather_jacket_1.jpg", {"category": "jacket", "material": "leather"}),
    ("https://images.unsplash.com/photo-1544022613-e87ca75a784a?w=400", "blazer_1.jpg", {"category": "blazer", "style": "formal"}),
    ("https://images.unsplash.com/photo-1559551409-dadc959f76b8?w=400", "coat_1.jpg", {"category": "coat", "style": "winter"}),
    
    # Pants & Jeans
    ("https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=400", "jeans_1.jpg", {"category": "jeans", "style": "casual"}),
    ("https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=400", "black_pants_1.jpg", {"category": "pants", "color": "black"}),
    ("https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=400", "chinos_1.jpg", {"category": "pants", "style": "chinos"}),
    
    # Accessories
    ("https://images.unsplash.com/photo-1556306535-0f09a537f0a3?w=400", "sunglasses_1.jpg", {"category": "accessory", "type": "sunglasses"}),
    ("https://images.unsplash.com/photo-1523170335258-f5ed11844a49?w=400", "watch_1.jpg", {"category": "accessory", "type": "watch"}),
    ("https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=400", "bag_1.jpg", {"category": "accessory", "type": "bag"}),
]

API_BASE = "http://localhost:8000"


async def download_and_index_image(
    client: httpx.AsyncClient,
    url: str,
    filename: str,
    metadata: dict
) -> bool:
    """Download an image and add it to the index."""
    try:
        # Download image
        response = await client.get(url, follow_redirects=True)
        if response.status_code != 200:
            print(f"  ❌ Failed to download {filename}: HTTP {response.status_code}")
            return False
        
        image_data = response.content
        
        # Upload to index
        files = {"image": (filename, image_data, "image/jpeg")}
        data = {"metadata": str(metadata).replace("'", '"')}
        
        response = await client.post(
            f"{API_BASE}/index/add",
            files=files,
            data=data,
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Indexed: {filename} (ID: {result['image_id'][:8]}...)")
            return True
        else:
            print(f"  ❌ Failed to index {filename}: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error with {filename}: {e}")
        return False


async def main():
    print("🌱 WearSearch Demo Seeder")
    print("=" * 40)
    
    # Check if backend is running
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE}/health")
            health = response.json()
            print(f"✅ Backend connected: {health['total_images']} images in index")
        except Exception as e:
            print(f"❌ Could not connect to backend at {API_BASE}")
            print(f"   Error: {e}")
            print("\n   Please start the backend first:")
            print("   cd backend && uvicorn app.main:app --reload")
            return
    
    print(f"\n📸 Adding {len(DEMO_IMAGES)} demo images...")
    
    async with httpx.AsyncClient() as client:
        success = 0
        for url, filename, metadata in DEMO_IMAGES:
            result = await download_and_index_image(client, url, filename, metadata)
            if result:
                success += 1
    
    print(f"\n✨ Done! Added {success}/{len(DEMO_IMAGES)} images to the index.")
    
    # Show final status
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/health")
        health = response.json()
        print(f"📊 Total images in index: {health['total_images']}")


if __name__ == "__main__":
    asyncio.run(main())

