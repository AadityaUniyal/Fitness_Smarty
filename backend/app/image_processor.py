"""
Image Processing Pipeline for Meal Analysis
Handles image validation, preprocessing, optimization, and secure storage
"""

from typing import Optional, Tuple, Dict, Any
from PIL import Image
import io
import hashlib
from datetime import datetime
import os
from pathlib import Path


class ImageValidationError(Exception):
    """Raised when image validation fails"""
    pass


class ImageProcessor:
    """
    Handles image validation, preprocessing, and optimization for computer vision analysis
    """
    
    # Supported image formats
    SUPPORTED_FORMATS = {'JPEG', 'JPG', 'PNG'}
    
    # Size constraints (in bytes)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MIN_FILE_SIZE = 1024  # 1KB
    
    # Dimension constraints (in pixels)
    MIN_WIDTH = 224
    MIN_HEIGHT = 224
    MAX_WIDTH = 4096
    MAX_HEIGHT = 4096
    
    # Optimization settings
    TARGET_WIDTH = 640
    TARGET_HEIGHT = 640
    JPEG_QUALITY = 85
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize ImageProcessor
        
        Args:
            storage_path: Path for local image storage (optional)
        """
        self.storage_path = storage_path or os.path.join(os.getcwd(), 'meal_images')
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
    
    def validate_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Validate image format, size, and dimensions
        
        Args:
            image_bytes: Raw image data
            
        Returns:
            Dict containing validation results and image metadata
            
        Raises:
            ImageValidationError: If validation fails
        """
        # Check file size
        file_size = len(image_bytes)
        if file_size < self.MIN_FILE_SIZE:
            raise ImageValidationError(f"Image too small: {file_size} bytes (minimum {self.MIN_FILE_SIZE} bytes)")
        
        if file_size > self.MAX_FILE_SIZE:
            raise ImageValidationError(f"Image too large: {file_size} bytes (maximum {self.MAX_FILE_SIZE} bytes)")
        
        # Try to open and validate image
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ImageValidationError(f"Invalid image file: {str(e)}")
        
        # Check format
        if image.format not in self.SUPPORTED_FORMATS:
            raise ImageValidationError(
                f"Unsupported format: {image.format}. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        # Check dimensions
        width, height = image.size
        if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
            raise ImageValidationError(
                f"Image dimensions too small: {width}x{height} (minimum {self.MIN_WIDTH}x{self.MIN_HEIGHT})"
            )
        
        if width > self.MAX_WIDTH or height > self.MAX_HEIGHT:
            raise ImageValidationError(
                f"Image dimensions too large: {width}x{height} (maximum {self.MAX_WIDTH}x{self.MAX_HEIGHT})"
            )
        
        return {
            'valid': True,
            'format': image.format,
            'width': width,
            'height': height,
            'file_size': file_size,
            'mode': image.mode
        }
    
    def optimize_for_analysis(self, image_bytes: bytes) -> bytes:
        """
        Optimize image for computer vision analysis
        - Resize to target dimensions while maintaining aspect ratio
        - Convert to RGB mode
        - Compress to reduce file size
        
        Args:
            image_bytes: Raw image data
            
        Returns:
            Optimized image bytes
        """
        # Open image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Calculate resize dimensions maintaining aspect ratio
        width, height = image.size
        aspect_ratio = width / height
        
        if aspect_ratio > 1:
            # Landscape orientation
            new_width = self.TARGET_WIDTH
            new_height = int(self.TARGET_WIDTH / aspect_ratio)
            
            # Ensure height doesn't fall below minimum
            if new_height < self.MIN_HEIGHT:
                new_height = self.MIN_HEIGHT
                new_width = int(self.MIN_HEIGHT * aspect_ratio)
                # Cap width at target if it exceeds due to minimum height enforcement
                if new_width > self.TARGET_WIDTH:
                    new_width = self.TARGET_WIDTH
        else:
            # Portrait orientation
            new_height = self.TARGET_HEIGHT
            new_width = int(self.TARGET_HEIGHT * aspect_ratio)
            
            # Ensure width doesn't fall below minimum
            if new_width < self.MIN_WIDTH:
                new_width = self.MIN_WIDTH
                new_height = int(self.MIN_WIDTH / aspect_ratio)
                # Cap height at target if it exceeds due to minimum width enforcement
                if new_height > self.TARGET_HEIGHT:
                    new_height = self.TARGET_HEIGHT
        
        # Resize image using high-quality resampling
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save to bytes with optimization
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=self.JPEG_QUALITY, optimize=True)
        output.seek(0)
        
        return output.read()
    
    def generate_filename(self, user_id: str, image_bytes: bytes) -> str:
        """
        Generate unique filename for image storage
        
        Args:
            user_id: User identifier
            image_bytes: Image data for hash generation
            
        Returns:
            Unique filename
        """
        # Create hash of image content
        image_hash = hashlib.sha256(image_bytes).hexdigest()[:16]
        
        # Create timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        # Combine into filename
        filename = f"{user_id}_{timestamp}_{image_hash}.jpg"
        
        return filename
    
    def store_image(self, image_bytes: bytes, user_id: str) -> str:
        """
        Store image to local filesystem (placeholder for cloud storage)
        
        Args:
            image_bytes: Image data to store
            user_id: User identifier
            
        Returns:
            Storage path/URL
        """
        filename = self.generate_filename(user_id, image_bytes)
        filepath = os.path.join(self.storage_path, filename)
        
        # Write image to file
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        # Return relative path (in production, this would be a cloud storage URL)
        return f"/meal_images/{filename}"
    
    def process_meal_image(self, image_bytes: bytes, user_id: str) -> Dict[str, Any]:
        """
        Complete image processing pipeline:
        1. Validate image
        2. Optimize for analysis
        3. Store image
        
        Args:
            image_bytes: Raw image data
            user_id: User identifier
            
        Returns:
            Dict containing processing results and storage information
        """
        # Validate
        validation_result = self.validate_image(image_bytes)
        
        # Optimize
        optimized_bytes = self.optimize_for_analysis(image_bytes)
        
        # Store
        storage_url = self.store_image(optimized_bytes, user_id)
        
        return {
            'success': True,
            'original_size': validation_result['file_size'],
            'optimized_size': len(optimized_bytes),
            'dimensions': {
                'original': (validation_result['width'], validation_result['height']),
                'optimized': self._get_image_dimensions(optimized_bytes)
            },
            'format': validation_result['format'],
            'storage_url': storage_url
        }
    
    def _get_image_dimensions(self, image_bytes: bytes) -> Tuple[int, int]:
        """Get dimensions of image from bytes"""
        image = Image.open(io.BytesIO(image_bytes))
        return image.size
    
    def assess_image_quality(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Assess image quality for meal analysis
        
        Args:
            image_bytes: Image data
            
        Returns:
            Dict containing quality assessment
        """
        image = Image.open(io.BytesIO(image_bytes))
        width, height = image.size
        
        # Calculate quality score based on various factors
        quality_issues = []
        quality_score = 100
        
        # Check resolution
        if width < 480 or height < 480:
            quality_issues.append("Low resolution - may affect detection accuracy")
            quality_score -= 30
        
        # Check if image is too dark or too bright (basic check)
        if image.mode == 'RGB':
            # Convert to grayscale and check average brightness
            grayscale = image.convert('L')
            pixels = list(grayscale.getdata())
            avg_brightness = sum(pixels) / len(pixels)
            
            if avg_brightness < 50:
                quality_issues.append("Image too dark - consider better lighting")
                quality_score -= 20
            elif avg_brightness > 200:
                quality_issues.append("Image too bright - may be overexposed")
                quality_score -= 15
        
        # Check aspect ratio (extreme ratios may indicate cropping issues)
        aspect_ratio = width / height
        if aspect_ratio > 3 or aspect_ratio < 0.33:
            quality_issues.append("Unusual aspect ratio - ensure full meal is visible")
            quality_score -= 10
        
        return {
            'quality_score': max(0, quality_score),
            'issues': quality_issues,
            'suitable_for_analysis': quality_score >= 50,
            'recommendations': self._generate_quality_recommendations(quality_issues)
        }
    
    def _generate_quality_recommendations(self, issues: list) -> list:
        """Generate recommendations based on quality issues"""
        recommendations = []
        
        if any('resolution' in issue.lower() for issue in issues):
            recommendations.append("Use a higher resolution camera or move closer to the meal")
        
        if any('dark' in issue.lower() for issue in issues):
            recommendations.append("Improve lighting conditions or use flash")
        
        if any('bright' in issue.lower() for issue in issues):
            recommendations.append("Reduce direct lighting or avoid flash")
        
        if any('aspect ratio' in issue.lower() for issue in issues):
            recommendations.append("Capture the entire meal in frame without extreme cropping")
        
        if not recommendations:
            recommendations.append("Image quality is good for analysis")
        
        return recommendations
