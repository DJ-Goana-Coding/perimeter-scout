from fastapi import APIRouter
from pydantic import BaseModel
import json
import os

router = APIRouter(prefix="/profile", tags=["profile"])

PROFILE_PATH = "data/user_profile.json"


class UserProfile(BaseModel):
    username: str


def load_profile():
    """Load user profile from file"""
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, "r") as f:
                return json.load(f)
        except:
            pass
    return {"username": "Operator"}


def save_profile(profile: dict):
    """Save user profile to file"""
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
    with open(PROFILE_PATH, "w") as f:
        json.dump(profile, f, indent=2)


@router.get("/")
async def get_profile():
    """Get current user profile"""
    return load_profile()


@router.put("/username")
async def update_username(profile: UserProfile):
    """Update username"""
    current = load_profile()
    current["username"] = profile.username
    save_profile(current)
    return {"status": "success", "username": profile.username}
