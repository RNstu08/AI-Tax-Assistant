# tests/unit/test_file_safety.py
from app.safety.files import sanitize_filename, validate_file


def test_sanitize_filename():
    assert " " not in sanitize_filename("my receipt.pdf")


def test_validate_file():
    assert validate_file("application/pdf", 1000)[0]
    assert not validate_file("application/zip", 1000)[0]
    assert not validate_file("image/png", 8 * 1024 * 1024)[0]
