import os
import secrets
from enum import StrEnum
from pathlib import Path
from typing import Annotated

from joserfc.rfc7518.oct_key import OctKey
from pydantic import BaseModel, BeforeValidator, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from .const import CURRENT_DIR, GOOSEBIT_ROOT_DIR, LOGGING_DEFAULT, PWD_CXT


class User(BaseModel):
    username: str
    hashed_pwd: Annotated[str, BeforeValidator(PWD_CXT.hash)] = Field(validation_alias="password")
    permissions: set[str]

    def get_json_permissions(self):
        return [str(p) for p in self.permissions]


class DeviceAuthMode(StrEnum):
    SETUP = "setup"  # setup mode, any devices polling with an auth token that don't have one will save it
    STRICT = "strict"  # all devices must have keys, and all keys must be set up with the API
    LAX = "lax"  # devices may or may not use keys, but device with keys set must poll with them


class DeviceAuthSettings(BaseModel):
    enable: bool = False
    mode: DeviceAuthMode = DeviceAuthMode.STRICT


class PrometheusSettings(BaseModel):
    enable: bool = False


class MetricsSettings(BaseModel):
    prometheus: PrometheusSettings = PrometheusSettings()


class GooseBitSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GOOSEBIT_")

    port: int = 60053  # GOOSE

    poll_time: str = "00:01:00"

    device_auth: DeviceAuthSettings = DeviceAuthSettings()

    secret_key: Annotated[OctKey, BeforeValidator(OctKey.import_key)] = secrets.token_hex(16)

    users: list[User] = Field(default_factory=list)

    plugins: list[str] = Field(default_factory=list)

    db_uri: str = f"sqlite:///{GOOSEBIT_ROOT_DIR.joinpath('db.sqlite3')}"
    artifacts_dir: Path = GOOSEBIT_ROOT_DIR.joinpath("artifacts")

    metrics: MetricsSettings = MetricsSettings()

    logging: dict = LOGGING_DEFAULT

    track_device_ip: bool = True

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        settings_sources = [env_settings]
        config_files = []

        if (path := os.getenv("GOOSEBIT_SETTINGS")) is not None:
            config_files.append(Path(path))

        config_files.extend(
            [
                CURRENT_DIR.joinpath("goosebit.yaml"),
                GOOSEBIT_ROOT_DIR.joinpath("goosebit.yaml"),
                Path("/etc/goosebit.yaml"),
            ]
        )

        cls.config_file = None
        for config_file in config_files:
            if config_file.exists():
                settings_sources.append(
                    YamlConfigSettingsSource(settings_cls, config_file),
                )
                cls.config_file = config_file
                break
        return tuple(settings_sources)
