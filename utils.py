import os
import io
import json
import requests
import openai
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from apiclient.http import MediaFileUpload
from PIL import Image,ImageOps

access_token = os.environ.get("IG_API_TOKEN")
openai.api_key = os.environ.get("OPENAI_API")
instagram_account_id = os.environ.get("IG_ACC_ID")
google_drive_folder_id = os.environ.get("GDRIVE_FOLDER_ID")
credentials = os.environ.get('GDRIVE_CREDENTIALS')
token = os.environ.get('GDRIVE_TOKEN')
token_json = json.loads(token)
credentials_json = json.loads(credentials)



json_file_name = 'published_files.json'  # Replace with the JSON file name you want to load

# Authenticate and create the Drive API client
SCOPES = ['https://www.googleapis.com/auth/drive']

creds = None
# The file token.json stores the user's access and refresh tokens, and is created automatically when the authorization flow completes for the first time.
creds = Credentials.from_authorized_user_info(token_json)

# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_config(
            credentials_json, SCOPES
        )

        creds = flow.run_local_server(port=0)

service = build('drive', 'v3', credentials=creds)

def is_file_published(file_id, published_files):
    # Search for the file_id in the list of uploaded files
    for file_record in published_files["published_files"]:
        if file_record["file_id"] == file_id:
            return True  # File ID exists
    return False  # File ID not found

def find_file_in_folder(file_name, folder_id):
    """Checks if a specific file exists in a Google Drive folder."""
    query = f"'{folder_id}' in parents and name = '{file_name}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    return files[0] if files else None

def download_json_file(file_id):
    """Downloads a JSON file from Google Drive and loads it as a Python dictionary."""
    request = service.files().get_media(fileId=file_id)
    file_stream = io.BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()
    
    file_stream.seek(0)  # Move to the start of the file stream
    return json.load(file_stream)  # Load JSON data from the stream

def list_images_in_folder(folder_id):
    """Lists all files in a specific Google Drive folder without the .json extension."""
    query = f"'{folder_id}' in parents and trashed = false and not name contains '.json'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    return results.get('files', [])

def make_file_public_and_download(file_id, image_name):
    # Set the permissions for the file to public
    permission_body = {
        'role': 'reader',
        'type': 'anyone'
    }

    # Create permission
    service.permissions().create(
        fileId=file_id,
        body=permission_body
    ).execute()

    # Get the public URL
    public_url = f"https://drive.google.com/uc?id={file_id}"

    # This URL is for downloading files from Google Drive
    os.mkdir('tmp')
    file_path = os.path.join(os.getcwd(), 'tmp', image_name)

    print("Downloading image....")
    # Send a GET request
    response = requests.get(public_url, stream=True)

    # Check if the request was successful
    if response.status_code == 200:
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"Image downloaded: {file_path}")
        delete_file(file_id, image_name)
    else:
        print(f"Failed to retrieve image. Status code: {response.status_code}")

    return public_url

def delete_file(file_id, file_name):
    try:
        # Delete the file
        service.files().delete(fileId=file_id).execute()
        print(f"File {file_name} has been deleted.")
    except Exception as e:
        print(f"An error occurred: {e}")

def upload_json_to_drive(data, file_name, folder_id):
    """Uploads a JSON file to a specific Google Drive folder."""
    # os.mkdir('tmp')
    # Create a temporary JSON file
    temp_file_path = os.path.join(os.getcwd(), 'tmp', file_name)
    with open(temp_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    # Set up file metadata and upload
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(temp_file_path, mimetype='application/json')

    # Upload the file
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    print(f"File '{file_name}' uploaded successfully.")

def post_to_instagram(url, image_name):
    captions = ""
    if "DSC" in image_name:
        captions = " #KottayamStudio #ShotOnSony #SonyAlpha"
    else:
        captions = " #KottayamStudio #ShotOnOneplus7T #ShotOnOneplus #MobilePhotography"
    # Step 1: Upload the image
    upload_url = f'https://graph.instagram.com/v21.0/{instagram_account_id}/media'

    upload_payload = {
        'image_url': process_image(url, image_name),
        'caption': get_caption(url, image_name) + captions,
        'access_token': access_token
    }

    upload_response = requests.post(upload_url, data=upload_payload)
    upload_response_json = upload_response.json()
    # Check for errors
    if 'id' in upload_response_json:
        creation_id = upload_response_json['id']

        # Step 2: Publish the image
        publish_url = f'https://graph.instagram.com/v21.0/{instagram_account_id}/media_publish'
        publish_payload = {
            'creation_id': creation_id,
            'access_token': access_token
        }
        print("Posting image...")
        publish_response = requests.post(publish_url, data=publish_payload)
        print("Image posted successfully...")

        return True
    else:
        print("Error uploading image:", upload_response_json)

def process_image(image_url, image_name, downsize = False, expiration="1h"):
    url = "https://file.io"
    img_path = os.path.join(os.getcwd(), 'tmp', image_name)

    if downsize:
        with Image.open(img_path) as img:
            img = ImageOps.exif_transpose(img)
            img.thumbnail((1000, 1000))  # Resizes while keeping the aspect ratio
            img_path = img_path.replace('.', '_downsized.')
            img.save(img_path, format='JPEG')
    else:
        with Image.open(img_path) as img:
            img = ImageOps.exif_transpose(img)
            max_width = 1440
            aspect_ratio = img.width / img.height

            # Ensure the image meets the aspect ratio and resizing rules
            if aspect_ratio < 1:  # Portrait (taller than wide)
                new_height = int(max_width / aspect_ratio)
                new_size = (max_width, new_height)
            elif aspect_ratio > 1.91:  # Landscape (wider than allowed)
                new_height = int(max_width / 1.91)
                new_size = (max_width, new_height)
            else:  # Within accepted range
                new_size = (max_width, int(max_width / aspect_ratio))

            # Resize and save the image
            resized_image = img.resize(new_size, Image.LANCZOS)
            print("Image resized to ", new_size)
            img_path = img_path.replace('.', '_insta_size.')
            resized_image.save(img_path, format='JPEG')
            
            file_metadata = {'name': image_name,'parents': [google_drive_folder_id]}
    
            # Define the media file upload
            media = MediaFileUpload(img_path, mimetype='image/jpeg')
            
            # Upload the file
            uploaded_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            # Get the file ID
            file_id = uploaded_file.get('id')
            
            # Make the file public
            permission = {
                'type': 'anyone',
                'role': 'reader',
            }
            service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            
            # Generate the public URL
            public_url = f"https://drive.google.com/uc?id={file_id}"
            print(f"Public URL: {public_url}")
            
            return public_url


    with open(img_path, "rb") as file:
        files = {
            "file": file
        }
        data = {
            "expires": expiration
        }
        response = requests.post(url, files=files, data=data)
        if response.status_code == 200:
            return response.json()["link"]
        else:
            raise Exception(f"Failed to upload image: {response.json()}")

def get_caption(drive_url, image_name):
    host_url = process_image(drive_url, image_name, True)
    print("Generating caption for the image..")
    try:
        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Generate a catchy instagram caption for this image with standard hashtags for the image."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": host_url,
                            }
                        },
                    ],
                }
            ],
        )
        print("Caption generated...")
        return completion.choices[0].message.content[1:-1]
    except Exception as ex:
        print(ex)

def add_published_file_to_json(js, id, name):
    js['published_files'].append(
        {
            'file_id' : id,
            'file_name' : name
        }
    )

    return js