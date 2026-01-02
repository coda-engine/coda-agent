from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
import pandas as pd
from pypdf import PdfReader
import io

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    content = ""
    file_type = file.content_type
    filename = file.filename
    
    try:
        import os
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".pdf":
            # Read PDF
            pdf_content = await file.read()
            pdf_file = io.BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            text = []
            for page in reader.pages:
                text.append(page.extract_text())
            content = "\n".join(text)
            
        elif ext == ".csv":
            # Read CSV
            # Reset file pointer if needed, but file.read() wasn't called yet
            await file.seek(0)
            df = pd.read_csv(file.file)
            content = df.to_markdown(index=False)
            
        elif ext in [".xlsx", ".xls"]:
            # Read Excel
            await file.seek(0)
            df = pd.read_excel(file.file)
            content = df.to_markdown(index=False)
            
        elif ext in [".txt", ".md", ".py", ".js", ".ts", ".json", ".html", ".css", ".xml", ".yaml", ".yml"]:
            # Read Text
            content_bytes = await file.read()
            content = content_bytes.decode("utf-8")
        else:
            # Fallback to text if unknown but looks text-ish?
            # Or assume text if not binary knowns?
            # Let's try to decode as UTF-8
            try:
                content_bytes = await file.read()
                content = content_bytes.decode("utf-8")
            except:
                 raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

        return {
            "filename": filename,
            "content_type": file_type,
            "content": content,
            "size": len(content)
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=422, detail=f"Failed to process file {file.filename}: {str(e)}")
