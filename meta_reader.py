"""
Functions for extracting creation date metadata from various image formats.
"""
import datetime
import os
from PIL import Image
import piexif
import pillow_heif

def get_creation_date(filepath):
    """
    Extracts the creation date from image metadata (EXIF).
    If EXIF is not found, falls back to the file's last modification time.
    """
    exif_dict = {}
    try:
        if filepath.lower().endswith('.heic'):
            heif_file = pillow_heif.read_heif(filepath)
            # Safety check: Only load exif if it exists
            if 'exif' in heif_file.info and heif_file.info['exif']:
                exif_dict = piexif.load(heif_file.info['exif'])
        else:
            with Image.open(filepath) as img:
                # Safety check: Only load exif if it exists
                if 'exif' in img.info and img.info['exif']:
                    exif_dict = piexif.load(img.info['exif'])
        
        if exif_dict and piexif.ExifIFD.DateTimeOriginal in exif_dict.get('Exif', {}):
            datetime_original = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
            date_part, time_part = datetime_original.split(' ')
            date_part = date_part.replace(':', '-')
            return f"{date_part} {time_part}"

    except Exception as e:
        print(f"Could not read EXIF for {os.path.basename(filepath)}: {e}.")
    
    # --- Fallback Method: Use file's last modification time ---
    try:
        mod_time = os.path.getmtime(filepath)
        return datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Could not get file mod date for {os.path.basename(filepath)}: {e}")

    return None

