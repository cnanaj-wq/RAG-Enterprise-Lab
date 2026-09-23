import pytest

from rag_enterprise_lab.adapters.docling import (
    CorruptedDocumentError,
    DoclingWorkerAdapter,
    MockDoclingAdapter,
    UnsupportedFormatError,
)


def test_mock_adapter_parses_text_formats():
    adapter = MockDoclingAdapter()
    result = adapter.parse(document_id="DOC-00001", content=b"# Title\ncontent", extension="md")
    assert "Title" in result.text
    assert result.metadata["document_id"] == "DOC-00001"
    assert result.metadata["source_format"] == "md"


def test_mock_adapter_parses_binary_formats():
    adapter = MockDoclingAdapter()
    result = adapter.parse(document_id="DOC-00002", content=b"%PDF-1.4 fake but long enough", extension="pdf")
    assert "binary pdf content" in result.text


def test_mock_adapter_produces_tables_for_tabular_formats():
    adapter = MockDoclingAdapter()
    result = adapter.parse(document_id="DOC-00003", content=b"field,value\na,b", extension="csv")
    assert result.tables is not None
    assert len(result.tables) >= 1


def test_mock_adapter_raises_on_unsupported_format():
    adapter = MockDoclingAdapter()
    with pytest.raises(UnsupportedFormatError):
        adapter.parse(document_id="DOC-00004", content=b"data", extension="zzz")


def test_mock_adapter_raises_on_empty_content():
    adapter = MockDoclingAdapter()
    with pytest.raises(CorruptedDocumentError):
        adapter.parse(document_id="DOC-00005", content=b"", extension="pdf")


def test_mock_adapter_raises_on_undecodable_text_content():
    adapter = MockDoclingAdapter()
    with pytest.raises(CorruptedDocumentError):
        adapter.parse(document_id="DOC-00006", content=b"\xff\xfe\x00\x01", extension="md")


def test_mock_adapter_raises_on_tiny_binary_content():
    adapter = MockDoclingAdapter()
    with pytest.raises(CorruptedDocumentError):
        adapter.parse(document_id="DOC-00007", content=b"\x00\x01", extension="pdf")


def test_docling_worker_adapter_fails_clearly_when_docling_not_installed():
    adapter = DoclingWorkerAdapter()
    with pytest.raises(RuntimeError, match="docling"):
        adapter.parse(document_id="DOC-00008", content=b"data", extension="pdf")
