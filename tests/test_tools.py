import pytest
from app.tools import safe_calculate
from database.db import Database

def test_safe_calculate_basic_arithmetic():
    assert safe_calculate("(1200 * 3) / 4") == 900
    assert safe_calculate("2 ** 3") == 8
    assert safe_calculate("-4 + 10") == 6

@pytest.mark.parametrize("expression", [
    "__import__('os').system('echo bad')",
    "open('secrets.txt')",
    "2 ** 99",
    "x + 1",
])
def test_safe_calculate_rejects_unsafe_expression(expression):
    with pytest.raises((ValueError, SyntaxError)):
        safe_calculate(expression)

def test_tasks_are_isolated_by_session(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    task_id = db.add_task("session-a", "Read the report")
    assert len(db.list_tasks("session-a")) == 1
    assert db.list_tasks("session-b") == []
    assert db.complete_task("session-b", task_id) is False
    assert db.complete_task("session-a", task_id) is True
    assert db.list_tasks("session-a")[0]["status"] == "done"

def test_message_history_round_trip(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.add_message("s1", "user", "Hello")
    db.add_message("s1", "assistant", "Hi")
    assert [m["content"] for m in db.get_messages("s1")] == ["Hello", "Hi"]
