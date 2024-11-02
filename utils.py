import os
import time
import io
import json
import requests
import openai
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from apiclient.http import MediaFileUpload

google_drive_folder_id = os.environ.get("GDRIVE_FOLDER_ID")
access_token = os.environ.get("IG_API_TOKEN")
instagram_account_id = os.environ.get("IG_ACC_ID")
openai.api_key = os.environ.get("OPENAI_API")

json_file_name = 'published_files.json'  # Replace with the JSON file name you want to load

credentials = os.environ.get('GDRIVE_CREDENTIALS')
token = os.environ.get('GDRIVE_TOKEN')
token_json = json.loads(token)
credentials_json = json.loads(credentials)

# Authenticate and create the Drive API client
SCOPES = ['https://www.googleapis.com/auth/drive']

creds = None
# The file token.json stores the user's access and refresh tokens, and is created automatically when the authorization flow completes for the first time.
creds = Credentials.from_authorized_user_info(token_json)
# if os.path.exists("token.json"):
#     creds = Credentials.from_authorized_user_file("token.json", SCOPES)

def set_heroku_env_variable(app_name, key, value):
    try:
        # Construct the command to set the environment variable
        command = f"heroku config:set {key}='{value}' --app {app_name}"
        print(value)
        # Execute the command
        subprocess.run(command, shell=True, check=True)
        print(f"Environment variable {key} set for app {app_name}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to set environment variable: {e}")

# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_config(
            credentials_json, SCOPES
        )
        # flow = InstalledAppFlow.from_client_secrets_file(
        #     "credentials.json", SCOPES
        # )
        creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    set_heroku_env_variable('kottayamstudio', 'GDRIVE_TOKEN', creds.to_json())
    # with open("token.json", "w") as token:
    #     token.write(creds.to_json())

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
    print(files)
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

def make_file_public(file_id):
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
    return public_url

def download_image(file_id, file_name):
    """Downloads a file from Google Drive to the ./tmp directory."""
    request = service.files().get_media(fileId=file_id)
    os.mkdir('tmp')
    file_path = os.path.join(os.getcwd(), 'tmp', file_name)
    with io.FileIO(file_path, 'wb') as file:
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Downloading {file_name}: {int(status.progress() * 100)}%.")

def delete_file(file_id):
    try:
        # Delete the file
        service.files().delete(fileId=file_id).execute()
        print(f"File with ID {file_id} has been deleted.")
    except Exception as e:
        print(f"An error occurred: {e}")

def upload_json_to_drive(data, file_name, folder_id):
    """Uploads a JSON file to a specific Google Drive folder."""
    os.mkdir('tmp')
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

    print(f"File '{file_name}' uploaded successfully with file ID: {file.get('id')}")

def post_to_instagram(url):
    # Step 1: Upload the image
    upload_url = f'https://graph.instagram.com/v21.0/{instagram_account_id}/media'

    upload_payload = {
        'image_url': url,
        'caption': get_caption(url),
        'access_token': access_token
    }

    upload_response = requests.post(upload_url, data=upload_payload)
    upload_response_json = upload_response.json()
    print(upload_response_json)
    # Check for errors
    if 'id' in upload_response_json:
        creation_id = upload_response_json['id']

        # Step 2: Publish the image
        publish_url = f'https://graph.instagram.com/v21.0/{instagram_account_id}/media_publish'
        publish_payload = {
            'creation_id': creation_id,
            'access_token': access_token
        }

        publish_response = requests.post(publish_url, data=publish_payload)
        print(publish_response)
    else:
        print("Error uploading image:", upload_response_json)

def get_caption(url):
    url = "https://drive.usercontent.google.com/download?id={}&authuser=0".format(url.split('=')[-1])
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
                                "url": url,
                            }
                        },
                    ],
                }
            ],
        )
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


