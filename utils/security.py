from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv
from fastapi import HTTPException,Depends
from fastapi.security import OAuth2PasswordBearer

# Load environment variables
load_dotenv()

# Fetch secret key and algorithm from environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

#debugging: print values to verify they are loaded correctly
print(SECRET_KEY)
print(ALGORITHM)

# Ensure SECRET_KEY and ALGORITHM are not None
if not SECRET_KEY or not ALGORITHM:
    raise ValueError("SECRET_KEY and ALGORITHM must be defined in the .env file")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash the given password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that the given plain password matches the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def create_jwt_token(data: dict, expires_delta: timedelta) -> str:
    """Create a JWT token with an expiration time."""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def check_role(user_role: str, required_role: str):
    """Check if the user has the required role to perform an action."""
    if user_role != required_role:
        raise HTTPException(status_code=403, detail="Unauthorized to perform this action")
    
def verify_token(token:str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload #Returns user data from token
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    
    
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        print("Token decoded successfully:", payload)  # ✅ Debugging log
        return {"user_id": payload["user_id"], "role": payload["role"]}
    except jwt.ExpiredSignatureError:
        print("Token expired!")  # ✅ Debugging log
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        print("Invalid token!")  # ✅ Debugging log
        raise HTTPException(status_code=401, detail="Invalid token")
