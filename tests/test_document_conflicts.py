from rag_enterprise_lab.domain.conflicts import ConflictCategory


def test_all_7_conflict_categories_are_present(document_dataset):
    present = {c.category for c in document_dataset.conflicts}
    assert present == set(ConflictCategory)


def test_conflict_ground_truth_is_coherent(document_dataset):
    for conflict in document_dataset.conflicts:
        assert conflict.ground_truth_source_document_id
        is_crm_source = conflict.ground_truth_source_document_id.startswith("CRM:")
        if not is_crm_source:
            assert conflict.ground_truth_source_document_id in conflict.document_ids
            assert (
                conflict.values_by_document[conflict.ground_truth_source_document_id]
                == conflict.ground_truth_value
            )


def test_payment_terms_scenario_matches_specification_example(document_dataset):
    payment_conflicts = [
        c for c in document_dataset.conflicts if c.category == ConflictCategory.PAYMENT_TERMS
    ]
    assert payment_conflicts
    for conflict in payment_conflicts:
        base_id, amendment_id = conflict.document_ids
        assert conflict.values_by_document[base_id] == 30
        assert conflict.values_by_document[amendment_id] == 45
        assert conflict.ground_truth_value == 45
        assert conflict.ground_truth_source_document_id == amendment_id
