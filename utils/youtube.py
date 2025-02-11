import os
import re
import googleapiclient.discovery

YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"  # Replace with your API key
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def extract_video_id(youtube_url: str):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", youtube_url)
    return match.group(1) if match else None

def fetch_youtube_metadata(youtube_url: str):
    video_id = extract_video_id(youtube_url)
    if not video_id:
        return None

    request = youtube.videos().list(
        part="snippet,statistics",
        id=video_id
    )
    response = request.execute()

    if not response["items"]:
        return None

    video_data = response["items"][0]
    return {
        "title": video_data["snippet"]["title"],
        "upload_date": video_data["snippet"]["publishedAt"],
        "views": video_data["statistics"].get("viewCount", "0"),
        "description": video_data["snippet"]["description"],
        "thumbnail": video_data["snippet"]["thumbnails"]["high"]["url"],
        "video_id": video_id
    }
