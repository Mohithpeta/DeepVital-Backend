from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel, ValidationError
from utils.security import hash_password, verify_password, create_jwt_token, get_current_user
from database import users_collection, doctors_collection
from datetime import timedelta
from typing import List, Optional  # Added Optional here
from bson import ObjectId
from fastapi.security import OAuth2PasswordBearer
import logging

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserSignupRequest(BaseModel):
    email: str
    password: str
    name: str
    phone: str
    deliveryStatus: Optional[str] = None  # 'postpartum', 'preconception', 'pregnancy'
    role: str  # 'user' or 'doctor'

class DoctorSignupRequest(BaseModel):
    email: str
    password: str
    name: str
    phone: str
    medicalID: str
    workExperience: str
    clinicName: str
    motherhoodStage: Optional[str] = None  # Added Optional for consistency
    role: str = "doctor"

class UserResponseWithToken(BaseModel):
    id: str
    email: str
    name: str
    phone: str
    role: str
    deliveryStatus: Optional[str] = None
    medicalID: Optional[str] = None
    workExperience: Optional[str] = None
    clinicName: Optional[str] = None
    motherhoodStage: Optional[str] = None
    watch_history: List[str]
    access_token: str
    token_type: str

class WatchHistoryRequest(BaseModel):
    user_id: str  # Ensure this is a non-empty string
    video_id: str  # Ensure this is a non-empty string

class WatchHistoryResponse(BaseModel):
    video_id: str

@router.post("/signup/user", response_model=UserResponseWithToken)
async def signup_user(user_data: UserSignupRequest):
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(user_data.password)
    new_user = {
        "email": user_data.email,
        "password": hashed_password,
        "name": user_data.name,
        "phone": user_data.phone,
        "deliveryStatus": user_data.deliveryStatus,
        "role": "user",
        "watch_history": []  # Explicitly initialize as an empty list
    }
    
    try:
        result = await users_collection.insert_one(new_user)
        logger.info(f"User created with ID: {result.inserted_id}, watch_history: {new_user['watch_history']}")
    except Exception as e:
        logger.error(f"Failed to insert user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
    
    access_token = create_jwt_token(
        data={"user_id": str(result.inserted_id), "role": "user"},
        expires_delta=timedelta(hours=1)
    )
    
    return UserResponseWithToken(
        id=str(result.inserted_id),
        email=user_data.email,
        name=user_data.name,
        phone=user_data.phone,
        role="user",
        deliveryStatus=user_data.deliveryStatus,
        watch_history=[],
        access_token=access_token,
        token_type="bearer"
    )

@router.post("/signup/doctor", response_model=UserResponseWithToken)
async def signup_doctor(doctor_data: DoctorSignupRequest):
    existing_doctor = await doctors_collection.find_one({"email": doctor_data.email})
    if existing_doctor:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(doctor_data.password)
    new_doctor = {
        "email": doctor_data.email,
        "password": hashed_password,
        "name": doctor_data.name,
        "phone": doctor_data.phone,
        "medicalID": doctor_data.medicalID,
        "workExperience": doctor_data.workExperience,
        "clinicName": doctor_data.clinicName,
        "motherhoodStage": doctor_data.motherhoodStage,
        "role": "doctor",
        "watch_history": []  # Explicitly initialize as an empty list
    }
    
    try:
        result = await doctors_collection.insert_one(new_doctor)
        logger.info(f"Doctor created with ID: {result.inserted_id}, watch_history: {new_doctor['watch_history']}")
    except Exception as e:
        logger.error(f"Failed to insert doctor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create doctor: {str(e)}")
    
    access_token = create_jwt_token(
        data={"user_id": str(result.inserted_id), "role": "doctor"},
        expires_delta=timedelta(hours=1)
    )
    
    return UserResponseWithToken(
        id=str(result.inserted_id),
        email=doctor_data.email,
        name=doctor_data.name,
        phone=doctor_data.phone,
        role="doctor",
        medicalID=doctor_data.medicalID,
        workExperience=doctor_data.workExperience,
        clinicName=doctor_data.clinicName,
        motherhoodStage=doctor_data.motherhoodStage,
        watch_history=[],
        access_token=access_token,
        token_type="bearer"
    )

@router.post("/login/user")
async def login_user(user_data: dict = Body(...)):
    email = user_data.get("email")
    password = user_data.get("password")
    
    user = await users_collection.find_one({"email": email})
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    access_token = create_jwt_token(
        data={"user_id": str(user["_id"]), "role": "user"},
        expires_delta=timedelta(hours=1)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"],
            "role": "user",
            "watch_history": user.get("watch_history", [])  # Ensure watch_history is returned
        }
    }

@router.post("/login/doctor")
async def login_doctor(user_data: dict = Body(...)):
    email = user_data.get("email")
    password = user_data.get("password")
    
    doctor = await doctors_collection.find_one({"email": email})
    if not doctor or not verify_password(password, doctor["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    access_token = create_jwt_token(
        data={"user_id": str(doctor["_id"]), "role": "doctor"},
        expires_delta=timedelta(hours=1)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(doctor["_id"]),
            "email": doctor["email"],
            "name": doctor["name"],
            "role": "doctor",
            "watch_history": doctor.get("watch_history", [])  # Ensure watch_history is returned
        }
    }

@router.post("/watch-history", response_model=WatchHistoryResponse)
async def update_watch_history(history: WatchHistoryRequest, user: dict = Depends(get_current_user)):
    try:
        user_id = history.user_id
        video_id = history.video_id
        
        logger.info(f"Received watch history update request: user_id={user_id}, video_id={video_id}")
        
        # Validate user_id and video_id before proceeding
        if not user_id or not isinstance(user_id, str) or user_id.strip() == "":
            raise HTTPException(status_code=422, detail="Invalid or empty user_id")
        if not video_id or not isinstance(video_id, str) or video_id.strip() == "":
            raise HTTPException(status_code=422, detail="Invalid or empty video_id")
        
        collection = users_collection if user["role"] == "user" else doctors_collection
        
        # Verify user exists and fetch the current document
        user_doc = await collection.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            logger.error(f"User not found for user_id: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Ensure watch_history is an array, handle any non-array values
        current_watch_history = user_doc.get("watch_history", [])
        if not isinstance(current_watch_history, list):
            await collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"watch_history": []}}
            )
            logger.info(f"Reset watch_history to empty array for user_id: {user_id} due to non-array value")
            current_watch_history = []
        
        # Update watch_history atomically to avoid conflicts
        new_watch_history = [video_id] + [vid for vid in current_watch_history if vid != video_id]
        if len(new_watch_history) > 50:
            new_watch_history = new_watch_history[:50]  # Limit to 50 entries
        
        result = await collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"watch_history": new_watch_history}}
        )
        logger.info(f"Update result: {result.modified_count} documents modified, new watch_history: {new_watch_history}")
        
        return WatchHistoryResponse(video_id=video_id)
    
    except ValidationError as ve:
        logger.error(f"Validation error in watch history request: {str(ve)}")
        raise HTTPException(status_code=422, detail=str(ve.errors()))
    except Exception as e:
        logger.error(f"Error updating watch history: {str(e)}, full error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update watch history: {str(e)}")

@router.get("/watch-history", response_model=List[WatchHistoryResponse])
async def get_watch_history(user: dict = Depends(get_current_user)):
    user_id = user["user_id"]
    collection = users_collection if user["role"] == "user" else doctors_collection
    
    user_data = await collection.find_one({"_id": ObjectId(user_id)})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    watch_history = user_data.get("watch_history", [])
    logger.info(f"Fetched watch history for user_id: {user_id}, history: {watch_history}")
    return [WatchHistoryResponse(video_id=video_id) for video_id in watch_history]