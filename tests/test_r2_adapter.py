import pytest

from rag_enterprise_lab.adapters.r2 import InMemoryObjectStore, credentials_available
from rag_enterprise_lab.core.config import Settings


def test_in_memory_store_put_get_head_delete():
    store = InMemoryObjectStore()
    store.put_bytes("raw/hr/DOC-00001.pdf", b"hello", content_type="application/pdf", checksum="abc")

    assert store.get_bytes("raw/hr/DOC-00001.pdf") == b"hello"

    head = store.head("raw/hr/DOC-00001.pdf")
    assert head is not None
    assert head.checksum == "abc"
    assert head.size == 5

    store.delete("raw/hr/DOC-00001.pdf")
    assert store.head("raw/hr/DOC-00001.pdf") is None


def test_in_memory_store_head_returns_none_for_missing_key():
    store = InMemoryObjectStore()
    assert store.head("raw/hr/DOES-NOT-EXIST.pdf") is None


def test_credentials_available_false_when_any_field_missing():
    settings = Settings(
        r2_endpoint="", r2_bucket="b", r2_access_key_id="k", r2_secret_access_key="s"
    )
    assert credentials_available(settings) is False


def test_credentials_available_true_when_all_fields_set():
    settings = Settings(
        r2_endpoint="https://example.r2.cloudflarestorage.com",
        r2_bucket="rag-enterprise-lab-dev",
        r2_access_key_id="key",
        r2_secret_access_key="secret",
    )
    assert credentials_available(settings) is True


def test_r2_storage_adapter_refuses_to_instantiate_without_credentials():
    from rag_enterprise_lab.adapters.r2 import R2StorageAdapter

    settings = Settings(r2_endpoint="", r2_bucket="", r2_access_key_id="", r2_secret_access_key="")
    with pytest.raises(RuntimeError, match="BLOCKED_BY_CREDENTIALS"):
        R2StorageAdapter(settings)
