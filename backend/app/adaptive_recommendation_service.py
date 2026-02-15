"""
Adaptive Recommendation Service

Provides adaptive recommendations that adjust based on:
- User progress tracking and metrics
- Historical trend analysis
- Goal achievement patterns
- Preference-based adaptation
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import statistics
from . import models
from .recommendation_engine import RecommendationEngine, NutritionalPattern
from pydantic import BaseModel


class ProgressMetrics(BaseModel):
    """Comprehensive progress metrics for a user"""
    goal_id: str
    goal_type: str
    progress_percentage: float
    velocity: float  # Rate of progress per day
    days_active: int
    consistency_score: float  # 0-1, how consistently user tracks
    predicted_completion_date: Optional[datetime]
    is_on_track: bool
    trend: str  # "improving", "stable", "declining"


class TrendAnalysis(BaseModel):
    """Trend analysis for goal optimization"""
    metric_name: str
    current_value: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    rate_of_change: float  # Change per day
    volatility: float  # Standard deviation
    recommendations: List[str]


class AdaptiveRecommendation(BaseModel):
    """Adaptive recommendation with adjustment reasoning"""
    recommendation_type: str
    title: str
    description: str
    confidence_score: float
    priority: str
    adjustment_reason: str  # Why this recommendation was adjusted
    based_on_metrics: List[str]  # Which metrics influenced this


class AdaptiveRecommendationService:
    """Service for generating adaptive recommendations based on progress"""

    def __init__(self, db: Session):
        self.db = db
        self.base_engine = RecommendationEngine(db)

    def calculate_progress_metrics(self, user_id: str) -> List[ProgressMetrics]:
        """
        Calculate comprehensive progress metrics for all active goals
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List of ProgressMetrics for each active goal
        """
        # Convert string UUID to UUID object if needed
        try:
            import uuid as uuid_module
            user_uuid = uuid_module.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, AttributeError):
            user_uuid = user_id
        
        goals = self.db.query(models.UserGoal).filter(
            models.UserGoal.user_id == user_uuid,
            models.UserGoal.is_active == True
        ).all()
        
        metrics_list = []
        
        for goal in goals:
            metrics = self._calculate_single_goal_metrics(goal)
            metrics_list.append(metrics)
        
        return metrics_list

    def _calculate_single_goal_metrics(self, goal: models.UserGoal) -> ProgressMetrics:
        """Calculate metrics for a single goal"""
        # Calculate progress percentage
        if goal.target_value > 0:
            progress_pct = (float(goal.current_value) / float(goal.target_value)) * 100
        else:
            progress_pct = 0
        
        # Calculate days active
        days_active = (datetime.utcnow() - goal.created_at).days
        if days_active == 0:
            days_active = 1
        
        # Calculate velocity (progress per day)
        velocity = progress_pct / days_active
        
        # Calculate consistency score based on goal type
        consistency_score = self._calculate_consistency_score(goal)
        
        # Predict completion date
        predicted_completion = None
        if velocity > 0 and progress_pct < 100:
            days_to_completion = (100 - progress_pct) / velocity
            predicted_completion = datetime.utcnow() + timedelta(days=days_to_completion)
        
        # Determine if on track
        is_on_track = True
        if goal.target_date:
            days_remaining = (goal.target_date - datetime.utcnow()).days
            total_days = (goal.target_date - goal.created_at).days
            
            if total_days > 0:
                expected_progress = ((total_days - days_remaining) / total_days) * 100
                is_on_track = progress_pct >= (expected_progress - 15)
        
        # Determine trend
        trend = self._determine_progress_trend(goal)
        
        return ProgressMetrics(
            goal_id=str(goal.id),
            goal_type=goal.goal_type,
            progress_percentage=min(progress_pct, 100),
            velocity=velocity,
            days_active=days_active,
            consistency_score=consistency_score,
            predicted_completion_date=predicted_completion,
            is_on_track=is_on_track,
            trend=trend
        )

    def _calculate_consistency_score(self, goal: models.UserGoal) -> float:
        """
        Calculate consistency score based on goal type and user activity
        
        Returns:
            Float between 0 and 1
        """
        # For now, use a simple heuristic based on update frequency
        # In a full implementation, this would analyze historical updates
        
        days_active = (datetime.utcnow() - goal.created_at).days
        if days_active == 0:
            return 0.5
        
        # If goal has been updated recently, higher consistency
        days_since_update = (datetime.utcnow() - goal.updated_at).days
        
        if days_since_update <= 1:
            return 0.9
        elif days_since_update <= 3:
            return 0.7
        elif days_since_update <= 7:
            return 0.5
        else:
            return 0.3

    def _determine_progress_trend(self, goal: models.UserGoal) -> str:
        """
        Determine if progress is improving, stable, or declining
        
        Returns:
            "improving", "stable", or "declining"
        """
        # This would ideally analyze historical progress data
        # For now, use a simple heuristic based on recent updates
        
        days_since_update = (datetime.utcnow() - goal.updated_at).days
        
        if days_since_update <= 2:
            return "improving"
        elif days_since_update <= 7:
            return "stable"
        else:
            return "declining"

    def analyze_trends(self, user_id: str) -> List[TrendAnalysis]:
        """
        Analyze trends in user's nutrition and exercise patterns
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List of TrendAnalysis for various metrics
        """
        trends = []
        
        # Analyze nutritional trends
        nutritional_trends = self._analyze_nutritional_trends(user_id)
        trends.extend(nutritional_trends)
        
        # Analyze weight trends if applicable
        weight_trends = self._analyze_weight_trends(user_id)
        if weight_trends:
            trends.append(weight_trends)
        
        return trends

    def _analyze_nutritional_trends(self, user_id: str) -> List[TrendAnalysis]:
        """Analyze trends in nutritional intake"""
        trends = []
        
        # Get meal logs from last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        try:
            import uuid as uuid_module
            user_uuid = uuid_module.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, AttributeError):
            user_uuid = user_id
        
        meal_logs = self.db.query(models.MealLog).filter(
            models.MealLog.user_id == user_uuid,
            models.MealLog.logged_at >= thirty_days_ago
        ).order_by(models.MealLog.logged_at).all()
        
        if len(meal_logs) < 7:
            return trends
        
        # Group by week and calculate averages
        weekly_calories = defaultdict(list)
        weekly_protein = defaultdict(list)
        
        for meal in meal_logs:
            week_key = meal.logged_at.isocalendar()[1]  # ISO week number
            weekly_calories[week_key].append(float(meal.total_calories or 0))
            weekly_protein[week_key].append(float(meal.total_protein_g or 0))
        
        # Calculate calorie trend
        if len(weekly_calories) >= 2:
            weeks = sorted(weekly_calories.keys())
            weekly_avg_calories = [statistics.mean(weekly_calories[w]) for w in weeks]
            
            # Calculate rate of change
            if len(weekly_avg_calories) >= 2:
                rate_of_change = (weekly_avg_calories[-1] - weekly_avg_calories[0]) / len(weeks)
                volatility = statistics.stdev(weekly_avg_calories) if len(weekly_avg_calories) > 1 else 0
                
                # Determine trend direction
                if rate_of_change > 50:
                    direction = "increasing"
                    recommendations = ["Calorie intake is increasing. Monitor portion sizes if weight loss is your goal."]
                elif rate_of_change < -50:
                    direction = "decreasing"
                    recommendations = ["Calorie intake is decreasing. Ensure you're meeting minimum nutritional needs."]
                else:
                    direction = "stable"
                    recommendations = ["Calorie intake is stable. Good consistency!"]
                
                trends.append(TrendAnalysis(
                    metric_name="daily_calories",
                    current_value=weekly_avg_calories[-1],
                    trend_direction=direction,
                    rate_of_change=rate_of_change,
                    volatility=volatility,
                    recommendations=recommendations
                ))
        
        # Calculate protein trend
        if len(weekly_protein) >= 2:
            weeks = sorted(weekly_protein.keys())
            weekly_avg_protein = [statistics.mean(weekly_protein[w]) for w in weeks]
            
            if len(weekly_avg_protein) >= 2:
                rate_of_change = (weekly_avg_protein[-1] - weekly_avg_protein[0]) / len(weeks)
                volatility = statistics.stdev(weekly_avg_protein) if len(weekly_avg_protein) > 1 else 0
                
                if rate_of_change > 5:
                    direction = "increasing"
                    recommendations = ["Protein intake is increasing. Great for muscle maintenance and growth!"]
                elif rate_of_change < -5:
                    direction = "decreasing"
                    recommendations = ["Protein intake is decreasing. Consider adding protein-rich foods."]
                else:
                    direction = "stable"
                    recommendations = ["Protein intake is stable."]
                
                trends.append(TrendAnalysis(
                    metric_name="daily_protein",
                    current_value=weekly_avg_protein[-1],
                    trend_direction=direction,
                    rate_of_change=rate_of_change,
                    volatility=volatility,
                    recommendations=recommendations
                ))
        
        return trends

    def _analyze_weight_trends(self, user_id: str) -> Optional[TrendAnalysis]:
        """Analyze weight trends from user profile updates"""
        # This would ideally track historical weight data
        # For now, return None as we don't have historical tracking yet
        return None

    def generate_adaptive_recommendations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[AdaptiveRecommendation]:
        """
        Generate adaptive recommendations based on progress and trends
        
        Args:
            user_id: UUID of the user
            limit: Maximum number of recommendations
            
        Returns:
            List of AdaptiveRecommendation objects
        """
        recommendations = []
        
        # Get progress metrics
        progress_metrics = self.calculate_progress_metrics(user_id)
        
        # Get trend analysis
        trends = self.analyze_trends(user_id)
        
        # Get user profile
        try:
            import uuid as uuid_module
            user_uuid = uuid_module.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, AttributeError):
            user_uuid = user_id
        
        profile = self.db.query(models.UserProfile).filter(
            models.UserProfile.user_id == user_uuid
        ).first()
        
        if not profile:
            return recommendations
        
        # Generate recommendations based on progress metrics
        for metric in progress_metrics:
            recs = self._generate_progress_based_recommendations(metric, profile)
            recommendations.extend(recs)
        
        # Generate recommendations based on trends
        for trend in trends:
            recs = self._generate_trend_based_recommendations(trend, profile)
            recommendations.extend(recs)
        
        # Generate preference-based adaptations
        pref_recs = self._generate_preference_adaptations(user_id, profile, progress_metrics)
        recommendations.extend(pref_recs)
        
        # Sort by confidence score and limit
        recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
        return recommendations[:limit]

    def _generate_progress_based_recommendations(
        self,
        metric: ProgressMetrics,
        profile: models.UserProfile
    ) -> List[AdaptiveRecommendation]:
        """Generate recommendations based on progress metrics"""
        recommendations = []
        
        # Recommendation for declining progress
        if metric.trend == "declining" and metric.consistency_score < 0.5:
            recommendations.append(AdaptiveRecommendation(
                recommendation_type="goal_adjustment",
                title=f"Boost Your {metric.goal_type.replace('_', ' ').title()} Progress",
                description=f"Your progress has slowed recently. Your consistency score is {metric.consistency_score:.1%}. "
                           f"Try setting daily reminders or breaking your goal into smaller milestones.",
                confidence_score=0.85,
                priority="high",
                adjustment_reason="Low consistency and declining trend detected",
                based_on_metrics=["consistency_score", "trend"]
            ))
        
        # Recommendation for off-track goals
        if not metric.is_on_track and metric.velocity > 0:
            days_behind = (100 - metric.progress_percentage) / metric.velocity
            recommendations.append(AdaptiveRecommendation(
                recommendation_type="goal_adjustment",
                title=f"Adjust {metric.goal_type.replace('_', ' ').title()} Timeline",
                description=f"You're at {metric.progress_percentage:.0f}% progress but behind schedule. "
                           f"At your current pace, you'll need about {days_behind:.0f} more days. "
                           f"Consider adjusting your target date or increasing your effort.",
                confidence_score=0.80,
                priority="medium",
                adjustment_reason="Progress velocity indicates timeline adjustment needed",
                based_on_metrics=["velocity", "is_on_track", "progress_percentage"]
            ))
        
        # Recommendation for exceeding expectations
        if metric.is_on_track and metric.progress_percentage > 75 and metric.trend == "improving":
            recommendations.append(AdaptiveRecommendation(
                recommendation_type="goal_adjustment",
                title=f"Consider Increasing Your {metric.goal_type.replace('_', ' ').title()} Target",
                description=f"Excellent progress! You're at {metric.progress_percentage:.0f}% and trending upward. "
                           f"You might be ready for a more challenging goal.",
                confidence_score=0.75,
                priority="low",
                adjustment_reason="Exceeding progress expectations with improving trend",
                based_on_metrics=["progress_percentage", "trend", "is_on_track"]
            ))
        
        return recommendations

    def _generate_trend_based_recommendations(
        self,
        trend: TrendAnalysis,
        profile: models.UserProfile
    ) -> List[AdaptiveRecommendation]:
        """Generate recommendations based on trend analysis"""
        recommendations = []
        
        # High volatility recommendations
        if trend.volatility > trend.current_value * 0.3:  # More than 30% variation
            recommendations.append(AdaptiveRecommendation(
                recommendation_type="meal",
                title=f"Stabilize Your {trend.metric_name.replace('_', ' ').title()}",
                description=f"Your {trend.metric_name.replace('_', ' ')} varies significantly day-to-day. "
                           f"More consistent intake can help you reach your goals more predictably. "
                           f"Try meal planning or setting daily targets.",
                confidence_score=0.70,
                priority="medium",
                adjustment_reason="High volatility detected in nutritional intake",
                based_on_metrics=["volatility", "trend_direction"]
            ))
        
        # Trend-specific recommendations
        if trend.metric_name == "daily_calories":
            if profile.primary_goal == "weight_loss" and trend.trend_direction == "increasing":
                recommendations.append(AdaptiveRecommendation(
                    recommendation_type="meal",
                    title="Calorie Intake Increasing",
                    description=f"Your calorie intake is trending upward ({trend.rate_of_change:+.0f} cal/week). "
                               f"For weight loss, consider portion control or lower-calorie alternatives.",
                    confidence_score=0.85,
                    priority="high",
                    adjustment_reason="Calorie trend conflicts with weight loss goal",
                    based_on_metrics=["trend_direction", "rate_of_change", "primary_goal"]
                ))
            
            elif profile.primary_goal == "weight_gain" and trend.trend_direction == "decreasing":
                recommendations.append(AdaptiveRecommendation(
                    recommendation_type="meal",
                    title="Calorie Intake Decreasing",
                    description=f"Your calorie intake is trending downward ({trend.rate_of_change:+.0f} cal/week). "
                               f"For weight gain, consider adding calorie-dense foods or larger portions.",
                    confidence_score=0.85,
                    priority="high",
                    adjustment_reason="Calorie trend conflicts with weight gain goal",
                    based_on_metrics=["trend_direction", "rate_of_change", "primary_goal"]
                ))
        
        return recommendations

    def _generate_preference_adaptations(
        self,
        user_id: str,
        profile: models.UserProfile,
        progress_metrics: List[ProgressMetrics]
    ) -> List[AdaptiveRecommendation]:
        """Generate recommendations adapted to user preferences"""
        recommendations = []
        
        # Adapt based on dietary restrictions
        if profile.dietary_restrictions:
            # Check if user is meeting nutritional needs with restrictions
            nutritional_pattern = self.base_engine.analyze_nutritional_patterns(user_id)
            
            if nutritional_pattern.deficiencies:
                deficiency_list = ", ".join(nutritional_pattern.deficiencies)
                recommendations.append(AdaptiveRecommendation(
                    recommendation_type="meal",
                    title=f"Address Nutritional Gaps with {', '.join(profile.dietary_restrictions)} Diet",
                    description=f"While following your {', '.join(profile.dietary_restrictions)} diet, "
                               f"you may have deficiencies in: {deficiency_list}. "
                               f"Consider fortified foods or supplements that align with your dietary preferences.",
                    confidence_score=0.80,
                    priority="medium",
                    adjustment_reason="Nutritional deficiencies detected with dietary restrictions",
                    based_on_metrics=["dietary_restrictions", "nutritional_deficiencies"]
                ))
        
        # Adapt based on activity level
        if profile.activity_level == "sedentary":
            # Check if user has exercise goals
            has_exercise_goal = any(m.goal_type == "weekly_exercise" for m in progress_metrics)
            
            if not has_exercise_goal:
                recommendations.append(AdaptiveRecommendation(
                    recommendation_type="exercise",
                    title="Start Building Activity Habits",
                    description="Your activity level is sedentary. Starting with just 10-15 minutes of daily "
                               "walking can significantly improve your health and support your fitness goals.",
                    confidence_score=0.90,
                    priority="high",
                    adjustment_reason="Sedentary activity level with no exercise goals",
                    based_on_metrics=["activity_level", "active_goals"]
                ))
        
        elif profile.activity_level in ["active", "very_active"]:
            # Recommend recovery and nutrition for active users
            recommendations.append(AdaptiveRecommendation(
                recommendation_type="meal",
                title="Fuel Your Active Lifestyle",
                description=f"As a {profile.activity_level.replace('_', ' ')} person, ensure you're eating enough "
                           f"to support your activity level. Focus on post-workout nutrition and adequate protein.",
                confidence_score=0.75,
                priority="medium",
                adjustment_reason="High activity level requires adequate nutrition",
                based_on_metrics=["activity_level"]
            ))
        
        # Adapt based on primary goal (always generate at least one recommendation)
        if profile.primary_goal:
            goal_recommendations = self._generate_goal_specific_recommendations(profile)
            recommendations.extend(goal_recommendations)
        
        return recommendations
    
    def _generate_goal_specific_recommendations(
        self,
        profile: models.UserProfile
    ) -> List[AdaptiveRecommendation]:
        """Generate recommendations specific to user's primary goal"""
        recommendations = []
        
        if profile.primary_goal == "weight_loss":
            recommendations.append(AdaptiveRecommendation(
                recommendation_type="meal",
                title="Optimize Nutrition for Weight Loss",
                description="Focus on creating a moderate calorie deficit while maintaining adequate protein "
                           "to preserve muscle mass. Aim for nutrient-dense, filling foods.",
                confidence_score=0.85,
                priority="high",
                adjustment_reason="Tailored to weight loss goal",
                based_on_metrics=["primary_goal"]
            ))
        
        elif profile.primary_goal == "weight_gain":
            recommendations.append(AdaptiveRecommendation(
                recommendation_type="meal",
                title="Increase Calorie Intake for Weight Gain",
                description="Focus on calorie-dense, nutritious foods to support healthy weight gain. "
                           "Consider adding snacks between meals and protein-rich foods.",
                confidence_score=0.85,
                priority="high",
                adjustment_reason="Tailored to weight gain goal",
                based_on_metrics=["primary_goal"]
            ))
        
        elif profile.primary_goal == "muscle_gain":
            recommendations.append(AdaptiveRecommendation(
                recommendation_type="meal",
                title="Fuel Muscle Growth with Protein",
                description="Prioritize protein intake (1.6-2.2g per kg body weight) and ensure adequate "
                           "calories to support muscle growth. Time protein intake around workouts.",
                confidence_score=0.85,
                priority="high",
                adjustment_reason="Tailored to muscle gain goal",
                based_on_metrics=["primary_goal"]
            ))
        
        elif profile.primary_goal == "athletic_performance":
            recommendations.append(AdaptiveRecommendation(
                recommendation_type="meal",
                title="Optimize Performance Nutrition",
                description="Focus on timing your nutrition around training. Ensure adequate carbohydrates "
                           "for energy and protein for recovery. Stay well-hydrated.",
                confidence_score=0.85,
                priority="high",
                adjustment_reason="Tailored to athletic performance goal",
                based_on_metrics=["primary_goal"]
            ))
        
        elif profile.primary_goal == "maintenance":
            recommendations.append(AdaptiveRecommendation(
                recommendation_type="meal",
                title="Maintain Balanced Nutrition",
                description="Focus on consistent, balanced meals that match your energy expenditure. "
                           "Maintain variety in your diet for optimal nutrition.",
                confidence_score=0.80,
                priority="medium",
                adjustment_reason="Tailored to maintenance goal",
                based_on_metrics=["primary_goal"]
            ))
        
        return recommendations

    def adjust_recommendations_by_progress(
        self,
        user_id: str,
        base_recommendations: List[Dict[str, Any]]
    ) -> List[AdaptiveRecommendation]:
        """
        Adjust existing recommendations based on user progress
        
        Args:
            user_id: UUID of the user
            base_recommendations: Base recommendations to adjust
            
        Returns:
            List of adjusted AdaptiveRecommendation objects
        """
        adjusted = []
        
        # Get progress metrics
        progress_metrics = self.calculate_progress_metrics(user_id)
        
        # Create a progress summary
        avg_consistency = statistics.mean([m.consistency_score for m in progress_metrics]) if progress_metrics else 0.5
        on_track_count = sum(1 for m in progress_metrics if m.is_on_track)
        total_goals = len(progress_metrics)
        
        for rec in base_recommendations:
            # Adjust confidence based on consistency
            adjusted_confidence = rec.get("confidence_score", 0.5) * (0.7 + 0.3 * avg_consistency)
            
            # Adjust priority based on progress
            priority = rec.get("priority", "medium")
            if total_goals > 0 and on_track_count / total_goals < 0.5:
                # If user is struggling, increase priority of supportive recommendations
                if rec.get("recommendation_type") == "goal_adjustment":
                    priority = "high"
            
            # Add adjustment reasoning
            adjustment_reason = f"Adjusted based on {avg_consistency:.0%} consistency"
            if total_goals > 0:
                adjustment_reason += f" and {on_track_count}/{total_goals} goals on track"
            
            adjusted.append(AdaptiveRecommendation(
                recommendation_type=rec.get("recommendation_type", "general"),
                title=rec.get("title", ""),
                description=rec.get("description", ""),
                confidence_score=adjusted_confidence,
                priority=priority,
                adjustment_reason=adjustment_reason,
                based_on_metrics=["consistency_score", "on_track_ratio"]
            ))
        
        return adjusted
