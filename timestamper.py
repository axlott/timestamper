"""
Main functions for timestamping images while preserving their original metadata.
"""
import os
import piexif
import pillow_heif
from PIL import Image, ImageDraw, ImageFont, ImageOps
from meta_reader import get_creation_date
from config import FONT_WIDTH_RATIO, MIN_FONT_SIZE, OUTPUT_FOLDER_NAME

def timestamp_image(input_path, output_path):
    """
    Adds a timestamp to an image, preserves all original EXIF data,
    and saves it to the output path.
    """
    creation_date = get_creation_date(input_path)
    if not creation_date:
        print(f"Skipping {os.path.basename(input_path)}: No creation date.")
        return

    try:
        exif_dict = {}
        if input_path.lower().endswith('.heic'):
            heif_file = pillow_heif.read_heif(input_path)
            image = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw")
            if 'exif' in heif_file.info:
                exif_dict = piexif.load(heif_file.info['exif'])
        else:
            image = Image.open(input_path)
            if 'exif' in image.info:
                exif_dict = piexif.load(image.info['exif'])
        
        image = ImageOps.exif_transpose(image)
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        draw = ImageDraw.Draw(image)
        text = creation_date
        longest_side = max(image.width, image.height)
        font_size = max(MIN_FONT_SIZE, int(longest_side / FONT_WIDTH_RATIO))

        font_names = [
            "/System/Library/Fonts/Courier.ttc", "C:/Windows/Fonts/consola.ttf",
            "C:/Windows/Fonts/cour.ttf", "Consolas.ttf", "Courier New.ttf"
        ]
        font = None
        for font_name in font_names:
            try:
                font = ImageFont.truetype(font_name, size=font_size)
                break
            except IOError:
                continue
        if not font:
            font = ImageFont.load_default()

        text_bbox = draw.textbbox((0, 0), text, font=font, stroke_width=5)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        margin = max(20, int(image.width * 0.02))
        x = image.width - text_width - margin
        y = image.height - text_height - margin
        
        final_draw = ImageDraw.Draw(image)
        final_draw.text((x, y), text, font=font, fill=(235, 188, 60), stroke_width=5, stroke_fill=(90, 70, 40))
        filename=os.path.splitext(os.path.basename(input_path))[0]
        final_dir=os.path.join(output_path, filename + ".png")
        i=0
        while os.path.exists(final_dir):
            i+=1
            final_dir=os.path.join(output_path, filename + str(i) + ".png")        
        exif_bytes_to_save = piexif.dump(exif_dict)
        image.save(final_dir, 'PNG', exif=exif_bytes_to_save)
        print(f"Successfully timestamped: {os.path.basename(final_dir)}")

    except Exception as e:
        print(f"Failed to process {os.path.basename(input_path)}: {e}")

def process_folder_for_timestamping(source_folder):
    """
    Processes all supported images in a folder, saving timestamped
    versions to a new output directory.
    """
    output_folder = OUTPUT_FOLDER_NAME
    
    print("--- Starting Folder Cleaning Process ---")
    folder_clearer(output_folder)
    print("--- Starting Image Timestamping Process ---")
    if not os.path.isdir(source_folder):
        print(f"Error: Source folder not found at '{source_folder}'")
        return None

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output directory: {output_folder}")

    supported_extensions = ('.heic', '.png', '.jpg', '.jpeg')
    for filename in os.listdir(source_folder):
        if filename.lower().endswith(supported_extensions):
            input_file_path = os.path.join(source_folder, filename)
            timestamp_image(input_file_path, output_folder)
    
    print("--- Image Timestamping Complete ---")
    return output_folder

def folder_clearer(folder_path):
    """
    Clears all files in the specified folder.
    """
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found at '{folder_path}'")
        return

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted file: {filename}")
        except Exception as e:
            print(f"Failed to delete {filename}: {e}")