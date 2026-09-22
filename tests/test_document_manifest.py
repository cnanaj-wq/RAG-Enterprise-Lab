from rag_enterprise_lab.domain.document_taxonomy import DOMAIN_VOLUME
from rag_enterprise_lab.domain.models import Classification


def test_exactly_5000_manifest_entries(document_dataset):
    assert len(document_dataset.manifest) == 5000


def test_domain_distribution_exact(document_dataset):
    counts: dict = {}
    for entry in document_dataset.manifest:
        counts[entry.domain] = counts.get(entry.domain, 0) + 1
    assert counts == DOMAIN_VOLUME


def test_no_duplicate_document_id(document_dataset):
    ids = [e.document_id for e in document_dataset.manifest]
    assert len(ids) == len(set(ids))


def test_employee_references_are_valid(document_dataset, dataset):
    employee_ids = {e.employee_id for e in dataset.employees}
    for entry in document_dataset.manifest:
        if entry.related_employee_id:
            assert entry.related_employee_id in employee_ids
        if entry.owner:
            assert entry.owner in employee_ids


def test_customer_references_are_valid(document_dataset, dataset):
    customer_ids = {c.customer_id for c in dataset.clients}
    for entry in document_dataset.manifest:
        if entry.related_customer_id:
            assert entry.related_customer_id in customer_ids


def test_supplier_references_are_valid(document_dataset, dataset):
    supplier_ids = {s.supplier_id for s in dataset.suppliers}
    for entry in document_dataset.manifest:
        if entry.related_supplier_id:
            assert entry.related_supplier_id in supplier_ids


def test_project_references_are_valid(document_dataset, dataset):
    project_ids = {p.project_id for p in dataset.projects}
    for entry in document_dataset.manifest:
        if entry.related_project_id:
            assert entry.related_project_id in project_ids


def test_acl_valid_deny_by_default(document_dataset):
    """Chaque entrée non ciblée par l'anomalie ACL_INCOHERENT doit avoir des
    allowed_groups cohérents : non vides, et jamais RAG_ALL_EMPLOYEES pour une
    classification restreinte."""
    acl_anomaly_ids = {
        doc_id
        for a in document_dataset.anomalies
        if a.type.value == "ACL_INCOHERENT"
        for doc_id in a.document_ids
    }
    restricted = {Classification.RESTRICTED, Classification.SENSITIVE_PERSONAL_DATA}
    for entry in document_dataset.manifest:
        if entry.document_id in acl_anomaly_ids:
            continue
        assert entry.allowed_groups, f"{entry.document_id} has no allowed_groups"
        if entry.classification in restricted:
            assert "RAG_ALL_EMPLOYEES" not in entry.allowed_groups


def test_classifications_are_valid_enum_values(document_dataset):
    for entry in document_dataset.manifest:
        assert entry.classification in Classification


def test_version_graph_has_no_cycle(document_dataset):
    by_id = {e.document_id: e for e in document_dataset.manifest}

    def has_cycle(start) -> bool:
        seen: set[str] = set()
        current = start
        while current.supersedes is not None:
            if current.supersedes in seen:
                return True
            seen.add(current.supersedes)
            current = by_id.get(current.supersedes)
            if current is None:
                break
        return False

    assert not any(has_cycle(e) for e in document_dataset.manifest)


def test_supersedes_points_to_existing_document(document_dataset):
    ids = {e.document_id for e in document_dataset.manifest}
    for entry in document_dataset.manifest:
        if entry.supersedes is not None:
            assert entry.supersedes in ids
            assert entry.supersedes != entry.document_id
