from os import path
# This constant controls the size of the font relative to the image's longest side.
# A smaller number will result in a LARGER font.
# A larger number will result in a SMALLER font.
FONT_WIDTH_RATIO = 35

# This is the smallest font size we will allow, to ensure readability on small images.
MIN_FONT_SIZE = 40

# --- Folder Paths ---
# The folder containing your original images.
SOURCE_IMAGE_FOLDER = path.join('img','input')

# The folder where the timestamped images will be saved.
# This will be created inside your SOURCE_IMAGE_FOLDER.
OUTPUT_FOLDER_NAME = path.join('img','timestamped_images')
# --- CONFIGURATION ---
# This should be the folder containing your timestamped PNGs.
IMAGE_FOLDER = OUTPUT_FOLDER_NAME
# This is the full path to your metadata JSON file.
METADATA_JSON_FILE = path.join(IMAGE_FOLDER, 'metadata_report.json')
# The name of the final Word document that will be created.
OUTPUT_DOCX_FILE = 'Photo_Album.docx'
PEOPLE_TO_ADD = "Jose Andres and Axel" 