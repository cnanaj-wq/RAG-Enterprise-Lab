"""Tests d'intégration réels contre Cloudflare R2 — jamais exécutés sans
credentials (skipped, pas d'échec). Ne jamais faire échouer la suite unitaire
parce qu'un compte cloud n'est pas configuré (CLAUDE.md Phase 3)."""

import pytest

from rag_enterprise_lab.adapters.r2 import R2StorageAdapter, credentials_available
from rag_enterprise_lab.core.config import Settings

pytestmark = pytest.mark.integration

_settings = Settings()


@pytest.mark.skipif(
    not credentials_available(_settings),
    reason="R2 credentials not configured (BLOCKED_BY_CREDENTIALS) — see PHASE-3-REPORT.md",
)
def test_real_r2_put_head_get_delete_roundtrip():
    adapter = R2StorageAdapter(_settings)
    key = "manifests/_phase3_integration_probe.txt"
    payload = b"phase3-integration-probe"
    checksum = "probe"

    adapter.put_bytes(key, payload, content_type="text/plain", checksum=checksum)
    try:
        head = adapter.head(key)
        assert head is not None
        assert head.checksum == checksum
        assert adapter.get_bytes(key) == payload
    finally:
        adapter.delete(key)
        assert adapter.head(key) is None
