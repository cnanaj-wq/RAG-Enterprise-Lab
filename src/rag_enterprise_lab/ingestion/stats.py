from pydantic import BaseModel

from rag_enterprise_lab.domain.processing import AuditEvent, ProcessingRecord


class RunStats(BaseModel):
    processed: int = 0
    uploaded: int = 0
    skipped: int = 0
    conflicts: int = 0
    quarantined: int = 0
    failed: int = 0
    bytes_uploaded: int = 0
    temp_disk_current_mb: float = 0.0
    temp_disk_peak_mb: float = 0.0
    duration_seconds: float = 0.0


class RunResult(BaseModel):
    stats: RunStats
    records: list[ProcessingRecord]
    audit_events: list[AuditEvent]
