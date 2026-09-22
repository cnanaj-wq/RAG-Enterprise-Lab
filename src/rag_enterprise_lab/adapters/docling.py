from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class ParsedDocument:
    text: str
    metadata: dict[str, object]

class DocumentParserPort(Protocol):
    async def parse_object(self, object_key: str) -> ParsedDocument:
        ...

class RemoteDoclingAdapter:
    async def parse_object(self, object_key: str) -> ParsedDocument:
        raise NotImplementedError("Remote Docling worker is implemented in a later phase.")
