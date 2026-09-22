"""Génère le dataset synthétique Phase 1 dans data/seed/ (déterministe, seed=42)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rag_enterprise_lab.generation.dataset import generate_dataset, write_dataset

SEED = 42


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    out_dir = repo_root / "data" / "seed"
    dataset = generate_dataset(SEED)
    write_dataset(dataset, out_dir)
    print(f"Dataset généré (seed={SEED}) dans {out_dir}")
    print(f"employees={len(dataset.employees)} clients={len(dataset.clients)} "
          f"prospects={len(dataset.prospects)} partners={len(dataset.partners)} "
          f"suppliers={len(dataset.suppliers)} projects={len(dataset.projects)} "
          f"opportunities={len(dataset.opportunities)} "
          f"identity_groups={len(dataset.identity_groups)}")


if __name__ == "__main__":
    main()
