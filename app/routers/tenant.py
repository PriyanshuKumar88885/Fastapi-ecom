from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..dependencies import get_db, require_platform_admin
from ..exceptions import ResourceAlreadyExistsError, ResourceNotFoundError
from typing import Union

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/", response_model=list)
def list_tenants_endpoint(db: Session = Depends(get_db), _=Depends(require_platform_admin)):
    """List all tenants. Only accessible by platform admins."""
    tenants = crud.list_tenants(db)
    return [schemas.TenantOut.from_orm(t) for t in tenants]


@router.post("/", response_model=schemas.TenantOut)
def create_tenant_endpoint(data: schemas.TenantCreate, db: Session = Depends(get_db), _=Depends(require_platform_admin)):
    existing = crud.get_tenant_by_name(db, data.name)
    if existing:
        raise ResourceAlreadyExistsError('Tenant', 'name')
    tenant = crud.create_tenant(db, data.name)
    return tenant


@router.delete("/{tenant_name}", response_model=schemas.SuccessResponse)
def delete_tenant_endpoint(tenant_name: str, db: Session = Depends(get_db), _=Depends(require_platform_admin)):
    tenant = crud.get_tenant_by_name(db, tenant_name)
    if not tenant:
        raise ResourceNotFoundError('Tenant', tenant_name)
    crud.delete_tenant(db, tenant)
    return schemas.SuccessResponse(message="Tenant deleted successfully")
