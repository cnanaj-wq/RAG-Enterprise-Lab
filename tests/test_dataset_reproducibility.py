from rag_enterprise_lab.generation.dataset import generate_dataset


def test_dataset_reproducible_with_same_seed():
    first = generate_dataset(42)
    second = generate_dataset(42)
    assert first == second


def test_dataset_differs_with_different_seed():
    first = generate_dataset(42)
    other = generate_dataset(43)
    assert first.employees != other.employees
