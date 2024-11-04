import os
import shutil
from utils import *

is_posted = False

# Find published_files.json in the folder, else create it
published_files = find_file_in_folder(json_file_name, google_drive_folder_id)

if published_files:
    published_files_json = download_json_file(published_files['id'])
    print("published_files.json loaded successfully.")
else:
    print(f"File '{json_file_name}' not found in the folder. Creating it.\n")
    published_files_json = {'published_files' : []}

images = list_images_in_folder(google_drive_folder_id)

for image in images:
    image_name = image['name']
    image_id = image['id']
    
    # Check if image has already been posted
    if not is_file_published(image_id, published_files_json):
        print(f"New image found: {image_name}. Retrieving its URL...\n")
        
        url = make_file_public_and_download(image_id, image_name)

        is_posted = post_to_instagram(url, image_name)

        published_files_json = add_published_file_to_json(published_files_json, image['id'], image_name)
        
        if published_files:
            delete_file(published_files['id'])

        upload_json_to_drive(published_files_json, json_file_name, google_drive_folder_id)
        
        shutil.rmtree('tmp')
        break

if not is_posted:
    print("No new images found. Existing images have all been already posted...")