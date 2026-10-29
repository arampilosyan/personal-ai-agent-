from pathlib import Path
import fitz

SUPPORTED_EXTENSIONS = {".pdf", ".txt"}

class DocumentError(ValueError):
    pass

def extract_text(filename: str, content: bytes, max_chars: int = 50_000) -> str:
    """Extract text from PDF/TXT bytes; no files are written to disk."""
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise DocumentError("Only PDF and TXT files are supported.")
    if not content:
        raise DocumentError("The uploaded file is empty.")
    try:
        if suffix == ".txt":
            text = content.decode("utf-8-sig")
        else:
            with fitz.open(stream=content, filetype="pdf") as pdf:
                text = "\n".join(page.get_text("text") for page in pdf)
    except (UnicodeDecodeError, fitz.FileDataError, RuntimeError) as exc:
        raise DocumentError("Could not read this file. Check that it is a valid UTF-8 TXT or PDF.") from exc
    text = text.strip()
    if not text:
        raise DocumentError("No readable text was found. Scanned PDFs may need OCR first.")
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[Text truncated at configured safety limit.]"
    return text
