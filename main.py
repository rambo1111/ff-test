from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import google.generativeai as genai
import tempfile
import os
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import requests
import time

app = FastAPI()

# Configure CORS to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from all origins
    allow_credentials=True,
    allow_methods=["POST"],
    allow_methods=["GET"],
    allow_methods=["HEAD"]
    allow_headers=["*"],
)

# Configure Google Generative AI
GOOGLE_API_KEY = 'AIzaSyCAzjRDfy9rbkP4v8CWCi9_vWaypLPY15c'
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
               4. Also write  the questions before answering them.'''],
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
        }
    )
    
    return response.text

def continuous_requests():
    try:
        response = requests.get("https://test-assingnement-api.onrender.com/keep-alive")
        print(response.text)
    except Exception as e:
        print(f"Error occurred: {e}")
    time.sleep(10)


# @app.head("/")
# async def head_root():
#     continuous_requests()
#     return JSONResponse(content={"message": "Continuous requests completed."})


@app.get("/keep-alive")
async def keep_alive():
    return JSONResponse(content={"message": "Server is active"})

@app.post("/process-file/")
async def process_file(file: UploadFile = File(...), subject: str = Form(...)):

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
                response = handle_pdf(file_path, subject, model)
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
