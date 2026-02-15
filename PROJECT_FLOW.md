# Smarty-Reco: End-to-End Project Flow

This document details the complete user journey and system data flow within the Smarty-Reco application, from initial sign-up to personalized daily recommendations.

## 1. User Onboarding & Profile Creation
**Goal:** Establish a baseline for personalization.

1.  **Authentication:** User signs in via **Clerk** (managed auth provider).
2.  **Bio-Profile Setup:**
    -   User enters: Age, Weight, Height, Gender, Activity Level.
    -   **System Action:** Calculates internal baselines (BMR, TDEE) using standard formulas.
3.  **Goal Setting:**
    -   User selects a primary goal (e.g., Weight Loss, Muscle Gain, Maintenance).
    -   **System Action:** Adjusts target nutritional macros and workout intensity based on the goal.

## 2. Daily Dashboard (Mission Control)
**Goal:** Provide an immediate snapshot of daily progress and required actions.

-   **Status Check:** Dashboard acts as the "Home Base," displaying:
    -   **Recovery Score:** Computed from previous day's activity vs. sleep (mocked/API).
    -   **Neural Integrity:** A fun, gamified metric representing adherence to the plan.
    -   **Daily Tasks:** Generated list (Hydration, Workout, Meal logging) sorted by priority.

## 3. Nutrition Flow (Fuel Matrix)
**Goal:** Log intake and receive real-time, AI-driven analysis.

1.  **Meal Capture:**
    -   User takes a photo of their meal or uploads an image.
2.  **AI Analysis Pipeline:**
    -   **Step A (Detection):** **YOLOv8** scans the image for immediate object detection (e.g., "apple", "sandwich") to provide instant feedback.
    -   **Step B (Deep Analysis):** The image is sent to **Gemini 1.5 Flash**.
        -   Identifies ingredients.
        -   Estimates portion sizes (visual estimation).
        -   Calculates caloric and macronutrient breakdown.
3.  **Personalization Check:**
    -   The **Personalization Neural Network** evaluates the meal against the user's specific goals.
    -   **Output:** "Good Match" or "Adjustment Needed" (e.g., "Too high in carbs for your cut phase").
4.  **Logging:** Data is saved to the database, updating the user's daily caloric intake.

## 4. Workout Flow (Kinetic Ops)
**Goal:** Guide the user through personalized physical training.

1.  **Selection:** User views the daily workout plan (dynamically generated or template-based).
2.  **Execution:**
    -   User marks exercises as complete.
    -   Logs sets, reps, and weights.
3.  **Analysis:**
    -   System tracks total volume (Weight * Reps).
    -   Updates "Muscle Readiness" scores for future recommendations.

## 5. Analytics & Long-Term Adaptation (Bio Calibration)
**Goal:** Visualize progress and adapt the plan over time.

1.  **Data Aggregation:** System aggregates daily logs (Nutrition + Workouts + Biometrics).
2.  **Visualization:**
    -   **Recharts** renders trend lines for Weight, Calories, and Activity.
3.  **Predictive Modeling:**
    -   **LSTM Model** analyzes the valid historical data points.
    -   **Output:** Forecasts future weight trends (e.g., "On track to reach goal by [Date]").
4.  **Feedback Loop:**
    -   If progress stalls, the Recommendation Engine adjusts daily calorie targets or workout intensity for the next week.

## Summary of Data Flow
`User Action` -> `Frontend (React)` -> `API (FastAPI)` -> `AI Models (Gemini/YOLO/LSTM)` -> `Database (PostgreSQL)` -> `Feedback to User`
