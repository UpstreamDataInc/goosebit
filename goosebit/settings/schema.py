import os
import secrets
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


class PrometheusSettings(BaseModel):
    enable: bool = False


class MetricsSettings(BaseModel):
    prometheus: PrometheusSettings = PrometheusSettings()


class GooseBitSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GOOSEBIT_")

    port: int = 60053  # GOOSE

    poll_time_default: str = "00:01:00"
    poll_time_updating: str = "00:00:05"
    poll_time_registration: str = "00:00:10"

    secret_key: Annotated[OctKey, BeforeValidator(OctKey.import_key)] = secrets.token_hex(16)

    users: list[User] = []

    db_uri: str = f"sqlite:///{GOOSEBIT_ROOT_DIR.joinpath('db.sqlite3')}"
    artifacts_dir: Path = GOOSEBIT_ROOT_DIR.joinpath("artifacts")

    metrics: MetricsSettings = MetricsSettings()

    logging: dict = LOGGING_DEFAULT

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
