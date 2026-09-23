"""DocumentParserPort : abstraction du parsing documentaire (Docling).

Docling n'est installé QUE dans l'environnement worker prévu (jamais dans le
venv de développement local — voir CLAUDE.md). `DoclingWorkerAdapter` importe
`docling` en lazy (au premier appel) et échoue avec un message clair si le
paquet est absent. `MockDoclingAdapter` fournit un parsing déterministe sans
dépendance, utilisé par les tests et le mode offline.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ParsedDocument:
    text: str
    metadata: dict[str, object]
    tables: list[dict[str, object]] | None = None


class DocumentParserPort(Protocol):
    def parse(self, *, document_id: str, content: bytes, extension: str) -> ParsedDocument: ...


class UnsupportedFormatError(ValueError):
    """Levée quand l'extension n'est pas supportée par le parseur."""


class CorruptedDocumentError(ValueError):
    """Levée quand le contenu ne peut pas être décodé/parsé."""


_SUPPORTED_EXTENSIONS = {"pdf", "docx", "xlsx", "pptx", "md", "html", "csv"}
_TEXT_EXTENSIONS = {"md", "html", "csv"}


class MockDoclingAdapter:
    """Parseur déterministe sans dépendance — le worker réel sera
    `DoclingWorkerAdapter`. Simule un résultat normalisé plausible à partir
    des octets bruts, pour tester tout le pipeline (y compris la mise en
    quarantaine) sans installer Docling."""

    def parse(self, *, document_id: str, content: bytes, extension: str) -> ParsedDocument:
        ext = extension.lower().lstrip(".")
        if ext not in _SUPPORTED_EXTENSIONS:
            raise UnsupportedFormatError(f"unsupported format: .{ext}")
        if len(content) == 0:
            raise CorruptedDocumentError(f"{document_id}: empty content")

        text: str
        if ext in _TEXT_EXTENSIONS:
            try:
                text = content[:2000].decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                raise CorruptedDocumentError(f"{document_id}: undecodable text content") from exc
        else:
            if len(content) < 8:
                raise CorruptedDocumentError(f"{document_id}: binary content too small to be valid")
            text = f"[binary {ext} content, {len(content)} bytes]"

        tables: list[dict[str, object]] | None = (
            [{"rows": 1, "columns": 2}] if ext in ("xlsx", "csv") else None
        )
        return ParsedDocument(
            text=text,
            metadata={"document_id": document_id, "source_format": ext, "byte_size": len(content)},
            tables=tables,
        )


class DoclingWorkerAdapter:
    """Adapter réel — à exécuter uniquement dans l'environnement worker où
    `docling` est installé (jamais dans le venv de développement local)."""

    def parse(self, *, document_id: str, content: bytes, extension: str) -> ParsedDocument:
        try:
            import docling  # type: ignore[import-not-found]  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "docling is not installed in this environment — install it only in "
                "the dedicated Docling worker environment (see docs/docling/README.md), "
                "never in the local dev venv."
            ) from exc
        raise NotImplementedError(
            "Docling worker integration ships once the worker environment is "
            "provisioned (not yet — see docs/phase-reports/PHASE-3-REPORT.md)."
        )
