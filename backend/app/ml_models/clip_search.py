"""
CLIP Multi-Modal Search

Search meals by text description using CLIP embeddings
"""

import os
from typing import List, Dict, Any, Optional
import numpy as np
from PIL import Image

try:
    import clip
    import torch
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    print("⚠️  CLIP not available. Install with: pip install git+https://github.com/openai/CLIP.git")


class CLIPSearch:
    """
    CLIP-based semantic search for meals
    """
    
    def __init__(self, model_name: str = "ViT-B/32"):
        """
        Initialize CLIP model
        
        Args:
            model_name: CLIP model variant (ViT-B/32, ViT-B/16, ViT-L/14)
        """
        self.model = None
        self.preprocess = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.mock_mode = False
        
        if CLIP_AVAILABLE:
            try:
                self.model, self.preprocess = clip.load(model_name, device=self.device)
                print(f"✓ Loaded CLIP model: {model_name} on {self.device}")
            except Exception as e:
                print(f"⚠️  Could not load CLIP: {e}")
                self.mock_mode = True
        else:
            print("⚠️  CLIP not installed. Using mock mode.")
            self.mock_mode = True
    
    def encode_image(self, image_path: str) -> np.ndarray:
        """
        Encode image to CLIP embedding (512-dim vector)
        
        Args:
            image_path: Path to image file
            
        Returns:
            512-dimensional embedding vector
        """
        if self.mock_mode:
            # Return random embedding for mock
            return np.random.randn(512).astype(np.float32)
        
        try:
            image = Image.open(image_path).convert('RGB')
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                # Normalize
                image_features /= image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy()[0]
            
        except Exception as e:
            print(f"Error encoding image: {e}")
            return np.random.randn(512).astype(np.float32)
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Encode text description to CLIP embedding
        
        Args:
            text: Text description (e.g., "high protein low carb meal")
            
        Returns:
            512-dimensional embedding vector
        """
        if self.mock_mode:
            return np.random.randn(512).astype(np.float32)
        
        try:
            text_input = clip.tokenize([text]).to(self.device)
            
            with torch.no_grad():
                text_features = self.model.encode_text(text_input)
                # Normalize
                text_features /= text_features.norm(dim=-1, keepdim=True)
            
            return text_features.cpu().numpy()[0]
            
        except Exception as e:
            print(f"Error encoding text: {e}")
            return np.random.randn(512).astype(np.float32)
    
    def search_by_description(
        self,
        query: str,
        meal_embeddings: Dict[int, np.ndarray],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search meals by text description
        
        Args:
            query: Text query (e.g., "healthy breakfast under 400 calories")
            meal_embeddings: Dict of {meal_id: embedding_vector}
            top_k: Number of results to return
            
        Returns:
            List of {meal_id, similarity_score} sorted by relevance
        """
        # Encode query
        query_embedding = self.encode_text(query)
        
        # Calculate cosine similarities
        similarities = []
        for meal_id, meal_embedding in meal_embeddings.items():
            similarity = self._cosine_similarity(query_embedding, meal_embedding)
            similarities.append({
                'meal_id': meal_id,
                'similarity': round(float(similarity), 3)
            })
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similarities[:top_k]
    
    def find_similar_images(
        self,
        query_image_path: str,
        meal_embeddings: Dict[int, np.ndarray],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find visually similar meals
        
        Args:
            query_image_path: Path to query image
            meal_embeddings: Dict of {meal_id: embedding_vector}
            top_k: Number of results
            
        Returns:
            List of similar meals
        """
        # Encode query image
        query_embedding = self.encode_image(query_image_path)
        
        # Calculate similarities
        similarities = []
        for meal_id, meal_embedding in meal_embeddings.items():
            similarity = self._cosine_similarity(query_embedding, meal_embedding)
            similarities.append({
                'meal_id': meal_id,
                'similarity': round(float(similarity), 3)
            })
        
        # Sort
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similarities[:top_k]
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def batch_encode_images(self, image_paths: List[str]) -> Dict[str, np.ndarray]:
        """
        Encode multiple images at once (more efficient)
        
        Returns:
            Dict of {image_path: embedding}
        """
        embeddings = {}
        
        for image_path in image_paths:
            try:
                embeddings[image_path] = self.encode_image(image_path)
            except Exception as e:
                print(f"Failed to encode {image_path}: {e}")
                continue
        
        return embeddings


# Singleton instance
_clip_instance: Optional[CLIPSearch] = None

def get_clip_search() -> CLIPSearch:
    """Get singleton CLIP instance"""
    global _clip_instance
    if _clip_instance is None:
        _clip_instance = CLIPSearch()
    return _clip_instance
