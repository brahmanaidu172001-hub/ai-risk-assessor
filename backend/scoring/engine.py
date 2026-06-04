"""
Risk scoring engine — pure computation, no LLM, no I/O.

Score formula: (likelihood × impact / 25) × 100 × category_weight
This maps likelihood [1–5] × impact [1–5] = [1–25] to a 0–100 scale,
then applies an optional category weight for industry-specific amplification.
"""

from backend.models.risk import RiskLevel


# Category weights by industry — adjust for domain-specific exposure
INDUSTRY_WEIGHTS: dict[str, dict[str, float]] = {
    "fintech": {
        "compliance": 1.4,
        "cyber": 1.3,
        "financial": 1.2,
        "operational": 1.0,
    },
    "healthcare": {
        "compliance": 1.5,
        "cyber": 1.4,
        "operational": 1.2,
        "financial": 1.0,
    },
    "ecommerce": {
        "cyber": 1.3,
        "vendor": 1.2,
        "market": 1.2,
        "operational": 1.0,
    },
    "ai": {
        "product": 1.3,
        "compliance": 1.2,
        "execution": 1.2,
        "cyber": 1.1,
    },
    "technology": {
        "cyber": 1.2,
        "execution": 1.1,
        "product": 1.1,
        "vendor": 1.0,
    },
}

DEFAULT_WEIGHTS: dict[str, float] = {
    "financial": 1.0,
    "operational": 1.0,
    "compliance": 1.0,
    "cyber": 1.0,
    "market": 1.0,
    "product": 1.0,
    "vendor": 1.0,
    "execution": 1.0,
}

# Category weights for overall score aggregation
CATEGORY_AGGREGATION_WEIGHTS: dict[str, float] = {
    "financial": 0.20,
    "compliance": 0.18,
    "cyber": 0.18,
    "operational": 0.15,
    "execution": 0.12,
    "market": 0.07,
    "product": 0.05,
    "vendor": 0.05,
}


def compute_risk_score(
    likelihood: int,
    impact: int,
    category_weight: float = 1.0,
) -> float:
    """Compute a 0–100 risk score from a 1–5 likelihood and 1–5 impact."""
    raw = (likelihood * impact) / 25.0
    return min(round(raw * 100 * category_weight, 1), 100.0)


def level_from_score(score: float) -> RiskLevel:
    """Map a 0–100 score to a RiskLevel enum."""
    if score >= 75:
        return RiskLevel.CRITICAL
    if score >= 55:
        return RiskLevel.HIGH
    if score >= 30:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def get_category_weight(industry: str, category: str) -> float:
    """Return the industry-adjusted weight for a given risk category."""
    industry_map = INDUSTRY_WEIGHTS.get(industry.lower(), {})
    return industry_map.get(category.lower(), DEFAULT_WEIGHTS.get(category.lower(), 1.0))


def compute_overall_score(category_scores: dict[str, float]) -> float:
    """
    Aggregate per-category scores into a single weighted overall score.
    Unrecognized categories are averaged with equal weight.
    """
    weighted_sum = 0.0
    total_weight = 0.0

    for category, score in category_scores.items():
        weight = CATEGORY_AGGREGATION_WEIGHTS.get(category.lower(), 0.05)
        weighted_sum += score * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    # Normalize in case not all categories are present
    return min(round(weighted_sum / total_weight, 1), 100.0)
