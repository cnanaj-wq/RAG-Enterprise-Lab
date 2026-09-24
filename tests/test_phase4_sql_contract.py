from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "database" / "migrations" / "0001_phase4_core.sql"
HYBRID = ROOT / "database" / "migrations" / "0002_phase4_hybrid_search.sql"


def _sql(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def test_core_schema_contains_required_phase4_tables_and_pgvector() -> None:
    sql = _sql(CORE)

    assert "create extension if not exists vector" in sql
    for table in (
        "documents",
        "document_versions",
        "document_acl",
        "chunks",
        "audit_events",
    ):
        assert f"create table if not exists {table}" in sql


def test_chunks_have_fts_vector_and_vector_indexes() -> None:
    sql = _sql(CORE)

    assert "embedding vector(1536)" in sql
    assert "using gin(content_tsv)" in sql
    assert "using hnsw (embedding vector_cosine_ops)" in sql


def test_acl_is_deny_by_default_contract() -> None:
    sql = _sql(CORE)

    assert "primary key (document_version_id, group_name)" in sql
    assert "no rows is not retrievable" in sql
    assert "default 'public'" not in sql


def test_hybrid_search_filters_acl_before_ranking() -> None:
    sql = _sql(HYBRID)

    authorized = sql.index("authorized as materialized")
    lexical = sql.index("lexical as")
    semantic = sql.index("semantic as")

    assert authorized < lexical
    assert authorized < semantic
    assert "from document_acl acl" in sql
    assert "acl.group_name = any(p_caller_groups)" in sql
    assert "cardinality(coalesce(p_caller_groups" in sql


def test_hybrid_search_is_not_security_definer_and_uses_rrf() -> None:
    sql = _sql(HYBRID)

    assert "security definer" not in sql
    assert "websearch_to_tsquery" in sql
    assert "<=> p_query_embedding" in sql
    assert "60.0 +" in sql
