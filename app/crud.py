from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app import models, schemas
from app.security import hash_password


# ---------- Users ----------

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.execute(select(models.User).where(models.User.email == email)).scalar_one_or_none()


def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    user = models.User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------- Tasks ----------

def create_task(db: Session, task_in: schemas.TaskCreate, owner_id: int) -> models.Task:
    task = models.Task(**task_in.model_dump(), owner_id=owner_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int, owner_id: int) -> Optional[models.Task]:
    return db.execute(
        select(models.Task).where(models.Task.id == task_id, models.Task.owner_id == owner_id)
    ).scalar_one_or_none()


def list_tasks(
    db: Session,
    owner_id: int,
    skip: int = 0,
    limit: int = 20,
    status: Optional[models.TaskStatus] = None,
    priority: Optional[models.TaskPriority] = None,
):
    query = select(models.Task).where(models.Task.owner_id == owner_id)
    count_query = select(func.count()).select_from(models.Task).where(models.Task.owner_id == owner_id)

    if status is not None:
        query = query.where(models.Task.status == status)
        count_query = count_query.where(models.Task.status == status)
    if priority is not None:
        query = query.where(models.Task.priority == priority)
        count_query = count_query.where(models.Task.priority == priority)

    total = db.execute(count_query).scalar_one()
    items = (
        db.execute(query.order_by(models.Task.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return total, items


def update_task(db: Session, task: models.Task, task_in: schemas.TaskUpdate) -> models.Task:
    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: models.Task) -> None:
    db.delete(task)
    db.commit()
