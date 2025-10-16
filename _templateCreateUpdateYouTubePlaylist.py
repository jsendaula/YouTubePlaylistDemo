import time

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import re

# YouTube Data API scope
SCOPES = ["https://www.googleapis.com/auth/youtube"]

def authenticate_youtube():
    """Authenticate and return an authorized YouTube API client."""
    flow = InstalledAppFlow.from_client_secrets_file("client_secret_897398147357-i5hdois41qobv01lmfhgg14suh02s9fg.apps.googleusercontent.com.json", SCOPES)
    creds = flow.run_local_server(port=0)
    youtube = build("youtube", "v3", credentials=creds)
    return youtube

# ---------------- Playlist Helpers ---------------- #

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

# ---------------- Video Helpers ---------------- #

def extract_video_id(url_or_id):
    """Extract video ID from YouTube URL or return ID directly."""
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

def add_video_to_playlist(youtube, playlist_id, video_id):
    """Add a single video to the playlist."""
    request = youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        }
    )
    """old code"""
    # response = request.execute()
    """new code"""
    request.execute()
    time.sleep(2)
    print(f"🎵 Added video: {video_id}")

# ---------------- Duplicate Handling ---------------- #

def deduplicate_links(video_links):
    """Remove duplicates within the provided list itself."""
    seen = set()
    unique_links = []
    removed_links = []

    for link in video_links:
        vid = extract_video_id(link)
        if vid and vid not in seen:
            seen.add(vid)
            unique_links.append(link)
        else:
            removed_links.append(link)

    print(f"\n🧹 Duplicate Check (Input List):")
    if removed_links:
        print(f"❌ Removed {len(removed_links)} duplicate(s):")
        for dup in removed_links:
            print(f"   ⏩ {dup}")
    else:
        print("✅ No duplicates found in input list.")
    print()
    return unique_links

def add_videos_no_duplicates(youtube, playlist_id, video_links):
    """Add videos to a playlist, avoiding duplicates locally and on YouTube."""
    # Step 1: Remove duplicates from video_links list
    video_links = deduplicate_links(video_links)
    print(f"📋 After cleanup, {len(video_links)} unique videos to process.")

    # Step 2: Skip videos already in the playlist
    existing_videos = get_existing_videos(youtube, playlist_id)
    print(f"🎞️ Found {len(existing_videos)} existing videos in playlist.")

    added_count = 0
    skipped_count = 0

    for link in video_links:
        video_id = extract_video_id(link.strip())
        if not video_id:
            continue
        if video_id in existing_videos:
            print(f"⏩ Skipped duplicate: {video_id}")
            skipped_count += 1
            continue
        add_video_to_playlist(youtube, playlist_id, video_id)
        added_count += 1

    """old code"""
    # print(f"\n✅ Done! Added {added_count} new videos, skipped {skipped_count} duplicates.")
    """NEW code"""
    print(f"\n✅ Summary:")
    print(f"   ➕ Added {added_count} new videos")
    print(f"   🚫 Skipped {skipped_count} duplicates (already in playlist)")

# ---------------- Main Program ---------------- #

if __name__ == "__main__":
    youtube = authenticate_youtube()

    # ---- Playlist details ----
    title = "Air Demo Update 002"
    description = "Automatically managed playlist via Python created with the assistance of ChatGPT."
    privacy = "private"

    # ---- Video list ----
    video_links = [
        ############################################################################### 2025xxxx
        "https://www.youtube.com/watch?v=h8htSF9X5sE&list=PLq9NE85nTBB0TCs7o8MMweQrrMONAA_IA&index=1&pp=gAQBiAQB8AUB",
        "https://www.youtube.com/watch?v=j7MU2PMC160&list=PLq9NE85nTBB0TCs7o8MMweQrrMONAA_IA&index=2&pp=gAQBiAQB8AUB",
        "https://www.youtube.com/watch?v=j7MU2PMC160&list=PLq9NE85nTBB0TCs7o8MMweQrrMONAA_IA&index=2&pp=gAQBiAQB8AUB",# duplicate
        "https://www.youtube.com/watch?v=bQHyBxwYsyk&list=PLq9NE85nTBB0TCs7o8MMweQrrMONAA_IA&index=3&pp=gAQBiAQB8AUB",
        "https://www.youtube.com/watch?v=V5n39OKPB_o&list=PLq9NE85nTBB0TCs7o8MMweQrrMONAA_IA&index=4&pp=gAQBiAQB8AUB",
        "https://www.youtube.com/watch?v=V5n39OKPB_o&list=PLq9NE85nTBB0TCs7o8MMweQrrMONAA_IA&index=4&pp=gAQBiAQB8AUB",# duplicate
        "https://www.youtube.com/watch?v=mMGhYq4H4eE",
        "https://www.youtube.com/watch?v=BMRQK9yc5vY&list=PLRp7y0-zdXyW3zbyxbEjbW-rDw4i_Wtil&index=93&pp=gAQBiAQB8AUB",
    ]

    # Step 1: Check if playlist already exists ----- NEW
    playlist_id = find_playlist_by_title(youtube, title)

    # Step 2: Create it if it doesn’t exist ----- pre-existing
    if not playlist_id:
        playlist_id = create_playlist(youtube, title, description, privacy)

    # Step 3: Add videos (skip duplicates) ----- pre-existing
    add_videos_no_duplicates(youtube, playlist_id, video_links)