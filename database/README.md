# Phase 4 database layer

PostgreSQL is the calculable source of truth for document registry, versions,
ACLs, chunks and audit. pgvector adds semantic retrieval; PostgreSQL full-text
search provides lexical retrieval.

## Migration order

1. `database/migrations/0001_phase4_core.sql`
2. `database/migrations/0002_phase4_hybrid_search.sql`

The migrations are intentionally plain SQL: they remain inspectable, portable
and executable without introducing a migration framework before it is needed.

## Data model

- `documents`: stable logical document families.
- `document_versions`: physical/business versions from the Phase 2 manifest.
- `document_acl`: allowed identity groups per version. **No ACL row = no access**.
- `chunks`: normalized text chunks, FTS vector and optional pgvector embedding.
- `audit_events`: retrieval/authorization/audit trail.

`document_versions.document_id` preserves the existing `DOC-xxxxx` identity.
`documents.logical_document_id` identifies the root of a version chain. During
seed loading, the logical id is the root reached by following `supersedes`; a
standalone document uses its own `document_id`.

## Embedding contract

Phase 4 starts with `VECTOR(1536)`. This is a storage contract, not a model
choice. The embedding provider remains behind an adapter. If another dimension
is selected, a dedicated migration must change the column/function signature
before production embeddings are loaded.

## Security invariant

The retrieval function implements:

`Identity groups -> ACL filter -> lexical/vector candidates -> RRF -> caller`

The `authorized AS MATERIALIZED` CTE is intentional. Unauthorized chunks are
removed before lexical or vector ranking. The function is SECURITY INVOKER and
there is no LLM/Jev call anywhere in the authorization path.

A caller with no groups, or a document version with no ACL rows, receives no
candidate rows.

## Hybrid ranking

`search_authorized_chunks` combines:

- PostgreSQL FTS using `websearch_to_tsquery('simple', ...)`;
- pgvector cosine distance using `<=>`;
- Reciprocal Rank Fusion (RRF), constant 60.

Each channel contributes up to `4 * p_limit` candidates before fusion. This is
deliberately simple, deterministic and explainable for the lab. Evaluation in a
later phase can tune candidate depth and RRF parameters.

## Indexes

- GIN on `chunks.content_tsv`;
- HNSW cosine index on non-null `chunks.embedding`;
- B-tree indexes for ACL, version lineage, business relations and audit.

The schema is now exercised by the Phase 4 demo against a dedicated PostgreSQL
database with pgvector enabled. The interactive demo uses a controlled subset of
the 5,000-document catalog for speed and cost control; the same loader can scale
to the full manifest for performance and retrieval benchmarking.
