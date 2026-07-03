"""
WebSocket Router for Real-Time YOLOv8 Food Detection
=====================================================
Processes streamed video frames with <100ms latency.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import base64
import os
import uuid
import logging
from app.ml_models.yolo_food_detector import get_yolo_detector

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Real-time Vision WebSockets"])

@router.websocket("/api/vision/ws-live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    conn_id = str(uuid.uuid4())[:8]
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"ws_frame_{conn_id}.jpg")
    
    logger.info(f"[WS] Client connected: {conn_id}")
    
    try:
        detector = get_yolo_detector()
        
        while True:
            # Receive frame as Base64 string
            data = await websocket.receive_text()
            
            # Clean base64 prefix if present
            if data.startswith("data:image"):
                data = data.split(",", 1)[1]
            
            # Decode and write to temporary file
            try:
                img_data = base64.b64decode(data)
                with open(temp_path, "wb") as f:
                    f.write(img_data)
                
                # Perform YOLOv8 detection
                result = detector.detect(temp_path, confidence_threshold=0.35)
                
                # Clean up detections and format for client
                response = {
                    "status": "success",
                    "detections": result.get("detections", []),
                    "total_foods": result.get("total_foods", 0),
                    "model_used": result.get("model_used", "yolov8"),
                    "image_size": result.get("image_size", [640, 480])
                }
                
                # Stream results back
                await websocket.send_json(response)
                
            except Exception as e:
                logger.warning(f"[WS] Error processing frame: {e}")
                await websocket.send_json({"status": "error", "message": str(e)})
                
    except WebSocketDisconnect:
        logger.info(f"[WS] Client disconnected: {conn_id}")
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"[WS] Error removing temp file: {e}")
