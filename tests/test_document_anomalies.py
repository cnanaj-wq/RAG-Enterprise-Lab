from rag_enterprise_lab.domain.anomalies import AnomalyType
from rag_enterprise_lab.generation.dataset import generate_dataset
from rag_enterprise_lab.generation.document_dataset import generate_document_dataset

DOCUMENT_SEED = 142


def test_all_15_anomaly_types_are_present(document_dataset):
    present_types = {a.type for a in document_dataset.anomalies}
    assert present_types == set(AnomalyType)


def test_every_anomaly_has_id_and_ground_truth(document_dataset):
    ids = [a.anomaly_id for a in document_dataset.anomalies]
    assert len(ids) == len(set(ids))
    for anomaly in document_dataset.anomalies:
        assert anomaly.anomaly_id.startswith("ANOM-")
        assert anomaly.ground_truth


def test_anomalies_reproducible_with_same_seed(dataset, tmp_path):
    first = generate_document_dataset(DOCUMENT_SEED, dataset, examples_dir=tmp_path / "a")
    second = generate_document_dataset(DOCUMENT_SEED, dataset, examples_dir=tmp_path / "b")
    assert first.anomalies == second.anomalies


def test_anomalies_differ_with_different_organization_seed(tmp_path):
    org_a = generate_dataset(42)
    org_b = generate_dataset(43)
    doc_a = generate_document_dataset(DOCUMENT_SEED, org_a, examples_dir=tmp_path / "a")
    doc_b = generate_document_dataset(DOCUMENT_SEED, org_b, examples_dir=tmp_path / "b")
    assert doc_a.manifest != doc_b.manifest
