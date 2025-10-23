"""
YouTube Playlist Creator / Updater
----------------------------------

This script authenticates with YouTube using OAuth 2.0, checks if a playlist with the given name
already exists on the user's channel, and either updates it or creates a new one.
It also removes duplicate videos (both from the input list and the playlist)
and gracefully handles deleted/unavailable videos or playlists.

Author: Jason + ChatGPT
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
import time

SCOPES = ["https://www.googleapis.com/auth/youtube"]

def authenticate_youtube():
    """Authenticate user via OAuth and return authorized API client."""
    try:
        flow = InstalledAppFlow.from_client_secrets_file("-------.json", SCOPES)
        creds = flow.run_local_server(port=0)
        return build("youtube", "v3", credentials=creds)
    except FileNotFoundError:
        print("❌ Error: client_secret.json not found. Please add your OAuth credentials file.")
        exit(1)
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        exit(1)


# ---------------- Playlist Helpers ---------------- # from old code
def find_playlist_by_title(youtube, title):
    """Return the playlist ID if a playlist with the given title exists."""
    next_page_token = None
    while True:
        request = youtube.playlists().list(
            part="snippet,contentDetails",
            mine=True,
            maxResults=50,
            pageToken=next_page_token,
        )
        response = request.execute()

        for playlist in response.get("items", []):
            if playlist["snippet"]["title"].lower() == title.lower():
                print(f"✅ Found existing playlist: {title}")
                print(f"🔗 URL: https://www.youtube.com/playlist?list={playlist['id']}")
                return playlist["id"]

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    print(f"ℹ️ No existing playlist found with title: {title}")
    return None

def create_playlist(youtube, title, description, privacy="public"):
    """Create a YouTube playlist."""
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {"title": title, "description": description},
            "status": {"privacyStatus": privacy},
        },
    )
    response = request.execute()
    playlist_id = response["id"]
    print(f"✅ Playlist created: {title}")
    print(f"🔗 URL: https://www.youtube.com/playlist?list={playlist_id}")
    return playlist_id


# def get_or_create_playlist(youtube, title, description, privacy="public"):
#     """Return the playlist ID if it exists, or create a new playlist."""
#     try:
#         request = youtube.playlists().list(
#             part="snippet,contentDetails",
#             mine=True,
#             maxResults=50
#         )
#         time.sleep(10)
#         response = request.execute()
#     except HttpError as e:
#         print(f"❌ Failed to fetch playlists: {e}")
#         exit(1)
#
#     for playlist in response.get("items", []):
#         if playlist["snippet"]["title"].lower() == title.lower():
#             print(f"🔁 Playlist '{title}' already exists.")
#             return playlist["id"]
#
#     # Create new playlist if not found
#     try:
#         request = youtube.playlists().insert(
#             part="snippet,status",
#             body={
#                 "snippet": {"title": title, "description": description},
#                 "status": {"privacyStatus": privacy},
#             },
#         )
#         response = request.execute()
#         print(f"✅ Created new playlist: {title}")
#         return response["id"]
#         time.sleep(10)
#     except HttpError as e:
#         print(f"❌ Error creating playlist: {e}")
#         exit(1)

# ---------------- Video Helpers ---------------- #

def extract_video_id(url_or_id):
    """Extract YouTube video ID from URL or return it directly."""
    pattern = r"(?:v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url_or_id)
    if match:
        return match.group(1)
    elif len(url_or_id) == 11:
        return url_or_id
    else:
        print(f"⚠️ Invalid YouTube link or ID: {url_or_id}")
        return None



def get_existing_videos(youtube, playlist_id):
    """Return a set of video IDs already in the playlist."""
    existing_videos = set()
    next_page_token = None
    time.sleep(2)

    while True:
        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token,
        )
        response = request.execute()

        for item in response.get("items", []):
            video_id = item["contentDetails"]["videoId"]
            existing_videos.add(video_id)

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return existing_videos

def check_video_exists(youtube, video_id):
    """Check if a video is available (not deleted or private)."""
    try:
        request = youtube.videos().list(part="status", id=video_id)
        response = request.execute()

        if not response.get("items"):
            print(f"🗑️ Skipping deleted/unavailable video: {video_id}")
            return False

        status = response["items"][0]["status"]
        if status.get("privacyStatus") in ["private"]:
            print(f"🔒 Skipping private video: {video_id}")
            return False
        return True
    except HttpError as e:
        if e.resp.status == 404:
            print(f"🗑️ Video not found: {video_id}")
        else:
            print(f"⚠️ Error checking video {video_id}: {e}")
        return False

def add_video_to_playlist(youtube, playlist_id, video_id):
    """Add a video to the playlist with retry logic."""
    try:
        request = youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id},
                }
            },
        )
        request.execute()
        # time.sleep(4)
        print(f"🎵 Added video: {video_id}")
    except HttpError as e:
        if e.resp.status in [403, 404]:
            print(f"🗑️ Could not add video {video_id}: it may be deleted or restricted.")
        else:
            print(f"⚠️ Error adding video {video_id}: {e}")
            time.sleep(2)  # retry delay

# ---------------- Duplicate Handling ---------------- #

def deduplicate_links(video_links):
    """Remove duplicates from the local list."""
    seen = set()
    unique_links = []
    for link in video_links:
        vid = extract_video_id(link)
        if vid and vid not in seen:
            seen.add(vid)
            unique_links.append(link)
        else:
            print(f"🗑️ Removed duplicate from input list: {link}")
    return unique_links

def add_videos_no_duplicates(youtube, playlist_id, video_links):
    """Add videos safely, avoiding duplicates and handling deleted/private videos."""
    # Step 1: Remove duplicates from local list
    video_links = deduplicate_links(video_links)

    # Step 2: Get existing playlist videos
    existing_videos = get_existing_videos(youtube, playlist_id)
    print(f"🎞️ Playlist already contains {len(existing_videos)} videos.")

    added_count = 0
    skipped_count = 0

    for link in video_links:
        video_id = extract_video_id(link)
        if not video_id:
            continue

        # Check availability
        if not check_video_exists(youtube, video_id):
            skipped_count += 1
            continue

        if video_id in existing_videos:
            print(f"⏩ Skipped existing video: {video_id}")
            skipped_count += 1
            continue

        add_video_to_playlist(youtube, playlist_id, video_id)
        added_count += 1

    print(f"\n✅ Done! Added {added_count} new videos, skipped {skipped_count} duplicates or unavailable.")

def main():
    youtube = authenticate_youtube()

    # ---- Playlist details ----
    title = "Comcast Business 009"
    description = "A playlist managed automatically with Python!"
    privacy = "private"

    # ---- Video list ----
    video_links = [
        ############################################################################### 2025xxxx
        # "https://www.youtube.com/watch?v=jjs0khcuCLY&list=WL&index=150&pp=gAQBiAQB",
        "EanwSh4LD5E",
        "xZEL3Pi4uYE",
        "XFxhvkOLw", # --- invalid link
        "slJeUiybFQA",
        "IUUHt8RINLY",
        # "Lp7_eTESC0Y",
        # "00rG4E1e1Qg",
        # "8es1FC8_wVE",
        # "dhJlDF9Hl28",
        # "W1lire7n1w0",
        # "S9QmMvgF0TI",
        # "FP5cHqkGxWU",
        # "jzGR0OuAYYQ",
        # "9gMdiYRhaf4",
        # "6YM0vEmgCyI",
        # "Smr_8Czc7MI",
        # "dyP-eFDNTRo",
        "https://www.youtube.com/watch?v=sFVVlzc1-HA&list=WL&index=165&pp=gAQBiAQB", # -- error causing line, account deleted --
        # "5tQ9ySeDdMA",
        # "7C2dw1cWZVU",
        # "LBnLA4qvE_0",
        # "fdflYG5mAhQ",
        # "D4fZoplu8Cg",
        # "H9b8H-B8V-w",
        # "OA93bn3eUsI",
        "F44zfIpmqLU",
        "F44zfIpmqLU",  # ---Duplicate line
    ]

    # Step 1: Check if playlist already exists ----- NEW
    playlist_id = find_playlist_by_title(youtube, title)

    # Step 2: Create it if it doesn’t exist ----- pre-existing
    if not playlist_id:
        playlist_id = create_playlist(youtube, title, description, privacy)

    # Step 3: Add videos (skip duplicates) ----- pre-existing
    add_videos_no_duplicates(youtube, playlist_id, video_links)

if __name__ == "__main__":
    main()
