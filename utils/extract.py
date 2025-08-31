"""utils/extract.py

Lightweight, readable helpers for pulling text out of PDFs and images.
Design goals: keep it human-friendly, preserve layout when asked, and
gracefully fall back to OCR for scans — without surprising the reader.
"""
import io
import os
import re
from typing import List, Optional

import pdfplumber
from pdfminer.high_level import extract_text as pdfminer_extract
from pdfminer.layout import LAParams
from pdf2image import convert_from_bytes
from PIL import Image, ImageOps, ImageFilter
import pytesseract


# ---------- Windows helpers (optional) ----------
# If you installed Poppler but didn't add it to PATH, set it here once:
POPPLER_PATH = os.getenv("POPPLER_PATH") or os.getenv("POPPLER_BIN")
if not POPPLER_PATH or not os.path.isdir(POPPLER_PATH):
    for _cand in [
        r"C:\\Poppler\\poppler-25.07.0\\Library\\bin",
        r"C:\\Program Files\\poppler\\bin",
    ]:
        if os.path.isdir(_cand):
            POPPLER_PATH = _cand
            break
# If Tesseract isn’t on PATH, set it once:
TESSERACT_CMD = os.getenv("TESSERACT_CMD", None)  # e.g., r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


# ---------- Additional configuration/detection ----------
# Preserve original layout: newlines and spacing kept where possible
PRESERVE_FORMATTING = os.getenv("PRESERVE_FORMATTING", "1").lower() not in {"0", "false", "no"}

def _ensure_tesseract_path() -> None:
    """If Tesseract isn't on PATH and no TESSERACT_CMD provided, try common Windows locations."""
    try:
        current = getattr(pytesseract.pytesseract, "tesseract_cmd", None)
        if current:
            return
    except Exception:
        pass
    for c in [
        r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
        r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
    ]:
        if os.path.isfile(c):
            pytesseract.pytesseract.tesseract_cmd = c
            break

_ensure_tesseract_path()

# ---------- Text utilities ----------
def _normalize_hyphenation_and_spaces(text: str) -> str:
    if not text:
        return ""
    # Join broken words across line-break hyphens: "trans-\nform" → "transform"
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    # Trim extra spaces on line boundaries
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    # Collapse >2 newlines to max 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _join_soft_linebreaks_keep_paragraphs(text: str) -> str:
    """Convert single linebreaks inside paragraphs to spaces, keep blank lines."""
    if not text:
        return ""
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = t.replace("\n\n", "<<<P>>>")
    t = t.replace("\n", " ")
    t = t.replace("<<<P>>>", "\n\n")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def _postprocess_text(text: str, preserve: bool) -> str:
    """Apply minimal or friendly normalization depending on preserve flag."""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if preserve:
        # Minimal cleanup: keep line breaks; trim trailing spaces; cap blank lines at 2
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
    # Non-preserve: join soft breaks and fix hyphenation for social-friendly text
    return _join_soft_linebreaks_keep_paragraphs(_normalize_hyphenation_and_spaces(text))


# ---------- PDF (digital text) extraction with layout ----------
def _extract_with_pdfplumber(pdf_bytes: bytes) -> str:
    out_lines: List[str] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            # x_tolerance/y_tolerance help group characters into words/lines
            text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            if text.strip():
                out_lines.append(text.strip())
    return _postprocess_text("\n\n".join(out_lines), PRESERVE_FORMATTING)


def _extract_with_pdfminer(pdf_bytes: bytes) -> str:
    laparams = LAParams(
        line_overlap=0.5,
        char_margin=2.0,
        word_margin=0.1,
        line_margin=0.15,
        boxes_flow=0.5,
        all_texts=True,
    )
    text = pdfminer_extract(io.BytesIO(pdf_bytes), laparams=laparams) or ""
    return _postprocess_text(text, PRESERVE_FORMATTING)


# ---------- OCR pre-processing ----------
def _prep_for_ocr(img: Image.Image) -> Image.Image:
    """
    Light, safe pre-processing that helps Tesseract without distorting text:
    - convert to grayscale
    - auto-contrast
    - slight sharpening
    - slight binarization
    """
    g = ImageOps.grayscale(img)
    g = ImageOps.autocontrast(g)
    g = g.filter(ImageFilter.SHARPEN)
    # light threshold: keep it gentle to avoid losing thin fonts
    g = g.point(lambda p: 255 if p > 200 else (0 if p < 80 else p))
    return g


def _ocr_image(img: Image.Image, psm: int = 6) -> str:
    img = _prep_for_ocr(img)
    cfg = f"--oem 3 --psm {psm}"
    if PRESERVE_FORMATTING:
        cfg += " -c preserve_interword_spaces=1"
    return pytesseract.image_to_string(img, lang="eng", config=cfg)


# ---------- PDF (scanned) OCR ----------
def _ocr_scanned_pdf(pdf_bytes: bytes) -> str:
    images = convert_from_bytes(
        pdf_bytes,
        dpi=300,  # 300 DPI is the sweet spot for documents
        poppler_path=POPPLER_PATH
    )
    page_texts: List[str] = []
    for idx, img in enumerate(images, start=1):
        txt = _ocr_image(img, psm=6).strip()
        if txt:
            page_texts.append(txt)
    return _postprocess_text("\n\n".join(page_texts), PRESERVE_FORMATTING)


# ---------- Public API ----------
def extract_text_from_pdf(file_stream) -> str:
    """
    Best-effort PDF extraction:
      1) Try pdfplumber (layout-friendly).
      2) Try pdfminer with tuned LAParams.
      3) If still empty, treat as scanned PDF and OCR at 300 DPI.
    """
    try:
        if hasattr(file_stream, "seek"):
            file_stream.seek(0)
        pdf_bytes = file_stream.read()

        # Step 1: layout-preserving text extraction
        text_plumber = _extract_with_pdfplumber(pdf_bytes)
        if text_plumber and len(text_plumber) > 10:
            return text_plumber

        # Step 2: pdfminer tuned
        text_miner = _extract_with_pdfminer(pdf_bytes)
        if text_miner and len(text_miner) > 10:
            return text_miner

        # Step 3: scanned PDF OCR
        ocr_text = _ocr_scanned_pdf(pdf_bytes)
        return ocr_text if ocr_text else "No text found (even with OCR)."

    except Exception as e:
        return f"Error extracting PDF text: {e}"


def extract_text_from_image(file_stream) -> str:
    """OCR for image uploads with gentle pre-processing."""
    try:
        if hasattr(file_stream, "seek"):
            file_stream.seek(0)
        img = Image.open(io.BytesIO(file_stream.read()))
        txt = _ocr_image(img, psm=6).strip()
        return _postprocess_text(txt, PRESERVE_FORMATTING)
    except Exception as e:
        return f"Error extracting image text: {e}"
