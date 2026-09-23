from pathlib import Path

from app.core.config import Settings, _as_bool


def test_boolean_parser() -> None:
    assert _as_bool("true") is True
    assert _as_bool("oui") is True
    assert _as_bool("0", True) is False


def test_settings_creates_runtime_directories(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    settings = Settings.load(tmp_path)
    assert settings.data_dir.is_dir()
    assert settings.log_dir.is_dir()
    assert settings.database_path == tmp_path / "data" / "jarvis.db"

