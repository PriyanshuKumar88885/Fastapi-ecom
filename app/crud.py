from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
from .exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    PermissionDeniedError,
    InvalidOperationError
)

# ============ TENANT OPERATIONS ============

def get_tenant_by_name(db: Session, name: str):
    return db.query(models.Tenant).filter(func.lower(models.Tenant.name) == name.lower()).first()

def get_tenant_by_id(db: Session, tenant_id: int):
    return db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()

def create_tenant(db: Session, name: str):
    existing = get_tenant_by_name(db, name)
    if existing:
        raise ResourceAlreadyExistsError('Tenant', 'name')
    tenant = models.Tenant(name=name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant

def delete_tenant(db: Session, tenant: models.Tenant):
    """Delete tenant. Users will be dissociated (tenant_id set to NULL), products deleted."""
    # Manually dissociate users from tenant before deletion
    # This ensures tenant_id is set to NULL explicitly
    db.query(models.User).filter(models.User.tenant_id == tenant.id).update(
        {models.User.tenant_id: None}, synchronize_session='fetch'
    )
    db.delete(tenant)
    db.commit()

def list_tenants(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Tenant).offset(skip).limit(limit).all()

# ============ USER OPERATIONS ============

def create_user(db: Session, username: str, role: str = 'user', tenant: models.Tenant = None):
    existing = get_user_by_username(db, username)
    if existing:
        raise ResourceAlreadyExistsError('User', 'username')
    user = models.User(username=username, role=role, tenant=tenant)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def convert_tenant_user_to_normal(db: Session, user: models.User):
    """Convert a tenant user to normal user: clear tenant_id, remove tenant-specific favourites."""
    if user.tenant_id:
        tenant_id = user.tenant_id
        # Remove favourites for products belonging to this tenant
        tenant_product_ids = db.query(models.Product.id).filter(
            models.Product.tenant_id == tenant_id
        ).all()
        tenant_product_ids = [p[0] for p in tenant_product_ids]
        
        if tenant_product_ids:
            # Remove from favourites
            db.execute(
                models.user_favourites.delete().where(
                    models.user_favourites.c.user_id == user.id
                ).where(
                    models.user_favourites.c.product_id.in_(tenant_product_ids)
                )
            )
        
        # Clear tenant association
        user.tenant_id = None
        user.role = 'user'  # Downgrade role
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# ============ PRODUCT OPERATIONS ============

def create_product(db: Session, tenant=None, data=None, **kwargs):
    """Create a product. Can be called with (db, tenant, data) or (db, tenant_id=..., name=..., etc.)"""
    # Support both styles: with schema object or with direct kwargs
    if data is not None:
        # Standard API call with schema
        tenant_obj = tenant
        tenant_id = tenant.id if tenant else kwargs.get('tenant_id')
        product_data = {
            'name': data.name,
            'description': data.description,
            'category': data.category,
            'price': data.price,
            'available_quantity': data.available_quantity,
        }
    else:
        # Direct call with kwargs (for tests)
        tenant_id = kwargs.get('tenant_id')
        if tenant_id:
            tenant_obj = get_tenant_by_id(db, tenant_id)
        elif tenant:
            tenant_obj = tenant
            tenant_id = tenant.id
        else:
            raise ValueError("Must provide tenant or tenant_id")
        
        product_data = {
            'name': kwargs.get('name'),
            'description': kwargs.get('description'),
            'category': kwargs.get('category'),
            'price': kwargs.get('price'),
            'available_quantity': kwargs.get('available_quantity'),
        }
    
    # Check for duplicate product name within tenant (enforced by DB constraint too)
    existing = db.query(models.Product).filter(
        models.Product.tenant_id == tenant_id,
        func.lower(models.Product.name) == product_data['name'].lower()
    ).first()
    if existing:
        raise ResourceAlreadyExistsError('Product', 'name')
    
    product = models.Product(
        name=product_data['name'],
        description=product_data['description'],
        category=product_data['category'],
        price=product_data['price'],
        available_quantity=product_data['available_quantity'],
        tenant_id=tenant_id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def list_all_products(db: Session, skip: int = 0, limit: int = 10, category: str = None, q: str = None):
    """List ALL products across all tenants (for platform admin or public catalog)."""
    qy = db.query(models.Product)
    if category:
        qy = qy.filter(models.Product.category == category)
    if q:
        qy = qy.filter(models.Product.name.ilike(f"%{q}%"))
    return qy.offset(skip).limit(limit).all()

def list_products(db: Session, tenant: models.Tenant, skip: int = 0, limit: int = 10, category: str = None, q: str = None):
    """List products for a specific tenant (tenant-scoped)."""
    qy = db.query(models.Product).filter(models.Product.tenant == tenant)
    if category:
        qy = qy.filter(models.Product.category == category)
    if q:
        qy = qy.filter(models.Product.name.ilike(f"%{q}%"))
    return qy.offset(skip).limit(limit).all()

def update_product(db: Session, product_id: int, updates: dict, user: models.User):
    """Update product. Enforce: only tenant admin of that tenant or platform admin can update."""
    product = get_product(db, product_id)
    if product is None:
        raise ResourceNotFoundError('Product', product_id)
    
    if user.role != 'platform_admin':
        if user.role != 'tenant_admin' or user.tenant_id != product.tenant_id:
            raise PermissionDeniedError('Only tenant admin can update products')
    
    for k, v in updates.items():
        setattr(product, k, v)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

def delete_product(db: Session, product_id: int, user: models.User):
    """Delete product. Enforce: only tenant admin of that tenant or platform admin."""
    product = get_product(db, product_id)
    if product is None:
        raise ResourceNotFoundError('Product', product_id)
    
    if user.role != 'platform_admin':
        if user.role != 'tenant_admin' or user.tenant_id != product.tenant_id:
            raise PermissionDeniedError('Only tenant admin can delete products')
    db.delete(product)
    db.commit()

# ============ FAVOURITE OPERATIONS ============

def add_favourite(db: Session, user: models.User, product: models.Product):
    """Add product to user favourites. All authenticated users can favourite any product."""
    # Check if already favourited
    if product in user.favourites:
        raise ResourceAlreadyExistsError('Favourite', 'product')
    
    # All users can favourite products from any tenant (tenant assignment only restricts management)
    
    user.favourites.append(product)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def remove_favourite(db: Session, user: models.User, product: models.Product):
    """Remove product from user favourites."""
    if product not in user.favourites:
        raise ResourceNotFoundError('Favourite', product.id)
    user.favourites.remove(product)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def list_favourites(db: Session, user: models.User, skip: int = 0, limit: int = 10):
    """List user's favourite products."""
    return user.favourites[skip:skip+limit]

# ============ ORDER OPERATIONS ============

def create_order(db: Session, user: models.User, items_data, tenant_context: models.Tenant = None):
    """Create order. All authenticated users can order from any tenant."""
    # items_data: list of {'product_id': int, 'quantity': int}
    
    if not items_data:
        raise InvalidOperationError('Order must contain at least one item')
    
    order = models.Order(user=user, total_quantity=0, total_amount=0.0)
    db.add(order)
    
    total_q = 0
    total_amount = 0.0
    
    for it in items_data:
        # Validate quantity
        quantity = it.get('quantity', 0)
        if quantity <= 0:
            raise ValueError(f"Invalid quantity: {quantity}. Quantity must be positive.")
        
        prod = get_product(db, it['product_id'])
        if prod is None:
            raise ResourceNotFoundError('Product', it['product_id'])
        
        # All users can order products from any tenant (tenant assignment only restricts management)
        
        if prod.available_quantity < it['quantity']:
            raise ValueError(f"Insufficient stock for product {prod.name}. Available: {prod.available_quantity}, requested: {it['quantity']}")
        
        unit_price = prod.price
        oi = models.OrderItem(order=order, product=prod, quantity=it['quantity'], unit_price=unit_price)
        db.add(oi)
        
        # Reduce stock
        prod.available_quantity -= it['quantity']
        db.add(prod)
        
        total_q += it['quantity']
        total_amount += unit_price * it['quantity']
    
    order.total_quantity = total_q
    order.total_amount = total_amount
    db.commit()
    db.refresh(order)
    return order

def list_orders_for_user(db: Session, user: models.User, skip: int = 0, limit: int = 10):
    query = db.query(models.Order).filter(models.Order.user == user)
    return query.offset(skip).limit(limit).all()

def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()

# ============ TENANT USER MANAGEMENT ============

def list_users_for_tenant(db: Session, tenant_id: int, skip: int = 0, limit: int = 10):
    return db.query(models.User).filter(models.User.tenant_id == tenant_id).offset(skip).limit(limit).all()
