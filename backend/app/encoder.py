"""
CLIP-based encoder for images and text.
"""
import torch
import open_clip
from PIL import Image
import numpy as np
from pathlib import Path
from typing import Union
import io

from app.config import settings


class CLIPEncoder:
    """
    CLIP encoder for generating embeddings from images and text.
    Uses OpenCLIP for flexibility in model selection.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern for encoder."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔧 Loading CLIP model ({settings.CLIP_MODEL}) on {self.device}...")
        
        # Load CLIP model
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            settings.CLIP_MODEL,
            pretrained=settings.CLIP_PRETRAINED,
            device=self.device
        )
        self.tokenizer = open_clip.get_tokenizer(settings.CLIP_MODEL)
        
        self.model.eval()
        self._initialized = True
        print("✅ CLIP model loaded successfully!")
    
    @torch.no_grad()
    def encode_text(self, text: str) -> np.ndarray:
        """
        Encode text into embedding vector.
        
        Args:
            text: Input text string
            
        Returns:
            Normalized embedding vector
        """
        tokens = self.tokenizer([text]).to(self.device)
        text_features = self.model.encode_text(tokens)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        return text_features.cpu().numpy().astype(np.float32).flatten()
    
    @torch.no_grad()
    def encode_texts(self, texts: list[str]) -> np.ndarray:
        """
        Encode multiple texts into embedding vectors.
        
        Args:
            texts: List of text strings
            
        Returns:
            Array of normalized embedding vectors
        """
        tokens = self.tokenizer(texts).to(self.device)
        text_features = self.model.encode_text(tokens)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        return text_features.cpu().numpy().astype(np.float32)
    
    @torch.no_grad()
    def encode_image(self, image: Union[Image.Image, Path, bytes, io.BytesIO]) -> np.ndarray:
        """
        Encode image into embedding vector.
        
        Args:
            image: PIL Image, file path, bytes, or BytesIO object
            
        Returns:
            Normalized embedding vector
        """
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")
        elif isinstance(image, bytes):
            image = Image.open(io.BytesIO(image)).convert("RGB")
        elif isinstance(image, io.BytesIO):
            image = Image.open(image).convert("RGB")
        elif isinstance(image, Image.Image):
            image = image.convert("RGB")
        
        image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
        image_features = self.model.encode_image(image_tensor)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        return image_features.cpu().numpy().astype(np.float32).flatten()
    
    @torch.no_grad()
    def encode_images(self, images: list[Union[Image.Image, Path]]) -> np.ndarray:
        """
        Encode multiple images into embedding vectors.
        
        Args:
            images: List of PIL Images or file paths
            
        Returns:
            Array of normalized embedding vectors
        """
        processed = []
        for img in images:
            if isinstance(img, (str, Path)):
                img = Image.open(img).convert("RGB")
            processed.append(self.preprocess(img))
        
        batch = torch.stack(processed).to(self.device)
        image_features = self.model.encode_image(batch)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        return image_features.cpu().numpy().astype(np.float32)
    
    def combine_features(
        self,
        image_features: np.ndarray,
        text_features: np.ndarray,
        image_weight: float = 0.5
    ) -> np.ndarray:
        """
        Combine image and text features for compositional queries.
        
        Args:
            image_features: Image embedding
            text_features: Text embedding
            image_weight: Weight for image features (text weight = 1 - image_weight)
            
        Returns:
            Combined normalized embedding
        """
        text_weight = 1.0 - image_weight
        combined = image_weight * image_features + text_weight * text_features
        combined = combined / np.linalg.norm(combined)
        return combined.astype(np.float32)


# Global encoder instance
encoder = CLIPEncoder()

