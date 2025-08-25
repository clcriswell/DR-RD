"""Minimal vision helpers with graceful degradation."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Dict, Any
import io

try:  # Optional dependencies
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None  # type: ignore
try:  # pragma: no cover
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None  # type: ignore
try:  # pragma: no cover
    import cv2
except Exception:  # pragma: no cover
    cv2 = None  # type: ignore


def analyze_image(file_or_bytes: Any, tasks: Iterable[str]) -> Dict[str, Any]:
    tasks = list(tasks)
    result: Dict[str, Any] = {}
    img = None
    if isinstance(file_or_bytes, (str, Path)):
        if Image:
            try:
                img = Image.open(file_or_bytes)
            except Exception:
                img = None
    else:
        if Image:
            try:
                img = Image.open(io.BytesIO(file_or_bytes))
            except Exception:
                img = None
    for task in tasks:
        if task == "ocr":
            if img is not None and pytesseract:
                try:
                    result["ocr"] = pytesseract.image_to_string(img)
                except Exception:
                    result["ocr"] = ""
            else:
                result["ocr"] = ""
        elif task in {"classify", "detect"}:
            result[task] = []
    return result


def analyze_video(file_path: str, sample_rate_fps: int, tasks: Iterable[str]) -> Dict[str, Any]:
    if cv2 is None:
        return {"error": "opencv_unavailable"}
    if not Path(file_path).exists():
        return {"error": "file_not_found"}
    cap = cv2.VideoCapture(str(file_path))
    if not cap.isOpened():
        return {"error": "file_not_found"}
    results = []
    fps = cap.get(cv2.CAP_PROP_FPS) or 1
    step = max(int(fps // sample_rate_fps), 1)
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % step == 0:
            if Image:
                success, buffer = cv2.imencode(".png", frame)
                if success:
                    results.append(analyze_image(buffer.tobytes(), tasks))
            else:
                results.append({})
        idx += 1
    cap.release()
    return {"frames": results}
