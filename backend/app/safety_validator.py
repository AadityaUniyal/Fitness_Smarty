"""
LLM Output Safety Validator

Post-processes AI-generated health/fitness advice to enforce physiological
safety bounds.  Runs AFTER the Gemini response and BEFORE it reaches the
user.

Key safety rules:
  - Calorie suggestions must be within safe physiological bounds
  - Exercise suggestions are cross-checked against user safety flags
    (pregnancy, joint injuries, menopause)
  - Medical disclaimer is automatically injected
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


MEDICAL_DISCLAIMER = (
    "⚠️ This is AI-generated guidance for informational purposes only. "
    "It is not medical advice. Consult a qualified healthcare professional "
    "before making changes to your diet or exercise routine, especially if "
    "you are pregnant, have a medical condition, or are on medication."
)


# ── Calorie Bounds ──────────────────────────────────────────────────────
# These represent physiologically safe ranges.  Values outside these are
# likely LLM hallucinations and get clamped or flagged.
CALORIE_BOUNDS = {
    "default": (1200, 4000),
    "pregnancy": (1800, 3500),
    "menopause": (1400, 3500),
}

# ── Unsafe Exercise Patterns ────────────────────────────────────────────
# Exercises that should be EXCLUDED for specific user flags.
PREGNANCY_UNSAFE_EXERCISES = {
    "deadlift", "barbell squat", "heavy squat", "box jump",
    "burpee", "sit-up", "crunch", "abdominal twist",
    "flat bench press", "supine press", "lying leg raise",
    "high-impact", "plyometric", "sprint", "jump rope",
}

JOINT_ISSUE_UNSAFE_EXERCISES = {
    "box jump", "plyometric", "jump squat", "burpee",
    "running", "sprinting", "high-impact",
}


@dataclass
class SafetyCheckResult:
    """Result of a safety validation pass."""
    is_safe: bool = True
    original_text: str = ""
    sanitized_text: str = ""
    warnings: List[str] = field(default_factory=list)
    modifications: List[str] = field(default_factory=list)


def validate_calorie_suggestion(
    text: str,
    pregnancy_mode: bool = False,
    menopause_mode: bool = False,
) -> SafetyCheckResult:
    """Check if any calorie numbers in the LLM output fall outside safe
    bounds and clamp them."""
    result = SafetyCheckResult(original_text=text, sanitized_text=text)

    if pregnancy_mode:
        low, high = CALORIE_BOUNDS["pregnancy"]
    elif menopause_mode:
        low, high = CALORIE_BOUNDS["menopause"]
    else:
        low, high = CALORIE_BOUNDS["default"]

    # Find calorie-like numbers: "1500 calories", "2800 kcal", etc.
    pattern = r"(\d{3,5})\s*(?:calories|kcal|cal)\b"
    matches = re.finditer(pattern, text, re.IGNORECASE)

    for match in matches:
        value = int(match.group(1))
        if value < low:
            result.warnings.append(
                f"Calorie suggestion {value} is below safe minimum "
                f"({low}). Clamped to {low}."
            )
            result.sanitized_text = result.sanitized_text.replace(
                match.group(0), f"{low} calories"
            )
            result.modifications.append(f"{value} → {low} calories")
            result.is_safe = False
        elif value > high:
            result.warnings.append(
                f"Calorie suggestion {value} exceeds safe maximum "
                f"({high}). Clamped to {high}."
            )
            result.sanitized_text = result.sanitized_text.replace(
                match.group(0), f"{high} calories"
            )
            result.modifications.append(f"{value} → {high} calories")
            result.is_safe = False

    return result


def validate_exercise_safety(
    text: str,
    pregnancy_mode: bool = False,
    has_joint_issues: bool = False,
) -> SafetyCheckResult:
    """Check if the LLM recommended unsafe exercises for the user's
    condition."""
    result = SafetyCheckResult(original_text=text, sanitized_text=text)

    unsafe_set: set = set()
    if pregnancy_mode:
        unsafe_set |= PREGNANCY_UNSAFE_EXERCISES
    if has_joint_issues:
        unsafe_set |= JOINT_ISSUE_UNSAFE_EXERCISES

    if not unsafe_set:
        return result

    text_lower = text.lower()
    flagged: List[str] = []
    for exercise in unsafe_set:
        if exercise in text_lower:
            flagged.append(exercise)

    if flagged:
        result.is_safe = False
        context = "pregnancy" if pregnancy_mode else "joint concerns"
        result.warnings.append(
            f"The following exercises are potentially unsafe given "
            f"your {context}: {', '.join(flagged)}. "
            f"Please consult a healthcare professional."
        )
        result.modifications.append(
            f"Flagged {len(flagged)} potentially unsafe exercise(s)"
        )

    return result


def sanitize_llm_response(
    text: str,
    user_flags: Optional[Dict[str, Any]] = None,
    add_disclaimer: bool = True,
) -> Dict[str, Any]:
    """
    Main entry point: runs all safety checks on an LLM-generated response.

    Args:
        text: Raw LLM output text
        user_flags: Dict with keys like 'pregnancy_mode', 'menopause_mode',
                    'has_joint_issues'
        add_disclaimer: Whether to append the medical disclaimer

    Returns:
        Dict with 'text', 'disclaimer', 'warnings', 'modifications',
        'safety_passed'
    """
    if user_flags is None:
        user_flags = {}

    pregnancy = user_flags.get("pregnancy_mode", False)
    menopause = user_flags.get("menopause_mode", False)
    joint_issues = user_flags.get("has_joint_issues", False)

    all_warnings: List[str] = []
    all_modifications: List[str] = []
    sanitized = text

    # 1. Calorie bounds check
    cal_result = validate_calorie_suggestion(
        sanitized, pregnancy_mode=pregnancy, menopause_mode=menopause
    )
    sanitized = cal_result.sanitized_text
    all_warnings.extend(cal_result.warnings)
    all_modifications.extend(cal_result.modifications)

    # 2. Exercise safety check
    ex_result = validate_exercise_safety(
        sanitized, pregnancy_mode=pregnancy, has_joint_issues=joint_issues
    )
    sanitized = ex_result.sanitized_text
    all_warnings.extend(ex_result.warnings)
    all_modifications.extend(ex_result.modifications)

    safety_passed = cal_result.is_safe and ex_result.is_safe

    if all_warnings:
        logger.warning(
            "LLM safety checks flagged issues: %s", "; ".join(all_warnings)
        )

    return {
        "text": sanitized,
        "disclaimer": MEDICAL_DISCLAIMER if add_disclaimer else None,
        "warnings": all_warnings,
        "modifications": all_modifications,
        "safety_passed": safety_passed,
    }
