import datetime as dt
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from app.models import Role, MovementKind, HistoryEvent


# ---------- Auth ----------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: Role

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: Role


# ---------- Locations ----------

class LocationCreate(BaseModel):
    name: str


class LocationOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class AssignmentCreate(BaseModel):
    user_id: int
    location_id: int


class AssignmentOut(BaseModel):
    id: int
    user_id: int
    location_id: int
    user_name: str
    location_name: str

    class Config:
        from_attributes = True


# ---------- Categories ----------

class CategoryCreate(BaseModel):
    name: str


class CategoryOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# ---------- Items ----------

class ItemCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    unit_of_measure: str
    reorder_level: int = 0
    category_id: int

    @field_validator("reorder_level")
    @classmethod
    def non_negative(cls, v):
        if v < 0:
            raise ValueError("reorder_level must be >= 0")
        return v


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    unit_of_measure: Optional[str] = None
    reorder_level: Optional[int] = None
    category_id: Optional[int] = None


class ItemOut(BaseModel):
    id: int
    sku: str
    name: str
    description: Optional[str]
    unit_of_measure: str
    reorder_level: int
    category_id: int
    category_name: str
    is_archived: bool
    on_hand_total: int

    class Config:
        from_attributes = True


class ItemListResponse(BaseModel):
    total: int
    items: list[ItemOut]


class ItemNoteCreate(BaseModel):
    note: str


# ---------- Movements ----------

class MovementCreate(BaseModel):
    item_id: int
    kind: MovementKind
    quantity: int
    location_id: Optional[int] = None
    from_location_id: Optional[int] = None
    to_location_id: Optional[int] = None
    reason: Optional[str] = None


class MovementOut(BaseModel):
    id: int
    item_id: int
    kind: MovementKind
    quantity: int
    location_id: Optional[int]
    from_location_id: Optional[int]
    to_location_id: Optional[int]
    reason: Optional[str]
    recorded_by_id: int
    recorded_by_name: str
    created_at: dt.datetime

    class Config:
        from_attributes = True


# ---------- History ----------

class HistoryOut(BaseModel):
    id: int
    event_type: HistoryEvent
    field_name: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    note: Optional[str]
    changed_by_id: int
    changed_by_name: str
    created_at: dt.datetime

    class Config:
        from_attributes = True


# ---------- Dashboard ----------

class DashboardOut(BaseModel):
    active_items: int
    items_at_or_below_reorder: int
    movements_today: int
    distinct_items_moved_this_week: int
    on_hand_by_category: list[dict]
    on_hand_by_location: list[dict]
    weekly_receipt_issue_volume: list[dict]


# ---------- Alerts ----------

class AlertOut(BaseModel):
    item_id: int
    sku: str
    name: str
    on_hand_total: int
    reorder_level: int


# ---------- Import/Export ----------

class ImportRowResult(BaseModel):
    row: int
    status: str  # "ok" | "error"
    message: Optional[str] = None


class ImportReport(BaseModel):
    total_rows: int
    imported: int
    failed: int
    results: list[ImportRowResult]
