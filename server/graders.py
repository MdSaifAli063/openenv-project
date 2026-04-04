"""Deterministic graders for OpenEnv email triage tasks."""

from ..models import RewardResult, TriageAction


def _clip_score(score_value: float) -> float:
    """Clip a score to the inclusive range [0.0, 1.0].
    Args:
        score_value: Raw score.
    Returns:
        Clipped score.
    """
    return max(0.0, min(1.0, score_value))


def _normalized_text(text_value: str) -> str:
    """Return normalized lowercase text for deterministic comparisons.
    Args:
        text_value: Input text.
    Returns:
        Normalized text.
    """
    return text_value.strip().lower()


def _route_matches(action_route: str, expected_route: str) -> bool:
    """Check if action route contains the expected route token.
    Args:
        action_route: Route provided by agent.
        expected_route: Route expected by ground truth.
    Returns:
        True when expected route is present in the action route.
    """
    normalized_action = _normalized_text(action_route)
    normalized_expected = _normalized_text(expected_route)
    if not normalized_expected:
        return False
    return normalized_expected in normalized_action


def grade_easy(action: TriageAction, ground_truth: dict) -> RewardResult:
    """Grade easy task with deterministic partial credit.
    Args:
        action: Agent action for one email.
        ground_truth: Expected label and route.
    Returns:
        Deterministic reward result in [0.0, 1.0].
    """
    expected_label = _normalized_text(str(ground_truth.get("label", "")))
    expected_route = _normalized_text(str(ground_truth.get("route_to", "")))

    label_correct = _normalized_text(action.label) == expected_label
    route_correct = _route_matches(action.route_to, expected_route)

    if label_correct and route_correct:
        score_value = 1.0
    elif route_correct:
        score_value = 0.3
    elif label_correct:
        score_value = 0.6
    else:
        score_value = 0.0

    score_value = _clip_score(score_value)
    breakdown = {
        "label_match": 1.0 if label_correct else 0.0,
        "route_match": 1.0 if route_correct else 0.0,
    }
    feedback = (
        "Correct label and route."
        if score_value == 1.0
        else "Partial credit applied based on label or routing correctness."
    )
    return RewardResult(score=score_value, breakdown=breakdown, feedback=feedback)


def grade_medium(actions: list[TriageAction], ground_truths: list[dict]) -> RewardResult:
    """Grade medium task using weighted per-email partial scoring.
    Args:
        actions: Agent actions for the medium task email queue.
        ground_truths: Expected action details for each email.
    Returns:
        Deterministic reward result in [0.0, 1.0].
    """
    comparable_count = min(len(actions), len(ground_truths))
    if comparable_count == 0:
        return RewardResult(
            score=0.0,
            breakdown={"emails_scored": 0.0, "weighted_average": 0.0},
            feedback="No actions available for grading.",
        )

    weighted_score_sum = 0.0
    weight_sum = 0.0
    label_hits = 0
    route_hits = 0

    for index in range(comparable_count):
        action = actions[index]
        truth = ground_truths[index]

        expected_label = _normalized_text(str(truth.get("label", "")))
        expected_route = _normalized_text(str(truth.get("route_to", "")))
        priority_weight = float(truth.get("priority_weight", 1.0))
        priority_weight = max(priority_weight, 0.1)

        label_correct = _normalized_text(action.label) == expected_label
        route_correct = _route_matches(action.route_to, expected_route)

        # Label carries most of the score; route correctness supplies dense signal.
        per_email_score = (0.7 if label_correct else 0.0) + (0.3 if route_correct else 0.0)
        per_email_score = _clip_score(per_email_score)

        weighted_score_sum += per_email_score * priority_weight
        weight_sum += priority_weight

        label_hits += 1 if label_correct else 0
        route_hits += 1 if route_correct else 0

    weighted_average = weighted_score_sum / weight_sum if weight_sum > 0.0 else 0.0
    score_value = _clip_score(weighted_average)

    breakdown = {
        "emails_scored": float(comparable_count),
        "label_accuracy": label_hits / comparable_count,
        "route_accuracy": route_hits / comparable_count,
        "weighted_average": score_value,
    }
    feedback = "Weighted medium-task grading completed."
    return RewardResult(score=score_value, breakdown=breakdown, feedback=feedback)


def grade_hard(action: TriageAction, ground_truth: dict) -> RewardResult:
    """Grade hard task using weighted policy-sensitive components.
    Args:
        action: Agent action for hard task case.
        ground_truth: Expected routing and urgency intent.
    Returns:
        Deterministic reward result in [0.0, 1.0].
    """
    expected_label = _normalized_text(str(ground_truth.get("label", "urgent")))
    primary_route = _normalized_text(str(ground_truth.get("route_to", "safety")))
    secondary_route = _normalized_text(str(ground_truth.get("cc_route", "billing")))
    spam_penalty = float(ground_truth.get("penalize_spam", 0.2))

    normalized_route = _normalized_text(action.route_to)
    has_primary_route = _route_matches(normalized_route, primary_route)
    has_secondary_route = _route_matches(normalized_route, secondary_route)
    urgent_label = _normalized_text(action.label) == expected_label

    escalation_component = 0.4 if has_primary_route else 0.0
    routing_component = 0.3 if has_secondary_route else 0.0
    urgency_component = 0.3 if urgent_label else 0.0

    raw_score = escalation_component + routing_component + urgency_component
    if _normalized_text(action.label) == "spam":
        raw_score -= spam_penalty

    score_value = _clip_score(raw_score)
    breakdown = {
        "escalation_component": escalation_component,
        "routing_component": routing_component,
        "urgency_component": urgency_component,
        "spam_penalty": spam_penalty if _normalized_text(action.label) == "spam" else 0.0,
    }
    feedback = "Hard-task weighted policy grading completed."
    return RewardResult(score=score_value, breakdown=breakdown, feedback=feedback)
