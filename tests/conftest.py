
import pytest

from rag_enterprise_lab.generation.dataset import generate_dataset
from rag_enterprise_lab.generation.document_dataset import generate_document_dataset

DATASET_SEED = 42
DOCUMENT_SEED = 142


@pytest.fixture(scope="session")
def dataset():
    return generate_dataset(DATASET_SEED)


@pytest.fixture(scope="session")
def document_dataset(dataset, tmp_path_factory):
    examples_dir = tmp_path_factory.mktemp("examples")
    return generate_document_dataset(DOCUMENT_SEED, dataset, examples_dir=examples_dir)
