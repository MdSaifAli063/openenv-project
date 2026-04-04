"""Core OpenEnv email triage environment implementation."""

from typing import cast

from pydantic import ValidationError

from .graders import grade_easy, grade_hard, grade_medium
from ..models import (
    EmailObservation,
    EnvironmentState,
    ResetResult,
    RewardResult,
    StepResult,
    TriageAction,
)
from .tasks import get_task_definition


class EmailTriageEnv:
    """Deterministic email triage environment implementing reset, step, and state."""

    def __init__(self, task_id: str) -> None:
        """Initialize environment with a selected task.
        Args:
            task_id: Task identifier such as task_easy, task_medium, or task_hard.
        """
        self.task_id = task_id
        self._task_definition = get_task_definition(task_id)
        self._emails = cast(list[dict[str, object]], self._task_definition.get("emails", []))
        self._ground_truth = cast(
            list[dict[str, object]], self._task_definition.get("ground_truth", [])
        )

        self._current_index = 0
        self._current_step = 0
        self._done = False
        self._max_steps = 10
        self._action_history: list[TriageAction] = []
        self._reward_history: list[float] = []
        self._base_score_history: list[float] = []

    def reset(self) -> ResetResult:
        """Reset episode state and return the first observation.
        Returns:
            ResetResult containing first observation and metadata.
        """
        self._task_definition = get_task_definition(self.task_id)
        self._emails = cast(list[dict[str, object]], self._task_definition.get("emails", []))
        self._ground_truth = cast(
            list[dict[str, object]], self._task_definition.get("ground_truth", [])
        )

        self._current_index = 0
        self._current_step = 0
        self._done = False
        self._action_history = []
        self._reward_history = []
        self._base_score_history = []

        first_observation = self._build_observation(self._current_index)
        return ResetResult(
            observation=first_observation,
            info={
                "task_id": self.task_id,
                "step": self._current_step,
            },
        )

    def step(self, action: TriageAction) -> StepResult:
        """Apply an action and return StepResult.
        Args:
            action: Proposed triage action.
        Returns:
            StepResult with next observation, reward, done flag, and metadata.
        """
        if self._done:
            return StepResult(
                observation=self._terminal_observation(),
                reward=0.0,
                done=True,
                info={
                    "task_id": self.task_id,
                    "step": self._current_step,
                    "already_done": True,
                },
            )

        try:
            validated_action = TriageAction.model_validate(action)
        except ValidationError as validation_error:
            self._current_step += 1
            self._reward_history.append(0.0)
            self._done = self._current_step >= self._max_steps
            return StepResult(
                observation=self._build_observation(self._current_index),
                reward=0.0,
                done=self._done,
                info={
                    "task_id": self.task_id,
                    "step": self._current_step,
                    "validation_error": str(validation_error),
                },
            )

        base_result = self._grade_current_step(validated_action)
        base_score = base_result.score

        self._action_history.append(validated_action)
        self._base_score_history.append(base_score)
        self._current_step += 1

        penalties = self._compute_penalties(validated_action)
        trajectory_bonus = self._compute_trajectory_bonus()
        final_reward = self._clip_reward(
            base_score - (self._current_step * 0.01) + trajectory_bonus - penalties
        )

        self._reward_history.append(final_reward)

        if self._current_index < len(self._emails):
            self._current_index += 1

        all_emails_processed = self._current_index >= len(self._emails)
        self._done = all_emails_processed or self._current_step >= self._max_steps

        next_observation = (
            self._terminal_observation()
            if self._done
            else self._build_observation(self._current_index)
        )

        info = {
            "task_id": self.task_id,
            "step": self._current_step,
            "base_score": round(base_score, 4),
            "penalties": round(penalties, 4),
            "trajectory_bonus": round(trajectory_bonus, 4),
        }
        return StepResult(
            observation=next_observation,
            reward=final_reward,
            done=self._done,
            info=info,
        )

    def state(self) -> EnvironmentState:
        """Return read-only snapshot of full internal state.
        Returns:
            EnvironmentState with progress and history.
        """
        return EnvironmentState(
            task_id=self.task_id,
            current_step=self._current_step,
            total_steps=self._max_steps,
            done=self._done,
            action_history=list(self._action_history),
            reward_history=list(self._reward_history),
        )

    def _build_observation(self, email_index: int) -> EmailObservation:
        """Build observation for the email at a given index.
        Args:
            email_index: Zero-based email index.
        Returns:
            EmailObservation for the selected email or terminal placeholder.
        """
        if not self._emails:
            return self._terminal_observation()

        safe_index = min(max(email_index, 0), len(self._emails) - 1)
        email_payload = self._emails[safe_index]

        return EmailObservation(
            email_id=str(email_payload.get("email_id", "")),
            subject=str(email_payload.get("subject", "")),
            body=str(email_payload.get("body", "")),
            sender=str(email_payload.get("sender", "")),
            timestamp=str(email_payload.get("timestamp", "")),
            thread_history=[str(item) for item in email_payload.get("thread_history", [])],
            task_id=self.task_id,
            step_number=self._current_step,
            total_emails=len(self._emails),
        )

    def _terminal_observation(self) -> EmailObservation:
        """Build terminal observation returned when episode is complete.
        Returns:
            Terminal EmailObservation payload.
        """
        return EmailObservation(
            email_id="terminal",
            subject="Episode complete",
            body="No further emails remain for this task.",
            sender="system",
            timestamp="",
            thread_history=[],
            task_id=self.task_id,
            step_number=self._current_step,
            total_emails=len(self._emails),
        )

    def _grade_current_step(self, action: TriageAction) -> RewardResult:
        """Select deterministic grader based on task and current progress.
        Args:
            action: Validated action for the current step.
        Returns:
            RewardResult from task-specific grader.
        """
        if not self._ground_truth:
            return RewardResult(
                score=0.0,
                breakdown={"missing_ground_truth": 1.0},
                feedback="Missing ground truth for task.",
            )

        if self.task_id == "task_easy":
            truth = self._ground_truth[min(self._current_index, len(self._ground_truth) - 1)]
            return grade_easy(action, truth)

        if self.task_id == "task_medium":
            actions_so_far = self._action_history + [action]
            truths_so_far = self._ground_truth[: len(actions_so_far)]
            return grade_medium(actions_so_far, truths_so_far)

        truth = self._ground_truth[min(self._current_index, len(self._ground_truth) - 1)]
        return grade_hard(action, truth)

    def _compute_penalties(self, action: TriageAction) -> float:
        """Compute deterministic penalties according to reward policy.
        Args:
            action: Validated action for the step.
        Returns:
            Total penalty value for current step.
        """
        penalty_total = 0.0

        summary_too_short = len(action.summary.strip()) < 10
        if action.label == "archive" and summary_too_short:
            penalty_total += 0.5

        if self._is_repeated_action_pattern(action):
            penalty_total += 0.3

        return penalty_total

    def _compute_trajectory_bonus(self) -> float:
        """Return trajectory bonus when episode completion quality is high.
        Returns:
            0.2 when mean base score is above threshold at completion, else 0.0.
        """
        if not self._base_score_history:
            return 0.0

        all_emails_done_after_step = self._current_index + 1 >= len(self._emails)
        if not all_emails_done_after_step:
            return 0.0

        mean_base = sum(self._base_score_history) / len(self._base_score_history)
        return 0.2 if mean_base > 0.8 else 0.0

    def _is_repeated_action_pattern(self, action: TriageAction) -> bool:
        """Detect whether same action appears three times consecutively.
        Args:
            action: Current action.
        Returns:
            True when repeated label and route occur three times in a row.
        """
        if len(self._action_history) < 2:
            return False

        previous_action = self._action_history[-1]
        older_action = self._action_history[-2]

        return (
            previous_action.label == older_action.label == action.label
            and previous_action.route_to.strip().lower()
            == older_action.route_to.strip().lower()
            == action.route_to.strip().lower()
        )

    def _clip_reward(self, reward_value: float) -> float:
        """Clip reward to the inclusive range [-1.0, 1.0].
        Args:
            reward_value: Raw reward value.
        Returns:
            Clipped reward.
        """
        return max(-1.0, min(1.0, reward_value))
