"""
Text Extraction Module
Extracts text from uploaded files (images, PDFs, DOCX).
"""
import os


def extract_text_from_image(img_path):
    """Extract text from an image using EasyOCR."""
    try:
        import easyocr
        reader = easyocr.Reader(['en'])
        result = reader.readtext(img_path)
        extracted_text = " ".join([text for (_, text, prob) in result if prob >= 0.2])
        return extracted_text
    except ImportError:
        return "[EasyOCR not installed - install with: pip install easyocr]"
    except Exception as e:
        return f"[OCR Error: {str(e)}]"


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except ImportError:
        return "[PyPDF2 not installed - install with: pip install PyPDF2]"
    except Exception as e:
        return f"[PDF Error: {str(e)}]"


def extract_text_from_docx(docx_path):
    """Extract text from DOCX file."""
    try:
        import docx
        doc = docx.Document(docx_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except ImportError:
        return "[python-docx not installed - install with: pip install python-docx]"
    except Exception as e:
        return f"[DOCX Error: {str(e)}]"


def extract_text_from_txt(txt_path):
    """Extract text from plain text file."""
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"[Text Error: {str(e)}]"


def extract_text_from_md(md_path):
    """Extract text from markdown file."""
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"[Markdown Error: {str(e)}]"


def extract_text(file_path):
    """Extract text from any supported file type."""
    ext = os.path.splitext(file_path)[1].lower()

    extractors = {
        '.png': extract_text_from_image,
        '.jpg': extract_text_from_image,
        '.jpeg': extract_text_from_image,
        '.bmp': extract_text_from_image,
        '.pdf': extract_text_from_pdf,
        '.docx': extract_text_from_docx,
        '.txt': extract_text_from_txt,
        '.md': extract_text_from_md,
    }

    extractor = extractors.get(ext)
    if extractor:
        return extractor(file_path)
    else:
        return f"[Unsupported file type: {ext}]"
