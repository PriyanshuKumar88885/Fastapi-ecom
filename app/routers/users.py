from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Any
from .. import crud, schemas, models
from ..dependencies import get_db, get_current_user
from ..exceptions import ResourceNotFoundError, ResourceAlreadyExistsError, AlreadyFavouritedError, NotFavouritedError
import os
import requests
from ..keycloak import keycloak_admin

router = APIRouter(prefix='/users', tags=['users'])

# --- Login endpoint ---
@router.post('/login')
def login(data: schemas.UserLogin):
    """
    Authenticate with Keycloak and return JWT token.
    Accepts: {"username": "...", "password": "..."}
    Returns: {"access_token": "...", "expires_in": ..., ...}
    """
    from ..config import settings
    
    token_url = f"{settings.KEYCLOAK_ADMIN_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
    payload = {
        "client_id": settings.KEYCLOAK_CLIENT_ID,
        "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
        "grant_type": "password",
        "username": data.username,
        "password": data.password
    }
    try:
        resp = requests.post(token_url, data=payload, timeout=5)
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail=resp.json().get('error_description', 'Invalid credentials'))
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post('/signup', response_model=schemas.UserOut)
def signup(data: schemas.UserSignup, db: Session = Depends(get_db)):
    """
    Public user signup. Always creates a regular user (role='user').
    For admin users, use the admin endpoint: POST /tenants/{tenant_name}/users/
    """
    # Check if user already exists
    user = crud.get_user_by_username(db, data.username)
    if user:
        raise ResourceAlreadyExistsError('User', 'username')

    # Force role to 'user' for public signup
    role = 'user'

    # Create user in Keycloak first
    try:
        keycloak_created = keycloak_admin.create_user(
            username=data.username,
            password=data.password,
            role=role  # Always 'user' for signup
        )
        if not keycloak_created:
            # User already exists in Keycloak, which is fine - continue with DB creation
            pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user in Keycloak: {str(e)}")

    # Create user in database (no tenant association for regular users)
    user = crud.create_user(db, username=data.username, role=role, tenant=None)
    return user


@router.post('/me/favourites/{product_id}')
def mark_favourite(product_id: int, db: Session = Depends(get_db), user: Any = Depends(get_current_user)):
    prod = crud.get_product(db, product_id)
    if not prod:
        raise ResourceNotFoundError('Product', str(product_id))
    crud.add_favourite(db, user, prod)
    return {'detail': 'added'}


@router.delete('/me/favourites/{product_id}')
def unmark_favourite(product_id: int, db: Session = Depends(get_db), user: Any = Depends(get_current_user)):
    prod = crud.get_product(db, product_id)
    if not prod:
        raise ResourceNotFoundError('Product', str(product_id))
    crud.remove_favourite(db, user, prod)
    return {'detail': 'removed'}


@router.get('/me/favourites', response_model=List[schemas.ProductOut])
def list_favourites(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), user: Any = Depends(get_current_user)):
    return crud.list_favourites(db, user, skip, limit)
