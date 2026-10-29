import fitz
import pytest
from app.document_reader import DocumentError, extract_text

def test_extract_txt():
    assert extract_text("notes.txt", b"Hello\\nWorld") == "Hello\\nWorld"

def test_rejects_unsupported_extension():
    with pytest.raises(DocumentError):
        extract_text("notes.docx", b"not a docx")

def test_extract_pdf_from_memory():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Personal AI Agent test")
    content = doc.tobytes()
    doc.close()
    assert "Personal AI Agent test" in extract_text("test.pdf", content)

def test_truncates_long_text():
    result = extract_text("notes.txt", b"a" * 30, max_chars=10)
    assert result.startswith("a" * 10)
    assert "truncated" in result.lower()
