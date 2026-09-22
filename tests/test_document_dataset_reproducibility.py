from rag_enterprise_lab.generation.document_dataset import generate_document_dataset

DOCUMENT_SEED = 142


def test_same_seed_produces_same_manifest(dataset, tmp_path):
    first = generate_document_dataset(DOCUMENT_SEED, dataset, examples_dir=tmp_path / "a")
    second = generate_document_dataset(DOCUMENT_SEED, dataset, examples_dir=tmp_path / "b")
    assert first.manifest == second.manifest
    assert first.conflicts == second.conflicts
    assert first.expected_answers == second.expected_answers


def test_different_seed_produces_different_manifest(dataset, tmp_path):
    first = generate_document_dataset(DOCUMENT_SEED, dataset, examples_dir=tmp_path / "a")
    other = generate_document_dataset(DOCUMENT_SEED + 1, dataset, examples_dir=tmp_path / "b")
    assert first.manifest != other.manifest
