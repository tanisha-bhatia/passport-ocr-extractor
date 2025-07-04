from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
from sqlalchemy import create_engine, Column, Integer, String, JSON, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database setup
DATABASE_URL = "postgresql+psycopg2://passport_user:passport_password@localhost/passport_ocr_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PassportData(Base):
    __tablename__ = "passport_data"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    extracted_data = Column(JSON)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "OCR.Space Passport OCR Flask Backend Running"})

def parse_mrz(mrz_lines):
    data = {}
    if len(mrz_lines) >= 2:
        line1 = mrz_lines[0]
        line2 = mrz_lines[1]

        data['document_type'] = line1[0] if len(line1) > 0 else ""
        data['issuing_country'] = line1[2:5] if len(line1) >= 5 else ""

        names = line1[5:].split('<<')
        data['surname'] = names[0].replace('<', ' ').strip() if len(names) > 0 else ""
        data['given_names'] = names[1].replace('<', ' ').strip() if len(names) > 1 else ""

        data['passport_number'] = line2[0:9].replace('<', '').strip() if len(line2) >= 9 else ""
        data['nationality'] = line2[10:13] if len(line2) >= 13 else ""

        dob_raw = line2[13:19] if len(line2) >= 19 else ""
        if len(dob_raw) == 6:
            data['date_of_birth'] = f"19{dob_raw[0:2]}-{dob_raw[2:4]}-{dob_raw[4:6]}"

        gender_value = line2[20] if len(line2) >= 21 else ""
        if gender_value in ['M', 'F']:
            data['gender'] = gender_value

        expiry_raw = line2[21:27] if len(line2) >= 27 else ""
        if len(expiry_raw) == 6:
            data['expiration_date'] = f"20{expiry_raw[0:2]}-{expiry_raw[2:4]}-{expiry_raw[4:6]}"

    return data

@app.route("/upload", methods=["POST"])
def upload_passport():
    try:
        file = request.files["file"]
        file_bytes = file.read()

        # OCR.Space API call
        api_key = "K89968979888957"
        response = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": (file.filename, file_bytes)},
            data={"apikey": api_key, "OCREngine": 2, "isTable": True},
        )
        result = response.json()

        if result.get("IsErroredOnProcessing"):
            return jsonify({"error": result.get("ErrorMessage", "OCR processing failed")}), 500

        parsed_text = result["ParsedResults"][0]["ParsedText"]

        # Extract MRZ lines
        mrz_matches = re.findall(r'[A-Z0-9<]{30,}', parsed_text)
        mrz_lines = mrz_matches[-2:] if len(mrz_matches) >= 2 else mrz_matches

        structured_data = parse_mrz(mrz_lines)

        # Date of Issue Extraction
        date_of_issue = None
        found_dates = re.findall(r'\d{2}/\d{2}/\d{4}', parsed_text)
        for dt in found_dates:
            day, month, year = dt.split("/")
            formatted_date = f"{year}-{month}-{day}"
            if formatted_date != structured_data.get('date_of_birth') and formatted_date != structured_data.get('expiration_date'):
                date_of_issue = formatted_date
                break
        if date_of_issue:
            structured_data['date_of_issue'] = date_of_issue

        if not any(structured_data.values()):
            return jsonify({
                "error": "No valid MRZ data detected in the uploaded image. Please ensure the image is clear and contains a readable passport MRZ."
            }), 422

        # Save structured_data with raw_text internally for logs
        structured_data_for_db = structured_data.copy()
        structured_data_for_db["raw_text"] = parsed_text

        db = SessionLocal()
        passport_entry = PassportData(
            filename=file.filename,
            extracted_data=structured_data_for_db
        )
        db.add(passport_entry)
        db.commit()
        db.refresh(passport_entry)
        db.close()

        return jsonify({
            "id": passport_entry.id,
            "filename": file.filename,
            "extracted_text": structured_data,
            "timestamp": passport_entry.timestamp.isoformat()
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": f"Error uploading or extracting data: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=8000)

