from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from utils.security import hash_password, verify_password, create_jwt_token
from database import users_collection, doctors_collection  # Separate collections
from datetime import timedelta

router = APIRouter()

# Define Pydantic models for input validation
class UserSignupRequest(BaseModel):
    email: str
    password: str
    name: str
    phone: str
    deliveryStatus: str
    role: str = "user"

class DoctorSignupRequest(BaseModel):
    email: str
    password: str
    name: str
    phone: str
    medicalID: str
    workExperience: str
    clinicName: str
    motherhoodStage: str
    role: str = "doctor"

# Define response model
class UserResponseWithToken(BaseModel):
    id: str
    email: str
    name: str
    phone: str
    role: str
    deliveryStatus: str | None = None
    medicalID: str | None = None
    workExperience: str | None = None
    clinicName: str | None = None
    motherhoodStage: str | None = None
    access_token: str
    token_type: str

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
    }
    
    result = await users_collection.insert_one(new_user)
    
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
    }
    
    result = await doctors_collection.insert_one(new_doctor)
    
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
        }
    }
