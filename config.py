from os import path

# --- Image Font Settings ---
FONT_WIDTH_RATIO = 35
MIN_FONT_SIZE = 40

# --- Video Font Settings (NEW) ---
# A smaller number makes the text BIGGER. This is the main setting to adjust.
VIDEO_FONT_SCALE_RATIO = 900
# A smaller number makes the text THICKER.
VIDEO_FONT_THICKNESS_RATIO = 350
# Minimum values to ensure readability on small videos.
MIN_VIDEO_FONT_SCALE = 1.0
MIN_VIDEO_FONT_THICKNESS = 2
MAX_PHOTOGRAMS_PER_BATCH = 250

# --- Folder Paths ---
SOURCE_IMAGE_FOLDER = path.join('img', 'input')
OUTPUT_FOLDER_NAME = path.join('img', 'timestamped_images')

# --- Document Creator Paths ---
IMAGE_FOLDER = OUTPUT_FOLDER_NAME
METADATA_JSON_FILE = path.join(IMAGE_FOLDER, 'metadata_report.json')
OUTPUT_DOCX_FILE = 'Photo_Album.docx'
PEOPLE_TO_ADD = "Jose Andres and Axel"

