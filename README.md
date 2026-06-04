
# 
# Giải Thích Đơn Thuốc

Prototype AI giúp người dùng hiểu đơn thuốc được bác sĩ kê trong bối cảnh demo hackathon.

Ứng dụng hỗ trợ:

- Upload ảnh đơn thuốc.
- OCR trích xuất tên thuốc, liều, tần suất, thời gian dùng.
- Nhập thông tin bệnh nhân và triệu chứng hiện tại.
- Safety screening để phát hiện dấu hiệu cần đánh giá y tế sớm.
- Giải thích công dụng thuốc, tác dụng phụ thường gặp và cảnh báo cần lưu ý.
- Nhận xét tổng quan bằng AI ở bước kết quả.

Đây không phải sản phẩm y tế hoàn chỉnh. Ứng dụng không chẩn đoán bệnh, không kê đơn, không đề xuất đổi thuốc, không tăng/giảm liều và không thay thế tư vấn của bác sĩ hoặc dược sĩ.

## Demo Flow

```text
Upload ảnh đơn thuốc
 ↓
Gemini Vision OCR
 ↓
Xác nhận thuốc đã nhận diện
 ↓
Nhập nhóm tuổi, tình trạng mang thai, triệu chứng hiện tại
 ↓
SafetyEngine kiểm tra red flags
 ↓
GPT-4o-mini giải thích thuốc và nhận xét tổng quan
 ↓
Hiển thị kết quả
```

## Safety Screening

Safety screening kiểm tra các triệu chứng nguy hiểm:

- Khó thở
- Sưng môi
- Sưng lưỡi
- Đau ngực
- Co giật
- Ngất

Nếu có ít nhất một dấu hiệu, app trả `risk_level = urgent` và hiển thị cảnh báo y tế. Nếu không có, app trả `risk_level = normal`, nhưng không kết luận người dùng “an toàn”.

## Kiến trúc

```text
UI
 ↓
Services
 ↓
Repositories
 ↓
Data Source
```

Các phần chính:

- `app/app.py`: Streamlit UI, form input, render output.
- `app/services/gemini_ocr_service.py`: OCR đơn thuốc qua Gemini Vision API.
- `app/services/safety_engine.py`: kiểm tra red flag symptoms.
- `app/services/gpt4o_mini_explanation_service.py`: giải thích thuốc và nhận xét tổng quan qua GPT-4o-mini.
- `app/services/prescription_workflow_service.py`: nối OCR, safety và explanation thành flow demo.
- `app/repositories/json_drug_repository.py`: truy vấn dữ liệu thuốc.
- `app/data/drugs.json`: dữ liệu thuốc mẫu.
- `app/prompts/`: prompt OCR, prompt giải thích thuốc, prompt nhận xét tổng quan.

## Drug Matching

OCR thường trả tên thuốc không khớp 100% với database, ví dụ có thêm liều, dạng bào chế hoặc tên thương mại.

Repository xử lý bằng:

- Chuẩn hóa chữ hoa/thường.
- Bỏ dấu tiếng Việt.
- Bỏ token như `mg`, `ml`, `tablet`, `capsule`, `film-coated`.
- Tự tạo alias từ tên trong ngoặc.
- Fuzzy matching bằng thư viện chuẩn `difflib`.
- Cảnh báo user nếu tên thuốc có thể bị nhầm với thuốc gần giống.

Ví dụ:

```text
OCR: Etoricoxib (Roticox)
Database: Etoricoxib (Roticox 90mg film-coated tablets)
Kết quả: tìm đúng thuốc
```

## Cài đặt local

Yêu cầu:

- Python 3.11
- Streamlit

Tạo môi trường ảo:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Tạo file `.env` từ mẫu:

```bash
cp .env.example .env
```

Điền API key:

```env
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.5-flash
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini
```

Chạy app:

```bash
streamlit run app/app.py
```

## Biến môi trường

| Biến | Mục đích |
| --- | --- |
| `GEMINI_API_KEY` | Key dùng cho Gemini Vision OCR |
| `GEMINI_MODEL` | Model Gemini dùng cho OCR |
| `OPENAI_API_KEY` | Key dùng cho GPT-4o-mini |
| `OPENAI_MODEL` | Model OpenAI dùng cho giải thích và nhận xét |
| `RAILWAY_TOKEN` | Tùy chọn, dùng khi deploy bằng Railway CLI/CI |

## Deploy Railway

Repo đã có các file chuẩn bị deploy:

- `railway.json`
- `requirements.txt`
- `.python-version`
- `.streamlit/config.toml`
- `.env.example`
- `RAILWAY_DEPLOY.md`

Start command trên Railway:

```bash
streamlit run app/app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true
```

Deploy bằng Railway CLI:

```bash
railway login
railway link
railway up
```

Sau khi deploy, thêm các biến môi trường trong Railway Variables, không upload `.env`.

## Tech Stack

- Python 3.11
- Streamlit
- Gemini Vision API
- GPT-4o-mini
- JSON drug database
- Railway

## Giới hạn hiện tại

- Dữ liệu thuốc là dữ liệu mẫu trong `app/data/drugs.json`.
- OCR phụ thuộc chất lượng ảnh và Gemini Vision API.
- Không có authentication, user account, admin dashboard hay lưu lịch sử.
- Không có drug interaction checker.
- Không có allergy checker.
- Không có medical diagnosis hoặc treatment recommendation.

## Cấu trúc thư mục

```text
app/
├── app.py
├── data/
│   └── drugs.json
├── database/
├── models/
│   ├── medication.py
│   └── patient.py
├── prompts/
│   ├── explanation_prompt.txt
│   ├── ocr_prompt.txt
│   └── review_prompt.txt
├── repositories/
│   ├── drug_repository.py
│   └── json_drug_repository.py
└── services/
    ├── explanation_service.py
    ├── gemini_ocr_service.py
    ├── gpt4o_mini_explanation_service.py
    ├── ocr_service.py
    ├── prescription_workflow_service.py
    └── safety_engine.py
```

## Demo Script

1. Mở app Streamlit.
2. Upload ảnh đơn thuốc.
3. Xem danh sách thuốc OCR nhận diện.
4. Chọn nhóm tuổi và triệu chứng hiện tại.
5. Xem mức rủi ro.
6. Mở từng thẻ thuốc để xem giải thích.
7. Xem nhận xét tổng quan của AI.
8. Nếu có cảnh báo khẩn cấp, nhấn mạnh user cần liên hệ cơ sở y tế hoặc bác sĩ.
