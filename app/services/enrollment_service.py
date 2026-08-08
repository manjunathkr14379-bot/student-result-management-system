from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.services.student_service import get_student
from app.services.course_service import get_course


def enroll_student(db: Session, enrollment_in: schemas.EnrollmentCreate) -> models.Enrollment:
    get_student(db, enrollment_in.student_id)   # 404s if missing
    get_course(db, enrollment_in.course_id)     # 404s if missing

    enrollment = models.Enrollment(**enrollment_in.model_dump())
    db.add(enrollment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student is already enrolled in this course",
        )
    db.refresh(enrollment)
    return enrollment


def set_grade(db: Session, enrollment_id: int, grade: float) -> models.Enrollment:
    enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    enrollment.grade = grade
    db.commit()
    db.refresh(enrollment)
    return enrollment


def unenroll(db: Session, enrollment_id: int) -> None:
    enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    db.delete(enrollment)
    db.commit()
