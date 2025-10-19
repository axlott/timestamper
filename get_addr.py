"""
Function to get address.
"""

from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

def get_addr(lat_dd, lon_dd):
    geolocator = Nominatim(user_agent="photo_metadata_extractor")
    geocode = RateLimiter(geolocator.reverse, min_delay_seconds=1)
    location = geocode((lat_dd, lon_dd), language='en')
    addr = location.address if location else "Address not found"
    return addr

if __name__ == "__main__":
    # # Step 1: Timestamp all images. This function creates the output
    # # folder and returns its path.
    # output_folder = process_folder_for_timestamping(SOURCE_IMAGE_FOLDER)
    
    # # # Step 2: Generate the metadata report. We read from the SOURCE folder
    # # # to get original, unaltered metadata and save the report to the OUTPUT folder.
    # # if output_folder:
    # generate_metadata_report(SOURCE_IMAGE_FOLDER, OUTPUT_FOLDER_NAME)
        
    # print("\nAll tasks complete.")
    lat_dd, lon_dd = -34.5530, -58.4676
    print(lat_dd, lon_dd)
    print(get_addr(lat_dd, lon_dd))