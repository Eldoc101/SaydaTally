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
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="static", html=True), name="static")

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
import os, json
from google.oauth2 import service_account
from google.cloud import vision

# قراءة بيانات Google Vision من الـ Environment Variable
credentials_info = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
credentials = service_account.Credentials.from_service_account_info(credentials_info)

# إنشاء العميل
vision_client = vision.ImageAnnotatorClient(credentials=credentials)


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
