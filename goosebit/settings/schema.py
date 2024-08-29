import secrets
import sys
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

from .args import parser
from .const import BASE_DIR, LOGGING_DEFAULT, PWD_CXT


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

    users: list[User] = [User(username="admin@goosebit.local", password="admin", permissions=["*"])]

    db_uri: str = f"sqlite:///{BASE_DIR.joinpath('db.sqlite3')}"
    migrations_dir: Path = BASE_DIR.joinpath("migrations")
    artifacts_dir: Path = BASE_DIR.joinpath("artifacts")

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
        # skip arg parsing if running pytest
        if "pytest" not in sys.modules:
            cli_args = parser.parse_args()
            return (
                init_settings,
                YamlConfigSettingsSource(settings_cls, cli_args.settings_file),
                env_settings,
                file_secret_settings,
            )
        return (
            init_settings,
            env_settings,
            file_secret_settings,
        )
