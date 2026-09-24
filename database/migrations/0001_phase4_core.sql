-- Phase 4 — PostgreSQL + pgvector core schema
-- Security invariant: authorization data is persisted here, but the LLM never
-- participates in an ALLOW/DENY decision.

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    logical_document_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_versions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id TEXT NOT NULL UNIQUE,
    logical_document_id BIGINT NOT NULL
        REFERENCES documents(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    document_type TEXT NOT NULL,
    domain TEXT NOT NULL,
    source_system TEXT NOT NULL,
    owner_employee_id TEXT NOT NULL,
    classification TEXT NOT NULL,
    version_label TEXT NOT NULL,
    status TEXT NOT NULL,
    authority_level TEXT NOT NULL,
    valid_from DATE,
    valid_to DATE,
    created_at TIMESTAMPTZ NOT NULL,
    approved_at TIMESTAMPTZ,
    signed_at TIMESTAMPTZ,
    supersedes_document_id TEXT,
    related_customer_id TEXT,
    related_supplier_id TEXT,
    related_employee_id TEXT,
    related_project_id TEXT,
    related_opportunity_id TEXT,
    related_expected_contract_id TEXT,
    contains_personal_data BOOLEAN NOT NULL DEFAULT FALSE,
    retention_policy TEXT NOT NULL,
    checksum TEXT NOT NULL,
    raw_object_key TEXT NOT NULL,
    processed_prefix TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_document_version_label UNIQUE (logical_document_id, version_label),
    CONSTRAINT fk_supersedes_document
        FOREIGN KEY (supersedes_document_id)
        REFERENCES document_versions(document_id)
        DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS document_acl (
    document_version_id BIGINT NOT NULL
        REFERENCES document_versions(id) ON DELETE CASCADE,
    group_name TEXT NOT NULL CHECK (btrim(group_name) <> ''),
    PRIMARY KEY (document_version_id, group_name)
);

CREATE TABLE IF NOT EXISTS chunks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_version_id BIGINT NOT NULL
        REFERENCES document_versions(id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    page_number INTEGER CHECK (page_number IS NULL OR page_number > 0),
    section_path TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    content TEXT NOT NULL CHECK (btrim(content) <> ''),
    content_tsv TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('simple', coalesce(content, ''))
    ) STORED,
    -- Phase 4 embedding contract. If the embedding model changes dimension,
    -- change this through a dedicated migration before loading production data.
    embedding VECTOR(1536),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_chunk_ordinal UNIQUE (document_version_id, ordinal)
);

CREATE TABLE IF NOT EXISTS audit_events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor_id TEXT,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    decision TEXT,
    reason TEXT,
    request_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_document_versions_logical
    ON document_versions(logical_document_id);
CREATE INDEX IF NOT EXISTS idx_document_versions_authority
    ON document_versions(logical_document_id, authority_level, valid_from, created_at);
CREATE INDEX IF NOT EXISTS idx_document_versions_customer
    ON document_versions(related_customer_id)
    WHERE related_customer_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_document_versions_employee
    ON document_versions(related_employee_id)
    WHERE related_employee_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_document_acl_group
    ON document_acl(group_name, document_version_id);

CREATE INDEX IF NOT EXISTS idx_chunks_version
    ON chunks(document_version_id);
CREATE INDEX IF NOT EXISTS idx_chunks_fts
    ON chunks USING GIN(content_tsv);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
    ON chunks USING hnsw (embedding vector_cosine_ops)
    WHERE embedding IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_audit_events_request
    ON audit_events(request_id)
    WHERE request_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_audit_events_resource
    ON audit_events(resource_type, resource_id, occurred_at DESC);

COMMENT ON TABLE document_acl IS
    'Deny-by-default ACL. A document version with no rows is not retrievable.';
COMMENT ON COLUMN chunks.embedding IS
    '1536-dimensional embedding used for semantic retrieval in Phase 4.';

COMMIT;
