from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Float,
    Table,
    UniqueConstraint,
    Index,
    DateTime,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


# Association table for user favourites
# - ondelete=CASCADE for product_id so when a product is removed, favourites are cleaned up
# - unique constraint to prevent duplicate favourites
user_favourites = Table(
    'user_favourites',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    Column('product_id', Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
    UniqueConstraint('user_id', 'product_id', name='uq_user_product_favourite'),
)


class Tenant(Base):
    __tablename__ = 'tenants'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Important: when a tenant is deleted, we want to keep users but dissociate them
    # so users become normal users of the platform. Therefore user's tenant_id uses
    # ondelete='SET NULL' and the relationship is passive for deletes.
    users = relationship('User', back_populates='tenant', passive_deletes=True)

    # Products belong to tenant. When tenant is deleted, tenant's products should be removed.
    products = relationship('Product', back_populates='tenant', cascade='all, delete-orphan')


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)

    # Role stored as string for simple permission checks
    # Valid values: 'user', 'tenant_admin', 'platform_admin'
    role = Column(String, default='user', nullable=False)

    # tenant_id when set means the user is operating within that tenant context. We set
    # ondelete='SET NULL' so deleting a tenant does not delete users but clears the link.
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='SET NULL'), nullable=True)
    tenant = relationship('Tenant', back_populates='users')

    favourites = relationship('Product', secondary=user_favourites, back_populates='favourited_by')
    orders = relationship('Order', back_populates='user', cascade='all, delete-orphan')


class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, index=True, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    available_quantity = Column(Integer, nullable=False, default=0)

    # product is owned by a tenant; when tenant is deleted, product should be deleted too.
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    tenant = relationship('Tenant', back_populates='products')

    favourited_by = relationship('User', secondary=user_favourites, back_populates='favourites')

    # When a product is deleted, order_items should be deleted as well to avoid orphaned order items.
    order_items = relationship('OrderItem', back_populates='product', cascade='all, delete-orphan')

    __table_args__ = (
        # Prevent duplicate product names within the same tenant
        UniqueConstraint('tenant_id', 'name', name='uq_tenant_product_name'),
    )


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, index=True)

    # When a user is deleted, their orders are deleted too
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    total_quantity = Column(Integer, nullable=False, default=0)
    total_amount = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='orders')
    items = relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')


class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)

    # When product is deleted, order_items are removed (historical orders will lose product link)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)

    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    order = relationship('Order', back_populates='items')
    product = relationship('Product', back_populates='order_items')
