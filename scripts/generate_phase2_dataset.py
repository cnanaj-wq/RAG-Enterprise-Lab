"""Génère le dataset documentaire Phase 2 dans data/seed/ + data/examples/
(déterministe, seed=142). Ne génère PAS les 5000 documents physiques."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rag_enterprise_lab.generation.dataset import generate_dataset
from rag_enterprise_lab.generation.document_dataset import (
    generate_document_dataset,
    write_document_dataset,
)

ORG_SEED = 42
DOC_SEED = 142


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    organization = generate_dataset(ORG_SEED)
    document_dataset = generate_document_dataset(
        DOC_SEED, organization, examples_dir=repo_root / "data" / "examples"
    )
    write_document_dataset(document_dataset, repo_root / "data" / "seed")

    examples = [e for e in document_dataset.manifest if e.generation_status.value == "EXAMPLE_GENERATED"]
    print(f"Manifest généré (seed={DOC_SEED}) : {len(document_dataset.manifest)} entrées")
    print(f"Anomalies : {len(document_dataset.anomalies)}")
    print(f"Conflits : {len(document_dataset.conflicts)}")
    print(f"Ground truth (Q&A) : {len(document_dataset.expected_answers)}")
    print(f"Documents physiques matérialisés : {len(examples)}")


if __name__ == "__main__":
    main()
