import datetime
from pathlib import Path
from typing import Optional

from fastapi.requests import Request

from goosebit.settings import TOKEN_SWU_DIR, UPDATES_DIR
from goosebit.updater.misc import get_newest_fw, sha1_hash_file


class FirmwareArtifact:
    def __init__(self, file: str = None, dev_id: str = None):
        if file == "latest":
            self.file = get_newest_fw()
        elif file == "pinned":
            self.file = None
        else:
            self.file = file
        self.dev_id = dev_id

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        elif isinstance(other, FirmwareArtifact):
            return self.file == other.file
        return False

    def is_empty(self) -> bool:
        return self.file is None

    def file_exists(self) -> bool:
        if self.is_empty():
            return False
        if self.file == "cloudflared.swu":
            return True
        return self.path.exists()

    @property
    def name(self):
        if not self.is_empty():
            return self.file.split(".")[0]

    @property
    def version(self):
        if not self.is_empty():
            return "_".join(self.name.split("_")[2:])

    @property
    def timestamp(self):
        return datetime.datetime.strptime(self.version, "%Y%m%d_%H%M%S")

    @property
    def path(self) -> Optional[Path]:
        if not self.is_empty():
            if self.file == "cloudflared.swu":
                return TOKEN_SWU_DIR.joinpath(self.dev_id, self.file)
            return UPDATES_DIR.joinpath(self.file)

    @property
    def dl_endpoint(self):
        if self.file == "cloudflared.swu":
            return "download_cfd_conf"
        return "download_file"

    def generate_chunk(self, request: Request, tenant: str, dev_id: str) -> list:
        if not self.file_exists():
            return []
        return [
            {
                "part": "os",
                "version": "1",
                "name": self.file,
                "artifacts": [
                    {
                        "filename": self.file,
                        "hashes": {"sha1": sha1_hash_file(self.path)},
                        "size": self.path.stat().st_size,
                        "_links": {
                            "download": {
                                "href": str(
                                    request.url_for(
                                        self.dl_endpoint,
                                        tenant=tenant,
                                        dev_id=dev_id,
                                        file=self.file,
                                    )
                                )
                            }
                        },
                    }
                ],
            }
        ]
