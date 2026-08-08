"""
ORM models.

Schema:
    User        -- login identity + role (admin / teacher / student), used for auth
    Student     -- a student's academic profile
    Course      -- a course that can be taught / enrolled in
    Enrollment  -- join table between Student and Course, carries the grade
                   (classic many-to-many "with extra data" pattern)
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Enum, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class RoleEnum(str, enum.Enum):
    admin = "admin"
    teacher = "teacher"
    student = "student"


class User(Base):
    """Login credentials, decoupled from the Student profile on purpose:
    not every user of the system is a student (admins/teachers aren't),
    and a student could exist in records before ever getting a login."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.student, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    student_profile = relationship("Student", back_populates="user", uselist=False)


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    roll_number = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    department = Column(String(100), nullable=False)
    year_of_study = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    user = relationship("User", back_populates="student_profile")

    enrollments = relationship(
        "Enrollment", back_populates="student", cascade="all, delete-orphan"
    )


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    credits = Column(Integer, nullable=False, default=3)
    department = Column(String(100), nullable=False)

    enrollments = relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan"
    )


class Enrollment(Base):
    """A student's enrollment in a course, with an optional grade.
    Unique constraint stops a student being enrolled in the same course twice."""
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    grade = Column(Float, nullable=True)  # null until graded, 0-100 scale
    enrolled_on = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
