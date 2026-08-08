from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import schemas, models, auth
from app.database import get_db
from app.services import enrollment_service

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


@router.post("", response_model=schemas.EnrollmentOut, status_code=status.HTTP_201_CREATED)
def enroll_student(
    enrollment_in: schemas.EnrollmentCreate,
    db: Session = Depends(get_db),
    _=Depends(auth.require_role(models.RoleEnum.admin, models.RoleEnum.teacher)),
):
    return enrollment_service.enroll_student(db, enrollment_in)


@router.patch("/{enrollment_id}/grade", response_model=schemas.EnrollmentOut)
def set_grade(
    enrollment_id: int,
    grade_in: schemas.GradeUpdate,
    db: Session = Depends(get_db),
    _=Depends(auth.require_role(models.RoleEnum.admin, models.RoleEnum.teacher)),
):
    return enrollment_service.set_grade(db, enrollment_id, grade_in.grade)


@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def unenroll(
    enrollment_id: int,
    db: Session = Depends(get_db),
    _=Depends(auth.require_role(models.RoleEnum.admin, models.RoleEnum.teacher)),
):
    enrollment_service.unenroll(db, enrollment_id)
