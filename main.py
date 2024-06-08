from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import google.generativeai as genai
import tempfile
import os
from google.generativeai.types import HarmCategory, HarmBlockThreshold

app = FastAPI()

# Configure CORS to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from all origins
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Configure Google Generative AI
GOOGLE_API_KEY = 'your_google_api_key'
genai.configure(api_key=GOOGLE_API_KEY)

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def handle_pdf(pdf_path, subject, model):
    extracted_text = extract_text_from_pdf(pdf_path)

    response = model.generate_content(
        [f'''I have extracted text from a pdf, which is my {subject} assignment. Please answer these questions:{extracted_text}.
         NOTE: 1. Start every answer with Ans1-, next with Ans2- and so on.
               2. Don't use any markdown, just give answer in normal text without any markdown symbols.
               3. You can use a line break for next line.
               4. Also wr'''],
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
        }
    )
    
    return response.text

def process_pdf_background(pdf_path, subject, model):
    # Check if the file path has a ".pdf" extension
    while not pdf_path.lower().endswith(".pdf"):
        print("File is not present")
    
    # Proceed with processing the PDF
    response = handle_pdf(pdf_path, subject, model)

@app.post("/process-file/")
async def process_file(file: UploadFile = File(...), subject: str = Form(...), background_tasks: BackgroundTasks):
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Save the uploaded file to the temporary directory
        file_path = os.path.join(tmpdirname, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Initialize the Generative AI model
        model = genai.GenerativeModel(model_name="gemini-pro")

        try:
            # Determine file type and process accordingly
            if file.filename.lower().endswith(".pdf"):
                # Add the background task to process the PDF
                background_tasks.add_task(process_pdf_background, file_path, subject, model)
                response = "Processing PDF in background"
            elif file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".docx", ".doc")):
                response = "WE ARE UNDER DEVELOPMENT"
            else:
                raise ValueError("Unsupported file type. Please provide a PDF or image file.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return JSONResponse(content={"response": response})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
