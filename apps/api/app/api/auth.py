from typing import Any, Dict
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import (
    create_access_token,
    get_current_user_optional,
)
from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class UserProfileResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    plan: str
    token: str


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user_optional),
) -> UserProfileResponse:
    token = create_access_token(current_user.id, current_user.email)
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role or "Lead manager",
        plan=current_user.plan or "Pro Plan",
        token=token,
    )


class SessionRequest(BaseModel):
    user_id: int


@router.post("/session", response_model=UserProfileResponse)
def create_session_for_user(
    payload: SessionRequest, db: Session = Depends(get_db)
) -> UserProfileResponse:
    user = db.get(User, payload.user_id)
    if not user:
        user = get_current_user_optional(db)
    token = create_access_token(user.id, user.email)
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role or "Lead manager",
        plan=user.plan or "Pro Plan",
        token=token,
    )
