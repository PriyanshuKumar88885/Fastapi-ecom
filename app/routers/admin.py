from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, List
from .. import crud, schemas, models
from ..dependencies import get_db, require_platform_admin, get_tenant_by_path
from ..exceptions import ResourceAlreadyExistsError, ResourceNotFoundError
from ..config import settings
from ..keycloak import keycloak_admin
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/tenants/{tenant_name}/users', tags=['tenant-users-admin'])


@router.get('/', response_model=List[schemas.UserOut])
def list_tenant_users(
    tenant_name: str,
    skip: int = Query(settings.DEFAULT_SKIP, ge=0),
    limit: int = Query(settings.DEFAULT_LIMIT, ge=1, le=settings.MAX_LIMIT),
    db: Session = Depends(get_db),
    _=Depends(require_platform_admin),
    tenant: Any = Depends(get_tenant_by_path)
):
    return crud.list_users_for_tenant(db, tenant.id, skip=skip, limit=limit)


@router.post('/', response_model=schemas.UserOut)
def create_tenant_user(tenant_name: str, data: schemas.UserCreate, db: Session = Depends(get_db), _=Depends(require_platform_admin), tenant: Any = Depends(get_tenant_by_path)):
    existing = crud.get_user_by_username(db, data.username)
    if existing:
        raise ResourceAlreadyExistsError('User', 'username')
    
    default_password = getattr(data, 'password', None)
    if not default_password:
        raise HTTPException(status_code=400, detail="Password is required for user creation")
    try:
        keycloak_created = keycloak_admin.create_user(
            username=data.username,
            password=default_password,
            role=data.role
        )
        if not keycloak_created:
            logger.info(f"User {data.username} already exists in Keycloak, syncing to database")
    except Exception as e:
        logger.error(f"Failed to create user in Keycloak: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create user in Keycloak: {str(e)}")
    
    user = crud.create_user(db, username=data.username, role=data.role, tenant=tenant)
    return user


@router.put('/{user_id}', response_model=schemas.UserOut)
def update_tenant_user(tenant_name: str, user_id: int, data: schemas.UserCreate, db: Session = Depends(get_db), _=Depends(require_platform_admin), tenant: Any = Depends(get_tenant_by_path)):
    user = db.query(models.User).filter(models.User.id == user_id, models.User.tenant_id == tenant.id).first()
    if not user:
        raise ResourceNotFoundError('User', str(user_id))
    
    if user.role != data.role:
        try:
            kc_user_id = keycloak_admin._get_user_id(user.username)
            if kc_user_id:
                keycloak_admin.update_user_role(kc_user_id, user.role, data.role)
                logger.info(f"Updated role for {user.username} in Keycloak from {user.role} to {data.role}")
        except Exception as e:
            logger.error(f"Failed to update role in Keycloak: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update role in Keycloak: {str(e)}")
    
    user.role = data.role
    
    if data.role in ['platform_admin', 'user']:
        user.tenant_id = None
        logger.info(f"Removed tenant association for {user.username} - changed to {data.role}")
    elif data.role == 'tenant_admin':
        user.tenant_id = tenant.id
        logger.info(f"Set tenant association for {user.username} to {tenant.name} (ID: {tenant.id})")
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post('/assign', response_model=schemas.UserOut)
def assign_user_to_tenant(tenant_name: str, data: schemas.UserCreate, db: Session = Depends(get_db), _=Depends(require_platform_admin), tenant: Any = Depends(get_tenant_by_path)):
    user = crud.get_user_by_username(db, data.username)
    if not user:
        raise ResourceNotFoundError('User', data.username)
    
    if user.role != data.role:
        try:
            kc_user_id = keycloak_admin._get_user_id(user.username)
            if kc_user_id:
                keycloak_admin.update_user_role(kc_user_id, user.role, data.role)
                logger.info(f"Updated role for {user.username} in Keycloak from {user.role} to {data.role}")
        except Exception as e:
            logger.error(f"Failed to update role in Keycloak: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update role in Keycloak: {str(e)}")
    
    user.role = data.role
    
    if data.role == 'tenant_admin':
        user.tenant_id = tenant.id
        logger.info(f"Assigned {user.username} as tenant_admin for tenant {tenant.name}")
    else:
        user.tenant_id = None
        logger.info(f"Changed {user.username} to {data.role}, removed tenant association")
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete('/{user_id}')
def delete_tenant_user(tenant_name: str, user_id: int, db: Session = Depends(get_db), _=Depends(require_platform_admin), tenant: Any = Depends(get_tenant_by_path)):
    user = db.query(models.User).filter(models.User.id == user_id, models.User.tenant_id == tenant.id).first()
    if not user:
        raise ResourceNotFoundError('User', str(user_id))

    try:
        keycloak_admin.delete_user(user.username)
        logger.info(f"Deleted user {user.username} from Keycloak")
    except Exception as e:
        logger.warning(f"Failed to delete user from Keycloak (may not exist): {e}")
    
    db.delete(user)
    db.commit()
    return {'detail': 'deleted'}
