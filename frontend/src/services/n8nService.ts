/**
 * n8n Service - Active Learning Integration
 * 
 * Sends corrected food data to n8n webhook for model retraining.
 */

const N8N_WEBHOOK_URL = import.meta.env.VITE_N8N_WEBHOOK_URL || 'https://primary.n8n.cloud/webhook/smarty-food-training';

export interface TrainingSample {
    original_image: File | Blob;
    predicted_label: string;
    corrected_label: string;
    corrected_calories?: number;
    user_id?: string;
    timestamp: string;
    confidence_score: number;
}

export const N8NService = {
    /**
     * Send correction data to n8n for training
     */
    async sendCorrection(sample: TrainingSample): Promise<boolean> {
        try {
            const formData = new FormData();
            formData.append('image', sample.original_image);
            formData.append('data', JSON.stringify({
                predicted: sample.predicted_label,
                corrected: sample.corrected_label,
                calories: sample.corrected_calories,
                user: sample.user_id,
                timestamp: sample.timestamp,
                confidence: sample.confidence_score
            }));

            // In a real scenario, we might want to use 'no-cors' if n8n isn't configured for CORS,
            // but for a proper setup, n8n should handle OPTIONS requests.
            // For now, we assume simple POST.
            const response = await fetch(N8N_WEBHOOK_URL, {
                method: 'POST',
                body: formData
            });

            return response.ok;
        } catch (error) {
            console.error("Failed to send training data to n8n:", error);
            return false;
        }
    }
};
