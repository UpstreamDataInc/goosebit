from typing import Any

from goosebit.settings import schema
from goosebit.settings.schema import GooseBitSettings, secret_key_was_generated


def test_secret_key_from_env_is_not_generated(monkeypatch: Any) -> None:
    # observe this construction in isolation
    monkeypatch.setattr(schema, "_secret_key_generated", False)
    monkeypatch.setenv("GOOSEBIT_SECRET_KEY", "my_very_top_secret_key123")

    settings = GooseBitSettings()

    assert settings.secret_key is not None
    assert secret_key_was_generated() is False


def test_secret_key_is_generated_when_absent(monkeypatch: Any) -> None:
    # observe this construction in isolation
    monkeypatch.setattr(schema, "_secret_key_generated", False)
    # no settings source provides a secret_key
    monkeypatch.delenv("GOOSEBIT_SECRET_KEY", raising=False)
    monkeypatch.delenv("GOOSEBIT_SETTINGS", raising=False)

    settings = GooseBitSettings()

    assert settings.secret_key is not None
    assert secret_key_was_generated() is True
