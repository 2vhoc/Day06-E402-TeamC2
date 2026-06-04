# AGENTS.md

# Project Context

Project: Giải Thích Đơn Thuốc (Healthcare Hackathon)

Đây là prototype hackathon.

Ưu tiên:

1. Hoàn thành demo end-to-end.
2. Dễ hiểu.
3. Dễ mở rộng.
4. Ít dependency.

Không tối ưu cho production.

---

# Development Philosophy

Luôn ưu tiên:

* Simplicity
* Readability
* Small codebase
* Fast iteration

Không tối ưu sớm.

Không tạo abstraction khi chưa cần.

Không tạo framework nội bộ.

---

# Architecture Rules

Bắt buộc tuân thủ:

```text
UI
 ↓
Services
 ↓
Repositories
 ↓
Data Source
```

Không được:

```text
UI
 ↓
JSON File
```

hoặc

```text
UI
 ↓
Database
```

trực tiếp.

---

# Allowed Stack

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

Không thay thế stack.

---

# Forbidden Technologies

Không thêm:

* FastAPI
* Flask
* Django
* React
* NextJS
* Angular

Không thêm:

* LangChain
* LlamaIndex
* ChromaDB
* Pinecone
* Weaviate

Không thêm:

* Redis
* PostgreSQL
* MongoDB

Không thêm:

* Celery
* RabbitMQ
* Kafka

Không thêm:

* Docker
* Kubernetes

trừ khi người dùng yêu cầu rõ ràng.

---

# Scope Protection

Không tự ý xây dựng:

* Authentication
* User Account
* Login
* Register
* Payment
* Notification
* Admin Panel
* Dashboard
* Analytics
* Recommendation Engine
* Medical Diagnosis
* Treatment Recommendation
* Prescription Generation
* Drug Interaction Checker
* Allergy Prediction

Nếu không được yêu cầu trong task hiện tại:

KHÔNG ĐƯỢC IMPLEMENT.

---

# Folder Ownership

## app.py

Chỉ xử lý:

* Streamlit UI
* Form input
* Rendering output

Không chứa business logic.

---

## services/

Chứa:

* OCR logic
* Explanation logic
* Safety logic

Business logic nằm ở đây.

---

## repositories/

Chứa:

* DrugRepository

Mọi truy cập dữ liệu thuốc phải đi qua repository.

---

## models/

Chứa:

* Domain model
* Data structure

Không chứa business logic.

---

## prompts/

Chứa:

* OCR prompts
* Explanation prompts

Prompt phải tách khỏi source code.

Không hardcode prompt dài trong Python.

---

# Dependency Rules

Ưu tiên thư viện chuẩn.

Chỉ thêm dependency mới khi:

1. Có lý do rõ ràng.
2. Không thể giải quyết bằng thư viện hiện tại.

Mỗi dependency mới phải có comment giải thích.

---

# File Creation Rules

Không tạo file mới nếu:

* Có thể sửa file hiện tại.
* Không giúp tăng tính rõ ràng.

Ưu tiên codebase nhỏ.

Tránh tạo:

```text
utils/
helpers/
common/
shared/
core/
```

nếu chỉ chứa 1-2 hàm.

---

# Error Handling

Không crash UI.

Không hiển thị:

* Stacktrace
* Raw Exception

Hiển thị thông báo thân thiện với người dùng.

---

# OCR Rules

OCR phải đi qua:

```python
OCRService
```

Không gọi Gemini trực tiếp từ UI.

Output OCR phải theo schema đã định.

---

# Repository Rules

Không đọc drugs.json trực tiếp từ UI.

Luôn thông qua:

```python
DrugRepository
```

Implementation hiện tại:

```python
JsonDrugRepository
```

Có thể thay thế trong tương lai.

---

# Explanation Rules

LLM chỉ được:

* Giải thích công dụng thuốc
* Giải thích tác dụng phụ thường gặp
* Hiển thị cảnh báo

LLM không được:

* Chẩn đoán bệnh
* Đề xuất thay đổi đơn thuốc
* Đề xuất tăng liều
* Đề xuất giảm liều
* Đề xuất đổi thuốc

---

# Safety Rules

Nếu xuất hiện:

* Khó thở
* Sưng môi
* Sưng lưỡi
* Đau ngực
* Co giật
* Ngất

Phải trả về:

```json
{
  "risk_level": "urgent"
}
```

và hiển thị cảnh báo y tế.

---

# Future Extension Policy

Thiết kế phải cho phép bổ sung sau này:

* Drug Interaction Checker
* Drug Allergy Checker
* External Drug API
* Multi-language Support
* Mobile App

Không được build các tính năng này ngay.

Chỉ chuẩn bị extension points.

---

# Coding Style

Ưu tiên:

* Hàm ngắn
* Tên rõ nghĩa
* Code dễ đọc

Tránh:

* Nested logic sâu
* Clever code
* Over-engineering

---

# Definition of Success

Một thay đổi được xem là thành công khi:

* Không phá vỡ flow demo.
* Không thêm dependency không cần thiết.
* Không thay đổi kiến trúc.
* Không mở rộng phạm vi sản phẩm.
* Giữ được khả năng mở rộng trong tương lai.

Khi phân vân giữa:

"kiến trúc đẹp hơn"

và

"demo chạy được"

hãy ưu tiên:

"demo chạy được".
