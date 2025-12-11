# E-Commerce Assignment (FastAPI)

This repository is a multi-tenant e-commerce application built with FastAPI. It's a complete assignment implementation with clear structure, role-based access control, full test coverage, and a Keycloak integration scaffold.

## Overview

- **Multi-tenancy**: endpoints are namespaced per tenant: `/{tenant_name}/...`
- **Models**: Tenant, User, Product, Order, OrderItem. Users have roles: `platform_admin`, `tenant_admin`, `user`.
- **Authentication**: Keycloak integration via JWT Bearer token. Falls back to debug header for tests.
- **Favourite products**: users can mark/unmark products as favourite and list them.
- **Pagination**: implemented on product listing and order history.
- **Error handling**: comprehensive HTTP exception handling with descriptive messages.

## Quick Start (Dev)

### 1. Create and activate a virtualenv, install dependencies:

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### 2. Run the app:

```bash
uvicorn app.main:app --reload
```

- API docs: http://127.0.0.1:8000/docs
- OpenAPI spec: http://127.0.0.1:8000/openapi.json

### 3. Run tests:

```bash
PYTHONPATH=. pytest -q
```

## Authentication

### For Development/Testing

Send a debug header:

```bash
curl -H "X-Debug-User: alice|tenant_admin|brandx" http://localhost:8000/brandx/products/
```

Format: `X-Debug-User: username|role|tenantName` (tenantName can be empty for platform admins)

### For Production (Keycloak)

Set environment variables and send a Bearer token:

```bash
export KEYCLOAK_JWKS_URL='https://<keycloak-host>/auth/realms/<realm>/protocol/openid-connect/certs'
export KEYCLOAK_AUDIENCE='<client-id>'  # optional
export KEYCLOAK_ISSUER='https://<keycloak-host>/auth/realms/<realm>'
```

Then:

```bash
curl -H "Authorization: Bearer <your_jwt_token>" http://localhost:8000/tenants/
```

Token claims mapped to app:
- `preferred_username` or `sub` → username
- `realm_access.roles` → role (if contains `platform_admin` or `tenant_admin`)
- `tenant` or `tenant_name` → tenant association

See `ENDPOINTS.md` for all API routes and examples.

## Project Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app entry, router registration, startup init |
| `app/database.py` | SQLAlchemy engine, SessionLocal, Base |
| `app/models.py` | ORM models: Tenant, User, Product, Order, OrderItem |
| `app/schemas.py` | Pydantic request/response models |
| `app/crud.py` | Database helper functions (CRUD operations) |
| `app/auth.py` | Keycloak JWT verification, debug header parser, JWKS fetching |
| `app/dependencies.py` | FastAPI dependencies: get_db, get_current_user, role checks |
| `app/routers/tenant.py` | Tenant CRUD endpoints (create, delete) |
| `app/routers/admin.py` | Platform admin user management (list, create, update, delete tenant users) |
| `app/routers/products.py` | Product CRUD, search, filter, pagination (tenant-scoped) |
| `app/routers/orders.py` | Order creation, order history (with quantity validation) |
| `app/routers/users.py` | User signup, favourite product management |
| `tests/conftest.py` | Pytest fixtures (DB setup, TestClient) |
| `tests/test_basic.py` | Tests for signup, tenant, products, orders, favourites |
| `tests/test_admin.py` | Tests for admin user management |
| `requirements.txt` | Python dependencies |
| `README.md` | This file |
| `ENDPOINTS.md` | Complete API reference with examples |

## Features Implemented

1. ✅ User signup, login, and purchase flow
2. ✅ Platform admin: add/remove tenants, manage tenant users
3. ✅ Tenant admin: add/update/remove products, manage product quantity
4. ✅ Multi-tenancy with tenant isolation
5. ✅ Product categorization and filtering
6. ✅ Product search by name
7. ✅ Order creation with order items
8. ✅ Order quantity validation (must be <= available)
9. ✅ Order history per user
10. ✅ Favourite products (bonus feature)
11. ✅ Pagination on product listing
12. ✅ Error handling with descriptive messages
13. ✅ Keycloak integration scaffold with JWT verification
14. ✅ Role-based access control (platform_admin, tenant_admin, user)
15. ✅ Unit tests for all features

## Architecture & Design Decisions

### Multi-Tenancy
- Tenant context is extracted from the URL path (`/{tenant_name}/...`).
- Tenant isolation is enforced at the CRUD layer and in permission checks.
- Each tenant's products and users are strictly scoped.

### Role-Based Access Control
- **platform_admin**: can create/delete tenants and manage tenant users
- **tenant_admin**: can CRUD products for their tenant
- **user**: can browse products and create orders

### Authentication Flow
1. Client sends Authorization header with a JWT.
2. If `KEYCLOAK_JWKS_URL` is set, the app fetches the public key from Keycloak's JWKS endpoint.
3. Token is verified (signature, expiration, audience, issuer).
4. Claims are mapped to application User record.
5. Fallback: if no valid token or JWKS URL missing, parse debug header.

### Data Persistence
- SQLite for simplicity (can be replaced with PostgreSQL by changing `DATABASE_URL` in `app/database.py`).
- SQLAlchemy ORM for type-safe queries and relationships.

## Running Examples

### Step 1: Login to Get JWT Token
```bash
curl -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

This returns:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Step 2: Use Token in Requests

Export the token for convenience:
```bash
export TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Create Tenant (Platform Admin)
```bash
curl -X POST http://localhost:8000/tenants/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Nike"}'
```

### Signup New User
```bash
curl -X POST http://localhost:8000/users/signup \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "secure123"}'
```

### Create Product (Tenant Admin)
```bash
curl -X POST http://localhost:8000/Nike/products/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Air Max 90",
    "description": "Classic sneaker",
    "category": "shoes",
    "price": 120.0,
    "available_quantity": 50
  }'
```

### List Products (Public - No Auth)
```bash
curl http://localhost:8000/products/?category=shoes&search=air
```

### Create Order (User)
```bash
curl -X POST http://localhost:8000/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": 1, "quantity": 2}]}'
```

### Mark Product as Favourite (User)
```bash
curl -X POST http://localhost:8000/users/me/favourites/1 \
  -H "Authorization: Bearer $TOKEN"
```

### View Favourites (User)
```bash
curl http://localhost:8000/users/me/favourites \
  -H "Authorization: Bearer $TOKEN"
```

## Testing

Production testing requires:
1. **Integration Tests**: Set up a test Keycloak instance and generate real JWT tokens
2. **Unit Tests**: Mock the JWT verification in `app.auth.verify_jwt_token()`
3. **API Tests**: Use Postman or similar tools with actual Keycloak authentication

Example test setup with mocking:
```python
# In tests/conftest.py
@pytest.fixture
def mock_jwt_verification(monkeypatch):
    def mock_verify(token):
        return {
            "preferred_username": "testuser",
            "realm_access": {"roles": ["user"]},
            "tenant": None
        }
    monkeypatch.setattr("app.auth.verify_jwt_token", mock_verify)
```

## Notes

- **SQLAlchemy 2.0 Deprecation**: Current code uses SQLAlchemy 1.4 syntax. A future version can migrate to SQLAlchemy 2.0 if needed.
- **Database**: SQLite is used for simplicity. For production, switch to PostgreSQL:
  - Update `DATABASE_URL` in `app/database.py`
  - Install `psycopg2-binary`
- **Migrations**: Consider adding Alembic for database schema management.
- **Logging**: Add structured logging (e.g., python-json-logger) for production.
- **Rate Limiting**: Add FastAPI middleware for rate limiting if needed.

## Next Steps (Optional Enhancements)

- [ ] Add Alembic for DB migrations
- [ ] Add structured logging with python-json-logger
- [ ] Add rate limiting middleware
- [ ] Add more comprehensive test coverage (concurrency, edge cases)
- [ ] Add API versioning (`/api/v1/...`)
- [ ] Add webhooks for order status updates
- [ ] Add payment gateway integration
- [ ] Add email notifications
- [ ] Deploy to Kubernetes with Helm charts

## Best Practices Applied

- **DRY**: Database logic in `crud.py`, shared across routers
- **Separation of Concerns**: auth, dependencies, models, schemas, CRUD, routes
- **Type Safety**: Pydantic models for validation, SQLAlchemy ORM for persistence
- **Error Handling**: Comprehensive HTTPException usage with descriptive messages
- **Testing**: Unit tests for core features
- **Documentation**: README, ENDPOINTS.md, code comments

---

Created as a FastAPI assignment demonstrating multi-tenancy, Keycloak integration, and role-based access control.

