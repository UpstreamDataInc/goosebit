from functools import total_ordering

from semver import Version as SemVersion


# Class that replicates version handling of swupdate. For reference see
# * https://sbabic.github.io/swupdate/sw-description.html#versioning-schemas-in-swupdate
# * https://github.com/sbabic/swupdate/blob/60322d5ad668e5603341c5f42b3c51d0a1c60226/core/artifacts_versions.c#L158
# * https://github.com/sbabic/swupdate/blob/60322d5ad668e5603341c5f42b3c51d0a1c60226/core/artifacts_versions.c#L217
@total_ordering
class Version:
    version_str: str
    default_version: int | None
    sem_version: SemVersion

    def __init__(self, version_str: str, default_version: int | None = None, sem_version: SemVersion = None):
        self.version_str = version_str
        self.default_version = default_version
        self.sem_version = sem_version

    @staticmethod
    def parse(version_str: str):
        default_version = Version._default_version_to_number(version_str)
        sem_version = None
        try:
            sem_version = SemVersion.parse(version_str, optional_minor_and_patch=True)
        except (TypeError, ValueError):
            pass

        if not default_version and not sem_version:
            raise ValueError(f"{version_str} is not valid swupdate version")

        return Version(version_str, default_version, sem_version)

    def __str__(self):
        return self.version_str

    def __eq__(self, other):
        # support comparison with strings as a convenience
        if isinstance(other, str):
            try:
                other = Version.parse(other)
            except ValueError:
                return False

        if not isinstance(other, Version):
            return NotImplemented

        if self.default_version and other.default_version:
            return self.default_version == other.default_version

        if self.sem_version and other.sem_version:
            return self.sem_version == other.sem_version

        # fallback to lexical comparison of no of the same type
        return self.version_str == other.version_str

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented

        if self.default_version and other.default_version:
            return self.default_version < other.default_version

        if self.sem_version and other.sem_version:
            return self.sem_version < other.sem_version

        # fallback to lexical comparison of no of the same type
        return self.version_str < other.version_str

    @staticmethod
    def _default_version_to_number(version_string: str) -> int | None:
        parts = version_string.split(".")
        count = min(len(parts), 4)
        version = 0

        for i in range(count):
            try:
                fld = int(parts[i])
            except ValueError:
                return None

            if fld > 0xFFFF:
                print(f"Version {version_string} had an element > 65535, falling back to semver")
                return None

            version = (version << 16) | fld

        if count < 4:
            version <<= 16 * (4 - count)

        return version
