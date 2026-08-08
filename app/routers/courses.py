from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import schemas, models, auth
from app.database import get_db
from app.services import course_service

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.post("", response_model=schemas.CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(
    course_in: schemas.CourseCreate,
    db: Session = Depends(get_db),
    _=Depends(auth.require_role(models.RoleEnum.admin, models.RoleEnum.teacher)),
):
    return course_service.create_course(db, course_in)


@router.get("", response_model=list[schemas.CourseOut])
def list_courses(db: Session = Depends(get_db), _=Depends(auth.get_current_user)):
    return course_service.list_courses(db)


@router.get("/{course_id}", response_model=schemas.CourseOut)
def get_course(course_id: int, db: Session = Depends(get_db), _=Depends(auth.get_current_user)):
    return course_service.get_course(db, course_id)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    _=Depends(auth.require_role(models.RoleEnum.admin)),
):
    course_service.delete_course(db, course_id)
