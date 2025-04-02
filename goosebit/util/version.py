from functools import total_ordering

from semver import Version as SemVersion


@total_ordering
class Version:
    def __init__(self, sem_version: SemVersion):
        self.sem_version = sem_version

    @staticmethod
    def parse(version_str: str):
        return Version(SemVersion.parse(version_str, optional_minor_and_patch=True))

    def __str__(self):
        return str(self.sem_version)

    def __eq__(self, other):
        if isinstance(other, str):
            try:
                other = Version.parse(other)
            except ValueError:
                return False

        if not isinstance(other, Version):
            return NotImplemented

        return self.sem_version == other.sem_version

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self.sem_version < other.sem_version
