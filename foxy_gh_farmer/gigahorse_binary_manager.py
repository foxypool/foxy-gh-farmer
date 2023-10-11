import tarfile
from logging import getLogger
from os.path import expanduser, join
from pathlib import Path
from platform import machine
from ssl import SSLContext
from sys import platform
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from aiohttp import ClientSession
from chia.server.server import ssl_context_for_root
from chia.ssl.create_ssl import get_mozilla_ca_crt

_gigahorse_release = "1.8.2.giga14"
_gigahorse_github_tag = f"v{_gigahorse_release}"
_gigahorse_release_archive_base = f"chia-gigahorse-farmer-{_gigahorse_release}"
_gigahorse_archive_root_dir = "chia-gigahorse-farmer"
_repo_download_url_base = "https://github.com/madMAx43v3r/chia-gigahorse/releases/download/"


class GigahorseBinaryManager:
    _cache_path: Path = Path(expanduser("~/.foxy-gh-farmer/bin-cache")).resolve()
    _ssl_context: SSLContext = ssl_context_for_root(get_mozilla_ca_crt())
    _logger = getLogger("binary_manager")

    async def get_binary_directory_path(self) -> Path:
        gigahorse_base_path = join(self._cache_path, _gigahorse_release)
        gigahorse_path = Path(join(gigahorse_base_path, _gigahorse_archive_root_dir))
        if gigahorse_path.exists():
            return gigahorse_path

        self._logger.info(f"Downloading Gigahorse {_gigahorse_release} ..")
        self._cache_path.mkdir(parents=True, exist_ok=True)
        archive_file_name = self._get_archive_file_name()
        with TemporaryDirectory() as temp_dir:
            archive_path = join(temp_dir, archive_file_name)
            await self._download_release(archive_path)
            self._extract_file(archive_path, gigahorse_base_path)

        return gigahorse_path

    def _extract_file(self, archive_file_path: str, destination_path: str):
        if archive_file_path.endswith(".zip"):
            with ZipFile(archive_file_path, 'r') as zip_ref:
                zip_ref.extractall(destination_path)

            return
        if archive_file_path.endswith(".tar.gz"):
            file = tarfile.open(archive_file_path)
            file.extractall(destination_path)
            file.close()

            return

        raise RuntimeError(f"Can not extract {archive_file_path}, unsupported extension")

    async def _download_release(self, to_path: str):
        chunk_size = 5 * 2**20  # MB
        async with ClientSession() as client:
            async with client.get(self._get_release_download_url(), ssl=self._ssl_context) as res:
                with open(to_path, 'wb') as fd:
                    async for chunk in res.content.iter_chunked(chunk_size):
                        fd.write(chunk)

    def _get_release_download_url(self):
        return f"{_repo_download_url_base}/{_gigahorse_github_tag}/{self._get_archive_file_name()}"

    def _get_archive_file_name(self):
        if platform == "win32":
            return f"{_gigahorse_release_archive_base}-windows.zip"
        if machine() == "aarch64":
            return f"{_gigahorse_release_archive_base}-aarch64.tar.gz"

        return f"{_gigahorse_release_archive_base}-x86_64.tar.gz"
