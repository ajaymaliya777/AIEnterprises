import re
import unicodedata
import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV (cv2) is not available. Image preprocessing will use basic fallback.")


def clean_text(text: str) -> str:
    """
    Clean, normalize unicode, collapse excessive whitespace and tabs.
    """
    if not text:
        return ""
    # Normalize unicode (NFKC)
    text = unicodedata.normalize("NFKC", text)
    # Replace non-breaking spaces and other irregular spaces
    text = re.sub(r"[\r\f\v]", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    # Remove excessive blank lines (more than 2)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def preprocess_image_cv(image_np: np.ndarray) -> np.ndarray:
    """
    OpenCV image enhancement pipeline for OCR:
    1. Convert to grayscale
    2. Denoise with bilateral filter or Gaussian blur
    3. Adaptive / Otsu thresholding for high contrast binarization
    4. Deskew image using minAreaRect
    """
    if not CV2_AVAILABLE or image_np is None:
        return image_np

    try:
        # 1. Grayscale
        if len(image_np.shape) == 3:
            gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        else:
            gray = image_np

        # 2. Denoise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # 3. Deskewing
        coords = np.column_stack(np.where(blurred < 250))
        angle = 0.0
        if coords.shape[0] > 100:
            rect = cv2.minAreaRect(coords)
            angle = rect[-1]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            else:
                angle = -angle

            if abs(angle) > 0.5 and abs(angle) < 45:
                (h, w) = gray.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                gray = cv2.warpAffine(
                    gray, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )

        # 4. Adaptive Binarization / Otsu
        _, binarized = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 5. Morphological opening to clean small salt-and-pepper noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        processed = cv2.morphologyEx(binarized, cv2.MORPH_OPEN, kernel)

        return processed
    except Exception as e:
        logger.warning(f"Error in OpenCV image preprocessing: {e}. Returning original.")
        return image_np
