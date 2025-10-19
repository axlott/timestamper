"""
Generate a text file and JSON report of all EXIF metadata for images and videos in a folder.
"""
import os
import piexif
import json
import cv2
from PIL import Image
import pillow_heif
from meta_reader import get_creation_date
from get_addr import get_addr

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
    Generates a text and JSON report of metadata from original source files.
    """
    print("\n--- Starting Metadata Report Generation ---")
    report_path_json = os.path.join(output_folder, "metadata_report.json")
    all_media_data = {}

    supported_media = ('.png', '.jpg', '.jpeg', '.heic', '.mov', '.mp4')

    for filename in os.listdir(source_folder):
        if not filename.lower().endswith(supported_media):
            continue

        file_path = os.path.join(source_folder, filename)
        is_video = filename.lower().endswith(('.mov', '.mp4'))
        
        try:
            timestamp = get_creation_date(file_path) or "NULL"
            
            # --- Initialize base data for all media types ---
            data = {
                "OriginalFileName": filename,
                "Timestamp": timestamp,
                "People": "NULL"
            }

            if is_video:
                cap = cv2.VideoCapture(file_path) # pylint: disable=no-member
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) # pylint: disable=no-member
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) # pylint: disable=no-member
                cap.release()
                
                # For videos, many fields are not applicable
                data.update({
                    "Dimensions": f"{width}x{height}",
                    "Location_Address": "N/A", "GPS_Location": "N/A",
                    "DeviceMake": "N/A", "DeviceModel": "N/A",
                    "FocalLength": "N/A", "Aperture": "N/A",
                    "ShutterSpeed": "N/A", "ISO": "N/A",
                    "Flash": "N/A", "Comments": "N/A"
                })
                processed_filename = os.path.splitext(filename)[0] + ".mp4"

            else:  # It's an image, so we do the full, detailed extraction
                exif_dict = {}
                img_obj = None
                
                if filename.lower().endswith('.heic'):
                    heif_file = pillow_heif.read_heif(file_path)
                    img_obj = heif_file
                    if 'exif' in heif_file.info and heif_file.info['exif']:
                        exif_dict = piexif.load(heif_file.info['exif'])
                else:
                    img_obj = Image.open(file_path)
                    if 'exif' in img_obj.info and img_obj.info['exif']:
                        exif_dict = piexif.load(img_obj.info['exif'])

                def get_exif(ifd, tag, default="NULL"):
                    try:
                        val = exif_dict[ifd][tag]
                        if isinstance(val, tuple):
                            if tag in [piexif.ExifIFD.UserComment, piexif.ImageIFD.XPComment]:
                                return bytes(val).decode('utf-16-le', 'ignore').strip('\x00')
                            return val
                        if isinstance(val, bytes):
                            if tag == piexif.ExifIFD.UserComment:
                                if val.startswith(b'UNICODE\x00'): return val[8:].decode('utf-16-le', 'ignore').strip('\x00')
                                if val.startswith(b'ASCII\x00\x00\x00'): return val[8:].decode('ascii', 'ignore').strip('\x00')
                            if tag == piexif.ImageIFD.XPComment: return val.decode('utf-16-le', 'ignore').strip('\x00')
                            return val.decode('utf-8', 'ignore').strip('\x00')
                        return val
                    except (KeyError, IndexError, TypeError):
                        return default

                if filename.lower().endswith('.heic'):
                    width, height = img_obj.size
                else:
                    width, height = img_obj.width, img_obj.height

                data['Dimensions'] = f"{width}x{height}"
                data['DeviceMake'] = get_exif('0th', piexif.ImageIFD.Make)
                data['DeviceModel'] = get_exif('0th', piexif.ImageIFD.Model)
                
                focal_length_raw = get_exif('Exif', piexif.ExifIFD.FocalLength, (0, 1))
                data['FocalLength'] = f"{int(focal_length_raw[0] / focal_length_raw[1])}mm" if focal_length_raw[1] > 0 else "NULL"
                
                aperture_raw = get_exif('Exif', piexif.ExifIFD.FNumber, (0, 1))
                data['Aperture'] = f"f/{aperture_raw[0] / aperture_raw[1]:.1f}" if aperture_raw[1] > 0 else "NULL"
                
                shutter_raw = get_exif('Exif', piexif.ExifIFD.ExposureTime, (0, 1))
                data['ShutterSpeed'] = f"1/{int(shutter_raw[1] / shutter_raw[0])}s" if shutter_raw[0] > 0 else "NULL"
                
                data['ISO'] = get_exif('Exif', piexif.ExifIFD.ISOSpeedRatings, "NULL")
                data['Flash'] = "Flash Fired" if get_exif('Exif', piexif.ExifIFD.Flash, 0) & 1 else "No Flash"

                comment_tags_to_check = [('Exif', piexif.ExifIFD.UserComment), ('0th', piexif.ImageIFD.ImageDescription), ('0th', piexif.ImageIFD.XPComment)]
                comments = "NULL"
                for ifd, tag in comment_tags_to_check:
                    found_comment = get_exif(ifd, tag)
                    if found_comment and found_comment != "NULL":
                        comments = found_comment
                        break
                data['Comments'] = comments

                gps_lat_dms = exif_dict.get('GPS', {}).get(piexif.GPSIFD.GPSLatitude)
                gps_lon_dms = exif_dict.get('GPS', {}).get(piexif.GPSIFD.GPSLongitude)
                if gps_lat_dms and gps_lon_dms:
                    gps_lat_ref = exif_dict.get('GPS', {}).get(piexif.GPSIFD.GPSLatitudeRef, b'N').decode()
                    gps_lon_ref = exif_dict.get('GPS', {}).get(piexif.GPSIFD.GPSLongitudeRef, b'E').decode()
                    lat_dd = dms_to_dd(gps_lat_dms, gps_lat_ref)
                    lon_dd = dms_to_dd(gps_lon_dms, gps_lon_ref)
                    data['GPS_Location'] = f"{lat_dd:.4f}, {lon_dd:.4f}"
                    try:
                        data['Location_Address'] = get_addr(lat_dd, lon_dd)
                    except Exception as geo_e:
                        data['Location_Address'] = f"Geocoding failed: {geo_e}"
                else:
                    data['GPS_Location'] = "NULL"
                    data['Location_Address'] = "NULL"

                processed_filename = os.path.splitext(filename)[0] + ".png"

            all_media_data[processed_filename] = data
            print(f"Processed metadata for: {filename}")

        except Exception as e:
            print(f"Could not process metadata for {filename}: {e}")

    with open(report_path_json, "w", encoding="utf-8") as f:
        json.dump(all_media_data, f, indent=4)
    print(f"\nJSON report successfully generated at: {report_path_json}")

