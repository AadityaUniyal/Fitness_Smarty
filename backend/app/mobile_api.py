"""
Mobile Deployment API Router

Endpoints for mobile model export and download
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, Any

router = APIRouter(prefix="/api/mobile", tags=["mobile-deployment"])


@router.post("/export/onnx/{model_name}")
async def export_model_to_onnx(model_name: str):
    """
    Export model to ONNX format
    
    Compatible with iOS, Android, and Web (ONNX.js)
     """
    try:
        from app.models.mobile_export import get_mobile_exporter
        exporter = get_mobile_exporter()
        
        result = exporter.export_to_onnx(model_name)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ONNX export failed: {str(e)}")


@router.post("/export/tflite/{model_name}")
async def export_model_to_tflite(
    model_name: str,
    quantize: bool = True
):
    """
    Export model to TensorFlow Lite
    
    Optimized for mobile (Android/iOS)
    """
    try:
        from app.models.mobile_export import get_mobile_exporter
        exporter = get_mobile_exporter()
        
        result = exporter.export_to_tflite(model_name, quantize)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TFLite export failed: {str(e)}")


@router.get("/models/list")
async def list_mobile_models():
    """
    List all exported mobile models
    
    Shows available downloads
    """
    try:
        from app.models.mobile_export import get_mobile_exporter
        exporter = get_mobile_exporter()
        
        models = exporter.list_exported_models()
        
        return models
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model listing failed: {str(e)}")


@router.get("/models/status")
async def get_mobile_deployment_status():
    """Check mobile deployment status"""
    
    status = {
        'onnx_export': {
            'available': True,
            'status': 'ready',
            'description': 'ONNX export for cross-platform deployment'
        },
        'tflite_export': {
            'available': True,
            'status': 'ready',
            'description': 'TensorFlow Lite export for mobile optimization'
        }
    }
    
    return {
        'exporters': status,
        'available_count': 2,
        'total_count': 2,
        'supported_formats': ['ONNX', 'TFLite'],
        'supported_platforms': ['iOS', 'Android', 'Web'],
        'phase': 7
    }
