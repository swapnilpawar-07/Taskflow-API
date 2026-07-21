from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.rate_limiter import limiter

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_default)
def create_task(
    request: Request,
    task_in: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    return crud.create_task(db, task_in, owner_id=current_user.id)


@router.get("", response_model=schemas.PaginatedTasks)
def list_tasks(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return (1-100)"),
    status_filter: Optional[models.TaskStatus] = Query(None, alias="status"),
    priority_filter: Optional[models.TaskPriority] = Query(None, alias="priority"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    total, items = crud.list_tasks(
        db,
        owner_id=current_user.id,
        skip=skip,
        limit=limit,
        status=status_filter,
        priority=priority_filter,
    )
    return schemas.PaginatedTasks(total=total, skip=skip, limit=limit, items=items)


@router.get("/{task_id}", response_model=schemas.TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    task = crud.get_task(db, task_id=task_id, owner_id=current_user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=schemas.TaskOut)
def update_task(
    task_id: int,
    task_in: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    task = crud.get_task(db, task_id=task_id, owner_id=current_user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return crud.update_task(db, task, task_in)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    task = crud.get_task(db, task_id=task_id, owner_id=current_user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    crud.delete_task(db, task)
    return None
