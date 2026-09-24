-- Phase 4 — governed hybrid retrieval.
-- ACL filtering is deliberately materialized BEFORE lexical/vector ranking.
-- The function is SECURITY INVOKER (default) and never delegates authorization
-- to an LLM or decision model.

BEGIN;

CREATE OR REPLACE FUNCTION search_authorized_chunks(
    p_query_text TEXT,
    p_caller_groups TEXT[],
    p_query_embedding VECTOR(1536) DEFAULT NULL,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    chunk_id BIGINT,
    document_id TEXT,
    title TEXT,
    version_label TEXT,
    content TEXT,
    lexical_rank BIGINT,
    semantic_rank BIGINT,
    hybrid_score DOUBLE PRECISION
)
LANGUAGE SQL
STABLE
AS $$
WITH authorized AS MATERIALIZED (
    SELECT
        c.id AS chunk_id,
        dv.document_id,
        dv.title,
        dv.version_label,
        c.content,
        c.content_tsv,
        c.embedding
    FROM chunks c
    JOIN document_versions dv
      ON dv.id = c.document_version_id
    WHERE cardinality(coalesce(p_caller_groups, ARRAY[]::TEXT[])) > 0
      AND EXISTS (
          SELECT 1
          FROM document_acl acl
          WHERE acl.document_version_id = dv.id
            AND acl.group_name = ANY(p_caller_groups)
      )
),
lexical AS (
    SELECT
        a.chunk_id,
        row_number() OVER (
            ORDER BY ts_rank_cd(
                a.content_tsv,
                websearch_to_tsquery('simple', p_query_text)
            ) DESC,
            a.chunk_id
        ) AS lexical_rank
    FROM authorized a
    WHERE btrim(coalesce(p_query_text, '')) <> ''
      AND a.content_tsv @@ websearch_to_tsquery('simple', p_query_text)
    ORDER BY
        ts_rank_cd(
            a.content_tsv,
            websearch_to_tsquery('simple', p_query_text)
        ) DESC,
        a.chunk_id
    LIMIT greatest(p_limit, 1) * 4
),
semantic AS (
    SELECT
        a.chunk_id,
        row_number() OVER (
            ORDER BY a.embedding <=> p_query_embedding,
                     a.chunk_id
        ) AS semantic_rank
    FROM authorized a
    WHERE p_query_embedding IS NOT NULL
      AND a.embedding IS NOT NULL
    ORDER BY a.embedding <=> p_query_embedding,
             a.chunk_id
    LIMIT greatest(p_limit, 1) * 4
),
fused AS (
    SELECT
        coalesce(l.chunk_id, s.chunk_id) AS chunk_id,
        l.lexical_rank,
        s.semantic_rank,
        (
            CASE
                WHEN l.lexical_rank IS NULL THEN 0.0
                ELSE 1.0 / (60.0 + l.lexical_rank)
            END
            +
            CASE
                WHEN s.semantic_rank IS NULL THEN 0.0
                ELSE 1.0 / (60.0 + s.semantic_rank)
            END
        )::DOUBLE PRECISION AS hybrid_score
    FROM lexical l
    FULL OUTER JOIN semantic s USING (chunk_id)
)
SELECT
    a.chunk_id,
    a.document_id,
    a.title,
    a.version_label,
    a.content,
    f.lexical_rank,
    f.semantic_rank,
    f.hybrid_score
FROM fused f
JOIN authorized a USING (chunk_id)
ORDER BY f.hybrid_score DESC, a.chunk_id
LIMIT greatest(p_limit, 1);
$$;

COMMENT ON FUNCTION search_authorized_chunks(TEXT, TEXT[], VECTOR, INTEGER) IS
    'ACL-first hybrid retrieval using lexical FTS + pgvector cosine distance + RRF.';

COMMIT;
