from pathlib import Path

from app.memory.database import Database
from app.memory.repository import NoteRepository


def test_note_round_trip(tmp_path: Path) -> None:
    database = Database(tmp_path / "test.db")
    database.initialize()
    repository = NoteRepository(database)
    created = repository.add("Acheter du café", "courses")
    notes = repository.recent()
    assert created.id > 0
    assert notes[0].text == "Acheter du café"
    assert notes[0].category == "courses"


def test_empty_note_is_rejected(tmp_path: Path) -> None:
    database = Database(tmp_path / "test.db")
    database.initialize()
    repository = NoteRepository(database)
    try:
        repository.add("   ")
        raise AssertionError("empty note should fail")
    except ValueError:
        pass

