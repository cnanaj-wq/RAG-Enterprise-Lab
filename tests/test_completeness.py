from rag_enterprise_lab.domain.completeness import (
    compute_completeness,
    load_mandatory_document_types,
)


def test_client_dossier_mandatory_types_loaded():
    types = load_mandatory_document_types("CLIENT")
    assert "CLIENT_CONTRACT" in types
    assert len(types) == 10


def test_supplier_dossier_mandatory_types_loaded():
    types = load_mandatory_document_types("SUPPLIER")
    assert "SUPPLIER_CONTRACT" in types


def test_hr_employee_dossier_mandatory_types_loaded():
    types = load_mandatory_document_types("HR_EMPLOYEE")
    assert "EMPLOYMENT_CONTRACT" in types


def test_compute_completeness_detects_missing_types():
    result = compute_completeness(
        dossier_type="CLIENT",
        related_id="CLI-0001",
        present_document_types={"CLIENT_CONTRACT", "NDA"},
    )
    assert not result.is_complete
    assert "DPA" in result.missing_types
    assert 0 < result.completeness_ratio < 1


def test_compute_completeness_full_dossier_is_complete():
    all_types = load_mandatory_document_types("HR_EMPLOYEE")
    result = compute_completeness(
        dossier_type="HR_EMPLOYEE",
        related_id="EMP-0001",
        present_document_types=set(all_types),
    )
    assert result.is_complete
    assert result.completeness_ratio == 1.0
