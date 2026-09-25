from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "scripts" / "demo_rag_enterprise.py"
SHORTCUTS = ROOT / "scripts" / "test_phase4_shortcuts.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def test_authority_resolution_is_acl_scoped() -> None:
    text = _text(DEMO)
    fetch_authority = text[text.index("def fetch_authority"):text.index("def build_context")]

    assert "from document_acl acl" in fetch_authority
    assert "acl.group_name = any" in fetch_authority
    assert "groups: list[str]" in fetch_authority


def test_business_shortcuts_are_acl_scoped() -> None:
    text = _text(SHORTCUTS)
    fetch_documents = text[
        text.index("def fetch_client_documents"):text.index("def resolve_authority")
    ]

    assert "from document_acl acl" in fetch_documents
    assert "acl.group_name = any" in fetch_documents
    assert "groups: list[str]" in fetch_documents


def test_unified_demo_routes_shortcuts_before_rag() -> None:
    text = _text(DEMO)

    assert "if decision.shortcut:" in text
    assert "run_shortcut(" in text
    assert "test_phase4_shortcuts.py" in text
    assert "test_phase4_signatures.py" in text


SIGNATURES = ROOT / "scripts" / "test_phase4_signatures.py"
SHORTCUTS_CONFIG = ROOT / "config" / "shortcuts.yml"


def test_signature_shortcut_requires_authorized_group() -> None:
    text = _text(SIGNATURES)
    config = _text(SHORTCUTS_CONFIG)

    assert "def authorize(groups: list[str]) -> bool:" in text
    assert "restricted_message" in text
    assert "--group" in text
    assert "rag_sales" in config
    assert "rag_finance" in config
    assert "rag_legal" in config
    assert "rag_executive" in config
