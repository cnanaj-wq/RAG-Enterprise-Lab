"""Règles de complétude documentaire : dossiers Client (Phase 0), Supplier et
HR Employee (Phase 2). Charge les YAML sous config/completeness/ — source de
vérité unique, jamais dupliquée dans le code."""

from pathlib import Path

import yaml
from pydantic import BaseModel

_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config" / "completeness"

_DOSSIER_FILES: dict[str, tuple[str, str]] = {
    "CLIENT": ("client.yml", "client_dossier"),
    "SUPPLIER": ("supplier.yml", "supplier_dossier"),
    "HR_EMPLOYEE": ("hr_employee.yml", "hr_employee_dossier"),
}


def load_mandatory_document_types(dossier_type: str) -> list[str]:
    filename, root_key = _DOSSIER_FILES[dossier_type]
    with open(_CONFIG_DIR / filename, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return list(data[root_key]["mandatory"])


class CompletenessResult(BaseModel):
    dossier_type: str
    related_id: str
    mandatory_types: list[str]
    present_types: list[str]
    missing_types: list[str]

    @property
    def is_complete(self) -> bool:
        return not self.missing_types

    @property
    def completeness_ratio(self) -> float:
        if not self.mandatory_types:
            return 1.0
        return len(self.present_types) / len(self.mandatory_types)


def compute_completeness(
    *,
    dossier_type: str,
    related_id: str,
    present_document_types: set[str],
) -> CompletenessResult:
    mandatory = load_mandatory_document_types(dossier_type)
    present = [t for t in mandatory if t in present_document_types]
    missing = [t for t in mandatory if t not in present_document_types]
    return CompletenessResult(
        dossier_type=dossier_type,
        related_id=related_id,
        mandatory_types=mandatory,
        present_types=present,
        missing_types=missing,
    )
