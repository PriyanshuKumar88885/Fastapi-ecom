from fastapi import FastAPI
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from starlette.middleware.base import BaseHTTPMiddleware
import time
from .database import init_db
from .config import settings
from .exceptions import BaseAPIException
from .logging_config import get_logger
from .routers import tenant as tenant_router
from .routers import products as products_router
from .routers import orders as orders_router
from .routers import users as users_router
from .routers import admin as admin_router

logger = get_logger(__name__)

security = HTTPBearer()

class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f'{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s'
        )
        return response


app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    openapi_url=settings.OPENAPI_URL,
)

# Add Bearer JWT security scheme to the OpenAPI schema so the Swagger UI shows the Authorize button.
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description=settings.API_DESCRIPTION,
        routes=app.routes,
    )
    components = openapi_schema.get("components", {})
    security_schemes = components.get("securitySchemes", {})
    # Define a standard HTTP bearer (JWT) security scheme
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    components["securitySchemes"] = security_schemes
    openapi_schema["components"] = components
    # Apply security requirement globally (optional): every path will show lock icon
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)
app.add_middleware(RequestLoggingMiddleware)


# Global exception handlers
@app.exception_handler(BaseAPIException)
async def api_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={'detail': exc.message}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f'Unhandled exception: {str(exc)}', exc_info=True)
    return JSONResponse(
        status_code=500,
        content={'detail': 'Internal server error'}
    ) 


@app.on_event('startup')
def on_startup():
    logger.info(f'Starting application in {settings.ENV} mode')
    init_db()
    logger.info('Database initialized')


app.include_router(tenant_router.router, prefix=settings.API_PREFIX)
app.include_router(products_router.router, prefix=settings.API_PREFIX)
app.include_router(products_router.global_router, prefix=settings.API_PREFIX)
app.include_router(orders_router.router, prefix=settings.API_PREFIX)
app.include_router(users_router.router, prefix=settings.API_PREFIX)
app.include_router(admin_router.router, prefix=settings.API_PREFIX)


