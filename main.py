import os
import shutil
from utils import *

# Find published_files.json in the folder, else create it
published_files = find_file_in_folder(json_file_name, google_drive_folder_id)

if published_files:
    published_files_json = download_json_file(published_files['id'])
    print("JSON data loaded successfully:", published_files_json)
else:
    print(f"File '{json_file_name}' not found in the folder. Creating it.\n")
    published_files_json = {'published_files' : []}

images = list_images_in_folder(google_drive_folder_id)

for image in images:
    image_name = image['name']
    image_id = image['id']
    
    # Check if image has already been posted
    if not is_file_published(image_id, published_files_json):
        print(f"New file found: {image_name}. Retrieving its URL...\n")
        
        url = make_file_public(image_id)

        post_to_instagram(url)

        published_files_json = add_published_file_to_json(published_files_json, image['id'], image_name)
        
        if published_files:
            delete_file(published_files['id'])

        upload_json_to_drive(published_files_json, json_file_name, google_drive_folder_id)
        
        shutil.rmtree('tmp')
        break

<<<<<<< HEAD
=======
    print("No new images found. Existing images have all been already posted...")

>>>>>>> 1b948d8 (Modified print statement)



