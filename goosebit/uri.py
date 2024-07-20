import copy
import dataclasses
import urllib.parse
from pathlib import Path
from urllib.parse import ParseResultBytes


@dataclasses.dataclass
class RemoteFirmwareURI:
    url: urllib.parse.ParseResult

    local = False

    def join(self, *other: str):
        remote_path = Path(self.url.path).joinpath(*other)
        url_copy = copy.copy(self.url)
        url_copy.path = str(remote_path)
        return url_copy

    def mkdir(self, *args, **kwargs):
        raise OSError("Cannot create directory on remote server.")

    def iterdir(self):
        # need to loop through remote files here somehow, then yield them.
        # may need to grab the directory structure on startup?
        return


@dataclasses.dataclass
class LocalFirmwareURI:
    path: Path

    local = True

    def join(self, *other: str):
        return LocalFirmwareURI(path=self.path.joinpath(*other))

    def mkdir(self, *args, **kwargs):
        return self.path.mkdir(*args, **kwargs)

    def iterdir(self):
        return self.path.iterdir()

    def __str__(self):
        return str(self.path)
