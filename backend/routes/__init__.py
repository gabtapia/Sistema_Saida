from routes.auth import router as auth_router
from routes.motivos import router as motivos_router
from routes.saidas import router as saidas_router

__all__ = ["auth_router", "motivos_router", "saidas_router"]