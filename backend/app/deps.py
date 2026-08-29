from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import decode_access_token
from app.models import User, Role, LocationAssignment

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return user


def require_manager(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.manager:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Manager role required")
    return user


def assert_can_act_at_location(db: Session, user: User, location_id: int) -> None:
    """
    Server-side enforcement of goal #1/#5: managers can act anywhere, staff only
    at locations they're explicitly assigned to. This is checked here, not just
    hidden in the UI.
    """
    if user.role == Role.manager:
        return
    assigned = (
        db.query(LocationAssignment)
        .filter(LocationAssignment.user_id == user.id, LocationAssignment.location_id == location_id)
        .first()
    )
    if not assigned:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not assigned to this location")
