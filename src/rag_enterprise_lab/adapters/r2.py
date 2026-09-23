"""Adapter de stockage objet S3-compatible (Cloudflare R2).

`ObjectStorePort` est synchrone (boto3 ne supporte pas asyncio nativement) —
changement par rapport au stub Phase 0, qui n'était implémenté nulle part et
n'est couvert par aucun test existant (vérifié avant modification).

Aucun credential n'est jamais codé en dur : `R2StorageAdapter` les lit
exclusivement depuis `core.config.Settings` (variables d'environnement
`R2_ENDPOINT`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`).
"""

from dataclasses import dataclass
from typing import Protocol

from rag_enterprise_lab.core.config import Settings


@dataclass(frozen=True)
class ObjectHead:
    key: str
    size: int
    checksum: str


class ObjectStorePort(Protocol):
    def put_bytes(
        self, object_key: str, payload: bytes, *, content_type: str, checksum: str
    ) -> None: ...

    def get_bytes(self, object_key: str) -> bytes: ...

    def head(self, object_key: str) -> ObjectHead | None:
        """Retourne les métadonnées de l'objet (dont son checksum stocké)
        sans transférer son contenu, ou None s'il n'existe pas."""
        ...

    def delete(self, object_key: str) -> None: ...


def credentials_available(settings: Settings) -> bool:
    return bool(
        settings.r2_endpoint
        and settings.r2_bucket
        and settings.r2_access_key_id
        and settings.r2_secret_access_key
    )


class InMemoryObjectStore:
    """Mock déterministe, sans réseau — utilisé par les tests unitaires et
    le mode offline. Implémente `ObjectStorePort` par duck typing."""

    def __init__(self) -> None:
        self._objects: dict[str, tuple[bytes, str, str]] = {}

    def put_bytes(
        self, object_key: str, payload: bytes, *, content_type: str, checksum: str
    ) -> None:
        self._objects[object_key] = (payload, content_type, checksum)

    def get_bytes(self, object_key: str) -> bytes:
        return self._objects[object_key][0]

    def head(self, object_key: str) -> ObjectHead | None:
        entry = self._objects.get(object_key)
        if entry is None:
            return None
        payload, _content_type, checksum = entry
        return ObjectHead(key=object_key, size=len(payload), checksum=checksum)

    def delete(self, object_key: str) -> None:
        self._objects.pop(object_key, None)

    def keys(self) -> list[str]:
        return sorted(self._objects)


class R2StorageAdapter:
    """Adapter réel S3-compatible pour Cloudflare R2, via boto3. N'est
    instancié (et ne touche le réseau) que si les credentials sont présents
    — vérifié par l'appelant via `credentials_available()` avant toute
    provisioning distante, conformément à CLAUDE.md Phase 3."""

    def __init__(self, settings: Settings) -> None:
        if not credentials_available(settings):
            raise RuntimeError(
                "R2 credentials missing: set R2_ENDPOINT, R2_BUCKET, "
                "R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY (BLOCKED_BY_CREDENTIALS)."
            )
        import boto3  # type: ignore[import-untyped]

        self._bucket = settings.r2_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
        )

    def put_bytes(
        self, object_key: str, payload: bytes, *, content_type: str, checksum: str
    ) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=object_key,
            Body=payload,
            ContentType=content_type,
            Metadata={"checksum": checksum},
        )

    def get_bytes(self, object_key: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=object_key)
        return response["Body"].read()

    def head(self, object_key: str) -> ObjectHead | None:
        from botocore.exceptions import ClientError  # type: ignore[import-untyped]

        try:
            response = self._client.head_object(Bucket=self._bucket, Key=object_key)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
                return None
            raise
        return ObjectHead(
            key=object_key,
            size=response["ContentLength"],
            checksum=response.get("Metadata", {}).get("checksum", ""),
        )

    def delete(self, object_key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=object_key)
