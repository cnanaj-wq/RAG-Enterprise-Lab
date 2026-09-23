import pytest

from rag_enterprise_lab.ingestion.temp_guard import TempDiskLimitExceeded, TempFileGuard


def test_write_and_release_tracks_current_and_peak(tmp_path):
    guard = TempFileGuard(tmp_path / "temp", max_temp_mb=1)
    path = guard.write("a.txt", b"hello")
    assert path.exists()
    assert guard.current_bytes == 5
    assert guard.peak_bytes == 5

    guard.release(path)
    assert not path.exists()
    assert guard.current_bytes == 0
    assert guard.peak_bytes == 5  # le pic est conservé


def test_cleanup_removes_all_temp_files(tmp_path):
    root = tmp_path / "temp"
    guard = TempFileGuard(root, max_temp_mb=1)
    guard.write("a.txt", b"hello")
    guard.write("b.txt", b"world")
    assert len(list(root.glob("*"))) == 2

    guard.cleanup()
    assert list(root.glob("*")) == []
    assert guard.current_bytes == 0


def test_context_manager_cleans_up_on_normal_exit(tmp_path):
    root = tmp_path / "temp"
    with TempFileGuard(root, max_temp_mb=1) as guard:
        guard.write("a.txt", b"hello")
    assert list(root.glob("*")) == []


def test_context_manager_cleans_up_on_exception(tmp_path):
    root = tmp_path / "temp"
    with pytest.raises(ValueError), TempFileGuard(root, max_temp_mb=1) as guard:
        guard.write("a.txt", b"hello")
        raise ValueError("boom")
    assert list(root.glob("*")) == []


def test_max_local_temp_mb_stop_cleanup_error(tmp_path):
    root = tmp_path / "temp"
    guard = TempFileGuard(root, max_temp_mb=0)  # 0 Mo -> toute écriture dépasse
    with pytest.raises(TempDiskLimitExceeded):
        guard.write("a.txt", b"hello")
    # CLEANUP : le répertoire est vide après l'échec (STOP / CLEANUP / ERROR)
    assert list(root.glob("*")) == []
    assert guard.current_bytes == 0
