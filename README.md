# Instagram Post Automation Script  

📸 Automate the process of posting your photos to Instagram using the **Google Drive API**, **Instagram API**, **ChatGPT**, and **GitHub Actions**.  

## Features  
- **Seamless Integration**: Monitors a Google Drive folder for new photos.  
- **Smart Caption Generation**: Uses ChatGPT to generate engaging captions for each photo.  
- **Automated Posting**: Posts photos directly to Instagram, complete with captions.  
- **Tracking System**: Maintains a record of already posted photos to avoid duplicates.  
- **Scheduled Execution**: Uses GitHub Actions to periodically run the script.  

---

## How It Works  
1. **Upload Photos**: After editing, upload your photos to a designated Google Drive folder.  
2. **Photo Check**: The script identifies photos that haven’t been posted yet, using a tracking file.  
3. **Processing**: New photos are downloaded, resized to Instagram’s media requirements, and prepped for posting.  
4. **Caption Creation**: ChatGPT generates captions to accompany the photos.  
5. **Posting**: The photos are automatically uploaded to Instagram, and the tracking file is updated.  
6. **Automation**: The entire process is scheduled using GitHub Actions to run at regular intervals.  

---

## Prerequisites  
1. **APIs**:  
   - Google Drive API (to access and download photos)  
   - Instagram API (to post photos)  
2. **Environment Setup**:  
   - Python 3.x  
   - Required libraries (listed in `requirements.txt`)  
3. **Credentials**:  
   - Google Cloud credentials for the Drive API  
   - Instagram App credentials  
4. **GitHub Actions**:  
   - A GitHub repository with the necessary workflow configured.  

---

## Setup Instructions  
1. Clone this repository:  
   ```bash  
   git clone https://github.com/ajktym94/KottayamStudio.git  
   cd KottayamStudio
   ```
2. Install dependencies:

   ```bash
   pip install -r requirements.txt  
   ```

3. Configure environment variables:
   - Add your Google Drive and Instagram API credentials.
   - Set up any additional configuration in a .env file.

4. Schedule the script using GitHub Actions:
   - Update the workflow.yml file to customize the schedule (default: once daily).

## Usage
- Manual Execution: Run the script locally with:
   ``` bash
   python main.py
   ``` 
- Automated Execution: The script will run automatically based on the GitHub Actions schedule.

## Customization
  - Caption Customization: Modify the caption generation logic by tweaking the ChatGPT prompt in the script.
  - Hashtag Management: Add or improve hashtags in the caption creation module.

## Future Enhancements
  - Adding location information to posts.
  - Smarter hashtag generation based on image content.
  - Enhanced logging and error handling.

## Contributions
Feel free to fork the repository, submit pull requests, or suggest new features in the Issues section!
