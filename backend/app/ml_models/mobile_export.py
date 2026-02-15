"""
Mobile Model Export Utilities

Convert ML models to mobile-friendly formats (ONNX, TFLite)
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

# Create mobile export directory
MOBILE_DIR = Path("models/mobile")
MOBILE_DIR.mkdir(parents=True, exist_ok=True)


class MobileModelExporter:
    """
    Export ML models for mobile deployment
    
    Supports ONNX and TensorFlow Lite formats
    """
    
    def __init__(self):
        """Initialize mobile exporter"""
        self.export_dir = MOBILE_DIR
        print(f"✓ Mobile Model Exporter initialized (export dir: {self.export_dir})")
    
    def export_to_onnx(
        self,
        model_name: str
    ) -> Dict[str, Any]:
        """
        Export model to ONNX format
        
        Args:
            model_name: Name of model to export
            
        Returns:
            Export status and file path
        """
        # Mock ONNX export (in production, use torch.onnx.export)
        onnx_path = self.export_dir / f"{model_name}.onnx"
        
        # Simulate export
        mock_model_sizes = {
            'yolov8': '25.6 MB',
            'resnet50': '98.4 MB',
            'lstm_weight': '12.3 MB',
            'bert_recipe': '125.7 MB'
        }
        
        return {
            'model': model_name,
            'format': 'onnx',
            'file_path': str(onnx_path),
            'file_size': mock_model_sizes.get(model_name, '50 MB'),
            'status': 'mock_export',
            'compatible_platforms': ['iOS', 'Android', 'Web (ONNX.js)'],
            'instructions': 'Load with ONNX Runtime or ONNX.js'
        }
    
    def export_to_tflite(
        self,
        model_name: str,
        quantize: bool = True
    ) -> Dict[str, Any]:
        """
        Export model to TensorFlow Lite
        
        Args:
            model_name: Name of model
            quantize: Apply quantization for smaller size
            
        Returns:
            Export status and file path
        """
        # Mock TFLite export
        suffix = '_quantized' if quantize else ''
        tflite_path = self.export_dir / f"{model_name}{suffix}.tflite"
        
        # Mock sizes (quantized = 4x smaller)
        base_sizes = {
            'yolov8': 25.6,
            'resnet50': 98.4,
            'lstm_weight': 12.3
        }
        
        base_size = base_sizes.get(model_name, 50.0)
        final_size = base_size / 4 if quantize else base_size
        
        return {
            'model': model_name,
            'format': 'tflite',
            'quantized': quantize,
            'file_path': str(tflite_path),
            'file_size_mb': round(final_size, 1),
            'status': 'mock_export',
            'compatible_platforms': ['Android', 'iOS (via TFLite)'],
            'instructions': 'Load with TensorFlow Lite Interpreter',
            'performance': '~4x faster inference' if quantize else 'Standard inference'
        }
    
    def list_exported_models(self) -> Dict[str, Any]:
        """List all exported mobile models"""
        # Mock exported models
        exported = [
            {'name': 'yolov8.onnx', 'size': '25.6 MB', 'format': 'ONNX'},
            {'name': 'resnet50_quantized.tflite', 'size': '24.6 MB', 'format': 'TFLite'},
            {'name': 'lstm_weight.onnx', 'size': '12.3 MB', 'format': 'ONNX'}
        ]
        
        return {
            'export_directory': str(self.export_dir),
            'total_models': len(exported),
            'models': exported,
            'total_size_mb': sum([float(m['size'].split()[0]) for m in exported])
        }


# Singleton instance
_exporter_instance: Optional[MobileModelExporter] = None

def get_mobile_exporter() -> MobileModelExporter:
    """Get singleton mobile exporter"""
    global _exporter_instance
    if _exporter_instance is None:
        _exporter_instance = MobileModelExporter()
    return _exporter_instance
