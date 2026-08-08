from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas


def create_course(db: Session, course_in: schemas.CourseCreate) -> models.Course:
    existing = db.query(models.Course).filter(models.Course.code == course_in.code).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Course code already exists")
    course = models.Course(**course_in.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def list_courses(db: Session):
    return db.query(models.Course).order_by(models.Course.id).all()


def get_course(db: Session, course_id: int) -> models.Course:
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


def delete_course(db: Session, course_id: int) -> None:
    course = get_course(db, course_id)
    db.delete(course)
    db.commit()
