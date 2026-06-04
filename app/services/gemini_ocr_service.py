import base64
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from app.services.ocr_service import OCRService


class GeminiOCRService(OCRService):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        prompt_path: str | Path | None = None,
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.prompt_path = Path(prompt_path) if prompt_path else self._default_prompt_path()
        self.timeout = timeout

    def extract_prescription(
        self,
        image: bytes,
        mime_type: str = "image/jpeg",
    ) -> dict[str, Any]:
        if not image:
            return self._low_confidence_result(status="invalid_image")

        if not self.api_key:
            return self._low_confidence_result(status="ocr_failed")

        try:
            response = self._call_gemini(image=image, mime_type=mime_type)
            text = self._extract_text(response)
            return self._parse_ocr_result(text)
        except (
            OSError,
            KeyError,
            ValueError,
            json.JSONDecodeError,
            urllib.error.URLError,
            urllib.error.HTTPError,
        ):
            return self._low_confidence_result(status="ocr_failed")

    def _call_gemini(self, image: bytes, mime_type: str) -> dict[str, Any]:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64.b64encode(image).decode("ascii"),
                            }
                        },
                        {"text": self._load_prompt()},
                    ]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
            },
        }
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _extract_text(response: dict[str, Any]) -> str:
        return response["candidates"][0]["content"]["parts"][0]["text"]

    def _parse_ocr_result(self, text: str) -> dict[str, Any]:
        data = self._load_json_text(text)
        confidence = data.get("confidence", "low")

        if confidence != "high":
            return self._low_confidence_result()

        medications = self._normalize_medications(data.get("medications", []))
        if not medications:
            return self._low_confidence_result()

        return {
            "confidence": "high",
            "medications": medications,
        }

    @staticmethod
    def _load_json_text(text: str) -> dict[str, Any]:
        cleaned_text = text.strip()

        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text.strip("`").strip()
            if cleaned_text.startswith("json"):
                cleaned_text = cleaned_text[4:].strip()

        start = cleaned_text.find("{")
        end = cleaned_text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("OCR response does not contain JSON")

        data = json.loads(cleaned_text[start : end + 1])
        if not isinstance(data, dict):
            raise ValueError("OCR response must be a JSON object")

        return data

    @classmethod
    def _normalize_medications(cls, medications: Any) -> list[dict[str, str]]:
        if not isinstance(medications, list):
            return []

        normalized_medications = []
        for medication in medications:
            if not isinstance(medication, dict):
                continue

            name = str(medication.get("name", "")).strip()
            if not name:
                continue

            normalized_medications.append(
                {
                    "name": name,
                    "dose": cls._localize_ocr_text(medication.get("dose", "")),
                    "frequency": cls._localize_ocr_text(medication.get("frequency", "")),
                    "duration": cls._localize_ocr_text(medication.get("duration", "")),
                }
            )

        return normalized_medications

    @staticmethod
    def _localize_ocr_text(value: Any) -> str:
        text = str(value).strip()
        if not text:
            return ""

        replacements = [
            (r"\btwice\s+(?:daily|a\s+day|per\s+day)\b", "2 lần/ngày"),
            (r"\bonce\s+(?:daily|a\s+day|per\s+day)\b", "1 lần/ngày"),
            (r"\b(?:thrice|three\s+times)\s+(?:daily|a\s+day|per\s+day)\b", "3 lần/ngày"),
            (r"\b(\d+)\s*times?\s*(?:/|per|a)?\s*day\b", r"\1 lần/ngày"),
            (r"\b(\d+)\s*times?\s*daily\b", r"\1 lần/ngày"),
            (r"\bevery\s+(\d+)\s+hours?\b", r"mỗi \1 giờ"),
            (r"\bevery\s+day\b", "mỗi ngày"),
            (r"\bdaily\b", "mỗi ngày"),
            (r"\bbefore\s+meals?\b", "trước ăn"),
            (r"\bafter\s+meals?\b", "sau ăn"),
            (r"\bwith\s+meals?\b", "cùng bữa ăn"),
            (r"\bbefore\s+food\b", "trước ăn"),
            (r"\bafter\s+food\b", "sau ăn"),
            (r"\bby\s+mouth\b", "uống"),
            (r"\borally\b", "uống"),
            (r"\btake\b", "dùng"),
            (r"\btablet(?:s)?\b", "viên"),
            (r"\btab(?:s)?\b", "viên"),
            (r"\bcapsule(?:s)?\b", "viên nang"),
            (r"\bcap(?:s)?\b", "viên nang"),
            (r"\bfor\s+(\d+)\s+days?\b", r"\1 ngày"),
            (r"\b(\d+)\s+days?\b", r"\1 ngày"),
            (r"\bfor\s+(\d+)\s+weeks?\b", r"\1 tuần"),
            (r"\b(\d+)\s+weeks?\b", r"\1 tuần"),
            (r"\bfor\s+(\d+)\s+months?\b", r"\1 tháng"),
            (r"\b(\d+)\s+months?\b", r"\1 tháng"),
            (r"\bmorning\b", "buổi sáng"),
            (r"\bnoon\b", "buổi trưa"),
            (r"\bevening\b", "buổi tối"),
            (r"\bnight\b", "buổi tối"),
            (r"\bbedtime\b", "trước khi ngủ"),
            (r"\bas\s+needed\b", "khi cần"),
        ]

        localized_text = text
        for pattern, replacement in replacements:
            localized_text = re.sub(pattern, replacement, localized_text, flags=re.IGNORECASE)

        localized_text = re.sub(r"\s+", " ", localized_text).strip()
        localized_text = localized_text.replace(" /", "/").replace("/ ", "/")
        return localized_text

    @staticmethod
    def _low_confidence_result(status: str | None = None) -> dict[str, Any]:
        if status:
            return {"status": status}

        return {"confidence": "low"}

    def _load_prompt(self) -> str:
        return self.prompt_path.read_text(encoding="utf-8").strip()

    @staticmethod
    def _default_prompt_path() -> Path:
        return Path(__file__).resolve().parents[1] / "prompts" / "ocr_prompt.txt"
