import requests
import json
import schedule
import time
import yaml

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Replace with your own values
access_token = 'das'#config['api_credentials']['api_token']
instagram_account_id = 'das'#config['api_credentials']['account_id']
image_url = 'https://testdriven.io/static/images/blog/oauth-python/web_auth_flow.png'
caption = 'Your caption here'

def post_to_instagram():
    # Step 1: Upload the image
    upload_url = f'https://graph.instagram.com/v21.0/{instagram_account_id}/media'

    # Specify the local file path
    local_file_path = 'sample.jpg'  # Replace with your actual file path

    # Prepare the files dictionary
    files = {'file': open(local_file_path, 'rb')}

    upload_payload = {
        'image_url': image_url,
        'caption': caption,
        'access_token': access_token
    }

    upload_response = requests.post(upload_url, files=files, data=upload_payload)
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

        publish_response = requests.post(publish_url, data=publish_payload)
        print(publish_response.json())
    else:
        print("Error uploading image:", upload_response_json)

post_to_instagram()
#     # Schedule your job (e.g., every day at 10:00 AM)
# schedule.every().day.at("10:00").do(post_to_instagram)

# while True:
#     schedule.run_pending()
#     time.sleep(1)




