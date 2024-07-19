import dataclasses
import urllib.parse
from pathlib import Path
from urllib.parse import ParseResultBytes


@dataclasses.dataclass
class FirmwareURI:
    path: ParseResultBytes | Path

    def join(self, *other: str):
        if isinstance(self.path, Path):
            return FirmwareURI(path=self.path.joinpath(*other))
        else:
            return FirmwareURI(
                path=urllib.parse.urlparse(
                    urllib.parse.urljoin(
                        urllib.parse.urlunparse(self.path), "/".join(other)
                    )
                )
            )

    @property
    def local(self):
        return isinstance(self.path, Path)

    def mkdir(self, *args, **kwargs):
        if self.local:
            return self.path.mkdir(*args, **kwargs)
        raise AttributeError(f"Could not create remote directory on server: {str(self)}")

    def iterdir(self):
        if self.local:
            return self.path.iterdir()
        raise AttributeError(f"Could not iterate remote directory on server: {str(self)}")

    def __str__(self):
        return str(self.path)