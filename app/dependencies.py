from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Any, Optional
from pydantic import BaseModel
from .database import SessionLocal
from . import crud, models
from .auth import parse_authorization_header, verify_jwt_token
from .config import settings
from .exceptions import UnauthorizedError, InvalidTokenError, PermissionDeniedError


class ProductFilterParams(BaseModel):
    """Query parameters for product listing."""
    skip: int = 0
    limit: int = 10
    category: Optional[str] = None
    search: Optional[str] = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_tenant_by_path(tenant_name: str, db: Session = Depends(get_db)):
    tenant = crud.get_tenant_by_name(db, tenant_name)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Resolve the current user from Authorization header with JWT token.

    Production authentication using Keycloak JWT tokens only.
    Maps roles from token claims and sets tenant if present in token.
    """
    token = parse_authorization_header(authorization)
    if not token:
        raise UnauthorizedError("Missing Authorization header. Provide 'Authorization: Bearer <token>'")

    claims = verify_jwt_token(token)
    if not claims:
        raise InvalidTokenError("Invalid or expired JWT token")

    username = claims.get('preferred_username') or claims.get('sub')
    if not username:
        raise InvalidTokenError("Token missing username/sub claim")

    # Determine role from token claims (realm_access.roles) or custom 'role' claim
    role = 'user'
    if 'realm_access' in claims and isinstance(claims['realm_access'], dict):
        roles = claims['realm_access'].get('roles', [])
        if 'platform_admin' in roles:
            role = 'platform_admin'
        elif 'tenant_admin' in roles:
            role = 'tenant_admin'
    if 'role' in claims:
        role = claims.get('role')

    tenant_name = claims.get('tenant') or claims.get('tenant_name')
    tenant = None
    if tenant_name:
        tenant = crud.get_tenant_by_name(db, tenant_name)

    # Get or create user. Do NOT grant elevated permissions based solely on tenant_id.
    user = crud.get_user_by_username(db, username)
    if not user:
        user = crud.create_user(db, username=username, role=role, tenant=tenant)
    else:
        updated = False
        # Only update role if different (token is source of truth for role)
        if user.role != role:
            user.role = role
            updated = True
        # Update tenant only when token explicitly contains tenant info
        if tenant is not None and (user.tenant is None or user.tenant.id != tenant.id):
            user.tenant = tenant
            updated = True
        if updated:
            db.add(user)
            db.commit()
            db.refresh(user)

    return user


def require_platform_admin(user: Any = Depends(get_current_user)):
    if user.role != 'platform_admin':
        raise PermissionDeniedError('Platform admin required')
    return user


def require_tenant_admin(tenant: models.Tenant = Depends(get_tenant_by_path), user: Any = Depends(get_current_user)):
    # platform admins bypass tenant checks
    if user.role == 'platform_admin':
        return user

    if user.role != 'tenant_admin':
        raise PermissionDeniedError('Tenant admin required')

    if user.tenant is None or user.tenant.id != tenant.id:
        raise PermissionDeniedError('Tenant admin for this tenant required')

    return user


def require_tenant_user(tenant: models.Tenant = Depends(get_tenant_by_path), user: Any = Depends(get_current_user)):
    """Require the user to be a tenant-scoped user (tenant_admin or user) for the given tenant."""
    # platform admin can access any tenant
    if user.role == 'platform_admin':
        return user

    if user.tenant is None or user.tenant.id != tenant.id:
        raise PermissionDeniedError('Access to this tenant is forbidden')

    # Allow tenant_admin and normal users within the tenant
    if user.role not in ('tenant_admin', 'user'):
        raise PermissionDeniedError('Tenant user role required')

    return user
