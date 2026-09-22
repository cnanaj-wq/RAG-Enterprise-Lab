"""Orchestrateur Phase 2 : construit le dataset documentaire complet
(manifest, anomalies, conflits, ground truth, exemples physiques) à partir
d'un seed unique et du dataset Phase 1, de façon déterministe et reproductible.
"""

import json
import random
from datetime import date
from pathlib import Path

from pydantic import BaseModel

from rag_enterprise_lab.domain.anomalies import AnomalyRecord
from rag_enterprise_lab.domain.conflicts import ConflictRecord
from rag_enterprise_lab.domain.documents import DocumentManifestEntry
from rag_enterprise_lab.domain.expected_answers import ExpectedAnswer
from rag_enterprise_lab.generation.anomaly_generator import (
    attach_conflict_anomalies,
    inject_anomalies,
)
from rag_enterprise_lab.generation.conflict_generator import generate_conflicts
from rag_enterprise_lab.generation.dataset import OrganizationDataset
from rag_enterprise_lab.generation.document_generator import generate_manifest
from rag_enterprise_lab.generation.example_documents import select_and_materialize_examples
from rag_enterprise_lab.generation.expected_answers_generator import generate_expected_answers
from rag_enterprise_lab.generation.version_chain_builder import link_versions_and_amendments

DOCUMENT_REFERENCE_DATE = date(2026, 9, 1)


class DocumentDataset(BaseModel):
    seed: int
    reference_date: date
    manifest: list[DocumentManifestEntry]
    anomalies: list[AnomalyRecord]
    conflicts: list[ConflictRecord]
    expected_answers: list[ExpectedAnswer]


def generate_document_dataset(
    seed: int,
    organization: OrganizationDataset,
    *,
    examples_dir: Path,
) -> DocumentDataset:
    rng = random.Random(seed)

    manifest = generate_manifest(
        rng,
        employees=organization.employees,
        clients=organization.clients,
        suppliers=organization.suppliers,
        projects=organization.projects,
        opportunities=organization.opportunities,
        expected_contracts=organization.expected_contracts,
        reference_date=DOCUMENT_REFERENCE_DATE,
    )
    link_versions_and_amendments(manifest)

    conflicts, conflict_counter = generate_conflicts(manifest, organization.clients)

    anomalies, anomaly_counter = inject_anomalies(
        rng, manifest, organization.expected_contracts, reference_date=DOCUMENT_REFERENCE_DATE
    )
    anomalies += attach_conflict_anomalies(anomaly_counter, conflicts)
    _ = conflict_counter  # conservé pour traçabilité, non réutilisé ici

    select_and_materialize_examples(manifest, conflicts, anomalies, out_dir=examples_dir)

    expected_answers = generate_expected_answers(
        conflicts=conflicts,
        manifest=manifest,
        clients=organization.clients,
        expected_contracts=organization.expected_contracts,
    )

    return DocumentDataset(
        seed=seed,
        reference_date=DOCUMENT_REFERENCE_DATE,
        manifest=manifest,
        anomalies=anomalies,
        conflicts=conflicts,
        expected_answers=expected_answers,
    )


def write_document_dataset(dataset: DocumentDataset, seed_dir: Path) -> None:
    seed_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "document_manifest.json": [e.model_dump(mode="json") for e in dataset.manifest],
        "document_anomalies.json": [a.model_dump(mode="json") for a in dataset.anomalies],
        "document_conflicts.json": [c.model_dump(mode="json") for c in dataset.conflicts],
        "document_expected_answers.json": [
            a.model_dump(mode="json") for a in dataset.expected_answers
        ],
    }
    for filename, payload in files.items():
        (seed_dir / filename).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
