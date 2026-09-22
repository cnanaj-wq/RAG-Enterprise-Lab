from rag_enterprise_lab.shortcuts.registry import SHORTCUTS


def test_signature_shortcut_exists():
    assert "/signatures" in SHORTCUTS

def test_commercial_close_shortcut_exists():
    assert "/cloture-commerciale" in SHORTCUTS
