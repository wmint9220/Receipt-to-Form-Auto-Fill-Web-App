from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn

app = FastAPI()

@app.get("/")
def home():
    return {"status": "online", "message": "Receipt-to-Form API is ready."}

@app.post("/api/extract")
async def extract_receipt(file: UploadFile = File(...)):
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Read image contents
    # In a real app, you would pass 'contents' to an OCR engine like pytesseract
    # or an API like OpenAI GPT-4o-vision or Google Gemini.
    contents = await file.read()
    
    # MOCK DATA: This simulates what an AI extraction would return
    extracted_data = {
        "success": True,
        "filename": file.filename,
        "merchant": {
            "name": "Central Market",
            "address": "123 Main St, City",
            "phone": "555-0199"
        },
        "transaction": {
            "date": "2023-10-25",
            "time": "14:30",
            "total_amount": 42.50,
            "currency": "USD",
            "tax": 3.40
        },
        "items": [
            {"description": "Organic Apples", "qty": 2, "unit_price": 5.00, "total": 10.00},
            {"description": "Coffee Beans", "qty": 1, "unit_price": 32.50, "total": 32.50}
        ]
    }
    
    return extracted_data
