"""Inference runner for the OpenEnv email triage environment."""

import argparse
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parent
SERVER_DIR = ROOT_DIR / "server"

for import_path in (str(SERVER_DIR), str(ROOT_DIR)):
    if import_path not in sys.path:
        sys.path.insert(0, import_path)

from environment import EmailTriageEnv
from models import EmailObservation, TriageAction

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
API_KEY = HF_TOKEN or os.getenv("API_KEY")


LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

MAX_STEPS = 10
TEMPERATURE = 0.2
MAX_TOKENS = 200
FALLBACK_ACTION = {
    "label": "normal",
    "summary": "Unable to parse response",
    "route_to": "general",
}

TASK_MAP = {
    "1": "task_easy",
    "2": "task_medium",
    "3": "task_hard",
}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.
    Returns:
        Parsed argparse namespace.
    """
    parser = argparse.ArgumentParser(description="Run OpenEnv email triage inference.")
    parser.add_argument(
        "--task",
        default="all",
        choices=["1", "2", "3", "all"],
        help="Task selection: 1, 2, 3, or all.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Optional model override. Falls back to MODEL_NAME environment variable.",
    )
    return parser.parse_args()


def validate_runtime_config(model_name: str | None) -> str:
    """Validate required API runtime configuration.
    Args:
        model_name: Optional model name from CLI override.
    Returns:
        Effective model name.
    Raises:
        ValueError: If required runtime settings are missing.
    """
    if not API_BASE_URL or API_BASE_URL == "your-active-url":
        raise ValueError("Missing API_BASE_URL environment variable.")
    if not API_KEY:
        raise ValueError("Missing HF_TOKEN or API_KEY environment variable.")

    effective_model = model_name or MODEL_NAME
    if not effective_model or effective_model == "your-active-model":
        raise ValueError("Missing MODEL_NAME environment variable or --model override.")
    return effective_model


def build_prompt(observation: EmailObservation, history: list[str]) -> str:
    """Build model prompt from current observation and recent history.
    Args:
        observation: Current observation payload.
        history: Episode history lines.
    Returns:
        Prompt string for inference.
    """
    recent_history = "\n".join(history[-5:]) if history else "None"
    observation_block = (
        f"email_id: {observation.email_id}\n"
        f"subject: {observation.subject}\n"
        f"sender: {observation.sender}\n"
        f"timestamp: {observation.timestamp}\n"
        f"body: {observation.body}\n"
        f"thread_history: {observation.thread_history}\n"
        f"task_id: {observation.task_id}\n"
        f"step_number: {observation.step_number}\n"
        f"total_emails: {observation.total_emails}"
    )

    return (
        "You are an email triage assistant. Choose one action with fields: "
        "label, summary, route_to. Allowed labels are urgent, normal, spam, archive. "
        "Route using general, billing, safety, support, or engineering when possible.\n\n"
        f"Recent history:\n{recent_history}\n\n"
        f"Current observation:\n{observation_block}\n\n"
        "Respond with either JSON or a text line containing label, summary, and route_to."
    )


def strip_action_prefixes(response_text: str) -> str:
    """Remove common textual prefixes from model output before parsing.
    Args:
        response_text: Raw model output.
    Returns:
        Cleaned model output.
    """
    cleaned = response_text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    cleaned = re.sub(r"^(next\s+action|action)\s*:\s*", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def parse_text_action(cleaned_text: str) -> dict[str, str]:
    """Parse action from free-form text using regex patterns.
    Args:
        cleaned_text: Normalized model text.
    Returns:
        Parsed action dict fields when available.
    """
    result: dict[str, str] = {}

    label_match = re.search(
        r"(?:\"label\"|label)\s*[:=]\s*\"?(urgent|normal|spam|archive)\"?",
        cleaned_text,
        flags=re.IGNORECASE,
    )
    if label_match:
        result["label"] = label_match.group(1).lower()

    route_match = re.search(
        r"(?:\"route_to\"|route_to|route)\s*[:=]\s*\"?([a-zA-Z0-9_\-/ ]+)\"?",
        cleaned_text,
        flags=re.IGNORECASE,
    )
    if route_match:
        result["route_to"] = route_match.group(1).strip().lower()

    summary_match = re.search(
        r"(?:\"summary\"|summary)\s*[:=]\s*\"?([^\"\n]+)\"?",
        cleaned_text,
        flags=re.IGNORECASE,
    )
    if summary_match:
        result["summary"] = summary_match.group(1).strip()

    return result


def parse_action_response(response_text: str) -> TriageAction:
    """Parse a model response into a TriageAction with deterministic fallback.
    Args:
        response_text: Raw model response content.
    Returns:
        Parsed TriageAction or fallback action.
    """
    cleaned_text = strip_action_prefixes(response_text)
    parsed_payload: dict[str, Any] = {}

    json_start = cleaned_text.find("{")
    json_end = cleaned_text.rfind("}")
    if json_start != -1 and json_end != -1 and json_end > json_start:
        candidate = cleaned_text[json_start : json_end + 1]
        try:
            loaded = json.loads(candidate)
            if isinstance(loaded, dict):
                parsed_payload = loaded
        except json.JSONDecodeError:
            parsed_payload = {}

    if not parsed_payload:
        parsed_payload = parse_text_action(cleaned_text)

    fallback_copy = dict(FALLBACK_ACTION)
    fallback_copy.update(parsed_payload)

    try:
        return TriageAction.model_validate(fallback_copy)
    except Exception:
        return TriageAction.model_validate(FALLBACK_ACTION)


def run_episode(client: OpenAI, model_name: str, task_id: str) -> tuple[float, int]:
    """Run one task episode and return score and step count.
    Args:
        client: OpenAI client instance.
        model_name: Model identifier.
        task_id: Task identifier to run.
    Returns:
        Tuple of (episode_score, steps_taken).
    """
    env = EmailTriageEnv(task_id=task_id)
    reset_result = env.reset()
    observation = reset_result.observation

    print(f"Episode: {task_id}")

    history: list[str] = []
    total_reward = 0.0
    steps_taken = 0

    for step in range(1, MAX_STEPS + 1):
        prompt = build_prompt(observation, history)

        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You triage professional emails using label, summary, and "
                            "route_to."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                stream=False,
            )
            response_text = completion.choices[0].message.content or ""
        except Exception as exc:
            print(f"Model request failed ({exc}). Using fallback action.")
            response_text = ""

        action = parse_action_response(response_text)
        step_result = env.step(action)

        steps_taken = step
        total_reward += step_result.reward

        action_text = f"label={action.label}, route={action.route_to}"
        history_line = f"Step {step}: {action_text} -> reward {step_result.reward:+.2f}"
        history.append(history_line)
        print(history_line)

        observation = step_result.observation
        if step_result.done:
            break

    episode_score = total_reward / max(steps_taken, 1)
    print(f"Final score: {episode_score:.2f}\n")
    return episode_score, steps_taken


def print_score_table(results: list[tuple[str, float, int]]) -> None:
    """Print a deterministic score table.
    Args:
        results: List of tuples (task_id, score, steps).
    """
    print("=== SCORE TABLE ===")
    print("Task         Score    Steps")
    for task_id, score, steps in results:
        print(f"{task_id:<12} {score:>5.2f}    {steps}")

    mean_score = sum(score for _, score, _ in results) / len(results) if results else 0.0
    print(f"Mean         {mean_score:>5.2f}")


def main() -> None:
    """Entrypoint for running inference across selected tasks."""
    args = parse_args()

    try:
        effective_model = validate_runtime_config(args.model)
    except ValueError as error:
        print(str(error))
        raise SystemExit(1) from error

    client = OpenAI(
        base_url=API_BASE_URL,
        api_key=API_KEY,
    )

    task_ids = [TASK_MAP[args.task]] if args.task in TASK_MAP else list(TASK_MAP.values())

    score_rows: list[tuple[str, float, int]] = []
    for task_id in task_ids:
        score, steps = run_episode(client, effective_model, task_id)
        score_rows.append((task_id, score, steps))

    print_score_table(score_rows)


if __name__ == "__main__":
    main()
