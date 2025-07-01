from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import easyocr
from PIL import Image
import numpy as np
import io
from sqlalchemy import create_engine, Column, Integer, String, JSON, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Initialize FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict appropriately
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

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

@app.get("/")
async def root():
    return {"message": "Passport OCR FastAPI Backend Working"}

def parse_mrz(mrz_lines):
    data = {}
    if len(mrz_lines) >= 2:
        line1 = mrz_lines[0].replace(' ', '').replace('\n', '')
        line2 = mrz_lines[1].replace(' ', '').replace('\n', '')

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

        if len(line2) >= 21:
            gender_value = line2[20]
            if gender_value in ['M', 'F']:
                data['gender'] = gender_value

        expiry_raw = line2[21:27] if len(line2) >= 27 else ""
        if len(expiry_raw) == 6:
            data['expiration_date'] = f"20{expiry_raw[0:2]}-{expiry_raw[2:4]}-{expiry_raw[4:6]}"

    return data


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        print("== Upload endpoint called ==")
        contents = await file.read()
        print(f"File read: {len(contents)} bytes")

        image = Image.open(io.BytesIO(contents)).convert('RGB')
        print("Image converted to RGB")
        image_array = np.array(image)
        print("Image converted to numpy array")

        # Perform OCR using EasyOCR
        results = reader.readtext(image_array, detail=0, paragraph=False)
        print(f"OCR Raw Results: {results}")

        # Extract MRZ lines: typically the last 2 lines of passport
        mrz_lines = results[-2:] if len(results) >= 2 else results
        mrz_lines = [line.replace(" ", "").replace("\n", "") for line in mrz_lines]
        print(f"Detected MRZ Lines: {mrz_lines}")

        # Parse structured MRZ data
        structured_data = parse_mrz(mrz_lines)
        print(f"Parsed Structured Data: {structured_data}")

        # Save to database
        db = SessionLocal()
        passport_entry = PassportData(
            filename=file.filename,
            extracted_data=structured_data
        )
        db.add(passport_entry)
        db.commit()
        db.refresh(passport_entry)
        db.close()
        print(f"Saved entry with ID: {passport_entry.id}")

        # Return with 'extracted_text' key for frontend compatibility
        return JSONResponse(content={
            "id": passport_entry.id,
            "filename": file.filename,
            "extracted_text": structured_data,
            "timestamp": passport_entry.timestamp.isoformat()
        })

    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

