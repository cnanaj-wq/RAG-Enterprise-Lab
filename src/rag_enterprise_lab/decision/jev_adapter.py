from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Intent(StrEnum):
    CONTRACT = "CONTRACT"
    CONFLICTS = "CONFLICTS"
    SOURCES = "SOURCES"
    COMPLETENESS = "COMPLETENESS"
    SIGNATURES_MONTH = "SIGNATURES_MONTH"
    GENERAL_RAG = "GENERAL_RAG"
    UNKNOWN = "UNKNOWN"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class JevDecision(BaseModel):
    intent: Intent
    shortcut: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    risk: RiskLevel
    needs_retrieval: bool
    needs_authority_resolution: bool
    reason: str


def decide(text: str) -> JevDecision:
    """
    Local deterministic stand-in for the future Jev adapter.

    Jev will later replace this routing/scoring logic, but the output contract
    remains stable.
    """
    normalized = text.strip().lower()

    if normalized.startswith("/contrat"):
        return JevDecision(
            intent=Intent.CONTRACT,
            shortcut="/contrat",
            confidence=0.99,
            risk=RiskLevel.MEDIUM,
            needs_retrieval=True,
            needs_authority_resolution=True,
            reason="Explicit contract shortcut",
        )

    if normalized.startswith("/conflits"):
        return JevDecision(
            intent=Intent.CONFLICTS,
            shortcut="/conflits",
            confidence=0.99,
            risk=RiskLevel.HIGH,
            needs_retrieval=True,
            needs_authority_resolution=True,
            reason="Explicit conflict shortcut",
        )

    if normalized.startswith("/sources"):
        return JevDecision(
            intent=Intent.SOURCES,
            shortcut="/sources",
            confidence=0.99,
            risk=RiskLevel.LOW,
            needs_retrieval=True,
            needs_authority_resolution=False,
            reason="Explicit source shortcut",
        )

    if normalized.startswith("/completude"):
        return JevDecision(
            intent=Intent.COMPLETENESS,
            shortcut="/completude",
            confidence=0.99,
            risk=RiskLevel.MEDIUM,
            needs_retrieval=False,
            needs_authority_resolution=False,
            reason="Explicit completeness shortcut",
        )

    if normalized.startswith("/signatures mois"):
        return JevDecision(
            intent=Intent.SIGNATURES_MONTH,
            shortcut="/signatures mois",
            confidence=0.99,
            risk=RiskLevel.MEDIUM,
            needs_retrieval=False,
            needs_authority_resolution=False,
            reason="Explicit signatures shortcut",
        )

    if "contrat" in normalized or "contract" in normalized:
        return JevDecision(
            intent=Intent.GENERAL_RAG,
            shortcut=None,
            confidence=0.85,
            risk=RiskLevel.MEDIUM,
            needs_retrieval=True,
            needs_authority_resolution=True,
            reason="Contract-related natural-language query",
        )

    if normalized:
        return JevDecision(
            intent=Intent.GENERAL_RAG,
            shortcut=None,
            confidence=0.70,
            risk=RiskLevel.LOW,
            needs_retrieval=True,
            needs_authority_resolution=False,
            reason="Generic RAG query",
        )

    return JevDecision(
        intent=Intent.UNKNOWN,
        shortcut=None,
        confidence=0.0,
        risk=RiskLevel.LOW,
        needs_retrieval=False,
        needs_authority_resolution=False,
        reason="Empty input",
    )
