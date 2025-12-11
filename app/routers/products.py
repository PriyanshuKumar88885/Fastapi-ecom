from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from .. import crud, schemas, models
from ..dependencies import get_db, get_tenant_by_path, require_tenant_admin, get_current_user, ProductFilterParams
from ..exceptions import ResourceNotFoundError, ValidationError
from ..config import settings


# Global (public) product catalog router
global_router = APIRouter(prefix='/products', tags=['products'])

router = APIRouter(prefix='/{tenant_name}/products', tags=['products'])


@router.post('/', response_model=schemas.ProductOut)
def create_product(tenant_name: str, data: schemas.ProductCreate, db: Session = Depends(get_db), user: Any = Depends(require_tenant_admin), tenant: Any = Depends(get_tenant_by_path)):
    # tenant admin or platform admin can create product for tenant
    product = crud.create_product(db, tenant, data)
    return product


@router.get('/', response_model=List[schemas.ProductOut])
def list_products(
    tenant_name: str,
    filters: ProductFilterParams = Depends(),
    db: Session = Depends(get_db),
    tenant: Any = Depends(get_tenant_by_path)
):
    return crud.list_products(
        db,
        tenant,
        skip=filters.skip,
        limit=filters.limit,
        category=filters.category,
        q=filters.search
    )


@router.get('/{product_id}', response_model=schemas.ProductOut)
def get_product(tenant_name: str, product_id: int, db: Session = Depends(get_db), tenant: Any = Depends(get_tenant_by_path)):
    p = crud.get_product(db, product_id)
    if not p or p.tenant_id != tenant.id:
        raise ResourceNotFoundError('Product', str(product_id))
    return p


@router.put('/{product_id}', response_model=schemas.ProductOut)
def update_product(tenant_name: str, product_id: int, data: schemas.ProductCreate, db: Session = Depends(get_db), user: Any = Depends(require_tenant_admin), tenant: Any = Depends(get_tenant_by_path)):
    p = crud.get_product(db, product_id)
    if not p or p.tenant_id != tenant.id:
        raise ResourceNotFoundError('Product', str(product_id))
    updates = data.dict(exclude_unset=True)
    return crud.update_product(db, product_id, updates, user)


@router.delete('/{product_id}')
def delete_product(tenant_name: str, product_id: int, db: Session = Depends(get_db), user: Any = Depends(require_tenant_admin), tenant: Any = Depends(get_tenant_by_path)):
    p = crud.get_product(db, product_id)
    if not p or p.tenant_id != tenant.id:
        raise ResourceNotFoundError('Product', str(product_id))
    crud.delete_product(db, product_id, user)
    return {'detail': 'deleted'}


# --- Global catalog endpoints ---


@global_router.get('/', response_model=List[schemas.ProductOut])
def list_all_products(filters: ProductFilterParams = Depends(), db: Session = Depends(get_db)):
    return crud.list_all_products(
        db,
        skip=filters.skip,
        limit=filters.limit,
        category=filters.category,
        q=filters.search,
    )


@global_router.get('/{product_id}', response_model=schemas.ProductOut)
def get_product_global(product_id: int, db: Session = Depends(get_db)):
    p = crud.get_product(db, product_id)
    if not p:
        raise ResourceNotFoundError('Product', str(product_id))
    return p
