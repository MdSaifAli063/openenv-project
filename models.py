"""Data models for the OpenEnv email triage environment."""

from typing import Literal

from pydantic import BaseModel


class EmailObservation(BaseModel):
    """Represents the email context visible to the agent at each step."""

    email_id: str
    subject: str
    body: str
    sender: str
    timestamp: str
    thread_history: list[str]
    task_id: str
    step_number: int
    total_emails: int


class TriageAction(BaseModel):
    """Represents the action chosen by the agent for an email."""

    label: Literal["urgent", "normal", "spam", "archive"]
    summary: str
    route_to: str


class RewardResult(BaseModel):
    """Represents deterministic grading output before reward shaping."""

    score: float
    breakdown: dict[str, float]
    feedback: str


class EnvironmentState(BaseModel):
    """Represents full internal environment state for debugging and evaluation."""

    task_id: str
    current_step: int
    total_steps: int
    done: bool
    action_history: list[TriageAction]
    reward_history: list[float]


class StepResult(BaseModel):
    """Represents the standardized output of environment step calls."""

    observation: EmailObservation
    reward: float
    done: bool
    info: dict[str, str | int | float | bool]


class ResetResult(BaseModel):
    """Represents the standardized output of environment reset calls."""

    observation: EmailObservation
    info: dict[str, str | int | float | bool]
