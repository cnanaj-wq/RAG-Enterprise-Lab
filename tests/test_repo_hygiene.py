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

FORBIDDEN_LOCAL_DIRS = [
    "data/raw",
    "data/processed",
    "data/archive",
    "data/quarantine",
    "documents",
    "embeddings",
    "vectorstore",
]

# Volume local Phase 1 (data/seed/) : doit rester très inférieur à 100 Mo.
MAX_SEED_DIR_BYTES = 5 * 1024 * 1024


def test_no_secrets_in_generated_seed_data():
    seed_dir = REPO_ROOT / "data" / "seed"
    assert seed_dir.exists(), "run scripts/generate_phase1_dataset.py first"
    for path in seed_dir.rglob("*.json"):
        content = path.read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            assert not pattern.search(content), f"potential secret found in {path}"


def test_generated_seed_manifest_has_no_credentials():
    manifest_path = REPO_ROOT / "data" / "seed" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    serialized = json.dumps(manifest).lower()
    for forbidden in ("password", "api_key", "secret", "token"):
        assert forbidden not in serialized


def test_no_large_local_corpus():
    for rel_dir in FORBIDDEN_LOCAL_DIRS:
        directory = REPO_ROOT / rel_dir
        if directory.exists():
            files = list(directory.rglob("*"))
            assert not any(f.is_file() for f in files), f"local corpus detected in {rel_dir}"


def test_seed_dataset_volume_is_lightweight():
    seed_dir = REPO_ROOT / "data" / "seed"
    total_bytes = sum(f.stat().st_size for f in seed_dir.rglob("*") if f.is_file())
    assert total_bytes < MAX_SEED_DIR_BYTES
