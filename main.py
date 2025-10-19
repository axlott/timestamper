"""
Main script to run the image timestamping and metadata reporting workflow.
"""
from timestamper import process_folder_for_timestamping
from reporter import generate_metadata_report
from config import SOURCE_IMAGE_FOLDER,OUTPUT_FOLDER_NAME, METADATA_JSON_FILE, IMAGE_FOLDER, PEOPLE_TO_ADD
from doc_creator import load_metadata_from_json, create_word_document

if __name__ == "__main__":
    # Step 1: Timestamp all images. This function creates the output
    # folder and returns its path.
    output_folder = process_folder_for_timestamping(SOURCE_IMAGE_FOLDER)
    
    # # Step 2: Generate the metadata report. We read from the SOURCE folder
    # # to get original, unaltered metadata and save the report to the OUTPUT folder.
    # if output_folder:
    generate_metadata_report(SOURCE_IMAGE_FOLDER, OUTPUT_FOLDER_NAME)

    loaded_data = load_metadata_from_json(METADATA_JSON_FILE)
    if loaded_data:
        create_word_document(IMAGE_FOLDER, loaded_data, PEOPLE_TO_ADD)
    print("\nAll tasks complete.")
