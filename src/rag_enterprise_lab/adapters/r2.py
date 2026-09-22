from typing import Protocol


class ObjectStorePort(Protocol):
    async def get_bytes(self, object_key: str) -> bytes:
        ...

    async def put_bytes(self, object_key: str, payload: bytes, content_type: str) -> None:
        ...
