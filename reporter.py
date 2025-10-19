"""
Generate a text file and JSON report of all EXIF metadata for images in a folder.
Supports HEIC, PNG, and JPG files. Uses geopy to convert GPS coordinates to human-readable addresses.
"""

import os
import piexif
import json
from PIL import Image
import pillow_heif
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from meta_reader import get_creation_date

def dms_to_dd(dms, ref):
    """Converts GPS DMS (degrees, minutes, seconds) to DD (decimal degrees)"""
    degrees = dms[0][0] / dms[0][1]
    minutes = dms[1][0] / dms[1][1] / 60.0
    seconds = dms[2][0] / dms[2][1] / 3600.0
    dd = degrees + minutes + seconds
    if ref in ['S', 'W']:
        dd *= -1
    return dd


def generate_metadata_report(source_folder, output_folder):
    """
    Generates a text and JSON report of EXIF metadata from original source images.
    """
    print("\n--- Starting Metadata Report Generation ---")
    report_path_txt = os.path.join(output_folder, "metadata_report.txt")
    report_path_json = os.path.join(output_folder, "metadata_report.json")
    
    geolocator = Nominatim(user_agent="photo_metadata_extractor")
    geocode = RateLimiter(geolocator.reverse, min_delay_seconds=1)

    all_photo_data = {}

    for filename in os.listdir(source_folder):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.heic')):
            continue

        file_path = os.path.join(source_folder, filename)
        try:
            exif_dict = {}
            img_obj = None # Will hold either a Pillow or heif object
            
            if filename.lower().endswith('.heic'):
                heif_file = pillow_heif.read_heif(file_path)
                img_obj = heif_file
                if 'exif' in heif_file.info and heif_file.info['exif']:
                    exif_dict = piexif.load(heif_file.info['exif'])
            else: # JPG, PNG, etc.
                img_obj = Image.open(file_path)
                if 'exif' in img_obj.info and img_obj.info['exif']:
                    exif_dict = piexif.load(img_obj.info['exif'])

            def get_exif(ifd, tag, default="NULL"):
                """
                Safely extracts and decodes EXIF data from various formats.
                """
                try:
                    val = exif_dict[ifd][tag]

                    # Case 1: Value is a tuple of integers
                    if isinstance(val, tuple):
                        # ONLY apply special decoding for known comment tags that use this format
                        if tag in [piexif.ExifIFD.UserComment, piexif.ImageIFD.XPComment]:
                            try:
                                # Convert tuple of ints to bytes and decode as UTF-16 LE
                                return bytes(val).decode('utf-16-le', 'ignore').strip('\x00')
                            except Exception:
                                return default # Fallback if decoding fails
                        # Otherwise, it's a numerical tuple (like Aperture), return it directly
                        return val

                    # Case 2: Value is a byte string
                    if isinstance(val, bytes):
                        # Handle specific known tags with special encoding
                        if tag == piexif.ExifIFD.UserComment:
                            if val.startswith(b'UNICODE\x00'):
                                return val[8:].decode('utf-16-le', 'ignore').strip('\x00')
                            if val.startswith(b'ASCII\x00\x00\x00'):
                                return val[8:].decode('ascii', 'ignore').strip('\x00')
                            return val.decode('utf-8', 'ignore').strip('\x00')
                        
                        if tag == piexif.ImageIFD.XPComment:
                            return val.decode('utf-16-le', 'ignore').strip('\x00')

                        # Generic fallback for other byte strings
                        return val.decode('utf-8', 'ignore').strip('\x00')

                    # Case 3: Value is already a string or number, return it as is
                    return val

                except (KeyError, IndexError, TypeError):
                    return default
            
            # --- Get Dimensions Safely ---
            if filename.lower().endswith('.heic'):
                width, height = img_obj.size
            else:
                width, height = img_obj.width, img_obj.height

            # --- Extract All Metadata Fields ---
            timestamp = get_creation_date(file_path) or "NULL"
            device_make = get_exif('0th', piexif.ImageIFD.Make)
            device_model = get_exif('0th', piexif.ImageIFD.Model)
            dimensions = f"{width}x{height}"
            
            focal_length_raw = get_exif('Exif', piexif.ExifIFD.FocalLength, (0,1))
            focal_length = f"{int(focal_length_raw[0] / focal_length_raw[1])}mm" if focal_length_raw[1] > 0 else "NULL"
            
            aperture_raw = get_exif('Exif', piexif.ExifIFD.FNumber, (0,1))
            aperture = f"f/{aperture_raw[0] / aperture_raw[1]:.1f}" if aperture_raw[1] > 0 else "NULL"
            
            shutter_raw = get_exif('Exif', piexif.ExifIFD.ExposureTime, (0,1))
            shutter = f"1/{int(shutter_raw[1] / shutter_raw[0])}s" if shutter_raw[0] > 0 else "NULL"
            
            iso = get_exif('Exif', piexif.ExifIFD.ISOSpeedRatings, "NULL")
            flash = "Flash Fired" if get_exif('Exif', piexif.ExifIFD.Flash, 0) & 1 else "No Flash"

            # --- Robust Comment Extraction ---
            # Define all possible comment tags in order of preference.
            comment_tags_to_check = [
                ('Exif', piexif.ExifIFD.UserComment),
                ('0th', piexif.ImageIFD.ImageDescription),
                ('0th', piexif.ImageIFD.XPComment)
            ]

            comments = "NULL"
            for ifd, tag in comment_tags_to_check:
                found_comment = get_exif(ifd, tag)
                # Check if the found comment is a non-empty, meaningful string
                if found_comment and found_comment != "NULL":
                    comments = found_comment
                    break # Stop as soon as we find the first valid comment

            gps_lat_dms = exif_dict.get('GPS', {}).get(piexif.GPSIFD.GPSLatitude)
            gps_lon_dms = exif_dict.get('GPS', {}).get(piexif.GPSIFD.GPSLongitude)
            gps_lat_ref = exif_dict.get('GPS', {}).get(piexif.GPSIFD.GPSLatitudeRef, b'N').decode()
            gps_lon_ref = exif_dict.get('GPS', {}).get(piexif.GPSIFD.GPSLongitudeRef, b'E').decode()

            location_address = "NULL"
            gps_location = "NULL"
            if gps_lat_dms and gps_lon_dms:
                lat_dd = dms_to_dd(gps_lat_dms, gps_lat_ref)
                lon_dd = dms_to_dd(gps_lon_dms, gps_lon_ref)
                gps_location = f"{lat_dd:.4f}, {lon_dd:.4f}"
                try:
                    location = geocode((lat_dd, lon_dd), language='en')
                    location_address = location.address if location else "Address not found"
                except Exception as geo_e:
                    location_address = f"Geocoding failed: {geo_e}"
            
            processed_filename = os.path.splitext(filename)[0] + ".png"
            all_photo_data[processed_filename] = {
                "OriginalFileName": filename,
                "Timestamp": timestamp, "People": "NULL",
                "Location_Address": location_address, "GPS_Location": gps_location,
                "DeviceMake": device_make, "DeviceModel": device_model,
                "Dimensions": dimensions, "FocalLength": focal_length,
                "Aperture": aperture, "ShutterSpeed": shutter, "ISO": iso, "Flash": flash,
                "Comments": comments
            }
            print(f"Processed metadata for: {filename}")

        except Exception as e:
            print(f"Could not process metadata for {filename}: {e}")

    # --- Write JSON Report ---
    with open(report_path_json, "w", encoding="utf-8") as f:
        json.dump(all_photo_data, f, indent=4)
    print(f"\nJSON report successfully generated at: {report_path_json}")

    # --- Write Text Report ---
    with open(report_path_txt, "w", encoding="utf-8") as report:
        for processed_filename, data in all_photo_data.items():
            report.write(f"========================================\n")
            report.write(f"FileName: {processed_filename} (Original: {data['OriginalFileName']})\n")
            report.write(f"----------------------------------------\n")
            for key, value in data.items():
                if key not in ["OriginalFileName"]: # Don't print this twice
                    report.write(f"{key}: {value}\n")
            report.write(f"========================================\n\n")

    print(f"Text report successfully generated at: {report_path_txt}")

