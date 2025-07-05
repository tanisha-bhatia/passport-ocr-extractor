# Passport OCR Extractor

A **Flask-based Passport OCR extraction API** using **OCR.Space API** and PostgreSQL for structured storage.

---

## Features

✅ Upload passport images via API.  
✅ Extract key fields (name, DOB, passport number, issuing country, etc.).  
✅ Stores extracted data in **PostgreSQL** for audit and retrieval.  
✅ Uses **OCR.Space API** for OCR extraction.  
✅ Designed for further integration with **frontend dashboards, automation pipelines, or verification workflows**.

---

## How it works

1. User sends a `POST` request to `/upload` with the passport image.
2. Flask server sends the image to **OCR.Space API** for text extraction.
3. Extracted text is parsed for:
   - Document type
   - Issuing country
   - Surname and given names
   - Passport number
   - Nationality
   - Date of birth
   - Gender
   - Expiration date
   - Date of issue
4. Structured data is saved in **PostgreSQL**.
5. JSON response with structured fields is returned to the user.

---

## Limitations

⚠️ This is not yet 100% accurate across all image qualities due to:
- Variations in passport layouts.
- OCR limitations on low-resolution/blurry images.
- API limits in the free OCR.Space tier.

**However, this setup provides significantly improved structured extraction compared to raw EasyOCR pipelines.**

---

## Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/tanisha-bhatia/passport-ocr-extractor.git
cd passport-ocr-extractor/backend

2️⃣ Create a virtual environment

python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

3️⃣ Install dependencies

pip install -r requirements.txt

4️⃣ Configure database

Ensure PostgreSQL is installed and running.

CREATE DATABASE passport_ocr_db;
CREATE USER passport_user WITH PASSWORD 'passport_password';
GRANT ALL PRIVILEGES ON DATABASE passport_ocr_db TO passport_user;

Update DATABASE_URL in main.py if you use different credentials.
5️⃣ Add your OCR.Space API Key

Replace:

api_key = "your_api_key_here"

in main.py with your OCR.Space API key.
6️⃣ Run the Flask server

python main.py

API will be available at:

http://127.0.0.1:8000/

API Usage
Health check

curl http://127.0.0.1:8000/

Upload endpoint

curl -X POST -F "file=@path_to_passport_image.jpg" http://127.0.0.1:8000/upload

Response:

{
    "id": 1,
    "filename": "passport_sample.jpg",
    "extracted_text": {
        "document_type": "P",
        "issuing_country": "IND",
        ...
    },
    "timestamp": "2025-07-03T12:30:00.123456"
}

Future Improvements

    Fine-tune post-processing for even cleaner field extraction.

    Integrate Google Sheets or Airtable for real-time dashboards.

    Add logging and monitoring for production use.

    Secure API with authentication tokens.
