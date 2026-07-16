from typing import Any

from goosebit.cache import configured_worker_count


def test_no_env_vars_defaults_to_one(monkeypatch: Any) -> None:
    monkeypatch.delenv("GUNICORN_CMD_ARGS", raising=False)
    monkeypatch.delenv("WEB_CONCURRENCY", raising=False)
    assert configured_worker_count() == 1


def test_web_concurrency(monkeypatch: Any) -> None:
    monkeypatch.delenv("GUNICORN_CMD_ARGS", raising=False)
    monkeypatch.setenv("WEB_CONCURRENCY", "3")
    assert configured_worker_count() == 3


def test_gunicorn_cmd_args_takes_precedence(monkeypatch: Any) -> None:
    monkeypatch.setenv("GUNICORN_CMD_ARGS", "--workers 4 --enable-stdio-inheritance")
    monkeypatch.setenv("WEB_CONCURRENCY", "3")
    assert configured_worker_count() == 4


def test_workers_equals_syntax(monkeypatch: Any) -> None:
    monkeypatch.delenv("WEB_CONCURRENCY", raising=False)
    monkeypatch.setenv("GUNICORN_CMD_ARGS", "--workers=2")
    assert configured_worker_count() == 2


def test_short_flag_with_space(monkeypatch: Any) -> None:
    monkeypatch.delenv("WEB_CONCURRENCY", raising=False)
    monkeypatch.setenv("GUNICORN_CMD_ARGS", "-w 8")
    assert configured_worker_count() == 8


def test_short_flag_without_space(monkeypatch: Any) -> None:
    monkeypatch.delenv("WEB_CONCURRENCY", raising=False)
    monkeypatch.setenv("GUNICORN_CMD_ARGS", "-w4")
    assert configured_worker_count() == 4


def test_garbage_values_default_to_one(monkeypatch: Any) -> None:
    monkeypatch.setenv("GUNICORN_CMD_ARGS", "--enable-stdio-inheritance")
    monkeypatch.setenv("WEB_CONCURRENCY", "not-a-number")
    assert configured_worker_count() == 1


def test_empty_values_default_to_one(monkeypatch: Any) -> None:
    monkeypatch.setenv("GUNICORN_CMD_ARGS", "")
    monkeypatch.setenv("WEB_CONCURRENCY", "")
    assert configured_worker_count() == 1
