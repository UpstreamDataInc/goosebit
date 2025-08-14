import os
import secrets
from enum import StrEnum
from pathlib import Path
from typing import Annotated

from joserfc.jwk import OctKey
from pydantic import BaseModel, BeforeValidator, Field, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from .const import CURRENT_DIR, GOOSEBIT_ROOT_DIR, LOGGING_DEFAULT


class DeviceAuthMode(StrEnum):
    SETUP = "setup"  # setup mode, any devices polling with an auth token that don't have one will save it
    STRICT = "strict"  # all devices must have keys, and all keys must be set up with the API
    EXTERNAL = "external"  # all devices must have keys, keys must be validated by external auth service
    LAX = "lax"  # devices may or may not use keys, but device with keys set must poll with them


class ExternalAuthMode(StrEnum):
    BEARER = "bearer"  # validate token with external service using Bearer token
    JSON = "json"  # validate token with external service using JSON payload


class DeviceAuthSettings(BaseModel):
    enable: bool = False
    mode: DeviceAuthMode = DeviceAuthMode.STRICT
    external_url: str | None = None
    external_mode: ExternalAuthMode = ExternalAuthMode.JSON
    external_json_key: str = "token"

    @model_validator(mode="after")
    def validate_external_mode_config(self):
        if self.mode == DeviceAuthMode.EXTERNAL:
            if self.external_url is None:
                raise ValueError("External URL is required when using external authentication mode")
            if self.external_mode == ExternalAuthMode.JSON and not self.external_json_key:
                raise ValueError("External JSON key is required when using JSON mode")
        return self


class PrometheusSettings(BaseModel):
    enable: bool = False


class MetricsSettings(BaseModel):
    prometheus: PrometheusSettings = PrometheusSettings()


class StorageType(StrEnum):
    FILESYSTEM = "filesystem"
    S3 = "s3"


class S3StorageSettings(BaseModel):
    bucket: str
    region: str = "us-east-1"
    endpoint_url: str | None = None
    access_key_id: str | None = None
    secret_access_key: str | None = None


class StorageSettings(BaseModel):
    backend: StorageType = StorageType.FILESYSTEM
    s3: S3StorageSettings | None = None


class GooseBitSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GOOSEBIT_", extra="ignore", env_nested_delimiter="__")

    port: int = 60053  # GOOSE
    tenant: str = "DEFAULT"

    poll_time: str = "00:01:00"

    max_concurrent_updates: int = 1000

    device_auth: DeviceAuthSettings = DeviceAuthSettings()

    secret_key: Annotated[OctKey, BeforeValidator(OctKey.import_key)] = secrets.token_hex(16)

    plugins: list[str] = Field(default_factory=list)

    db_uri: str = f"sqlite:///{GOOSEBIT_ROOT_DIR.joinpath('db.sqlite3')}"
    db_ssl_crt: Path | None = None

    artifacts_dir: Path = GOOSEBIT_ROOT_DIR.joinpath("artifacts")

    storage: StorageSettings = StorageSettings()

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
