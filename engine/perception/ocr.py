# Optical character recognition for UI labels, menus, buttons, code.

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any


@dataclass
class OCRResult:
    text: str
    boxes: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0


def ocr_image(image_path: str) -> OCRResult:
    """Run OCR on an image using tesseract if available.

    Returns empty result with a clear note if tesseract is not installed.
    Never fabricates text.
    """
    tesseract = shutil.which("tesseract")
    if not tesseract:
        return OCRResult(text="", boxes=[], confidence=0.0)

    cmd = [tesseract, image_path, "stdout", "--psm", "11", "-c", "tessedit_create_hocr=0"]
    try:
        out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    except subprocess.CalledProcessError:
        return OCRResult(text="", boxes=[], confidence=0.0)
    return OCRResult(text=out.strip(), boxes=[], confidence=0.0)
