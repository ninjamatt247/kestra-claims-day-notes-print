import os
import traceback
from PyPDF2 import PdfReader, PdfWriter

US_LETTER_WIDTH = 8.5 * 72  # Convert inches to points (1 inch = 72 points)
US_LETTER_HEIGHT = 11 * 72   # Convert inches to points

from concurrent.futures import ProcessPoolExecutor  # Added import statement

def add_blank_page_if_needed(input_path, continuation_line):
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        needs_blank_page = False  # Flag to indicate if a blank page is needed
        current_page = 0  # Start page numbering from 0

        for page in reader.pages:
            current_page += 1
            text = page.extract_text() or ""  # Ensure text is not None
            
            # Check if the page is not the first page of the document
            if current_page != 1:
                # Check if the current page is odd and the continuation line is not found
                if current_page % 2 == 1 and continuation_line not in text:
                    # Add a blank page with US Letter page size
                    blank_page = PdfWriter()
                    blank_page.add_blank_page(width=US_LETTER_WIDTH, height=US_LETTER_HEIGHT)
                    # Insert the blank page before the current page
                    writer.insert_page(blank_page.pages[0], current_page - 1)
                writer.add_page(page)

        # Save the new PDF with 'RTP_' prefix
        base_directory = os.path.dirname(input_path)
        filename = os.path.basename(input_path)
        output_path = os.path.join(base_directory, f"RTP_{filename}")
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        # Move the original file to the 'processed' directory
        processed_directory = os.path.join(base_directory, "processed")
        os.makedirs(processed_directory, exist_ok=True)
        processed_file_path = os.path.join(processed_directory, filename)
        os.rename(input_path, processed_file_path)
        
        return f"Processed {output_path}"
    
    except Exception as e:
        # Log the error message along with the traceback
        error_msg = f"Error processing {input_path}: {str(e)}\n{traceback.format_exc()}"
        error_output_path = os.path.join(base_directory, f"error_{filename}")
        os.rename(input_path, error_output_path)
        return error_msg

def process_files_in_directory(directory, continuation_phrase):
    # Collect all applicable PDF files
    pdf_files = [os.path.join(directory, f) for f in os.listdir(directory) 
                 if f.endswith(".pdf") and not (f.startswith("RTP_") or f.startswith("error_"))]
    
    results = []
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(add_blank_page_if_needed, pdf_files, [continuation_phrase] * len(pdf_files)))
    
    # Log results
    with open(os.path.join(directory, "processing_log.txt"), "a") as log_file:
        for result in results:
            if result:
                log_file.write(result + "\n")
                print(result)

# Specify the directory containing the PDF files
pdf_directory = './pdfs'
continuation_phrase = "*** continued from previous page ***"
process_files_in_directory(pdf_directory, continuation_phrase)
