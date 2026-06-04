from abc import ABC, abstractmethod
from typing import Any

from app.models.patient import Patient


class ExplanationService(ABC):
    @abstractmethod
    def explain_medication(
        self,
        medication: dict[str, Any],
        patient: Patient | None = None,
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    def review_prescription(
        self,
        medications: list[dict[str, Any]],
        patient: Patient,
        safety_result: dict[str, Any],
        explanations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        pass
