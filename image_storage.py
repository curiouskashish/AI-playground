"""Pluggable storage backend for generated idea images.

For local-first deployment, only LocalStorageBackend ships. The interface is
designed so adding S3StorageBackend / GCSStorageBackend later is a single new
class + an env-var flip — keys (the "path" strings) stay identical, so a one-
shot `aws s3 sync` of the local root migrates everything without rewrites.
"""
import os
from abc import ABC, abstractmethod
from typing import Optional


class StorageBackend(ABC):
    """Object-store-like interface. Keys are forward-slash paths
    (e.g. 'ideas/idea_V1StGXR8/large.png') and are NEVER absolute.
    """

    @abstractmethod
    def put(self, key: str, data: bytes) -> str:
        """Write `data` at `key`. Returns the key unchanged."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """True if an object already lives at `key`."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove the object at `key`. No-op if absent."""


class LocalStorageBackend(StorageBackend):
    """Writes objects to disk under `root_dir`. The on-disk layout mirrors
    the cloud object-key layout, so migration to S3/GCS is just an rsync.
    """

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        os.makedirs(self.root_dir, exist_ok=True)

    def _full_path(self, key: str) -> str:
        # Reject anything that could escape the storage root.
        if key.startswith('/') or '..' in key.split('/'):
            raise ValueError(f"Invalid storage key: {key!r}")
        return os.path.join(self.root_dir, key)

    def put(self, key: str, data: bytes) -> str:
        path = self._full_path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data)
        return key

    def exists(self, key: str) -> bool:
        return os.path.isfile(self._full_path(key))

    def delete(self, key: str) -> None:
        path = self._full_path(key)
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


# Future backends:
#
# class S3StorageBackend(StorageBackend):
#     """Uploads to s3://<bucket>/<key>. Key layout matches the local one."""
#     # def __init__(self, bucket, prefix='', region=None): ...
#
# class GCSStorageBackend(StorageBackend):
#     """Uploads to gs://<bucket>/<key>. Key layout matches the local one."""
#     # def __init__(self, bucket, prefix=''): ...


_backend_singleton: Optional[StorageBackend] = None


def get_storage_backend() -> StorageBackend:
    """Returns the configured backend. Process-cached.

    Environment variables:
      IDEA_IMAGE_STORAGE_PROVIDER  'local' (default). Future: 's3', 'gcs'.
      IDEA_IMAGE_LOCAL_ROOT        Local-mode root dir. Default: results/idea_images
                                    (resolved relative to the project root).
    """
    global _backend_singleton
    if _backend_singleton is not None:
        return _backend_singleton

    provider = os.environ.get('IDEA_IMAGE_STORAGE_PROVIDER', 'local').strip().lower()
    if provider == 'local':
        base_dir = os.path.dirname(os.path.abspath(__file__))
        root = os.environ.get('IDEA_IMAGE_LOCAL_ROOT', os.path.join(base_dir, 'results', 'idea_images'))
        if not os.path.isabs(root):
            root = os.path.join(base_dir, root)
        _backend_singleton = LocalStorageBackend(root)
        return _backend_singleton

    raise NotImplementedError(
        f"Storage provider {provider!r} is not implemented yet. "
        "Currently supported: 'local'. Add an S3/GCS backend class to extend."
    )
