# drive_helper.py
# This file contains all the functions for talking to Google Drive

from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

# ── 1. Connect to Google Drive ──────────────────────────────────────────────

def get_drive_service():
    """
    Log in to Google Drive using the service account key file.
    Returns a 'service' object we use to talk to Drive.
    """

    # Path to your downloaded JSON key file
    KEY_FILE = "hot-folder-transcription-c5a0d168400d.json"

    # This tells Google what permissions we need (read + write Drive files)
    SCOPES = ["https://www.googleapis.com/auth/drive"]

    # Load the credentials from the key file
    credentials = service_account.Credentials.from_service_account_file(
        KEY_FILE,
        scopes=SCOPES
    )

    # Build and return the Drive service object
    service = build("drive", "v3", credentials=credentials)
    return service


# ── 2. List Videos in a Folder ──────────────────────────────────────────────

def list_videos_in_folder(service, folder_id):
    """
    Look inside a Drive folder and return a list of video files.
    
    Parameters:
        service   : the Drive service object from get_drive_service()
        folder_id : the ID of the folder to look inside
    
    Returns:
        A list of dictionaries, each with 'id' and 'name' of a video file
    """

    # This filter tells Drive: give me files that are videos AND are in this folder
    query = f"'{folder_id}' in parents and mimeType contains 'video/' and trashed = false"

    # Call the Drive API to get the list of matching files
    results = service.files().list(
        q=query,
        fields="files(id, name)",  # we only need the file ID and name
        supportsAllDrives=True,         # ← add this
        includeItemsFromAllDrives=True  # ← and this
    ).execute()

    # Extract just the list of files from the response
    videos = results.get("files", [])  # if nothing found, return empty list

    return videos


# ── 3. Upload a Text File to Drive ──────────────────────────────────────────

def upload_txt_to_drive(service, folder_id, file_name, text_content):
    """
    Upload a .txt file directly to a Drive folder.
    
    Parameters:
        service      : the Drive service object
        folder_id    : where to upload the file
        file_name    : what to name the file (e.g. "transcript_video1.txt")
        text_content : the actual text to put inside the file
    """

    from googleapiclient.http import MediaInMemoryUpload

    # Metadata: the file name and which folder to put it in
    file_metadata = {
        "name": file_name,
        "parents": [folder_id]
    }

    # Convert the text string into bytes so Drive can upload it
    media = MediaInMemoryUpload(
        text_content.encode("utf-8"),  # convert text → bytes
        mimetype="text/plain"
    )

    # Upload the file to Drive
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id",
        supportsAllDrives=True
    ).execute()

    print(f"Uploaded: {file_name} (Drive ID: {uploaded_file.get('id')})")


# ── 4. Move a File to Another Folder ────────────────────────────────────────

def move_file_to_folder(service, file_id, new_folder_id, old_folder_id):
    """
    Move a file from one Drive folder to another.
    Google Drive doesn't have a true 'move' — instead we add the new
    parent folder and remove the old one.

    Parameters:
        service       : the Drive service object
        file_id       : the ID of the file to move
        new_folder_id : the folder to move it INTO
        old_folder_id : the folder to move it OUT OF
    """

    updated_file = service.files().update(
        fileId=file_id,
        addParents=new_folder_id,
        removeParents=old_folder_id,
        fields="id, parents",
        supportsAllDrives=True   # needed since processed_videos may live in a Shared Drive context
    ).execute()

    print(f"Moved file {file_id} to processed_videos folder.")
    return updated_file