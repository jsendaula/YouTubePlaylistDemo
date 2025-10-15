# YouTubePlaylist
Python Project using ChatGPT to manage playlists on YouTube

## PREREQUISITES
    
### Create a Google Cloud project
Go to [Google Cloud Console](https://console.cloud.google.com/).  
Create a new project (or select one).  
Enable the YouTube Data API v3.  
### Create OAuth 2.0 credentials
Go to APIs & Services → Credentials → Create Credentials → OAuth client ID.  
Choose Desktop app.  
Download the client_secret.json file and save it in your project folder.
Add yourself as a user [Audience](https://console.cloud.google.com/auth/audience) 
### Install the required Python libraries
`pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client`
