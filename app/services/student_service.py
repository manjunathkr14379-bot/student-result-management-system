"""
Service layer for Student operations.

Routers stay thin (HTTP concerns only); all business logic + DB queries
live here. This separation makes the logic unit-testable without spinning
up the HTTP layer, and keeps routers readable.
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app import models, schemas


def create_student(db: Session, student_in: schemas.StudentCreate) -> models.Student:
    existing = db.query(models.Student).filter(
        or_(models.Student.roll_number == student_in.roll_number,
            models.Student.email == student_in.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this roll number or email already exists",
        )
    student = models.Student(**student_in.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def get_student(db: Session, student_id: int) -> models.Student:
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


def list_students(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    department: Optional[str] = None,
    search: Optional[str] = None,
):
    query = db.query(models.Student)
    if department:
        query = query.filter(models.Student.department.ilike(f"%{department}%"))
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(models.Student.first_name.ilike(like),
                models.Student.last_name.ilike(like),
                models.Student.roll_number.ilike(like))
        )
    total = query.count()
    items = query.order_by(models.Student.id).offset((page - 1) * page_size).limit(page_size).all()
    return total, items


def update_student(db: Session, student_id: int, student_in: schemas.StudentUpdate) -> models.Student:
    student = get_student(db, student_id)
    for field, value in student_in.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


def delete_student(db: Session, student_id: int) -> None:
    student = get_student(db, student_id)
    db.delete(student)
    db.commit()


def get_transcript(db: Session, student_id: int) -> dict:
    """Builds a student's transcript: enrolled courses + computed GPA.
    GPA here is a simple credit-weighted average of grades on a 100-point
    scale, converted to a 4.0 scale (grade/25) -- documented so it's easy
    to swap for a real institution's grading policy."""
    student = get_student(db, student_id)
    graded = [e for e in student.enrollments if e.grade is not None]

    total_credits = sum(e.course.credits for e in graded)
    if total_credits > 0:
        weighted_sum = sum((e.grade / 25.0) * e.course.credits for e in graded)
        gpa = round(weighted_sum / total_credits, 2)
    else:
        gpa = None

    return {
        **schemas.StudentOut.model_validate(student).model_dump(),
        "gpa": gpa,
        "total_credits": total_credits,
        "courses": student.enrollments,
    }
