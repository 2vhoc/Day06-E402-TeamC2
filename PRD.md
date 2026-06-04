# Build Prototype: Giải Thích Đơn Thuốc (Healthcare Hackathon)

# Project Goal

Xây dựng prototype AI giúp người dùng hiểu đơn thuốc được bác sĩ kê.

Đây là build slice để demo hackathon.

Đây KHÔNG phải sản phẩm y tế hoàn chỉnh.

Mục tiêu:

* Giải thích thuốc trong đơn thuốc.
* Giúp người dùng hiểu mục đích sử dụng thuốc.
* Hiểu tác dụng phụ thường gặp.
* Nhận diện các dấu hiệu nguy hiểm cần đi khám.
* Hiển thị cảnh báo cho các nhóm đối tượng đặc biệt.

Prototype không được đưa ra quyết định điều trị.

---

# User Story

Người dùng vừa nhận đơn thuốc từ bác sĩ.

Người dùng muốn:

* Hiểu thuốc dùng để làm gì.
* Hiểu tác dụng phụ thường gặp.
* Biết khi nào cần liên hệ bác sĩ.
* Biết các lưu ý nếu là:

  * Trẻ em
  * Người cao tuổi
  * Phụ nữ mang thai
  * Phụ nữ cho con bú

Người dùng KHÔNG được sử dụng hệ thống để:

* Tự chẩn đoán bệnh.
* Tự thay đổi đơn thuốc.
* Tự ngừng thuốc.
* Tự giảm liều.
* Tự tăng liều.
* Tự đổi thuốc.

---

# Scope Lock

Chỉ xây dựng:

1. OCR đơn thuốc.
2. Trích xuất tên thuốc.
3. Thu thập thông tin người dùng.
4. Safety screening.
5. Giải thích thuốc.
6. Hiển thị kết quả.

Không xây dựng:

* User authentication
* User profile
* Multi-user support
* Payment
* Notification
* Chat history
* Admin dashboard
* Medical diagnosis
* Treatment recommendation
* Prescription generation
* Hospital integration
* EMR integration
* EHR integration
* Fine-tuning
* RAG
* Vector database
* Semantic search

Nếu tính năng không được mô tả trong tài liệu này thì không được tự ý xây dựng.

---

# Architecture Principles

Ưu tiên:

* Đơn giản
* Ít dependency
* Dễ demo
* Dễ mở rộng

Business logic không được đặt trực tiếp trong UI.

UI chỉ gọi Service Layer.

---

# Core Flow

## Step 1

User upload ảnh đơn thuốc.

Hỗ trợ:

* JPG
* JPEG
* PNG

---

## Step 2

OCR đọc đơn thuốc.

Output chuẩn:

```json
{
  "confidence": "high",
  "medications": [
    {
      "name": "Paracetamol",
      "dose": "500mg",
      "frequency": "2 lần/ngày",
      "duration": "5 ngày"
    }
  ]
}
```

Nếu OCR không chắc chắn:

```json
{
  "confidence": "low"
}
```

---

## Step 3

Thu thập thông tin bệnh nhân.

Input:

* Age Group
* Pregnant
* Breastfeeding
* Symptoms

Age Group:

* Child
* Adult
* Elderly

---

## Step 4

Safety Engine phân tích.

### Special Population

Xác định:

* Child
* Elderly
* Pregnant
* Breastfeeding

### Red Flag Symptoms

Danh sách:

* Khó thở
* Sưng môi
* Sưng lưỡi
* Đau ngực
* Co giật
* Ngất

Nếu có ít nhất một dấu hiệu:

```json
{
  "risk_level": "urgent"
}
```

Ngược lại:

```json
{
  "risk_level": "normal"
}
```

---

## Step 5

Explanation Engine giải thích thuốc.

Cho mỗi thuốc:

* Công dụng
* Tác dụng phụ thường gặp
* Khi nào cần liên hệ bác sĩ
* Lưu ý cho nhóm đối tượng đặc biệt

---

# Layered Architecture

## UI Layer

Chỉ chịu trách nhiệm:

* Nhận input
* Hiển thị output

Không chứa business logic.

---

## OCR Layer

Tạo interface:

```python
class OCRService:
    def extract_prescription(image):
        pass
```

Prototype hiện tại:

```python
GeminiOCRService
```

Tương lai có thể thay bằng:

* OpenAI Vision
* Azure OCR
* Tesseract

Không ảnh hưởng UI.

---

## Drug Repository Layer

Tạo interface:

```python
class DrugRepository:
    def get_drug(name):
        pass
```

Prototype hiện tại:

```python
JsonDrugRepository
```

Sử dụng:

```text
data/drugs.json
```

Tương lai có thể thay bằng:

* SQLiteDrugRepository
* PostgresDrugRepository
* DrugAPIRepository

Không thay đổi business logic.

---

## Explanation Layer

Tạo interface:

```python
class ExplanationService:
    def explain_medication():
        pass
```

Prototype hiện tại:

```python
GPT4oMiniExplanationService
```

Tương lai có thể thay bằng:

* GPT-4.1
* Gemini
* Claude

Không thay đổi UI.

---

## Safety Layer

Tạo module riêng:

```python
SafetyEngine
```

Input:

```json
{
  "medications": [],
  "patient_info": {},
  "symptoms": []
}
```

Output:

```json
{
  "risk_level": "normal",
  "warnings": []
}
```

Không đặt logic safety trong app.py.

---

# Drug Data Source

Prototype hiện tại sử dụng:

```text
data/drugs.json
```

Dữ liệu thuốc phải truy cập thông qua:

```python
DrugRepository
```

Không đọc file JSON trực tiếp từ UI.

---

# Explanation Output Contract

LLM phải trả về JSON hợp lệ.

```json
{
  "drug_name": "",
  "purpose": "",
  "common_side_effects": [],
  "doctor_contact_warning": [],
  "special_population_warning": []
}
```

Cho phép bổ sung field mới trong tương lai.

Không được làm hỏng các field hiện có.

Không trả về:

* HTML
* Markdown
* XML

Chỉ trả về JSON.

---

# Safety Requirements

LLM tuyệt đối không được:

* Chẩn đoán bệnh.
* Kết luận người dùng an toàn.
* Đề xuất bỏ thuốc.
* Đề xuất đổi thuốc.
* Đề xuất giảm liều.
* Đề xuất tăng liều.
* Đề xuất ngừng thuốc.
* Kê đơn mới.
* Đưa ra phác đồ điều trị.

Nếu OCR confidence thấp:

Hiển thị:

"Cần ảnh rõ hơn để giải thích chính xác."

---

# Error Handling

OCR thất bại:

```json
{
  "status": "ocr_failed"
}
```

Ảnh không hợp lệ:

```json
{
  "status": "invalid_image"
}
```

Không tìm thấy thuốc:

```json
{
  "status": "drug_not_found"
}
```

Không hiển thị stacktrace trên giao diện.

---

# UI Requirements

## Page 1

Upload Prescription

Thành phần:

* Upload image

---

## Page 2

Patient Information

Thành phần:

* Age Group
* Pregnant
* Breastfeeding
* Symptoms

---

## Page 3

Result

Card cho từng thuốc:

* Drug Name
* Purpose
* Common Side Effects
* Doctor Contact Warning
* Special Population Warning

---

## Safety Alert

Nếu:

```json
{
  "risk_level": "urgent"
}
```

Hiển thị banner:

"Có dấu hiệu cần được đánh giá y tế sớm. Vui lòng liên hệ cơ sở y tế hoặc bác sĩ."

---

# Future Extension Points

Kiến trúc phải cho phép bổ sung sau này:

* Drug Interaction Checker
* Drug Allergy Checker
* External Drug API
* Medication Reminder
* Multi-language Support

Không được build các tính năng này trong prototype.

Chỉ chuẩn bị kiến trúc để có thể thêm sau.

---

# Technology Stack

Frontend:

* Streamlit

OCR:

* Gemini Vision API

LLM:

* GPT-4o-mini

Database:

* SQLite

Deploy:

* Railway

Python:

* 3.11

---

# Folder Structure

```text
app/
├── app.py
├── services/
│   ├── ocr_service.py
│   ├── explanation_service.py
│   └── safety_engine.py
│
├── repositories/
│   └── drug_repository.py
│
├── models/
│   ├── medication.py
│   └── patient.py
│
├── prompts/
│   ├── ocr_prompt.txt
│   └── explanation_prompt.txt
│
├── data/
│   └── drugs.json
│
└── database/
    └── app.db
```

---

# Build Constraints

Ưu tiên:

* Dễ đọc
* Dễ demo
* Dễ mở rộng

Không xây dựng:

* Docker
* Kubernetes
* CI/CD
* Monitoring
* Distributed system
* Microservice

Toàn bộ prototype phải chạy bằng:

```bash
streamlit run app/app.py
```

---

# Definition of Done

Prototype được coi là hoàn thành khi:

1. Upload được ảnh đơn thuốc.
2. OCR trích xuất được thuốc.
3. Giải thích được công dụng thuốc.
4. Nhận diện được nhóm đối tượng đặc biệt.
5. Nhận diện được red flag symptoms.
6. Có safety warning.
7. Không đề xuất thay đổi đơn thuốc.
8. Chạy được trên Railway.
9. Demo end-to-end dưới 2 phút.
10. Business logic nằm trong Service Layer.
11. Dữ liệu thuốc truy cập qua Repository Pattern.
12. Có ít nhất 3 extension points cho tương lai.
13. Chạy được bằng:

```bash
streamlit run app/app.py
```
