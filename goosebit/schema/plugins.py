import inspect
from typing import Any, Awaitable, Callable, Type

from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, computed_field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from goosebit.db import Device
from goosebit.device_manager import HandlingType
from goosebit.schema.updates import UpdateChunk
from goosebit.settings import config


def get_module_name():
    module = inspect.getmodule(inspect.stack()[2][0])
    if module is not None:
        return module.__name__.split(".")[0]
    raise TypeError("Could not discover plugin module name")


class PluginSchema(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    name: str = Field(
        default_factory=get_module_name
    )  # get the name of the package this was initialized in (plugin package)
    middleware: Type[Any] | None = None  # ASGI middleware class
    router: APIRouter | None = None
    db_model_path: str | None = None
    static_files: StaticFiles | None = None
    templates: Jinja2Templates | None = None
    update_source_hook: Callable[[Request, Device], Awaitable[tuple[HandlingType, UpdateChunk | None]]] | None = None
    config_data_hook: Callable[[Device, dict[str, Any]], Awaitable[None]] | None = None

    @computed_field  # type: ignore[misc]
    @property
    def url_prefix(self) -> str:
        return f"/plugins/{self.name}"

    @computed_field  # type: ignore[misc]
    @property
    def static_files_name(self) -> str:
        return f"{self.name}_static"


class PluginSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return tuple([env_settings, YamlConfigSettingsSource(settings_cls, config.config_file)])
