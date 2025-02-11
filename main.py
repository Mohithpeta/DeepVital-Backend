from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes.auth_routes import router as auth_router
from routes.video_routes import router as video_router
from routes.youtube_routes import router as youtube_router

load_dotenv()

app = FastAPI(title="Video Streaming Platform")

# ✅ CORS Configuration
origins = [
    "http://localhost:5173",  # React Frontend
    "http://127.0.0.1:5173",
    "*"  # Allow all (for development only)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# ✅ Include API Routes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(video_router, prefix="/videos", tags=["Videos"])
app.include_router(youtube_router, prefix="/youtube", tags=["YouTube"])

# ✅ Root Endpoint with Access-Control Headers
@app.get("/")
def home(request: Request, response: Response):
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return {"message": "Welcome to the Video Streaming API!"}
