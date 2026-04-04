"""Task definitions and static email data for the OpenEnv email triage environment."""

TASK_EASY: dict[str, object] = {
    "task_id": "task_easy",
    "description": "Classify and route one unambiguous operational email.",
    "emails": [
        {
            "email_id": "easy-001",
            "subject": "Quarterly invoice available",
            "body": (
                "Hello Team, your Q1 invoice is now ready in the billing portal. "
                "Please confirm the purchase order number by Friday."
            ),
            "sender": "accounts@billing.vendor.example",
            "timestamp": "2026-03-25T09:15:00Z",
            "thread_history": [
                "Last month: requested invoice schedule for Q1 and Q2."
            ],
        }
    ],
    "ground_truth": [
        {
            "label": "normal",
            "route_to": "billing",
            "priority_weight": 1.0,
        }
    ],
}

TASK_MEDIUM: dict[str, object] = {
    "task_id": "task_medium",
    "description": "Triage five mixed-priority emails where cues are sometimes misleading.",
    "emails": [
        {
            "email_id": "med-001",
            "subject": "URGENT: Your account will be disabled in 30 minutes",
            "body": (
                "Click this external short link to keep your mailbox active. "
                "If you do not click now, your account will be deleted."
            ),
            "sender": "it-admin@secure-mail.example",
            "timestamp": "2026-03-26T07:08:00Z",
            "thread_history": [],
        },
        {
            "email_id": "med-002",
            "subject": "Can someone review production error spikes?",
            "body": (
                "We are seeing a 28% spike in checkout failures after the 06:10 UTC deploy. "
                "Please triage and assign on-call ownership immediately."
            ),
            "sender": "ops-manager@acme-enterprise.example",
            "timestamp": "2026-03-26T06:21:00Z",
            "thread_history": ["Pager alert opened at 06:18 UTC."],
        },
        {
            "email_id": "med-003",
            "subject": "RE: promo campaign winner list",
            "body": (
                "Subject line looks like a campaign thread, but this message confirms "
                "a customer reported duplicate card charges. Please review and respond."
            ),
            "sender": "care-escalations@acme-enterprise.example",
            "timestamp": "2026-03-26T11:42:00Z",
            "thread_history": ["Marketing team forwarded customer complaint for billing review."],
        },
        {
            "email_id": "med-004",
            "subject": "Safety escalation: charger overheating case #4812",
            "body": (
                "Customer reports visible smoke from charging dock during normal use. "
                "No injuries reported, but immediate safety review requested."
            ),
            "sender": "support-lead@acme-enterprise.example",
            "timestamp": "2026-03-26T10:03:00Z",
            "thread_history": ["Ticket severity raised from P2 to P1."],
        },
        {
            "email_id": "med-005",
            "subject": "FYI: April all-hands agenda",
            "body": (
                "Sharing the all-hands agenda draft. No action required unless you want "
                "to propose additional topics by Monday."
            ),
            "sender": "people-ops@acme-enterprise.example",
            "timestamp": "2026-03-26T14:25:00Z",
            "thread_history": [],
        },
    ],
    "ground_truth": [
        {
            "label": "spam",
            "route_to": "general",
            "priority_weight": 1.0,
        },
        {
            "label": "urgent",
            "route_to": "engineering",
            "priority_weight": 1.5,
        },
        {
            "label": "normal",
            "route_to": "billing",
            "priority_weight": 1.2,
        },
        {
            "label": "urgent",
            "route_to": "safety",
            "priority_weight": 1.6,
        },
        {
            "label": "archive",
            "route_to": "general",
            "priority_weight": 0.8,
        },
    ],
}

# Set to 2 later to expand hard-mode from one email to two emails.
HARD_TASK_EMAIL_COUNT: int = 1

HARD_TASK_EMAIL_POOL: list[dict[str, object]] = [
    {
        "email_id": "hard-001",
        "subject": "Formal complaint: unsafe device behavior and disputed charges",
        "body": (
            "I was charged twice for the replacement kit, and during testing the unit "
            "became hot enough to scorch the desk surface. I need billing correction "
            "and urgent safety follow-up today."
        ),
        "sender": "legal-customer@enterprise-client.example",
        "timestamp": "2026-03-26T08:33:00Z",
        "thread_history": [
            "Support asked customer to share photos; customer replied with incident details."
        ],
    },
    {
        "email_id": "hard-002",
        "subject": "Escalation follow-up: compliance and refund timeline",
        "body": (
            "Following up on the same incident, compliance team requests confirmation of "
            "safety escalation and billing refund timeline before we close the case."
        ),
        "sender": "procurement@enterprise-client.example",
        "timestamp": "2026-03-26T09:07:00Z",
        "thread_history": ["Legal requested cross-team response within 4 business hours."],
    },
]

HARD_TASK_GROUND_TRUTH_POOL: list[dict[str, object]] = [
    {
        "label": "urgent",
        "route_to": "safety",
        "cc_route": "billing",
        "penalize_spam": 0.2,
    },
    {
        "label": "urgent",
        "route_to": "safety",
        "cc_route": "billing",
        "penalize_spam": 0.2,
    },
]

TASK_HARD: dict[str, object] = {
    "task_id": "task_hard",
    "description": (
        "Handle an ambiguous complaint that requires safety escalation and billing context."
    ),
    "emails": HARD_TASK_EMAIL_POOL[:HARD_TASK_EMAIL_COUNT],
    "ground_truth": HARD_TASK_GROUND_TRUTH_POOL[:HARD_TASK_EMAIL_COUNT],
}

TASKS_BY_ID: dict[str, dict[str, object]] = {
    "task_easy": TASK_EASY,
    "task_medium": TASK_MEDIUM,
    "task_hard": TASK_HARD,
}


def get_task_definition(task_id: str) -> dict[str, object]:
    """Return a task definition by task_id.
    Args:
        task_id: Task identifier.
    Returns:
        Task definition dictionary.
    Raises:
        KeyError: If task_id is not defined.
    """
    if task_id not in TASKS_BY_ID:
        raise KeyError(f"Unknown task_id: {task_id}")
    return TASKS_BY_ID[task_id]


def list_task_ids() -> list[str]:
    """Return all supported task identifiers in deterministic order."""
    return ["task_easy", "task_medium", "task_hard"]
