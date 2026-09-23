import hashlib
import io
import zipfile

from rag_enterprise_lab.generation.document_content_generator import generate_content
from rag_enterprise_lab.generation.document_format_rules import format_for


def _first_entry_of_format(document_dataset, extension: str):
    for entry in document_dataset.manifest:
        if format_for(entry.document_id, entry.document_type) == extension:
            return entry
    raise AssertionError(f"no manifest entry generates format {extension}")


def test_content_generation_is_deterministic(document_dataset):
    entry = document_dataset.manifest[0]
    content1, ctype1, ext1 = generate_content(entry)
    content2, ctype2, ext2 = generate_content(entry)
    assert content1 == content2
    assert ctype1 == ctype2
    assert ext1 == ext2


def test_all_seven_formats_are_represented(document_dataset):
    seen = {format_for(e.document_id, e.document_type) for e in document_dataset.manifest}
    assert seen == {"pdf", "docx", "xlsx", "pptx", "md", "html", "csv"}


def test_format_distribution_is_not_uniform(document_dataset):
    from collections import Counter

    counts = Counter(format_for(e.document_id, e.document_type) for e in document_dataset.manifest)
    assert len(set(counts.values())) > 1


def test_pdf_content_is_structurally_valid(document_dataset):
    entry = _first_entry_of_format(document_dataset, "pdf")
    content, content_type, ext = generate_content(entry)
    assert ext == "pdf"
    assert content_type == "application/pdf"
    assert content.startswith(b"%PDF-1.4")
    assert content.rstrip().endswith(b"%%EOF")


def test_docx_xlsx_pptx_are_valid_zip_archives(document_dataset):
    for fmt in ("docx", "xlsx", "pptx"):
        entry = _first_entry_of_format(document_dataset, fmt)
        content, _content_type, ext = generate_content(entry)
        assert ext == fmt
        zf = zipfile.ZipFile(io.BytesIO(content))
        assert zf.testzip() is None
        assert "[Content_Types].xml" in zf.namelist()


def test_md_html_csv_are_utf8_text(document_dataset):
    for fmt in ("md", "html", "csv"):
        entry = _first_entry_of_format(document_dataset, fmt)
        content, _content_type, ext = generate_content(entry)
        assert ext == fmt
        content.decode("utf-8")  # must not raise


def test_checksum_is_stable_across_regeneration(document_dataset):
    entry = document_dataset.manifest[10]
    content1, _, _ = generate_content(entry)
    content2, _, _ = generate_content(entry)
    assert hashlib.sha256(content1).hexdigest() == hashlib.sha256(content2).hexdigest()
