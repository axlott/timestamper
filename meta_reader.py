import datetime
import os
from PIL import Image
import piexif
import pillow_heif
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

def get_creation_date(filepath):
    """
    Extracts the creation date from image or video metadata.
    Falls back to the file's last modification time if metadata is not found.
    """
    # --- Video Metadata Extraction using Hachoir ---
    if filepath.lower().endswith(('.mov', '.mp4')):
        try:
            parser = createParser(filepath)
            metadata = extractMetadata(parser)
            if metadata and metadata.has('creation_date'):
                return metadata.get('creation_date').strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"Could not read video metadata for {os.path.basename(filepath)}: {e}")
    
    # --- Image EXIF Metadata Extraction ---
    try:
        if filepath.lower().endswith('.heic'):
            heif_file = pillow_heif.read_heif(filepath)
            if 'exif' in heif_file.info and heif_file.info['exif']:
                exif_dict = piexif.load(heif_file.info['exif'])
            else:
                exif_dict = {}
        else:
            with Image.open(filepath) as img:
                if 'exif' in img.info and img.info['exif']:
                    exif_dict = piexif.load(img.info['exif'])
                else:
                    exif_dict = {}
        
        if exif_dict and piexif.ExifIFD.DateTimeOriginal in exif_dict.get('Exif', {}):
            datetime_original = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
            date_part, time_part = datetime_original.split(' ')
            date_part = date_part.replace(':', '-')
            return f"{date_part} {time_part}"

    except Exception:
        # This is not an error, just an attempt. We can ignore failures here.
        pass

    # --- Fallback Method: Use file's last modification time for all types ---
    try:
        mod_time = os.path.getmtime(filepath)
        return datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Could not get file modification date for {os.path.basename(filepath)}: {e}")

    return None

