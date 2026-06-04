import unicodedata
from collections.abc import Iterable
from typing import Any


class SafetyEngine:
    RED_FLAG_SYMPTOMS = (
        "Khó thở",
        "Sưng môi",
        "Sưng lưỡi",
        "Đau ngực",
        "Co giật",
        "Ngất",
    )
    URGENT_WARNING = "Có dấu hiệu cần được đánh giá y tế sớm. Vui lòng liên hệ cơ sở y tế hoặc bác sĩ."

    def screen(self, symptoms: Iterable[str] | str | None) -> dict[str, Any]:
        normalized_symptoms = self._normalize_symptoms(symptoms)

        has_red_flag = any(
            self._normalize(red_flag) in normalized_symptoms
            for red_flag in self.RED_FLAG_SYMPTOMS
        )

        if has_red_flag:
            return {
                "risk_level": "urgent",
                "warnings": [self.URGENT_WARNING],
            }

        return {
            "risk_level": "normal",
            "warnings": [],
        }

    @classmethod
    def _normalize_symptoms(cls, symptoms: Iterable[str] | str | None) -> str:
        if symptoms is None:
            return ""

        if isinstance(symptoms, str):
            return cls._normalize(symptoms)

        return " ".join(cls._normalize(str(symptom)) for symptom in symptoms)

    @staticmethod
    def _normalize(text: str) -> str:
        without_accents = "".join(
            character
            for character in unicodedata.normalize("NFD", text)
            if unicodedata.category(character) != "Mn"
        )
        return without_accents.replace("đ", "d").replace("Đ", "D").casefold().strip()
