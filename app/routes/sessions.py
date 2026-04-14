from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import sessions_collection
from app.models import SessionCreate
from jose import jwt
from datetime import datetime
from bson import ObjectId

router = APIRouter()

SECRET_KEY = "attendease_secret_key"
ALGORITHM = "HS256"
security = HTTPBearer()

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/create")
async def create_session(session: SessionCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = decode_token(token)
    
    if user["role"] != "faculty":
        raise HTTPException(status_code=403, detail="Only faculty can create sessions")
    
    new_session = {
        "subject": session.subject,
        "room": session.room,
        "faculty_id": user["id"],
        "faculty_name": user["name"],
        "active": True,
        "created_at": datetime.utcnow()
    }
    result = await sessions_collection.insert_one(new_session)
    return {
        "message": "Session created",
        "session_id": str(result.inserted_id)
    }

@router.get("/active")
async def get_active_sessions():
    sessions = []
    async for session in sessions_collection.find({"active": True}):
        sessions.append({
            "session_id": str(session["_id"]),
            "subject": session["subject"],
            "room": session["room"],
            "faculty_name": session["faculty_name"],
            "created_at": str(session["created_at"])
        })
    return sessions

@router.put("/close/{session_id}")
async def close_session(session_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = decode_token(token)
    
    if user["role"] != "faculty":
        raise HTTPException(status_code=403, detail="Only faculty can close sessions")
    
    await sessions_collection.update_one(
        {"_id": ObjectId(session_id)},
        {"$set": {"active": False}}
    )
    return {"message": "Session closed"}