"""
End-of-workflow finalizer.

Triggered after either interview consumer commits its update. We only
finalize once both interviews are done (and we have a CV score). The
`fully_completed` flag makes the operation idempotent.

final_score = cv*0.3 + hr*0.3 + tech*0.4
(HR/tech are 0-10 → scaled to 0-100 before mixing with cv which is 0-100.)
"""

from __future__ import annotations

import logging

from .notifier import notify_user
from .profile_db import update_final_score
from .workflow_completed_publisher import publish_workflow_completed
from .workflow_state import load_state, merge_state

logger = logging.getLogger(__name__)


def _normalize_interview_score(raw: float | int | None) -> int | None:
    """HR/tech analyzers return 1-10; we rescale to 0-100 for blending."""
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value <= 10:
        value = value * 10
    return max(0, min(100, round(value)))


def _compute_final_score(cv: int | None, hr: int | None, tech: int | None) -> int:
    """Weighted blend. Missing components contribute 0 — caller decides whether
    to call this only when all three are present."""
    cv_v = cv if cv is not None else 0
    hr_v = hr if hr is not None else 0
    tech_v = tech if tech is not None else 0
    return round(cv_v * 0.3 + hr_v * 0.3 + tech_v * 0.4)


async def maybe_finalize_workflow(user_id: str) -> None:
    state = await load_state(user_id)
    if state.get("fully_completed"):
        return  # already finalized — idempotent.

    if not (state.get("hr_completed") and state.get("tech_completed")):
        return  # waiting for the other half.

    cv_score = state.get("cv_score")
    hr_score = _normalize_interview_score(state.get("hr_score"))
    tech_score = _normalize_interview_score(state.get("tech_score"))
    final_score = _compute_final_score(cv_score, hr_score, tech_score)

    await merge_state(
        user_id,
        {
            "fully_completed": True,
            "final_score": final_score,
            "current_node": "workflow_completed",
        },
    )

    await update_final_score(user_id, final_score)
    await publish_workflow_completed(
        user_id=user_id,
        final_score=final_score,
        cv_score=cv_score,
        hr_score=hr_score,
        tech_score=tech_score,
    )
    await notify_user(
        user_id,
        event_type="workflow.completed",
        payload={"final_score": final_score, "message": "Your career assessment is complete!"},
    )
    logger.info("Workflow finalized for %s (final_score=%d).", user_id, final_score)
