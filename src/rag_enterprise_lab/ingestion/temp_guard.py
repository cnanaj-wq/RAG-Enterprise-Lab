"""Garde-fou disque temporaire : répertoire dédié, nettoyable, borné par
`MAX_LOCAL_TEMP_MB`. Le corpus complet ne doit jamais être conservé
durablement sur le poste utilisateur (CLAUDE.md Phase 3) — chaque fichier
temporaire est supprimé dès son upload/traitement terminé, et tout le
répertoire est nettoyé à la sortie du contexte, même en cas d'erreur."""

from pathlib import Path
from types import TracebackType
from typing import Self


class TempDiskLimitExceeded(RuntimeError):
    """STOP / CLEANUP / ERROR : levée quand une écriture dépasserait
    MAX_LOCAL_TEMP_MB. L'appelant doit considérer le run comme interrompu."""


class TempFileGuard:
    def __init__(self, root: Path, max_temp_mb: int) -> None:
        self.root = root
        self.max_bytes = max_temp_mb * 1024 * 1024
        self.current_bytes = 0
        self.peak_bytes = 0
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, filename: str, payload: bytes) -> Path:
        projected = self.current_bytes + len(payload)
        if projected > self.max_bytes:
            self.cleanup()
            raise TempDiskLimitExceeded(
                f"writing {filename} ({len(payload)} bytes) would exceed "
                f"MAX_LOCAL_TEMP_MB ({self.max_bytes} bytes); run stopped and "
                f"temp directory cleaned up."
            )
        path = self.root / filename
        path.write_bytes(payload)
        self.current_bytes = projected
        self.peak_bytes = max(self.peak_bytes, self.current_bytes)
        return path

    def release(self, path: Path) -> None:
        if not path.exists():
            return
        size = path.stat().st_size
        path.unlink()
        self.current_bytes = max(0, self.current_bytes - size)

    def cleanup(self) -> None:
        for child in self.root.glob("*"):
            if child.is_file():
                child.unlink(missing_ok=True)
        self.current_bytes = 0

    @property
    def current_mb(self) -> float:
        return self.current_bytes / (1024 * 1024)

    @property
    def peak_mb(self) -> float:
        return self.peak_bytes / (1024 * 1024)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.cleanup()
