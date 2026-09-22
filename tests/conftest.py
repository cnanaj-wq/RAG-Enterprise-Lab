import pytest

from rag_enterprise_lab.generation.dataset import generate_dataset

DATASET_SEED = 42


@pytest.fixture(scope="session")
def dataset():
    return generate_dataset(DATASET_SEED)
