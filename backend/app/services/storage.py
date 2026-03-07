import os
from pathlib import Path
from typing import Protocol


class StorageBackend(Protocol):
    name: str

    def read_bytes(self, key: str) -> bytes: ...


class LocalStorageBackend:
    name = "local"

    def __init__(self, root_dir: str | None = None):
        self.root_dir = Path(root_dir or os.getenv("STORAGE_LOCAL_ROOT", "./storage")).resolve()

    def read_bytes(self, key: str) -> bytes:
        resolved_path = (self.root_dir / key).resolve()
        if self.root_dir not in resolved_path.parents and resolved_path != self.root_dir:
            raise ValueError(f"invalid storage key outside root: {key}")
        return resolved_path.read_bytes()


class StorageManager:
    def __init__(self, backends: dict[str, StorageBackend] | None = None):
        self.backends = backends or {"local": LocalStorageBackend()}

    def read_bytes(self, *, backend_name: str, key: str) -> bytes:
        backend = self.backends.get(backend_name)
        if not backend:
            raise ValueError(f"unsupported storage backend: {backend_name}")
        return backend.read_bytes(key)
