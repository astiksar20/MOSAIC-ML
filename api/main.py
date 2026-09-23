from fastapi import FastAPI, UploadFile, File
import tempfile
import os

from analyzer.apk_analyzer import analyze_apk


app = FastAPI(
    title="MOSAIC-ML API",
    description="Android vulnerability and intrusion risk analysis API",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "project": "MOSAIC-ML",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/analyze-apk")
async def analyze_uploaded_apk(file: UploadFile = File(...)):

    suffix = ".apk"

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as temp_file:

        contents = await file.read()
        temp_file.write(contents)
        temp_path = temp_file.name

    try:
        result = analyze_apk(temp_path)

        return {
            "filename": file.filename,
            "analysis": result
        }

    finally:
        os.remove(temp_path)