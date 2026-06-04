import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from app.models.patient import Patient
from app.repositories.drug_repository import DrugRepository
from app.services.explanation_service import ExplanationService


class GPT4oMiniExplanationService(ExplanationService):
    def __init__(
        self,
        drug_repository: DrugRepository,
        api_key: str | None = None,
        model: str | None = None,
        prompt_path: str | Path | None = None,
        review_prompt_path: str | Path | None = None,
        timeout: int = 30,
    ) -> None:
        self.drug_repository = drug_repository
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.prompt_path = Path(prompt_path) if prompt_path else self._default_prompt_path()
        self.review_prompt_path = (
            Path(review_prompt_path) if review_prompt_path else self._default_review_prompt_path()
        )
        self.timeout = timeout

    def explain_medication(
        self,
        medication: dict[str, Any],
        patient: Patient | None = None,
    ) -> dict[str, Any]:
        drug_name = str(medication.get("name", "")).strip()
        if not drug_name:
            return self._drug_not_found("")

        drug = self.drug_repository.get_drug(drug_name)
        if drug is None:
            return self._drug_not_found(drug_name)

        if not self.api_key:
            return self._fallback_explanation(drug=drug, patient=patient)

        try:
            return self._normalize_explanation(
                self._call_openai(
                    drug=drug,
                    medication=medication,
                    patient=patient,
                ),
                fallback_drug=drug,
                patient=patient,
            )
        except (
            OSError,
            KeyError,
            ValueError,
            json.JSONDecodeError,
            urllib.error.URLError,
            urllib.error.HTTPError,
        ):
            return self._fallback_explanation(drug=drug, patient=patient)

    def review_prescription(
        self,
        medications: list[dict[str, Any]],
        patient: Patient,
        safety_result: dict[str, Any],
        explanations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if safety_result.get("risk_level") != "normal":
            return {}

        if not self.api_key:
            return self._fallback_review(patient=patient, explanations=explanations)

        try:
            return self._normalize_review(
                self._call_openai_review(
                    medications=medications,
                    patient=patient,
                    safety_result=safety_result,
                    explanations=explanations,
                )
            )
        except (
            OSError,
            KeyError,
            ValueError,
            json.JSONDecodeError,
            urllib.error.URLError,
            urllib.error.HTTPError,
        ):
            return self._fallback_review(patient=patient, explanations=explanations)

    def _call_openai(
        self,
        drug: dict[str, Any],
        medication: dict[str, Any],
        patient: Patient | None,
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self._load_prompt(),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "medication": medication,
                            "drug_reference": drug,
                            "patient": self._patient_to_dict(patient),
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))

        content = data["choices"][0]["message"]["content"]
        explanation = json.loads(content)
        if not isinstance(explanation, dict):
            raise ValueError("Explanation response must be a JSON object")

        return explanation

    def _call_openai_review(
        self,
        medications: list[dict[str, Any]],
        patient: Patient,
        safety_result: dict[str, Any],
        explanations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self._load_review_prompt(),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "medications_from_ocr": medications,
                            "patient": self._patient_to_dict(patient),
                            "safety_result": safety_result,
                            "drug_explanations": explanations,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))

        content = data["choices"][0]["message"]["content"]
        review = json.loads(content)
        if not isinstance(review, dict):
            raise ValueError("Review response must be a JSON object")

        return review

    def _fallback_explanation(
        self,
        drug: dict[str, Any],
        patient: Patient | None,
    ) -> dict[str, Any]:
        return {
            "drug_name": str(drug.get("name", "")),
            "purpose": str(drug.get("purpose", "")),
            "common_side_effects": self._string_list(drug.get("common_side_effects", [])),
            "doctor_contact_warning": self._string_list(drug.get("doctor_contact_warning", [])),
            "special_population_warning": self._special_population_warnings(drug, patient),
            "patient_specific_note": self._fallback_patient_note(drug=drug, patient=patient),
            "verification_checklist": self._fallback_verification_checklist(drug=drug),
            "questions_for_doctor": self._fallback_doctor_questions(drug=drug),
            "match_warning": str(drug.get("_match_warning", "")),
            "match_candidates": self._string_list(drug.get("_match_candidates", [])),
        }

    def _normalize_explanation(
        self,
        explanation: dict[str, Any],
        fallback_drug: dict[str, Any],
        patient: Patient | None,
    ) -> dict[str, Any]:
        return {
            "drug_name": str(explanation.get("drug_name") or fallback_drug.get("name", "")),
            "purpose": str(explanation.get("purpose") or fallback_drug.get("purpose", "")),
            "common_side_effects": self._string_list(
                explanation.get("common_side_effects")
                or fallback_drug.get("common_side_effects", [])
            ),
            "doctor_contact_warning": self._string_list(
                explanation.get("doctor_contact_warning")
                or fallback_drug.get("doctor_contact_warning", [])
            ),
            "special_population_warning": self._string_list(
                explanation.get("special_population_warning")
                or self._special_population_warnings(fallback_drug, patient)
            ),
            "patient_specific_note": str(
                explanation.get("patient_specific_note")
                or self._fallback_patient_note(drug=fallback_drug, patient=patient)
            ),
            "verification_checklist": self._string_list(
                explanation.get("verification_checklist")
                or self._fallback_verification_checklist(drug=fallback_drug)
            ),
            "questions_for_doctor": self._string_list(
                explanation.get("questions_for_doctor")
                or self._fallback_doctor_questions(drug=fallback_drug)
            ),
            "match_warning": str(fallback_drug.get("_match_warning", "")),
            "match_candidates": self._string_list(fallback_drug.get("_match_candidates", [])),
        }

    def _fallback_review(
        self,
        patient: Patient,
        explanations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        known_drugs = [
            explanation.get("drug_name", "")
            for explanation in explanations
            if not explanation.get("status") and explanation.get("drug_name")
        ]

        notes = ["Chưa ghi nhận triệu chứng thuộc nhóm cảnh báo khẩn cấp trong thông tin đã nhập."]
        if patient.age_group == "Elderly" or patient.pregnant:
            notes.append("Có nhóm đối tượng cần lưu ý, hãy đọc kỹ phần cảnh báo của từng thuốc.")
        if any(explanation.get("match_warning") for explanation in explanations):
            notes.append("Có thuốc cần kiểm tra lại tên do OCR có thể nhầm với thuốc gần giống.")

        if known_drugs:
            drug_text = ", ".join(str(drug) for drug in known_drugs)
            review_text = (
                f"Dựa trên thông tin hiện có, đơn thuốc gồm {drug_text}. "
                "Hãy đối chiếu tên thuốc trên ảnh với kết quả OCR trước khi đọc giải thích."
            )
        else:
            review_text = "Chưa có đủ dữ liệu thuốc trong cơ sở dữ liệu mẫu để tạo nhận xét chi tiết."

        return {
            "review_text": review_text,
            "notes": notes,
            "verify_checklist": [
                "Đối chiếu tên từng thuốc trên ảnh đơn với kết quả OCR.",
                "Kiểm tra lại liều, tần suất dùng và thời gian dùng thuốc trên đơn gốc.",
                "Nếu có tên thuốc gần giống hoặc OCR không rõ, hỏi lại dược sĩ trước khi sử dụng.",
            ],
            "doctor_questions": [
                "Tôi cần lưu ý dấu hiệu nào khi dùng các thuốc này?",
                "Nếu triệu chứng không cải thiện hoặc nặng hơn thì khi nào cần liên hệ bác sĩ?",
            ],
            "next_steps": [
                "Làm theo đơn thuốc bác sĩ đã kê.",
                "Đọc kỹ nhãn thuốc và thông tin liều dùng trên đơn gốc.",
                "Liên hệ bác sĩ hoặc cơ sở y tế nếu xuất hiện triệu chứng bất thường.",
            ],
        }

    def _normalize_review(self, review: dict[str, Any]) -> dict[str, Any]:
        return {
            "review_text": str(review.get("review_text", "")).strip(),
            "notes": self._string_list(review.get("notes", [])),
            "verify_checklist": self._string_list(review.get("verify_checklist", [])),
            "doctor_questions": self._string_list(review.get("doctor_questions", [])),
            "next_steps": self._string_list(review.get("next_steps", [])),
        }

    def _fallback_patient_note(
        self,
        drug: dict[str, Any],
        patient: Patient | None,
    ) -> str:
        if patient is None:
            return "Hãy đối chiếu thông tin thuốc với đơn gốc trước khi sử dụng."

        notes = ["Hãy đối chiếu tên thuốc, liều và cách dùng với đơn gốc."]
        if patient.age_group == "Elderly":
            notes.append("Người cao tuổi nên đọc kỹ phần lưu ý và theo dõi tác dụng phụ thường gặp.")
        elif patient.age_group == "Child":
            notes.append("Trẻ em cần dùng thuốc đúng theo hướng dẫn của bác sĩ hoặc người giám hộ.")
        if patient.pregnant:
            notes.append("Người đang mang thai nên hỏi lại bác sĩ hoặc dược sĩ nếu còn băn khoăn.")
        if drug.get("_match_warning"):
            notes.append("Tên thuốc OCR có thể chưa chắc chắn, cần kiểm tra lại trên ảnh đơn.")

        return " ".join(notes)

    def _fallback_verification_checklist(self, drug: dict[str, Any]) -> list[str]:
        checklist = [
            f"Tên thuốc trên đơn có đúng là {drug.get('name', 'thuốc này')} không?",
            "Liều dùng trên đơn gốc có khớp với kết quả OCR không?",
            "Tần suất và thời gian dùng thuốc đã được ghi rõ chưa?",
        ]
        if drug.get("_match_warning"):
            checklist.append("Tên thuốc có thể gần giống thuốc khác, cần kiểm tra lại trước khi đọc kết quả.")

        return checklist

    @staticmethod
    def _fallback_doctor_questions(drug: dict[str, Any]) -> list[str]:
        drug_name = drug.get("name", "thuốc này")
        return [
            f"Khi dùng {drug_name}, dấu hiệu nào cần liên hệ bác sĩ?",
            f"Nếu quên một lần dùng {drug_name}, tôi nên hỏi bác sĩ hoặc dược sĩ như thế nào?",
            "Tôi có cần lưu ý gì thêm vì tuổi, tình trạng mang thai hoặc triệu chứng hiện tại không?",
        ]

    def _special_population_warnings(
        self,
        drug: dict[str, Any],
        patient: Patient | None,
    ) -> list[str]:
        if patient is None:
            return []

        is_special_population = (
            patient.age_group in {"Child", "Elderly"}
            or patient.pregnant
            or patient.breastfeeding
        )
        if not is_special_population:
            return []

        return self._string_list(drug.get("special_population_warning", []))

    @staticmethod
    def _drug_not_found(drug_name: str) -> dict[str, Any]:
        return {
            "status": "drug_not_found",
            "drug_name": drug_name,
            "purpose": "",
            "common_side_effects": [],
            "doctor_contact_warning": [],
            "special_population_warning": [],
        }

    @staticmethod
    def _string_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]

        if isinstance(value, str) and value.strip():
            return [value.strip()]

        return []

    @staticmethod
    def _patient_to_dict(patient: Patient | None) -> dict[str, Any]:
        if patient is None:
            return {}

        return {
            "age_group": patient.age_group,
            "pregnant": patient.pregnant,
            "breastfeeding": patient.breastfeeding,
            "symptoms": patient.symptoms,
        }

    def _load_prompt(self) -> str:
        return self.prompt_path.read_text(encoding="utf-8").strip()

    def _load_review_prompt(self) -> str:
        return self.review_prompt_path.read_text(encoding="utf-8").strip()

    @staticmethod
    def _default_prompt_path() -> Path:
        return Path(__file__).resolve().parents[1] / "prompts" / "explanation_prompt.txt"

    @staticmethod
    def _default_review_prompt_path() -> Path:
        return Path(__file__).resolve().parents[1] / "prompts" / "review_prompt.txt"
