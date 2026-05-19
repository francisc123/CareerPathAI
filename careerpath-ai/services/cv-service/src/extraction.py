import io
import pdfplumber
import fitz
import docx
import pytesseract
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def _sanitize(text: str) -> str:
    """Postgres respinge NULL bytes (0x00) în coloanele TEXT/VARCHAR. Unele PDF-uri
    (mai ales cele exportate din browser) conțin \\x00 în text. Le strip-uim aici
    plus alte control chars problematice — păstrăm \\n, \\r, \\t."""
    if not text:
        return ""
    return "".join(
        ch for ch in text
        if ch in ("\n", "\r", "\t") or ord(ch) >= 0x20
    )


def extract_text_from_bytes(file_bytes: bytes, mime_type: str) -> str:
    """Extrage textul din fișier în funcție de tipul MIME."""

    # 1. PDF
    if mime_type == 'application/pdf':
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
                if text.strip():
                    return _sanitize(text)
                raise ValueError("pdfplumber nu a găsit text (posibil scan).")
        except Exception as e:
            logger.warning(f"pdfplumber a eșuat ({e}), trecem la fallback PyMuPDF (fitz)...")
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                return _sanitize("\n".join(page.get_text() for page in doc))
            except Exception as fitz_e:
                logger.error(f"Fallback PyMuPDF a eșuat: {fitz_e}")
                return ""

    # 2. DOCX
    elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            return _sanitize("\n".join(para.text for para in doc.paragraphs))
        except Exception as e:
            logger.error(f"Eroare extragere DOCX: {e}")
            return ""

    # 3. Imagine -> OCR
    elif mime_type in ['image/jpeg', 'image/jpg']:
        try:
            img = Image.open(io.BytesIO(file_bytes))
            return _sanitize(pytesseract.image_to_string(img))
        except Exception as e:
            logger.error(f"Eroare OCR: {e}")
            return ""

    return ""