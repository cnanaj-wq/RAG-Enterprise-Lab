from rag_enterprise_lab.domain.document_taxonomy import DocumentDomain
from rag_enterprise_lab.storage.bucket_layout import (
    RAW_DOMAIN_FOLDER,
    archive_key,
    manifest_key,
    processed_key,
    quarantine_key,
    raw_key,
)


def test_raw_key_uses_expected_domain_folders():
    expected = {
        DocumentDomain.HR: "hr",
        DocumentDomain.LEGAL_CONTRACTS: "legal",
        DocumentDomain.CLIENTS_PROSPECTS: "clients",
        DocumentDomain.PRICING_SALES: "pricing",
        DocumentDomain.IT_ARCHITECTURE_SECURITY: "technical",
        DocumentDomain.PROJECTS_PROCEDURES: "projects",
        DocumentDomain.FINANCE_COMPLIANCE: "finance",
    }
    assert RAW_DOMAIN_FOLDER == expected
    for domain, folder in expected.items():
        assert raw_key("DOC-00001", domain, "pdf") == f"raw/{folder}/DOC-00001.pdf"


def test_raw_key_strips_leading_dot_in_extension():
    assert raw_key("DOC-00001", DocumentDomain.HR, ".pdf") == "raw/hr/DOC-00001.pdf"


def test_processed_key_structure():
    assert processed_key("DOC-00001", "document.json") == "processed/DOC-00001/document.json"
    assert processed_key("DOC-00001", "content.md") == "processed/DOC-00001/content.md"
    assert processed_key("DOC-00001", "tables.json") == "processed/DOC-00001/tables.json"


def test_quarantine_and_archive_and_manifest_keys():
    assert quarantine_key("DOC-00001", "pdf") == "quarantine/DOC-00001.pdf"
    assert archive_key("DOC-00001", "pdf") == "archive/DOC-00001.pdf"
    assert manifest_key("document_manifest.json") == "manifests/document_manifest.json"


def test_all_document_domains_have_a_raw_folder():
    for domain in DocumentDomain:
        assert domain in RAW_DOMAIN_FOLDER
