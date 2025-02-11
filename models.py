from pydantic import BaseModel
from typing import Optional

# User Schema
class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    phone: str
    deliveryStatus: Optional[str] = None  # 'postpartum', 'preconception', 'pregnancy'
    role: str  # 'user' or 'doctor'

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: str
    role: str
    deliveryStatus: Optional[str] = None

# Video Schema
class VideoCreate(BaseModel):
    youtube_url: str  # URL for YouTube videos
    title: Optional[str] = None
    description: Optional[str] = None
    category: str  # 'Postpartum', 'Preconception', 'Pregnancy'
    # uploaded_by: str  # Doctor's user ID
