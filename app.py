from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
import os
import pytesseract
from PIL import Image
import pdfplumber
from docx import Document
from text_processing import append_to_json_file, json_to_csv

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Set the path to Tesseract executable (Modify for your system)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# OCR for images
def extract_text_from_image(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text

# Extract text from PDFs
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Extract text from DOCX files
def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])

# Extract text from Markdown files
def extract_text_from_md(md_path):
    with open(md_path, 'r') as f:
        return f.read()

# Flask route to handle uploads
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            try:
                # Extract text based on file type
                if filename.endswith(('png', 'jpg', 'jpeg', 'tiff')):
                    extracted_text = extract_text_from_image(file_path)
                elif filename.endswith('.pdf'):
                    extracted_text = extract_text_from_pdf(file_path)
                elif filename.endswith('.docx'):
                    extracted_text = extract_text_from_docx(file_path)
                elif filename.endswith('.md'):
                    extracted_text = extract_text_from_md(file_path)
                else:
                    raise ValueError(f"Unsupported file type: {filename}")

                # Prepare data to be saved as JSON
                new_data = {
                    "filename": filename,
                    "text": extracted_text
                }

                # Append the new data to the JSON file
                append_to_json_file(new_data)

                # Convert the updated JSON to CSV
                csv_path = json_to_csv()

                return render_template('result.html', 
                                       extracted_text=extracted_text, 
                                       csv_path=csv_path)

            except Exception as e:
                return render_template('error.html', message=f"Error: {str(e)}")

    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)