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
