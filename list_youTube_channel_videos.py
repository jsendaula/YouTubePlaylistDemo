from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# YouTube Data API scope (read-only)
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

def authenticate_youtube():
    """Authenticate and return a YouTube API client."""
    flow = InstalledAppFlow.from_client_secrets_file("------------.com.json", SCOPES)
    creds = flow.run_local_server(port=0)
    youtube = build("youtube", "v3", credentials=creds)
    return youtube

def get_channel_uploads_playlist_id(youtube, channel_id=None, for_username=None):
    """Fetch the special uploads playlist ID for a given channel."""
    if channel_id:
        request = youtube.channels().list(part="contentDetails", id=channel_id)
    elif for_username:
        request = youtube.channels().list(part="contentDetails", forUsername=for_username)
    else:
        raise ValueError("Must provide either channel_id or for_username")

    response = request.execute()
    items = response.get("items", [])
    if not items:
        print("❌ Channel not found.")
        return None

    uploads_playlist_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    return uploads_playlist_id

def list_videos_in_playlist(youtube, playlist_id):
    """Return a list of videos (title, videoId, publish date) from a playlist."""
    videos = []
    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token,
        )
        response = request.execute()

        for item in response.get("items", []):
            snippet = item["snippet"]
            video = {
                "title": snippet["title"],
                "videoId": snippet["resourceId"]["videoId"],
                "publishedAt": snippet["publishedAt"],
            }
            videos.append(video)

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return videos

def main():
    youtube = authenticate_youtube()

    # Provide one of the following:
    # Example 1: by channel username (older channels)
    # uploads_id = get_channel_uploads_playlist_id(youtube, for_username="Latelier__de__Musique)

    # Example 2: by channel ID (most reliable)
    # uploads_id = get_channel_uploads_playlist_id(youtube, channel_id="UCiEzJ2MVFxBMSds9Axrz5mw")  # Google Developers
    uploads_id = get_channel_uploads_playlist_id(youtube, channel_id=UCMxPERwMmMcJrDJM-yihUlA") #Comcast Business)

    if not uploads_id:
        return

    videos = list_videos_in_playlist(youtube, uploads_id)

    print(f"\n📺 Found {len(videos)} videos:\n")
    for v in videos:
        print(f"• {v['title']}")
        print(f"  https://www.youtube.com/watch?v={v['videoId']}")
        print(f"  Published: {v['publishedAt']}\n")

if __name__ == "__main__":
    main()
