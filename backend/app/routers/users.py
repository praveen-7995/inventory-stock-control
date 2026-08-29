from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserOut
from app.auth import hash_password
from app.deps import require_manager

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_manager)):
    return db.query(User).order_by(User.name).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_manager)):
    """
    Only a manager can create accounts (staff or additional managers). There
    is no public self-signup - accounts are provisioned by whoever runs
    purchasing/inventory for the business, matching the real-world scenario.
    """
    if len(payload.password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must be at least 8 characters")
    user = User(
        email=payload.email.lower(), hashed_password=hash_password(payload.password),
        name=payload.name.strip(), role=payload.role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "A user with that email already exists")
    db.refresh(user)
    return user
