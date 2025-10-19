"""
Main functions for timestamping images and videos.
This version includes multithreaded video processing and configurable font sizes.
"""
import os
import piexif
import pillow_heif
import cv2
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from PIL import Image, ImageDraw, ImageFont, ImageOps
from meta_reader import get_creation_date
from config import (FONT_WIDTH_RATIO, MIN_FONT_SIZE, OUTPUT_FOLDER_NAME,
                    VIDEO_FONT_SCALE_RATIO, VIDEO_FONT_THICKNESS_RATIO,
                    MIN_VIDEO_FONT_SCALE, MIN_VIDEO_FONT_THICKNESS,MAX_PHOTOGRAMS_PER_BATCH)

def process_video_frame(frame, text_info):
    """
    Draws the timestamp on a single video frame. Called by worker threads.
    """
    text, pos, font_face, font_scale, color, thickness = text_info
    # Add a dark stroke for readability
    cv2.putText(frame, text, pos, font_face, font_scale, (0, 0, 0), thickness + 4, cv2.LINE_AA) # pylint: disable=no-member
    # Add the main text color
    cv2.putText(frame, text, pos, font_face, font_scale, color, thickness, cv2.LINE_AA) # pylint: disable=no-member
    return frame

def timestamp_video(input_path, output_path):
    """
    Adds a timestamp to each frame of a video using multiple threads.
    """
    print(f"Processing video: {os.path.basename(input_path)}")
    creation_date = get_creation_date(input_path)
    if not creation_date:
        print(f"Skipping video {os.path.basename(input_path)}: No creation date found.")
        return

    try:
        cap = cv2.VideoCapture(input_path) # pylint: disable=no-member
        if not cap.isOpened():
            print(f"Error: Could not open video file {input_path}")
            return

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) # pylint: disable=no-member
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) # pylint: disable=no-member
        fps = cap.get(cv2.CAP_PROP_FPS) # pylint: disable=no-member
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) # pylint: disable=no-member
        
        output_filename = os.path.splitext(os.path.basename(input_path))[0] + ".mp4"
        final_video_path = os.path.join(output_path, output_filename)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') # pylint: disable=no-member
        out = cv2.VideoWriter(final_video_path, fourcc, fps, (width, height)) # pylint: disable=no-member

        # ==================== MODIFICATION START ====================
        # --- Pre-calculate text styling using new config values ---
        longest_side = max(width, height)
        
        # Calculate size based on the ratio, enforcing a minimum
        font_scale = max(MIN_VIDEO_FONT_SCALE, longest_side / VIDEO_FONT_SCALE_RATIO)
        # Calculate thickness based on the ratio, enforcing a minimum
        font_thickness = max(MIN_VIDEO_FONT_THICKNESS, int(longest_side / VIDEO_FONT_THICKNESS_RATIO))
        
        font_face = cv2.FONT_HERSHEY_SIMPLEX # pylint: disable=no-member
        text = creation_date
        
        (text_width, _), _ = cv2.getTextSize(text, font_face, font_scale, font_thickness) # pylint: disable=no-member
        margin = int(width * 0.02)
        x = width - text_width - margin
        y = height - margin 
        
        text_info = (text, (x, y), font_face, font_scale, (60, 188, 235), font_thickness)
        # ===================== MODIFICATION END =====================
        
        batch_size = MAX_PHOTOGRAMS_PER_BATCH
        frames_batch = []
        
        with tqdm(total=total_frames, desc=f"Timestamping {os.path.basename(input_path)}") as pbar:
            with ThreadPoolExecutor() as executor:
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        if frames_batch:
                            processed_frames = executor.map(process_video_frame, frames_batch, [text_info] * len(frames_batch))
                            for proc_frame in processed_frames:
                                out.write(proc_frame)
                                pbar.update(1)
                        break
                    
                    frames_batch.append(frame)
                    
                    if len(frames_batch) == batch_size:
                        processed_frames = executor.map(process_video_frame, frames_batch, [text_info] * len(frames_batch))
                        for proc_frame in processed_frames:
                            out.write(proc_frame)
                            pbar.update(1)
                        frames_batch = []

        cap.release()
        out.release()
        print(f"\nSuccessfully timestamped video: {output_filename}")

    except Exception as e:
        print(f"Failed to process video {os.path.basename(input_path)}: {e}")

# The rest of your timestamper.py file (timestamp_image, process_folder, etc.) remains the same.
def timestamp_image(input_path, output_path):
    creation_date = get_creation_date(input_path)
    if not creation_date:
        print(f"Skipping {os.path.basename(input_path)}: No creation date.")
        return
    try:
        exif_dict = {}
        if input_path.lower().endswith('.heic'):
            heif_file = pillow_heif.read_heif(input_path)
            image = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw")
            if 'exif' in heif_file.info: exif_dict = piexif.load(heif_file.info['exif'])
        else:
            image = Image.open(input_path)
            if 'exif' in image.info: exif_dict = piexif.load(image.info['exif'])
        
        image = ImageOps.exif_transpose(image)
        if image.mode != 'RGBA': image = image.convert('RGBA')

        draw = ImageDraw.Draw(image)
        text = creation_date
        longest_side = max(image.width, image.height)
        font_size = max(MIN_FONT_SIZE, int(longest_side / FONT_WIDTH_RATIO))
        font_names = ["/System/Library/Fonts/Courier.ttc", "C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/cour.ttf", "Consolas.ttf", "Courier New.ttf"]
        font = None
        for font_name in font_names:
            try:
                font = ImageFont.truetype(font_name, size=font_size)
                break
            except IOError: continue
        if not font: font = ImageFont.load_default()
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
    output_folder = OUTPUT_FOLDER_NAME
    print("--- Starting Folder Cleaning Process ---")
    folder_clearer(output_folder)
    print("--- Starting Media Timestamping Process ---")
    if not os.path.isdir(source_folder):
        print(f"Error: Source folder not found at '{source_folder}'")
        return None
    os.makedirs(output_folder, exist_ok=True)

    supported_images = ('.heic', '.png', '.jpg', '.jpeg')
    supported_videos = ('.mov', '.mp4')
    for filename in os.listdir(source_folder):
        input_file_path = os.path.join(source_folder, filename)
        if filename.lower().endswith(supported_images):
            timestamp_image(input_file_path, output_folder)
        elif filename.lower().endswith(supported_videos):
            timestamp_video(input_file_path, output_folder)
    
    print("--- Media Timestamping Complete ---")
    return output_folder

def folder_clearer(folder_path):
    if not os.path.isdir(folder_path): return
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path): os.remove(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")

