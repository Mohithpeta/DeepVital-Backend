from fastapi import APIRouter, Depends, HTTPException
from models import VideoCreate
from database import videos_collection
from utils.security import get_current_user
from bson import ObjectId
from typing import List, Dict
import requests
import os
from dotenv import load_dotenv

router = APIRouter()

# Load environment variables
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/videos"

# Extract video ID from YouTube URL
def extract_video_id(youtube_url: str) -> str:
    if "youtu.be/" in youtube_url:
        return youtube_url.split("youtu.be/")[-1].split("?")[0]
    elif "youtube.com/watch?v=" in youtube_url:
        return youtube_url.split("watch?v=")[-1].split("&")[0]
    raise ValueError("Invalid YouTube URL format")

# Fetch video metadata from YouTube API
def fetch_youtube_metadata(youtube_url: str) -> Dict:
    try:
        video_id = extract_video_id(youtube_url)
        response = requests.get(
            YOUTUBE_API_URL,
            params={"part": "snippet,statistics", "id": video_id, "key": YOUTUBE_API_KEY},
        )
        data = response.json()

        if "items" not in data or not data["items"]:
            raise HTTPException(status_code=404, detail="YouTube video not found")

        video_info = data["items"][0]
        metadata = {
            "title": video_info["snippet"]["title"],
            "description": video_info["snippet"]["description"],
            "upload_date": video_info["snippet"]["publishedAt"],
            "view_count": video_info["statistics"].get("viewCount", "N/A"),
            "thumbnail": video_info["snippet"]["thumbnails"]["high"]["url"],
            "youtube_url": youtube_url,
        }
        return metadata
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching metadata: {str(e)}")

# Upload a new YouTube video
@router.post("/videos")
async def upload_video(video: VideoCreate, user: dict = Depends(get_current_user)):
    if user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can upload videos")

    youtube_metadata = fetch_youtube_metadata(video.youtube_url)
    video_data = {
        "youtube_url": video.youtube_url,
        "title": youtube_metadata["title"],
        "description": video.description if video.description else youtube_metadata["description"],
        "category": video.category,
        "uploaded_by": user["user_id"],
        "upload_date": youtube_metadata["upload_date"],
        "view_count": youtube_metadata["view_count"],
        "thumbnail": youtube_metadata["thumbnail"],
    }
    result = await videos_collection.insert_one(video_data)
    video_data["_id"] = str(result.inserted_id)  # Convert ObjectId to string
    return {
        "message": "Video uploaded successfully",
        "video": video_data
    }

# Get videos - Doctors see their own videos, Users see all
@router.get("/")
async def get_videos(user: dict = Depends(get_current_user)):
    try:
        if user["role"] == "doctor":
            query = {"uploaded_by": user["user_id"]}  # Doctors see only their own videos
        else:
            query = {}  # Users see all videos

        videos = await videos_collection.find(query).to_list(1000)

        formatted_videos = [
            {
                "_id": str(video["_id"]),
                "title": video["title"],
                "thumbnail": video.get("thumbnail", ""),
                "upload_date": video.get("upload_date", "N/A"),
                "views": video.get("view_count", 0),
                "uploaded_by": video["uploaded_by"],
                "doctor": {
                    "name": video.get("doctor", {}).get("name", "Unknown"),
                    "avatar": video.get("doctor", {}).get("avatar", ""),
                    "verified": video.get("doctor", {}).get("verified", False),
                }
            }
            for video in videos
        ]
        return formatted_videos

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving videos: {str(e)}")

# Delete a video
@router.delete("/videos/{video_id}")
async def delete_video(video_id: str, user: dict = Depends(get_current_user)):
    video = await videos_collection.find_one({"_id": ObjectId(video_id)})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if user["role"] != "doctor" or user["user_id"] != video["uploaded_by"]:
        raise HTTPException(status_code=403, detail="Unauthorized to delete this video")
    await videos_collection.delete_one({"_id": ObjectId(video_id)})
    return {"message": "Video deleted successfully"}
