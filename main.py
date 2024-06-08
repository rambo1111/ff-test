from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
import google.generativeai as genai
import tempfile
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
GOOGLE_API_KEY = 'AIzaSyCAzjRDfy9rbkP4v8CWCi9_vWaypLPY15c'
genai.configure(api_key=GOOGLE_API_KEY)

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text()
    return text

def handle_pdf(pdf_path, subject, model):
    extracted_text = extract_text_from_pdf(pdf_path)

    response = model.generate_content(
        [f'I have extracted text from a pdf, which is my {subject} assignment. Please answer these questions:{extracted_text}'],
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
        }
    )
    
    return response.text

def convert_image_to_pdf(image_path, pdf_path):
    # Open the image using Pillow
    img = Image.open(image_path)

    # Create a PDF canvas using ReportLab
    pdf_canvas = canvas.Canvas(pdf_path, pagesize=letter)

    # Get the dimensions of the image
    img_width, img_height = img.size

    # Calculate the aspect ratio to maintain the image's proportions
    aspect_ratio = img_height / float(img_width)

    # Add the image to the PDF
    pdf_canvas.drawImage(image_path, 0, 0, width=letter[0], height=letter[0]*aspect_ratio)

    # Save the PDF
    pdf_canvas.save()

def handle_image(image_path, subject, model):
    # Create a temporary directory to store the PDF
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Generate a temporary PDF file path
        pdf_path = os.path.join(tmpdirname, "temp.pdf")
        
        # Convert the image to PDF
        convert_image_to_pdf(image_path, pdf_path)
        
        # Process the PDF using the existing function
        response = handle_pdf(pdf_path, subject, model)
    
    return response

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
            elif file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
                response = handle_image(file_path, subject, model)
            else:
                raise ValueError("Unsupported file type. Please provide a PDF or image file.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return JSONResponse(content={"response": response})

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
