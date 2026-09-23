"""Suivi du traitement physique d'un document (Phase 3) : statut, checksum
réel vs placeholder, quarantaine, audit. Distinct du `DocumentManifestEntry`
(métadonnées déclaratives Phase 2) — un `ProcessingRecord` décrit ce qui
s'est *réellement* passé lors de la génération/upload/parsing."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ProcessingStatus(StrEnum):
    PLANNED = "PLANNED"
    GENERATING = "GENERATING"
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    QUARANTINED = "QUARANTINED"
    FAILED = "FAILED"


class QuarantineReason(StrEnum):
    PARSING_ERROR = "PARSING_ERROR"
    OCR_LOW_CONFIDENCE = "OCR_LOW_CONFIDENCE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    CORRUPTED_FILE = "CORRUPTED_FILE"
    METADATA_MISMATCH = "METADATA_MISMATCH"
    CHECKSUM_MISMATCH = "CHECKSUM_MISMATCH"


class AuditEvent(BaseModel):
    document_id: str
    event_type: str
    timestamp: datetime
    details: dict[str, object] = Field(default_factory=dict)


class ProcessingRecord(BaseModel):
    document_id: str
    status: ProcessingStatus
    format: str
    raw_key: str | None = None

    # Le manifest Phase 2 ne porte qu'un placeholder. Le checksum réel n'est
    # calculé qu'une fois le document physique généré (voir docs/storage).
    expected_checksum_placeholder: str
    actual_checksum: str | None = None

    processed_keys: list[str] = Field(default_factory=list)
    quarantine_reason: QuarantineReason | None = None
    error_message: str | None = None
    updated_at: datetime
