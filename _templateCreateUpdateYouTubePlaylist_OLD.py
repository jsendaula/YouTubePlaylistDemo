"""
YouTube Playlist Creator / Updater
----------------------------------

This script authenticates with YouTube using OAuth 2.0, checks if a playlist with the given name
already exists on the user's channel, and either updates it or creates a new one.
It also removes duplicate videos (both from the input list and the playlist).

Author: Jason + ChatGPT
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import re

SCOPES = ["https://www.googleapis.com/auth/youtube"]

def authenticate_youtube():
    """Authenticate user via OAuth and return authorized API client."""
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=creds)

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

def get_or_create_playlist(youtube, title, description, privacy="public"):
    """Return the playlist ID if it exists, or create a new playlist."""
    request = youtube.playlists().list(
        part="snippet,contentDetails",
        mine=True,
        maxResults=50
    )
    response = request.execute()

    for playlist in response.get("items", []):
        if playlist["snippet"]["title"].lower() == title.lower():
            print(f"🔁 Playlist '{title}' already exists.")
            return playlist["id"]

    # Create if not found
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {"title": title, "description": description},
            "status": {"privacyStatus": privacy},
        },
    )
    response = request.execute()
    print(f"✅ Created new playlist: {title}")
    return response["id"]

def get_existing_videos(youtube, playlist_id):
    """Return a set of video IDs already in the playlist."""
    existing_videos = set()
    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token,
        )
        response = request.execute()

        for item in response.get("items", []):
            existing_videos.add(item["contentDetails"]["videoId"])

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return existing_videos

def add_video_to_playlist(youtube, playlist_id, video_id):
    """Add a video to the playlist."""
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
    print(f"🎵 Added video: {video_id}")

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
    """Add videos safely, avoiding duplicates in both input and playlist."""
    # Step 1: Clean duplicates from input
    video_links = deduplicate_links(video_links)

    # Step 2: Check existing playlist videos
    existing_videos = get_existing_videos(youtube, playlist_id)
    print(f"🎞️ Playlist already contains {len(existing_videos)} videos.")

    added_count = 0
    skipped_count = 0

    for link in video_links:
        video_id = extract_video_id(link)
        if not video_id:
            continue
        if video_id in existing_videos:
            print(f"⏩ Skipped existing video: {video_id}")
            skipped_count += 1
            continue
        add_video_to_playlist(youtube, playlist_id, video_id)
        added_count += 1

    print(f"\n✅ Done! Added {added_count} new videos, skipped {skipped_count} duplicates.")

def main():
    youtube = authenticate_youtube()

    # Customize these
    title = "My YouTube Playlist"
    description = "A playlist managed automatically with Python!"
    privacy = "unlisted"

    # Example video list (can be URLs or IDs)
    video_links = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/3JZ_D3ELwOQ",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # duplicate
    ]

    playlist_id = get_or_create_playlist(youtube, title, description, privacy)
    add_videos_no_duplicates(youtube, playlist_id, video_links)

if __name__ == "__main__":
    main()
