from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import vision
from supabase import create_client, Client
import os
import uuid

# -----------------------------------
# إعداد FastAPI
# -----------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ممكن تحدد الدومينات المسموح لها
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------
# الاتصال بـ Supabase
# -----------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------------
# إعداد Google Vision API
# -----------------------------------
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
vision_client = vision.ImageAnnotatorClient()

# -----------------------------------
# رفع صورة وتشغيل OCR
# -----------------------------------
@app.post("/ocr")
async def ocr_image(file: UploadFile = File(...)):
    try:
        # قراءة الصورة
        contents = await file.read()
        image = vision.Image(content=contents)

        # تحليل النصوص
        response = vision_client.text_detection(image=image)
        texts = response.text_annotations

        if not texts:
            return {"success": False, "message": "No text detected"}

        extracted_text = texts[0].description.strip()

        # حفظ النتيجة في Supabase
        data = {
            "id": str(uuid.uuid4()),
            "file_name": file.filename,
            "extracted_text": extracted_text
        }
        supabase.table("ocr_results").insert(data).execute()

        return {"success": True, "extracted_text": extracted_text}

    except Exception as e:
        return {"success": False, "error": str(e)}

# -----------------------------------
# فحص حالة السيرفر
# -----------------------------------
@app.get("/")
def health_check():
    return {"status": "running"}
