
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import uvicorn
import os
import io
from supabase import create_client
from google.cloud import vision
import google.auth
import requests

app = FastAPI(title="SaydaTally API", version="1.0")

# إعداد Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# إعداد Google Vision API
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "vision_api_key.json"
vision_client = vision.ImageAnnotatorClient()

# إعداد Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

class DrugQuery(BaseModel):
    name: str

@app.post("/upload-prescription")
async def upload_prescription(file: UploadFile = File(...)):
    # قراءة الصورة
    content = await file.read()
    image = vision.Image(content=content)

    # استخراج النصوص من الروشتة
    response = vision_client.text_detection(image=image)
    texts = response.text_annotations

    if not texts:
        return {"error": "لم يتم التعرف على أي نصوص"}

    prescription_text = texts[0].description

    # تحليل النصوص باستخدام Gemini
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    payload = {
        "contents": [{"parts": [{"text": f"استخرج أسماء الأدوية من النص التالي: {prescription_text}"}]}]
    }

    ai_response = requests.post(GEMINI_URL, headers=headers, params=params, json=payload)
    drugs = ai_response.json()

    return {
        "extracted_text": prescription_text,
        "ai_analysis": drugs
    }

@app.post("/search-drug")
async def search_drug(query: DrugQuery):
    result = supabase.table("drugs").select("*").ilike("name", f"%{query.name}%").execute()
    return {"results": result.data}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
