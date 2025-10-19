# 🎬 YouTube Playlist Creator / Updater (Python)

A simple Python tool that can:
- Create or update a YouTube playlist.
- Add new videos from a list of URLs or video IDs.
- Automatically skip duplicates (both in the input and the playlist).

---

## 🚀 How to Use

### 1. Prerequisites
- Python 3.8+
- A Google account with a YouTube channel.

### 2. Enable YouTube Data API
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Enable **YouTube Data API v3**.
4. Create **OAuth client ID** credentials (type: *Desktop App*).
5. Download your credentials file and save it as **`client_secret.json`** in this folder.

### 3. Install dependencies
```bash
pip install -r requirements.txt
