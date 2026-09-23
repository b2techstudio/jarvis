from pathlib import Path

from app.tools.apps import ApplicationResolver


def test_custom_application_mapping(tmp_path: Path) -> None:
    executable = tmp_path / "demo.exe"
    executable.touch()
    resolver = ApplicationResolver({"démo": str(executable)})
    assert resolver.resolve("DÉMO") == str(executable)


def test_unknown_application() -> None:
    assert ApplicationResolver().resolve("application-inexistante-xyz") is None

