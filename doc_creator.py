"""
This script reads the output from the image processing workflow:
1. The 'metadata_report.json' file.
2. The folder of timestamped images.

It then generates a Microsoft Word document (.docx) with one page per image,
containing the image itself and its corresponding metadata.
"""
import os
import json
from PIL import Image
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from config import IMAGE_FOLDER, METADATA_JSON_FILE, OUTPUT_DOCX_FILE, PEOPLE_TO_ADD

def load_metadata_from_json(json_path):
    """
    Loads the structured metadata from the JSON report file.
    """
    if not os.path.exists(json_path):
        print(f"Error: JSON report file not found at '{json_path}'")
        return None
    
    print(f"Loading metadata from '{json_path}'...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Successfully loaded metadata for {len(data)} photos.")
    return data


def create_word_document(image_folder, metadata_dict, people_in_photo):
    """
    Creates a Word document from images and their metadata with specific formatting.
    """
    if not os.path.isdir(image_folder):
        print(f"Error: Image folder not found at '{image_folder}'")
        return

    print("Creating Word document...")
    document = Document()
    
    style = document.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)

    for processed_filename, metadata in metadata_dict.items():
        image_path = os.path.join(image_folder, processed_filename)
        
        if not os.path.exists(image_path):
            print(f"Warning: Image '{processed_filename}' not in folder. Skipping.")
            continue

        print(f"Adding '{processed_filename}' to document...")

        # --- Update People Field (if necessary) ---
        if metadata.get('People') == "NULL" and people_in_photo:
            metadata['People'] = people_in_photo

        original_filename = metadata.get('OriginalFileName', processed_filename)
        heading = document.add_heading(original_filename, level=2)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # --- Smart Image Sizing and Centering ---
        with Image.open(image_path) as img:
            width_px, height_px = img.size

        if width_px > height_px:  # Landscape
            document.add_picture(image_path, width=Inches(7.0))
        else:  # Portrait or square
            document.add_picture(image_path, height=Inches(5.7))
        
        last_paragraph = document.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        document.add_paragraph() 
        for key, value in metadata.items():
            # Skip the 'Comments' key here because it's handled separately below
            # as the 'Description' field. This prevents duplication.
            field_name=""
            field_content=""
            if key == 'Comments':
                continue
            elif key == 'GPS_Location':
                field_name="GPS Location"
            elif key == 'OriginalFileName':
                field_name="Original File Name"
            elif key == 'Location_Address':
                field_name="Location Address"
            elif key == 'DeviceMake':
                field_name="Device Make"
            elif key == 'DeviceModel':
                field_name="DeviceModel"
            elif key == 'FocalLength':
                field_name="Focal Length"
            elif key == 'ShutterSpeed':
                field_name="Shutter Speed"
            else:
                field_name=key
#         "OriginalFileName": "20220710_041555.jpg",
    #     "Timestamp": "2022-07-10 04:15:55",
    #     "People": "NULL",
    #     "Location_Address": "Vorterix, Avenida Federico Lacroze, Colegiales, Buenos Aires, Distrito Audiovisual, Comuna 13, Autonomous City of Buenos Aires, C1427CCG, Argentina",
    #     "GPS_Location": "-34.5801, -58.4509",
    #     "DeviceMake": "samsung",
    #     "DeviceModel": "SM-S908E",
    #     "Dimensions": "4000x2252",
    #     "FocalLength": "6mm",
    #     "Aperture": "f/1.8",
    #     "ShutterSpeed": "1/25s",
    #     "ISO": 1000,
    #     "Flash": "No Flash",
    #     "Comments": "Us togheter in our bachelor's party."
    # },
            field_content = value[0].upper() + value[1:] if isinstance(value, str) else value
            p = document.add_paragraph()
            p.add_run(f'{field_name}: ').bold = True
            p.add_run(str(field_content))
            p.paragraph_format.space_after = Pt(0)

        # --- Add Description Field, populated from Comments ---
        p = document.add_paragraph()
        p.add_run('Description: ').bold = True
        p.paragraph_format.space_after = Pt(0)
        
        comments = metadata.get('Comments')
        if comments and comments != "NULL":
            p.add_run(comments)
        
        document.add_page_break()

    try:
        document.save(OUTPUT_DOCX_FILE)
        print(f"\nSuccessfully created Word document: '{OUTPUT_DOCX_FILE}'")
    except Exception as e:
        print(f"Error saving document: {e}")

# --- SCRIPT EXECUTION ---
if __name__ == "__main__":
    if not PEOPLE_TO_ADD:
        print("Error: Please edit the script and set the 'PEOPLE_TO_ADD' variable before running.")
    else:
        loaded_data = load_metadata_from_json(METADATA_JSON_FILE)
        if loaded_data:
            create_word_document(IMAGE_FOLDER, loaded_data, PEOPLE_TO_ADD)



