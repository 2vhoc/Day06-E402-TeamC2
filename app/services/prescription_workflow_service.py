from typing import Any

from app.models.patient import Patient
from app.services.explanation_service import ExplanationService
from app.services.ocr_service import OCRService
from app.services.safety_engine import SafetyEngine


class PrescriptionWorkflowService:
    def __init__(
        self,
        ocr_service: OCRService,
        safety_engine: SafetyEngine,
        explanation_service: ExplanationService,
    ) -> None:
        self.ocr_service = ocr_service
        self.safety_engine = safety_engine
        self.explanation_service = explanation_service

    def extract_prescription(
        self,
        image: bytes,
        mime_type: str,
    ) -> dict[str, Any]:
        return self.ocr_service.extract_prescription(image=image, mime_type=mime_type)

    def explain_prescription(
        self,
        medications: list[dict[str, Any]],
        patient: Patient,
    ) -> dict[str, Any]:
        safety_result = self.safety_engine.screen(patient.symptoms)
        explanations = [
            self.explanation_service.explain_medication(
                medication=medication,
                patient=patient,
            )
            for medication in medications
        ]
        ai_review = self.explanation_service.review_prescription(
            medications=medications,
            patient=patient,
            safety_result=safety_result,
            explanations=explanations,
        )

        return {
            "safety": safety_result,
            "explanations": explanations,
            "ai_review": ai_review,
        }
