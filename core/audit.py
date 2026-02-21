"""
Simple audit trail: log who updated applicant (or other) status.
"""
import logging

logger = logging.getLogger(__name__)


def log_status_change(model_name, instance_id, old_status, new_status, user, extra=None):
    extra = extra or {}
    logger.info(
        "status_change model=%s id=%s old=%s new=%s user_id=%s",
        model_name,
        instance_id,
        old_status,
        new_status,
        getattr(user, "id", None),
        extra=extra,
    )
