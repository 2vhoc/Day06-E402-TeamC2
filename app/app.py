from html import escape
import os
from pathlib import Path
import sys
from typing import Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file(PROJECT_ROOT / ".env")

from app.models.patient import Patient
from app.repositories.json_drug_repository import JsonDrugRepository
from app.services.gemini_ocr_service import GeminiOCRService
from app.services.gpt4o_mini_explanation_service import GPT4oMiniExplanationService
from app.services.prescription_workflow_service import PrescriptionWorkflowService
from app.services.safety_engine import SafetyEngine

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

AGE_GROUP_OPTIONS = {
    "Child": ("🧒", "Trẻ em", "Dưới 18 tuổi"),
    "Adult": ("🧑", "Người lớn", "18 – 60 tuổi"),
    "Elderly": ("👴", "Người cao tuổi", "Trên 60 tuổi"),
}

STEPS = [
    ("upload", "1", "Tải ảnh đơn thuốc", "Chụp hoặc tải ảnh đơn thuốc lên"),
    ("patient", "2", "Thông tin bệnh nhân", "Bổ sung tuổi, triệu chứng"),
    ("result", "3", "Kết quả giải thích", "Xem giải thích & cảnh báo"),
]

MAX_FILE_SIZE_MB = 10
SUPPORTED_TYPES = ["jpg", "jpeg", "png"]


# ─────────────────────────────────────────────
# Service layer (cached)
# ─────────────────────────────────────────────

@st.cache_resource
def get_workflow_service() -> PrescriptionWorkflowService:
    drug_repository = JsonDrugRepository()
    return PrescriptionWorkflowService(
        ocr_service=GeminiOCRService(),
        safety_engine=SafetyEngine(),
        explanation_service=GPT4oMiniExplanationService(drug_repository=drug_repository),
    )


# ─────────────────────────────────────────────
# State management
# ─────────────────────────────────────────────

def initialize_state() -> None:
    defaults = {
        "page": "upload",
        "ocr_result": None,
        "patient": None,
        "result": None,
        "uploaded_image_bytes": None,
        "error_context": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_flow() -> None:
    for key in ("page", "ocr_result", "patient", "result", "uploaded_image_bytes", "error_context"):
        st.session_state[key] = None
    st.session_state["page"] = "upload"


def go_to(page: str) -> None:
    st.session_state["page"] = page
    st.session_state["error_context"] = None
    st.rerun()


def can_navigate_to(page: str) -> bool:
    if page == "upload":
        return True
    if page == "patient":
        return st.session_state.get("ocr_result") is not None
    if page == "result":
        return st.session_state.get("result") is not None
    return False


def get_medications() -> list[dict[str, Any]]:
    ocr_result = st.session_state.get("ocr_result") or {}
    medications = ocr_result.get("medications", [])
    if not isinstance(medications, list):
        return []
    return [m for m in medications if isinstance(m, dict)]


# ─────────────────────────────────────────────
# Styles — consolidated, scoped, minimal
# ─────────────────────────────────────────────

def apply_styles() -> None:
    st.markdown(
        """
        <style>
        /* ── Design tokens ── */
        :root {
            --rx-primary: #2563eb;
            --rx-primary-hover: #1d4ed8;
            --rx-primary-soft: #eff6ff;
            --rx-ink: #0f172a;
            --rx-muted: #64748b;
            --rx-surface: #ffffff;
            --rx-border: #e2e8f0;
            --rx-success: #16a34a;
            --rx-success-soft: #f0fdf4;
            --rx-warning: #d97706;
            --rx-warning-soft: #fffbeb;
            --rx-danger: #dc2626;
            --rx-danger-soft: #fef2f2;
            --rx-radius: 12px;
            --rx-radius-sm: 8px;
            --rx-shadow-sm: 0 1px 2px rgba(0,0,0,.05);
            --rx-shadow: 0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.04);
        }

        /* ── Layout ── */
        .main .block-container {
            max-width: 960px;
            padding: 1.5rem 1rem 4rem;
        }

        /* ── Typography ── */
        h1 { font-size: 1.65rem !important; font-weight: 800 !important; color: var(--rx-ink) !important; }
        h2 { font-size: 1.25rem !important; font-weight: 700 !important; }
        h3 { font-size: 1.05rem !important; font-weight: 700 !important; }

        /* ── Buttons ── */
        div.stButton > button,
        div[data-testid="stFormSubmitButton"] button {
            border-radius: var(--rx-radius-sm);
            border: 1.5px solid var(--rx-primary);
            background: var(--rx-primary);
            color: white;
            font-weight: 700;
            padding: 0.6rem 1.25rem;
            transition: all 0.15s ease;
        }
        div.stButton > button:hover,
        div[data-testid="stFormSubmitButton"] button:hover {
            background: var(--rx-primary-hover);
            border-color: var(--rx-primary-hover);
            box-shadow: var(--rx-shadow);
        }

        /* ── Secondary / ghost button ── */
        div.stButton > button[kind="secondary"] {
            background: transparent;
            color: var(--rx-primary);
        }

        /* ── File uploader ── */
        div[data-testid="stFileUploader"] section {
            border: 2px dashed #93b4e8;
            border-radius: var(--rx-radius);
            background: var(--rx-primary-soft);
            transition: border-color 0.2s;
        }
        div[data-testid="stFileUploader"] section:hover {
            border-color: var(--rx-primary);
        }

        /* ── Image preview ── */
        div[data-testid="stImage"] img {
            max-height: 380px;
            max-width: 100%;
            object-fit: contain;
            border-radius: var(--rx-radius-sm);
            border: 1px solid var(--rx-border);
        }

        /* ── Stepper ── */
        .rx-stepper {
            display: flex;
            gap: 0;
            margin: 0.75rem 0 1.5rem;
            padding: 0;
        }
        .rx-step {
            flex: 1;
            display: flex;
            align-items: center;
            gap: 0.65rem;
            padding: 0.75rem 1rem;
            border: 1px solid var(--rx-border);
            border-right: none;
            background: var(--rx-surface);
            cursor: default;
            transition: all 0.15s;
        }
        .rx-step:first-child { border-radius: var(--rx-radius) 0 0 var(--rx-radius); }
        .rx-step:last-child  { border-radius: 0 var(--rx-radius) var(--rx-radius) 0; border-right: 1px solid var(--rx-border); }
        .rx-step.active {
            background: var(--rx-primary-soft);
            border-color: var(--rx-primary);
            position: relative;
            z-index: 1;
        }
        .rx-step.active + .rx-step { border-left-color: var(--rx-primary); }
        .rx-step.completed { background: var(--rx-success-soft); border-color: #bbf7d0; }
        .rx-step.completed + .rx-step { border-left-color: #bbf7d0; }
        .rx-step-num {
            width: 28px; height: 28px;
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.78rem; font-weight: 800;
            background: var(--rx-border); color: var(--rx-muted);
            flex-shrink: 0;
        }
        .rx-step.active .rx-step-num  { background: var(--rx-primary); color: white; }
        .rx-step.completed .rx-step-num { background: var(--rx-success); color: white; }
        .rx-step-text { line-height: 1.3; }
        .rx-step-label { font-size: 0.72rem; color: var(--rx-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
        .rx-step-title { font-size: 0.88rem; color: var(--rx-ink); font-weight: 700; }
        .rx-step.active .rx-step-title { color: var(--rx-primary); }

        /* ── Cards ── */
        .rx-card {
            border: 1px solid var(--rx-border);
            border-radius: var(--rx-radius);
            background: var(--rx-surface);
            padding: 1.15rem;
            box-shadow: var(--rx-shadow-sm);
            margin-bottom: 0.75rem;
        }

        /* ── Metric row ── */
        .rx-metrics {
            display: flex;
            gap: 0.75rem;
            margin: 1rem 0;
        }
        .rx-metric {
            flex: 1;
            border: 1px solid var(--rx-border);
            border-radius: var(--rx-radius-sm);
            padding: 0.85rem 1rem;
            text-align: center;
        }
        .rx-metric-value { font-size: 1.35rem; font-weight: 800; color: var(--rx-ink); }
        .rx-metric-label { font-size: 0.8rem; color: var(--rx-muted); margin-top: 0.15rem; }
        .rx-metric.urgent { border-color: var(--rx-danger); background: var(--rx-danger-soft); }
        .rx-metric.urgent .rx-metric-value { color: var(--rx-danger); }
        .rx-metric.normal { border-color: var(--rx-success); background: var(--rx-success-soft); }
        .rx-metric.normal .rx-metric-value { color: var(--rx-success); }

        /* ── Safety banner ── */
        .rx-safety-banner {
            border: 1.5px solid var(--rx-danger);
            border-radius: var(--rx-radius);
            background: var(--rx-danger-soft);
            padding: 1rem 1.15rem;
            margin-bottom: 1rem;
            display: flex;
            gap: 0.75rem;
            align-items: flex-start;
        }
        .rx-safety-icon { font-size: 1.35rem; flex-shrink: 0; line-height: 1; }
        .rx-safety-text { font-size: 0.94rem; color: #991b1b; line-height: 1.5; }
        .rx-safety-text strong { font-weight: 800; }

        /* ── Notice ── */
        .rx-notice {
            border: 1px solid var(--rx-warning);
            border-radius: var(--rx-radius);
            background: var(--rx-warning-soft);
            padding: 1rem 1.15rem;
        }
        .rx-notice-title { font-weight: 800; color: #92400e; margin-bottom: 0.3rem; font-size: 0.95rem; }
        .rx-notice-body  { color: #78350f; font-size: 0.9rem; line-height: 1.55; }

        /* ── Section heading ── */
        .rx-section-heading {
            font-size: 0.85rem;
            font-weight: 700;
            color: var(--rx-muted);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin: 1.25rem 0 0.5rem;
            padding-bottom: 0.35rem;
            border-bottom: 1px solid var(--rx-border);
        }

        /* ── Disclaimer footer ── */
        .rx-disclaimer {
            text-align: center;
            font-size: 0.78rem;
            color: var(--rx-muted);
            padding: 2rem 0 0.5rem;
            border-top: 1px solid var(--rx-border);
            margin-top: 2rem;
        }

        /* ── Hide default Streamlit footer ── */
        footer { visibility: hidden; }

        /* ── Responsive ── */
        @media (max-width: 768px) {
            .rx-stepper { flex-direction: column; }
            .rx-step { border-right: 1px solid var(--rx-border); border-bottom: none; }
            .rx-step:first-child { border-radius: var(--rx-radius) var(--rx-radius) 0 0; }
            .rx-step:last-child  { border-radius: 0 0 var(--rx-radius) var(--rx-radius); border-bottom: 1px solid var(--rx-border); }
            .rx-metrics { flex-direction: column; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# Components
# ─────────────────────────────────────────────

def render_header() -> None:
    # st.markdown(
    #     '<p style="color:#2563eb;font-size:0.78rem;font-weight:800;letter-spacing:0.06em;'
    #     'text-transform:uppercase;margin-bottom:0;">PRESCRIPTION READER</p>',
    #     unsafe_allow_html=True,
    # )
    st.title("Giải Thích Đơn Thuốc")
    st.caption("Thông tin tham khảo — không thay thế tư vấn y tế từ bác sĩ hoặc cơ sở y tế.")


def render_stepper() -> None:
    """Render a connected stepper bar showing progress through the wizard."""
    current = st.session_state["page"]
    page_order = [s[0] for s in STEPS]
    current_idx = page_order.index(current) if current in page_order else 0

    html_parts = ['<div class="rx-stepper" role="navigation" aria-label="Tiến trình">']
    for idx, (page_key, num, title, _subtitle) in enumerate(STEPS):
        if idx < current_idx and can_navigate_to(page_key):
            cls = "completed"
            check = "✓"
        elif idx == current_idx:
            cls = "active"
            check = num
        else:
            cls = ""
            check = num

        aria = ' aria-current="step"' if idx == current_idx else ""
        html_parts.append(
            f'<div class="rx-step {cls}"{aria}>'
            f'  <div class="rx-step-num">{check}</div>'
            f'  <div class="rx-step-text">'
            f'    <div class="rx-step-label">Bước {num}</div>'
            f'    <div class="rx-step-title">{escape(title)}</div>'
            f"  </div>"
            f"</div>"
        )
    html_parts.append("</div>")
    st.markdown("".join(html_parts), unsafe_allow_html=True)


def render_notice_panel() -> None:
    st.markdown(
        '<div class="rx-notice">'
        '  <div class="rx-notice-title">⚠️ Lưu ý an toàn</div>'
        '  <div class="rx-notice-body">'
        "    Công cụ này chỉ giúp giải thích thông tin thuốc ở mức <strong>tham khảo</strong>. "
        "    Không tự ý đổi thuốc, tăng liều, giảm liều hoặc ngừng thuốc mà không có chỉ dẫn của bác sĩ."
        "  </div>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_back_button(label: str, target_page: str) -> None:
    if st.button(f"← {label}", key=f"back_to_{target_page}"):
        go_to(target_page)


def render_medication_cards(medications: list[dict[str, Any]]) -> None:
    """Compact medication summary cards."""
    cols_per_row = 2
    for row_start in range(0, len(medications), cols_per_row):
        cols = st.columns(cols_per_row, gap="medium")
        for col_idx, col in enumerate(cols):
            med_idx = row_start + col_idx
            if med_idx >= len(medications):
                break
            med = medications[med_idx]
            name = med.get("name", "") or "Không rõ tên thuốc"
            dose = med.get("dose", "")
            freq = med.get("frequency", "")
            dur = med.get("duration", "")
            meta_lines = []
            if dose:
                meta_lines.append(f"<strong>Liều:</strong> {escape(str(dose))}")
            if freq:
                meta_lines.append(f"<strong>Tần suất:</strong> {escape(str(freq))}")
            if dur:
                meta_lines.append(f"<strong>Thời gian:</strong> {escape(str(dur))}")
            meta_html = "<br>".join(meta_lines) if meta_lines else '<span style="color:var(--rx-muted)">Chưa rõ chi tiết</span>'

            col.markdown(
                f'<div class="rx-card">'
                f'  <div style="font-weight:800;font-size:1rem;color:var(--rx-ink);margin-bottom:0.4rem;">💊 {escape(str(name))}</div>'
                f'  <div style="font-size:0.88rem;color:var(--rx-muted);line-height:1.5;">{meta_html}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )


def render_list(title: str, items: list[str]) -> None:
    st.markdown(f'<div class="rx-section-heading">{escape(title)}</div>', unsafe_allow_html=True)
    if not items:
        st.caption("Không có cảnh báo bổ sung.")
        return
    for item in items:
        st.write(f"- {item}")


# ─────────────────────────────────────────────
# Pages
# ─────────────────────────────────────────────

def render_upload_page() -> None:
    left_col, right_col = st.columns([1.4, 1], gap="large")

    with left_col:
        st.header("Tải ảnh đơn thuốc")
        st.caption(f"Hỗ trợ JPG, JPEG, PNG — tối đa {MAX_FILE_SIZE_MB} MB")

        uploaded_file = st.file_uploader(
            "Chọn hoặc kéo thả ảnh đơn thuốc",
            type=SUPPORTED_TYPES,
            accept_multiple_files=False,
            label_visibility="collapsed",
        )

        if uploaded_file is not None:
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                st.error(f"Ảnh quá lớn ({file_size_mb:.1f} MB). Vui lòng chọn ảnh dưới {MAX_FILE_SIZE_MB} MB.")
                return

            st.image(uploaded_file, caption="Ảnh đã chọn", use_container_width=True)

        st.markdown("")  # spacing

        if st.button(
            "📷  Đọc đơn thuốc",
            disabled=uploaded_file is None,
            use_container_width=True,
            type="primary",
        ):
            if uploaded_file is None:
                return
            _process_upload(uploaded_file)

    with right_col:
        render_notice_panel()

        # Tips card
        st.markdown(
            '<div class="rx-card">'
            '  <div style="font-weight:700;margin-bottom:0.5rem;">📸 Mẹo chụp ảnh rõ</div>'
            '  <div style="font-size:0.88rem;color:var(--rx-muted);line-height:1.6;">'
            "    • Đặt đơn thuốc trên mặt phẳng, đủ ánh sáng<br>"
            "    • Chụp thẳng, không nghiêng hoặc bị cắt<br>"
            "    • Đảm bảo chữ rõ ràng, không bị mờ hoặc nhòe<br>"
            "    • Chụp toàn bộ đơn thuốc trong một ảnh"
            "  </div>"
            "</div>",
            unsafe_allow_html=True,
        )


def _process_upload(uploaded_file: Any) -> None:
    """Handle OCR extraction with clear error states."""
    with st.spinner("Đang đọc đơn thuốc… Vui lòng đợi trong giây lát."):
        try:
            ocr_result = get_workflow_service().extract_prescription(
                image=uploaded_file.getvalue(),
                mime_type=uploaded_file.type or "image/jpeg",
            )
        except Exception:
            st.error("Không thể kết nối dịch vụ nhận dạng. Vui lòng kiểm tra kết nối mạng và thử lại.")
            return

    status = ocr_result.get("status", "")

    if status == "invalid_image":
        st.error("Ảnh không hợp lệ hoặc không phải đơn thuốc. Vui lòng chọn ảnh khác.")
        return

    if status == "ocr_failed":
        st.error("Không thể nhận dạng nội dung. Vui lòng thử lại với ảnh rõ hơn.")
        return

    if ocr_result.get("confidence") != "high":
        st.warning(
            "Ảnh chưa đủ rõ để đọc chính xác. Hãy thử chụp lại với ánh sáng tốt hơn "
            "và đảm bảo chữ trên đơn thuốc rõ ràng."
        )
        return

    medications = ocr_result.get("medications", [])
    if not medications:
        st.warning("Không tìm thấy thuốc nào trong ảnh. Vui lòng kiểm tra lại ảnh đơn thuốc.")
        return

    st.session_state["ocr_result"] = ocr_result
    st.session_state["uploaded_image_bytes"] = uploaded_file.getvalue()
    go_to("patient")


def render_patient_page() -> None:
    medications = get_medications()
    if not medications:
        st.warning("Chưa có thông tin đơn thuốc. Vui lòng tải ảnh đơn thuốc trước.")
        render_back_button("Quay lại tải ảnh", "upload")
        return

    # Navigation
    render_back_button("Quay lại tải ảnh", "upload")

    st.header("Thông tin bệnh nhân")

    # Show recognized medications
    st.markdown('<div class="rx-section-heading">Thuốc đã nhận diện</div>', unsafe_allow_html=True)
    render_medication_cards(medications)

    st.markdown('<div class="rx-section-heading">Thông tin sức khỏe</div>', unsafe_allow_html=True)

    # Age group — card-style selector
    age_group_cols = st.columns(3, gap="small")
    selected_age = st.session_state.get("_age_group", "Adult")
    for col, (key, (icon, label, desc)) in zip(age_group_cols, AGE_GROUP_OPTIONS.items()):
        with col:
            is_selected = key == selected_age
            variant = "primary" if is_selected else "secondary"
            if st.button(
                f"{icon} {label}\n{desc}",
                key=f"age_{key}",
                use_container_width=True,
                type=variant,
            ):
                st.session_state["_age_group"] = key
                st.rerun()

    age_group = st.session_state.get("_age_group", "Adult")

    with st.form("patient_form", border=True):
        pregnant = False
        breastfeeding = False

        if age_group in {"Adult", "Elderly"}:
            special = st.radio(
                "Tình trạng đặc biệt",
                options=["none", "pregnant"],
                format_func=lambda v: {"none": "Không có", "pregnant": "🤰 Mang thai"}[v],
                horizontal=True,
            )
            pregnant = special == "pregnant"

        st.markdown("")  # spacing

        red_flag_symptoms = st.multiselect(
            "Triệu chứng đáng lưu ý",
            options=list(SafetyEngine.RED_FLAG_SYMPTOMS),
            help="Chọn các triệu chứng bạn đang gặp (nếu có)",
        )

        other_symptoms = st.text_area(
            "Triệu chứng khác (tuỳ chọn)",
            height=80,
            placeholder="Ví dụ: đau bụng nhẹ, khó ngủ…",
        )

        st.markdown("")  # spacing
        submitted = st.form_submit_button("📋  Xem kết quả giải thích", use_container_width=True)

    if submitted:
        symptoms = list(red_flag_symptoms)
        if other_symptoms.strip():
            symptoms.append(other_symptoms.strip())

        patient = Patient(
            age_group=age_group,
            pregnant=pregnant,
            breastfeeding=breastfeeding,
            symptoms=symptoms,
        )

        with st.spinner("Đang phân tích và tạo giải thích… Vui lòng đợi."):
            try:
                result = get_workflow_service().explain_prescription(
                    medications=medications,
                    patient=patient,
                )
            except Exception:
                st.error("Không thể tạo kết quả lúc này. Vui lòng thử lại sau.")
                return

        st.session_state["patient"] = patient
        st.session_state["result"] = result
        go_to("result")


def render_result_page() -> None:
    result = st.session_state.get("result")
    if not result:
        st.warning("Chưa có kết quả.")
        render_back_button("Quay lại tải ảnh", "upload")
        return

    # Navigation
    nav_left, nav_right = st.columns(2)
    with nav_left:
        render_back_button("Chỉnh sửa thông tin", "patient")
    with nav_right:
        if st.button("🔄  Đọc đơn thuốc mới", use_container_width=True):
            reset_flow()
            st.rerun()

    st.header("Kết quả giải thích")

    # Safety alert — prominent
    safety = result.get("safety", {})
    render_safety_alert(safety)

    # Metrics
    explanations = result.get("explanations", [])
    risk_level = safety.get("risk_level", "normal")
    risk_cls = "urgent" if risk_level == "urgent" else "normal"
    risk_label = "Cần đánh giá y tế sớm" if risk_level == "urgent" else "Chưa có dấu hiệu khẩn cấp"

    st.markdown(
        f'<div class="rx-metrics">'
        f'  <div class="rx-metric">'
        f'    <div class="rx-metric-value">{len(explanations)}</div>'
        f'    <div class="rx-metric-label">Số thuốc</div>'
        f"  </div>"
        f'  <div class="rx-metric {risk_cls}">'
        f'    <div class="rx-metric-value">{"⚠️" if risk_level == "urgent" else "✅"} {escape(risk_label)}</div>'
        f'    <div class="rx-metric-label">Mức rủi ro</div>'
        f"  </div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # AI review
    render_ai_review(result.get("ai_review", {}))

    # Individual drug explanations
    st.markdown('<div class="rx-section-heading">Chi tiết từng thuốc</div>', unsafe_allow_html=True)
    for explanation in explanations:
        render_explanation_card(explanation)

    # Disclaimer footer
    st.markdown(
        '<div class="rx-disclaimer">'
        "Thông tin trên chỉ mang tính chất tham khảo. "
        "Luôn tuân thủ hướng dẫn của bác sĩ hoặc dược sĩ."
        "</div>",
        unsafe_allow_html=True,
    )


def render_safety_alert(safety_result: dict[str, Any]) -> None:
    if safety_result.get("risk_level") != "urgent":
        return
    warnings = safety_result.get("warnings", [])
    warning_text = warnings[0] if warnings else SafetyEngine.URGENT_WARNING
    st.markdown(
        f'<div class="rx-safety-banner" role="alert">'
        f'  <div class="rx-safety-icon">🚨</div>'
        f'  <div class="rx-safety-text"><strong>Cảnh báo quan trọng:</strong> {escape(str(warning_text))}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_ai_review(ai_review: dict[str, Any]) -> None:
    if not ai_review:
        return
    review_text = ai_review.get("review_text", "")
    notes = ai_review.get("notes", [])
    verify_checklist = ai_review.get("verify_checklist", [])
    doctor_questions = ai_review.get("doctor_questions", [])
    next_steps = ai_review.get("next_steps", [])
    if not review_text and not notes and not verify_checklist and not doctor_questions and not next_steps:
        return

    st.markdown('<div class="rx-section-heading">Nhận xét tổng quan của AI</div>', unsafe_allow_html=True)
    with st.container(border=True):
        if review_text:
            st.info(review_text)
        if notes:
            render_list("Ghi chú bổ sung", notes)
        if verify_checklist:
            render_list("Checklist cần kiểm tra lại", verify_checklist)
        if doctor_questions:
            render_list("Câu hỏi nên hỏi bác sĩ hoặc dược sĩ", doctor_questions)
        if next_steps:
            render_list("Bước tiếp theo an toàn", next_steps)


def render_explanation_card(explanation: dict[str, Any]) -> None:
    drug_name = explanation.get("drug_name", "") or "Không rõ tên thuốc"

    with st.expander(f"💊 {drug_name}", expanded=False):
        if explanation.get("status") == "drug_not_found":
            st.warning("Chưa có dữ liệu tham khảo cho thuốc này trong hệ thống.")
            return

        if explanation.get("match_warning"):
            st.warning(explanation["match_warning"])

        purpose = explanation.get("purpose") or "Chưa có thông tin."
        st.markdown(f"**Công dụng:** {purpose}")

        patient_specific_note = explanation.get("patient_specific_note")
        if patient_specific_note:
            st.info(patient_specific_note)

        render_list("Tác dụng phụ thường gặp", explanation.get("common_side_effects", []))
        render_list("Khi nào cần liên hệ bác sĩ", explanation.get("doctor_contact_warning", []))
        render_list("Lưu ý cho nhóm đặc biệt", explanation.get("special_population_warning", []))
        render_list("Checklist cần kiểm tra lại", explanation.get("verification_checklist", []))
        render_list("Câu hỏi nên hỏi bác sĩ hoặc dược sĩ", explanation.get("questions_for_doctor", []))


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Giải Thích Đơn Thuốc",
        page_icon="💊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    initialize_state()
    apply_styles()
    render_header()
    render_stepper()

    page = st.session_state["page"]
    if page == "upload":
        render_upload_page()
    elif page == "patient":
        render_patient_page()
    else:
        render_result_page()


if __name__ == "__main__":
    main()
