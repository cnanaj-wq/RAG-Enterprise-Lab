from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from anthropic import Anthropic
from openai import OpenAI

from rag_enterprise_lab.decision.jev_adapter import decide
from rag_enterprise_lab.evaluation.llm_judge import evaluate


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"

CONTAINER = "genai-postgres"
DATABASE = "rag_enterprise_lab"
DB_USER = "genai"

EMBEDDING_MODEL = "text-embedding-3-small"
CLAUDE_MODEL = "claude-sonnet-5"


AUTHORITY_RANK = {
    "SIGNED_AMENDMENT": 0,
    "SIGNED_CONTRACT": 1,
    "SIGNED_PURCHASE_ORDER": 2,
    "APPROVED_PROPOSAL": 3,
    "APPROVED_PRICING_GRID": 4,
    "DRAFT": 5,
}


def load_env() -> None:
    for line in ENV_PATH.read_text(
        encoding="utf-8"
    ).splitlines():
        line = line.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(
            key,
            value,
        )


def run_sql(sql: str) -> str:
    result = subprocess.run(
        [
            "docker",
            "exec",
            CONTAINER,
            "psql",
            "-U",
            DB_USER,
            "-d",
            DATABASE,
            "-At",
            "-F",
            "\t",
            "-c",
            sql,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
        )

    return result.stdout.strip()


def sql_literal(value: str) -> str:
    return "'" + value.replace(
        "'",
        "''",
    ) + "'"


def vector_literal(
    values: list[float],
) -> str:
    return (
        "["
        + ",".join(
            str(value)
            for value in values
        )
        + "]"
    )


def extract_client_name(
    question: str,
) -> str:
    known_clients = [
        "Axion Solutions",
        "Solace Systems",
        "Driftwood Systems",
    ]

    question_lower = question.lower()

    for client in known_clients:
        if client.lower() in question_lower:
            return client

    return ""



def _shortcut_client(
    question: str,
    shortcut: str,
) -> str:
    known = extract_client_name(question)
    if known:
        return known

    remainder = question.strip()[len(shortcut):].strip()
    return remainder


def run_shortcut(
    question: str,
    shortcut: str,
    groups: list[str],
) -> None:
    print("🧭 SHORTCUT ROUTING")
    print(f"   Shortcut      : {shortcut}")
    print(f"   ACL groups    : {', '.join(groups)}")
    print()

    if shortcut == "/signatures mois":
        match = re.search(r"\b(20\d{2}-\d{2})\b", question)
        month = match.group(1) if match else "2026-09"

        command = [
            sys.executable,
            str(ROOT / "scripts" / "test_phase4_signatures.py"),
            "--month",
            month,
        ]
    else:
        client_name = _shortcut_client(question, shortcut)

        if not client_name:
            print("⚠️ Client manquant dans le shortcut.")
            return

        shortcut_name = shortcut.removeprefix("/")
        command = [
            sys.executable,
            str(ROOT / "scripts" / "test_phase4_shortcuts.py"),
            shortcut_name,
            client_name,
        ]

        for group in groups:
            command.extend(["--group", group])

    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Shortcut failed with exit code {result.returncode}"
        )


def retrieve(
    question: str,
    groups: list[str],
    embedding: list[float],
) -> list[dict[str, str]]:
    vector = vector_literal(
        embedding
    )

    groups_sql = ",".join(
        sql_literal(group)
        for group in groups
    )

    sql = f"""
SELECT
    document_id,
    title,
    coalesce(lexical_rank::text, ''),
    coalesce(semantic_rank::text, ''),
    hybrid_score::text,
    encode(
        convert_to(content, 'UTF8'),
        'hex'
    )
FROM search_authorized_chunks(
    {sql_literal(question)},
    ARRAY[{groups_sql}],
    '{vector}'::vector,
    5
);
""".strip()

    output = run_sql(sql)

    if not output:
        return []

    results: list[
        dict[str, str]
    ] = []

    for line in output.splitlines():
        (
            document_id,
            title,
            lexical_rank,
            semantic_rank,
            hybrid_score,
            content_hex,
        ) = line.split(
            "\t",
            5,
        )

        results.append(
            {
                "document_id": document_id,
                "title": title,
                "lexical_rank": lexical_rank,
                "semantic_rank": semantic_rank,
                "hybrid_score": hybrid_score,
                "content": bytes.fromhex(
                    content_hex
                ).decode("utf-8"),
            }
        )

    return results


def fetch_authority(
    client_name: str,
    groups: list[str],
) -> tuple[
    dict[str, str] | None,
    bool,
]:
    if not client_name:
        return None, False

    groups_sql = ",".join(
        sql_literal(group)
        for group in groups
    )

    sql = f"""
SELECT
    dv.document_id,
    dv.title,
    dv.document_type,
    dv.status,
    dv.authority_level,
    coalesce(dv.valid_from::text, ''),
    coalesce(dv.created_at::text, ''),
    coalesce(dv.supersedes_document_id, '')
FROM document_versions dv
WHERE dv.title ILIKE
    '%' || {sql_literal(client_name)} || '%'
  AND cardinality(ARRAY[{groups_sql}]::TEXT[]) > 0
  AND EXISTS (
      SELECT 1
      FROM document_acl acl
      WHERE acl.document_version_id = dv.id
        AND acl.group_name = ANY(ARRAY[{groups_sql}]::TEXT[])
  )
ORDER BY dv.created_at;
""".strip()

    output = run_sql(sql)

    if not output:
        return None, False

    documents: list[
        dict[str, str]
    ] = []

    for line in output.splitlines():
        (
            document_id,
            title,
            document_type,
            status,
            authority_level,
            valid_from,
            created_at,
            supersedes,
        ) = line.split("\t")

        documents.append(
            {
                "document_id": document_id,
                "title": title,
                "document_type": document_type,
                "status": status,
                "authority_level": authority_level,
                "valid_from": valid_from,
                "created_at": created_at,
                "supersedes": supersedes,
            }
        )

    best_rank = min(
        AUTHORITY_RANK.get(
            doc["authority_level"],
            999,
        )
        for doc in documents
    )

    same_authority = [
        doc
        for doc in documents
        if AUTHORITY_RANK.get(
            doc["authority_level"],
            999,
        )
        == best_rank
    ]

    authoritative = sorted(
        same_authority,
        key=lambda doc: (
            doc["valid_from"],
            doc["created_at"],
        ),
        reverse=True,
    )[0]

    distinct_authorities = {
        doc["authority_level"]
        for doc in documents
    }

    conflict_candidate = (
        len(documents) > 1
        and len(distinct_authorities) > 1
    )

    return (
        authoritative,
        conflict_candidate,
    )


def build_context(
    retrieval_results: list[
        dict[str, str]
    ],
    authority: dict[str, str]
    | None,
) -> str:
    blocks: list[str] = []

    if authority:
        blocks.append(
            "\n".join(
                [
                    "AUTHORITY_DECISION",
                    (
                        "document_id="
                        f"{authority['document_id']}"
                    ),
                    (
                        "title="
                        f"{authority['title']}"
                    ),
                    (
                        "type="
                        f"{authority['document_type']}"
                    ),
                    (
                        "status="
                        f"{authority['status']}"
                    ),
                    (
                        "authority_level="
                        f"{authority['authority_level']}"
                    ),
                    (
                        "valid_from="
                        f"{authority['valid_from']}"
                    ),
                    (
                        "supersedes="
                        f"{authority['supersedes']}"
                    ),
                ]
            )
        )

    for result in retrieval_results:
        blocks.append(
            "\n".join(
                [
                    "RETRIEVED_SOURCE",
                    (
                        "document_id="
                        f"{result['document_id']}"
                    ),
                    (
                        "title="
                        f"{result['title']}"
                    ),
                    (
                        "lexical_rank="
                        f"{result['lexical_rank'] or '-'}"
                    ),
                    (
                        "semantic_rank="
                        f"{result['semantic_rank'] or '-'}"
                    ),
                    (
                        "hybrid_score="
                        f"{result['hybrid_score']}"
                    ),
                    "content:",
                    result["content"],
                ]
            )
        )

    return "\n\n---\n\n".join(
        blocks
    )


def ask_claude(
    question: str,
    context: str,
) -> str:
    client = Anthropic(
        api_key=os.environ[
            "CLAUDE_API_KEY"
        ]
    )

    prompt = f"""
Tu es l'assistant RAG de GenAI Enterprise Lab.

Règles non négociables :
- Réponds uniquement à partir du contexte autorisé fourni.
- N'invente aucune information absente des sources.
- La décision AUTHORITY_DECISION prime pour déterminer
  quel document fait foi.
- Si les preuves sont insuffisantes, dis-le explicitement.
- Cite les document_id utilisés.
- Sois concis et professionnel.

QUESTION
{question}

CONTEXTE AUTORISÉ
{context}
""".strip()

    response = (
        client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
    )

    return response.content[0].text


def print_header() -> None:
    print()
    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    print(
        "🏢 RAG ENTERPRISE LAB — DEMO"
    )
    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    print()


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "question",
        nargs="?",
        default=(
            "Quel est le contrat applicable "
            "pour Axion Solutions ?"
        ),
    )

    parser.add_argument(
        "--group",
        action="append",
        default=None,
        help=(
            "Groupe ACL utilisateur. "
            "Répétable. Défaut: RAG_LEGAL."
        ),
    )

    args = parser.parse_args()
    groups = args.group or ["RAG_LEGAL"]

    load_env()
    print_header()

    print(
        f"❓ Question : {args.question}"
    )
    print(
        "👤 Groupes  : "
        + ", ".join(groups)
    )
    print()

    decision = decide(
        args.question
    )

    print(
        "🧠 JEV DECISION LAYER"
    )
    print(
        f"   Intent        : "
        f"{decision.intent}"
    )
    print(
        f"   Confidence    : "
        f"{decision.confidence:.2f}"
    )
    print(
        f"   Risk          : "
        f"{decision.risk}"
    )
    print(
        f"   Retrieval     : "
        f"{decision.needs_retrieval}"
    )
    print(
        f"   Authority     : "
        f"{decision.needs_authority_resolution}"
    )
    print()

    if decision.shortcut:
        run_shortcut(
            args.question,
            decision.shortcut,
            groups,
        )
        return

    openai_client = OpenAI(
        api_key=os.environ[
            "OPENAI_API_KEY"
        ]
    )

    embedding = (
        openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=args.question,
        )
        .data[0]
        .embedding
    )

    retrieval_results = retrieve(
        args.question,
        groups,
        embedding,
    )

    if not retrieval_results:
        print(
            "🔒 Aucun résultat suffisamment "
            "pertinent dans le périmètre autorisé."
        )
        return

    print(
        "🔎 HYBRID RETRIEVAL"
    )
    print()

    for result in retrieval_results:
        print(
            f"📄 {result['document_id']} — "
            f"{result['title']}"
        )

        print(
            f"   🔎 Lexical rank  : "
            f"{result['lexical_rank'] or '-'}"
        )

        print(
            f"   🧠 Semantic rank : "
            f"{result['semantic_rank'] or '-'}"
        )

        print(
            f"   📊 Hybrid score  : "
            f"{float(result['hybrid_score']):.6f}"
        )

        print()

    client_name = extract_client_name(
        args.question
    )

    authority = None
    conflict_candidate = False

    if (
        decision.needs_authority_resolution
    ):
        (
            authority,
            conflict_candidate,
        ) = fetch_authority(
            client_name,
            groups,
        )

    if authority:
        print(
            "⚖️ AUTHORITY RESOLUTION"
        )

        print(
            f"   Document faisant foi : "
            f"{authority['document_id']}"
        )

        print(
            f"   Type                  : "
            f"{authority['document_type']}"
        )

        print(
            f"   Statut                : "
            f"{authority['status']}"
        )

        print(
            f"   Autorité              : "
            f"{authority['authority_level']}"
        )

        print(
            f"   Valid from            : "
            f"{authority['valid_from']}"
        )

        print(
            f"   ⚠️ Conflict candidate : "
            f"{conflict_candidate}"
        )

        print()

    context = build_context(
        retrieval_results,
        authority,
    )

    answer = ask_claude(
        args.question,
        context,
    )

    print(
        "🤖 CLAUDE ANSWER"
    )
    print()
    print(answer)
    print()

    print(
        "🛡️ GUARDRAILS"
    )
    print(
        "   ✅ ACL before retrieval"
    )
    print(
        "   ✅ Semantic relevance >= 0.50"
    )
    print(
        "   ✅ Authority resolution"
    )
    print(
        "   ✅ Sources constrained"
    )
    print()

    judge = evaluate(
        question=args.question,
        answer=answer,
        context=context,
    )

    print(
        "🧪 LLM-AS-A-JUDGE"
    )
    print()

    print(
        f"   🎯 Relevance           : "
        f"{judge.relevance:.2f}"
    )

    print(
        f"   📚 Faithfulness        : "
        f"{judge.faithfulness:.2f}"
    )

    print(
        f"   📋 Completeness        : "
        f"{judge.completeness:.2f}"
    )

    print(
        f"   ⚖️ Conflict awareness : "
        f"{judge.conflict_awareness:.2f}"
    )

    print(
        f"   📊 Overall             : "
        f"{judge.overall:.2f}"
    )

    print()

    verdict_icon = (
        "✅"
        if judge.verdict == "PASS"
        else "⚠️"
        if judge.verdict == "REVIEW"
        else "❌"
    )

    print(
        f"   {verdict_icon} Verdict             : "
        f"{judge.verdict}"
    )

    print(
        f"   💬 Reason              : "
        f"{judge.reason}"
    )

    print()

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    print(
        "📊 FINAL RESPONSE STATUS"
    )
    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    print(
        "✅ Answer generated      : YES"
    )

    print(
        "🛡️ ACL enforced          : YES"
    )

    print(
        "🎯 Relevance guardrail   : >= 0.50"
    )

    if authority:
        print(
            f"⚖️ Authority document    : "
            f"{authority['document_id']}"
        )

    print(
        f"⚠️ Conflict detected     : "
        f"{conflict_candidate}"
    )

    print(
        f"🧪 Judge verdict         : "
        f"{judge.verdict}"
    )

    print(
        f"📊 Judge overall         : "
        f"{judge.overall:.2f}"
    )

    print()


if __name__ == "__main__":
    main()