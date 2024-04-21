"""Defines OCI transport adapter for CondaSession (requests.Session)."""
from __future__ import annotations

import json
import os
from email.utils import formatdate
from logging import getLogger
from mimetypes import guess_type
from os import stat
from tempfile import SpooledTemporaryFile
from typing import TYPE_CHECKING

from conda_oci_mirror.repo import PackageRepo

from conda.common.compat import ensure_binary
from conda.models.dist import Dist
from conda.plugins.types import ChannelBaseAdapter
from conda.gateways.connection import (
    CaseInsensitiveDict,
    Response,
)

log = getLogger(__name__)

if TYPE_CHECKING:
    from .. import PreparedRequest

cache_dir = os.path.join(os.getcwd(), 'cache')
# repo = PackageRepo('conda-forge', 'linux-64', cache_dir, registry='http://127.0.0.1:5000/dinosaur')


class OCIAdapter(ChannelBaseAdapter):
    def get_repo(self, registry: str, cache_dir: str | None = None) -> PackageRepo:
        # http://127.0.0.1:5000/dinosaur/conda-forge/linux-64/zlib:1.2.11-0'
        registry, channel = registry.rsplit('/', 1)
        return PackageRepo(
            channel=channel,
            registry=registry,
            cache_dir=cache_dir,
        )

    def send(
        self,
        request: PreparedRequest,
        stream: bool = False,
        timeout: None | float | tuple[float, float] | tuple[float, None] = None,
        verify: bool | str = True,
        cert: None | bytes | str | tuple[bytes | str, bytes | str] = None,
        proxies: dict[str, str] | None = None,
    ) -> Response:
        if request.url.startswith(("oci+http://", "oci+https://")):
            request.url = request.url.replace("oci+", "")
        dist = Dist.from_url(request.url)
        repo = self.get_repo(registry=self.channel_name)
        pathname = repo.get_package(f"{dist.name}:{dist.version}")

        breakpoint()

        resp = Response()
        resp.status_code = 200
        resp.url = request.url

        try:
            stats = stat(pathname)
        except OSError as exc:
            resp.status_code = 404
            message = {
                "error": "file does not exist",
                "path": pathname,
                "exception": repr(exc),
            }
            fh = SpooledTemporaryFile()
            fh.write(ensure_binary(json.dumps(message)))
            fh.seek(0)
            resp.raw = fh
            resp.close = resp.raw.close
        else:
            modified = formatdate(stats.st_mtime, usegmt=True)
            content_type = guess_type(pathname)[0] or "text/plain"
            resp.headers = CaseInsensitiveDict(
                {
                    "Content-Type": content_type,
                    "Content-Length": stats.st_size,
                    "Last-Modified": modified,
                }
            )

            resp.raw = open(pathname, "rb")
            resp.close = resp.raw.close
        return resp

    def close(self) -> None:
        pass  # pragma: no cover
