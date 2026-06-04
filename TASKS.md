# TASKS.md

# Project

Giải Thích Đơn Thuốc (Healthcare Hackathon)

---

# Rules For Agent

Trước khi bắt đầu:

1. Đọc PRD.md
2. Đọc AGENTS.md
3. Chỉ thực hiện task chưa hoàn thành đầu tiên.
4. Không tự ý làm task tiếp theo.
5. Không làm Stretch Goal nếu MVP chưa hoàn thành.
6. Sau mỗi task:

   * Báo cáo thay đổi
   * Đánh dấu task hoàn thành
   * Dừng lại chờ xác nhận

---

# MVP Tasks

## Task 01 - Project Structure

### Goal

Tạo cấu trúc thư mục theo PRD.

### Deliverables

```text
app/
├── app.py
├── services/
├── repositories/
├── models/
├── prompts/
├── data/
└── database/
```

### Definition of Done

* [x] Folder structure được tạo
* [x] File placeholder được tạo
* [x] App chạy được

### Status

* [x] DONE

---

## Task 02 - Domain Models

### Goal

Tạo các model cơ bản.

### Deliverables

* medication.py
* patient.py

### Definition of Done

* [x] Medication model
* [x] Patient model
* [x] Có type hints

### Status

* [x] DONE

---

## Task 03 - Drug Repository

### Goal

Tạo repository layer.

### Deliverables

* DrugRepository interface
* JsonDrugRepository implementation
* drugs.json mẫu

### Definition of Done

* [x] Có interface
* [x] Đọc dữ liệu từ drugs.json
* [x] Có dữ liệu mẫu tối thiểu 3 thuốc

### Status

* [x] DONE

---

## Task 04 - OCR Layer

### Goal

Tạo OCRService.

### Deliverables

* OCRService interface
* GeminiOCRService

### Definition of Done

* [x] Nhận image input
* [x] Trả về schema OCR chuẩn
* [x] Xử lý confidence low

### Status

* [x] DONE

---

## Task 05 - Safety Engine

### Goal

Xây dựng safety screening.

### Deliverables

* SafetyEngine

### Definition of Done

* [x] Nhận symptoms
* [x] Kiểm tra red flags
* [x] Trả về risk_level

### Status

* [x] DONE

---

## Task 06 - Explanation Service

### Goal

Tạo service giải thích thuốc.

### Deliverables

* ExplanationService
* Prompt template

### Definition of Done

* [x] Nhận medication
* [x] Truy vấn repository
* [x] Trả về JSON đúng schema

### Status

* [x] DONE

---

## Task 07 - Streamlit UI

### Goal

Xây dựng giao diện.

### Deliverables

Page 1

* Upload Prescription

Page 2

* Patient Information

Page 3

* Result

### Definition of Done

* [x] Upload hoạt động
* [x] Nhập thông tin bệnh nhân
* [x] Hiển thị kết quả

### Status

* [x] DONE

---

## Task 08 - Integration

### Goal

Kết nối toàn bộ flow.

### Flow

```text
Upload
 ↓
OCR
 ↓
Patient Info
 ↓
Safety Engine
 ↓
Explanation Service
 ↓
Result
```

### Definition of Done

* [x] End-to-end flow chạy được
* [x] Không crash
* [x] Có error handling

### Status

* [x] DONE

---

## Task 09 - Railway Deployment

### Goal

Deploy prototype.

### Definition of Done

* [ ] Chạy được trên Railway
* [ ] Có URL demo

### Status

* [ ] TODO

---

# MVP Completion Checklist

MVP hoàn thành khi:

* [x] Upload được ảnh đơn thuốc
* [x] OCR hoạt động
* [x] Trích xuất được tên thuốc
* [x] Giải thích được thuốc
* [x] Safety screening hoạt động
* [x] Có cảnh báo khẩn cấp
* [ ] Chạy được trên Railway
* [ ] Demo dưới 2 phút

---

# Stretch Goals

Chỉ thực hiện khi toàn bộ MVP hoàn thành.

---

## Stretch 01 - Drug Interaction Checker

### Goal

Kiểm tra tương tác thuốc cơ bản.

### Status

* [ ] TODO

---

## Stretch 02 - Multi-language Support

### Goal

Hỗ trợ:

* Vietnamese
* English

### Status

* [ ] TODO

---

## Stretch 03 - Better OCR Validation

### Goal

Cảnh báo OCR không chắc chắn.

### Status

* [ ] TODO

---

## Stretch 04 - Medication Reminder Architecture

### Goal

Chuẩn bị extension point cho reminder.

Không cần implement reminder.

### Status

* [ ] TODO

---

# Final Demo Checklist

Demo script:

1. Upload đơn thuốc
2. OCR nhận diện thuốc
3. Chọn thông tin bệnh nhân
4. Nhập triệu chứng
5. Safety screening
6. Giải thích thuốc
7. Hiển thị warning
8. Hoàn thành trong dưới 2 phút

---

# Agent Command

Mặc định agent phải làm:

"Complete the first unchecked MVP task only."

Không được tự ý làm task tiếp theo.
