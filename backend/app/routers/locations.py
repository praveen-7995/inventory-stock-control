from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Location, LocationAssignment, User, Role
from app.schemas import LocationCreate, LocationOut, AssignmentCreate, AssignmentOut
from app.deps import get_current_user, require_manager

router = APIRouter(tags=["locations"])


@router.get("/locations", response_model=list[LocationOut])
def list_locations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == Role.manager:
        return db.query(Location).order_by(Location.name).all()
    # Staff only see locations they're assigned to.
    return (
        db.query(Location)
        .join(LocationAssignment, LocationAssignment.location_id == Location.id)
        .filter(LocationAssignment.user_id == current_user.id)
        .order_by(Location.name)
        .all()
    )


@router.post("/locations", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
def create_location(payload: LocationCreate, db: Session = Depends(get_db), _: User = Depends(require_manager)):
    loc = Location(name=payload.name.strip())
    db.add(loc)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Location already exists")
    db.refresh(loc)
    return loc


@router.get("/assignments", response_model=list[AssignmentOut])
def list_assignments(db: Session = Depends(get_db), _: User = Depends(require_manager)):
    rows = db.query(LocationAssignment).all()
    return [
        AssignmentOut(
            id=a.id, user_id=a.user_id, location_id=a.location_id,
            user_name=a.user.name, location_name=a.location.name,
        )
        for a in rows
    ]


@router.post("/assignments", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
def create_assignment(payload: AssignmentCreate, db: Session = Depends(get_db), _: User = Depends(require_manager)):
    user = db.get(User, payload.user_id)
    location = db.get(Location, payload.location_id)
    if not user or not location:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User or location not found")
    existing = (
        db.query(LocationAssignment)
        .filter_by(user_id=payload.user_id, location_id=payload.location_id)
        .first()
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Assignment already exists")
    assignment = LocationAssignment(user_id=payload.user_id, location_id=payload.location_id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return AssignmentOut(
        id=assignment.id, user_id=user.id, location_id=location.id,
        user_name=user.name, location_name=location.name,
    )


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(assignment_id: int, db: Session = Depends(get_db), _: User = Depends(require_manager)):
    assignment = db.get(LocationAssignment, assignment_id)
    if not assignment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    db.delete(assignment)
    db.commit()


@router.get("/staff", response_model=list[dict])
def list_staff(db: Session = Depends(get_db), _: User = Depends(require_manager)):
    """Manager-only convenience: list staff users to build assignments against."""
    staff = db.query(User).filter(User.role == Role.staff).order_by(User.name).all()
    return [{"id": s.id, "name": s.name, "email": s.email} for s in staff]
