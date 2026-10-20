import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AuditLog

logger = logging.getLogger(__name__)


async def write_audit(
    db: AsyncSession,
    actor_label: str,
    tool_or_endpoint: str,
    outcome: str,
    request_id: str | None = None,
    metadata: str | None = None,
) -> None:
    try:
        log = AuditLog(
            actor_label=actor_label,
            tool_or_endpoint=tool_or_endpoint,
            outcome=outcome,
            request_id=request_id,
            metadata_json=metadata,
        )
        db.add(log)
        await db.commit()
    except Exception as exc:
        logger.warning("Audit write failed (continuing): %s", exc)
        await db.rollback()
