import logging
import io
import numpy as np
from PIL import Image
from typing import Optional, Tuple
from app.config import settings
from app.ingestion.preprocessor import preprocess_image_cv

logger = logging.getLogger(__name__)

# Lazy singleton for OCR engine
_PADDLE_OCR = None
_PADDLE_INITIALIZED = False


def get_ocr_engine():
    global _PADDLE_OCR, _PADDLE_INITIALIZED
    if _PADDLE_INITIALIZED:
        return _PADDLE_OCR

    _PADDLE_INITIALIZED = True
    try:
        from paddleocr import PaddleOCR
        # Initialize PaddleOCR with English language, angle classifier enabled
        _PADDLE_OCR = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        logger.info("PaddleOCR engine initialized successfully.")
    except Exception as e:
        logger.warning(f"PaddleOCR could not be loaded: {e}. Trying pytesseract fallback.")
        try:
            import pytesseract
            _PADDLE_OCR = "pytesseract"
            logger.info("Pytesseract fallback OCR engine detected.")
        except Exception as e2:
            logger.warning(f"No external OCR engine found ({e2}). Using lightweight visual OCR fallback.")
            _PADDLE_OCR = None

    return _PADDLE_OCR


def detect_ocr_needed(page_text: str, page_width: float = 612.0, page_height: float = 792.0) -> bool:
    """
    Determines if OCR is required for a page based on printable character density.
    Standard Letter page is 612x792 pt. If char count is negligible (< 50 chars or < threshold density),
    page is deemed a scanned / image document.
    """
    if not page_text or len(page_text.strip()) == 0:
        return True

    text_chars = len(page_text.strip())
    # If text is extremely short on a full page, likely an image/scanned artifact
    if text_chars < 50:
        return True

    # Character density per square inch (72 points/inch)
    page_area_sq_in = (page_width * page_height) / (72.0 * 72.0)
    if page_area_sq_in > 0:
        density = text_chars / page_area_sq_in
        if density < settings.OCR_DENSITY_THRESHOLD * 100:
            return True

    return False


def run_ocr_on_image(image_input) -> str:
    """
    Executes OCR pipeline on an image (PIL Image, numpy array, or bytes):
    1. Converts to numpy array
    2. Runs OpenCV preprocessing (deskew, binarize, denoise)
    3. Feeds preprocessed image to PaddleOCR (or fallback)
    4. Formats detected text into coherent lines
    """
    if not settings.OCR_ENABLED:
        logger.info("OCR is disabled in settings.")
        return ""

    try:
        # Convert image_input to numpy array (BGR)
        if isinstance(image_input, bytes):
            pil_img = Image.open(io.BytesIO(image_input)).convert("RGB")
            np_img = np.array(pil_img)[:, :, ::-1].copy()
        elif isinstance(image_input, Image.Image):
            rgb_img = image_input.convert("RGB")
            np_img = np.array(rgb_img)[:, :, ::-1].copy()
        elif isinstance(image_input, np.ndarray):
            np_img = image_input.copy()
        else:
            logger.error(f"Unsupported image format for OCR: {type(image_input)}")
            return ""

        # Run OpenCV preprocessing
        preprocessed = preprocess_image_cv(np_img)

        ocr_engine = get_ocr_engine()

        if ocr_engine == "pytesseract":
            import pytesseract
            pil_prep = Image.fromarray(preprocessed)
            text = pytesseract.image_to_string(pil_prep)
            return text.strip()

        if ocr_engine is not None and hasattr(ocr_engine, "ocr"):
            # PaddleOCR returns list of lines: [[[[x1,y1],...], ("text", confidence)], ...]
            result = ocr_engine.ocr(preprocessed, cls=True)
            extracted_lines = []
            if result and len(result) > 0 and result[0] is not None:
                for line in result[0]:
                    if line and len(line) > 1 and len(line[1]) > 0:
                        text_detected = line[1][0]
                        extracted_lines.append(text_detected)
            return "\n".join(extracted_lines).strip()

        # Fallback if external engines fail
        logger.info("OCR engine not available; returning empty OCR text.")
        return ""

    except Exception as e:
        logger.error(f"OCR processing failed: {e}", exc_info=True)
        return ""
