"""
Pydantic schemas: define the "shape" of data crossing the API boundary.
Kept separate from ORM models (app.models) on purpose -- this lets us
control exactly what a client can send/see (e.g. never expose hashed_password).
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models import RoleEnum


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: RoleEnum = RoleEnum.student


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    role: RoleEnum
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Student ----------
class StudentBase(BaseModel):
    roll_number: str = Field(min_length=1, max_length=50)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    department: str = Field(min_length=1, max_length=100)
    year_of_study: int = Field(ge=1, le=6)


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    year_of_study: Optional[int] = Field(default=None, ge=1, le=6)


class StudentOut(StudentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class StudentTranscript(StudentOut):
    """Student profile plus computed academic summary."""
    gpa: Optional[float] = None
    total_credits: int = 0
    courses: List["EnrollmentOut"] = []


# ---------- Course ----------
class CourseBase(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    title: str = Field(min_length=1, max_length=200)
    credits: int = Field(ge=1, le=10, default=3)
    department: str = Field(min_length=1, max_length=100)


class CourseCreate(CourseBase):
    pass


class CourseOut(CourseBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Enrollment ----------
class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int


class GradeUpdate(BaseModel):
    grade: float = Field(ge=0, le=100)


class EnrollmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    course: CourseOut
    grade: Optional[float] = None
    enrolled_on: datetime


class PaginatedStudents(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[StudentOut]
