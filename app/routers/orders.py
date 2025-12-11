from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any
from .. import crud, schemas, models
from ..dependencies import get_db, get_tenant_by_path, get_current_user
from ..exceptions import ResourceNotFoundError
from sqlalchemy.orm import joinedload
from ..config import settings

router = APIRouter(prefix='/orders', tags=['orders'])


@router.post('/', response_model=schemas.OrderOut)
def create_order(data: schemas.OrderCreate, db: Session = Depends(get_db), user: Any = Depends(get_current_user)):
    # Orders are global: they belong to the user and can contain products from any tenant.
    try:
        items = [it.dict() for it in data.items]
        order = crud.create_order(db, user, items, tenant_context=None)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/', response_model=list[schemas.OrderOut])
def list_orders(
    skip: int = Query(settings.DEFAULT_SKIP, ge=0),
    limit: int = Query(settings.DEFAULT_LIMIT, ge=1, le=settings.MAX_LIMIT),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    # Return orders for current user across all tenants
    orders = crud.list_orders_for_user(db, user, skip=skip, limit=limit)
    return orders



