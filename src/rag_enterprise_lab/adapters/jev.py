from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TypedDecision:
    label: str
    confidence: float
    metadata: dict[str, object]

class JevDecisionPort(Protocol):
    async def classify(self, *, task: str, text: str, labels: list[str]) -> TypedDecision:
        ...

class DisabledJevAdapter:
    async def classify(self, *, task: str, text: str, labels: list[str]) -> TypedDecision:
        raise RuntimeError("Jev is disabled. Configure a remote adapter explicitly.")
