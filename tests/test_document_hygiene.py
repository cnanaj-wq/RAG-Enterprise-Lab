import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"BEGIN (RSA|EC|OPENSSH) PRIVATE KEY"),
    re.compile(r"password\s*=\s*['\"][^'\"]+['\"]"),
]

# Volume total attendu très inférieur à 100 Mo (limite Phase 2).
MAX_REPO_DATA_BYTES = 20 * 1024 * 1024
MAX_EXAMPLE_DOCUMENTS = 50
MANUAL_DEMO_IDS = {"DOC-01346"}


def test_no_secrets_in_document_seed_files():
    seed_dir = REPO_ROOT / "data" / "seed"
    for filename in (
        "document_manifest.json",
        "document_anomalies.json",
        "document_conflicts.json",
        "document_expected_answers.json",
    ):
        path = seed_dir / filename
        assert path.exists(), f"run scripts/generate_phase2_dataset.py first ({filename} missing)"
        content = path.read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            assert not pattern.search(content), f"potential secret found in {filename}"


def test_no_secrets_in_example_documents():
    examples_dir = REPO_ROOT / "data" / "examples"
    for path in examples_dir.glob("*.md"):
        content = path.read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            assert not pattern.search(content), f"potential secret found in {path.name}"


def test_no_large_document_corpus_locally():
    """Aucun fichier bureautique (pdf/docx/xlsx/pptx) ne doit exister
    localement — seuls JSON/YAML/CSV/Markdown sont autorisés (voir CLAUDE.md
    Phase 2, section LOCAL STORAGE)."""
    forbidden_extensions = {".pdf", ".docx", ".xlsx", ".pptx"}
    for path in (REPO_ROOT / "data").rglob("*"):
        if path.is_file():
            assert path.suffix.lower() not in forbidden_extensions, f"forbidden office file: {path}"


def test_max_50_physical_example_documents():
    examples_dir = REPO_ROOT / "data" / "examples"
    files = list(examples_dir.glob("*.md"))
    assert 0 < len(files) <= MAX_EXAMPLE_DOCUMENTS


def test_manifest_generation_status_matches_physical_examples():
    manifest_path = REPO_ROOT / "data" / "seed" / "document_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    examples_dir = REPO_ROOT / "data" / "examples"
    physical_ids = {p.stem for p in examples_dir.glob("*.md")}
    generated_ids = {
        e["document_id"] for e in manifest if e["generation_status"] == "EXAMPLE_GENERATED"
    }
    # DOC-01346 is an explicit hand-authored Phase 4 demo fixture rather than
    # an output of the Phase 2 example generator.
    assert MANUAL_DEMO_IDS <= physical_ids
    assert generated_ids | MANUAL_DEMO_IDS == physical_ids
    assert len(physical_ids) <= MAX_EXAMPLE_DOCUMENTS


def test_total_repository_data_volume_under_limit():
    total_bytes = sum(f.stat().st_size for f in (REPO_ROOT / "data").rglob("*") if f.is_file())
    assert total_bytes < MAX_REPO_DATA_BYTES
