/**
 * Vision Service - Frontend Integration
 * 
 * TypeScript service for YOLOv8 and advanced computer vision features
 */

const API_BASE = 'http://localhost:8000';

export interface YOLODetection {
    class: string;
    confidence: number;
    bbox: number[];  // [x1, y1, x2, y2]
    portion_estimate_g: number;
}

export interface YOLOResult {
    detections: YOLODetection[];
    total_foods: number;
    model_used: string;
    image_size: number[];
    annotated_image_url?: string;
}

export interface HybridDetection {
    food: string;
    confidence: number;
    portion_g?: number;
    source: 'yolov8' | 'gemini';
}

export interface HybridResult {
    yolo: YOLOResult;
    gemini: any;
    final_detections: HybridDetection[];
    total_unique_foods: number;
    ensemble_confidence: number;
}

export interface NutritionItem {
    food: string;
    portion_g: number;
    calories: number;
    protein_g: number;
    carbs_g: number;
    fat_g: number;
}

export interface NutritionEstimate {
    calories: number;
    protein_g: number;
    carbs_g: number;
    fat_g: number;
    items: NutritionItem[];
}

export class VisionService {

    /**
     * Detect foods using YOLOv8
     */
    static async detectWithYOLO(
        imageFile: File,
        confidence: number = 0.5,
        annotate: boolean = false
    ): Promise<YOLOResult> {
        const formData = new FormData();
        formData.append('file', imageFile);

        const response = await fetch(
            `${API_BASE}/api/vision/detect-yolo?confidence=${confidence}&annotate=${annotate}`,
            {
                method: 'POST',
                body: formData
            }
        );

        if (!response.ok) {
            throw new Error(`YOLOv8 detection failed: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Detect foods using hybrid ensemble (YOLOv8 + Gemini)
     */
    static async detectHybrid(
        imageFile: File,
        userId?: number
    ): Promise<HybridResult> {
        const formData = new FormData();
        formData.append('file', imageFile);

        const url = userId
            ? `${API_BASE}/api/vision/detect-hybrid?user_id=${userId}`
            : `${API_BASE}/api/vision/detect-hybrid`;

        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Hybrid detection failed: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Check which vision models are available
     */
    static async getModelsStatus(): Promise<any> {
        const response = await fetch(`${API_BASE}/api/vision/models/status`);

        if (!response.ok) {
            throw new Error(`Failed to check models: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Estimate nutrition from detection results
     */
    static async estimateNutrition(
        detectionResult: { detections: YOLODetection[] }
    ): Promise<NutritionEstimate> {
        const response = await fetch(
            `${API_BASE}/api/vision/estimate-nutrition`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(detectionResult)
            }
        );

        if (!response.ok) {
            throw new Error(`Nutrition estimation failed: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Complete workflow: Detect → Estimate Nutrition
     */
    static async scanAndAnalyze(
        imageFile: File,
        useHybrid: boolean = true
    ): Promise<{ detection: YOLOResult | HybridResult, nutrition: NutritionEstimate }> {

        let detection: any;

        if (useHybrid) {
            detection = await this.detectHybrid(imageFile);
        } else {
            detection = await this.detectWithYOLO(imageFile);
        }

        // Convert to nutrition
        const detectionForNutrition = useHybrid
            ? { detections: detection.yolo.detections }
            : { detections: detection.detections };

        const nutrition = await this.estimateNutrition(detectionForNutrition);

        return { detection, nutrition };
    }
}

export default VisionService;
