from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.models import Usuario
from backend.app.routers.dependencies import get_current_user
from backend.app.schemas.auth import CurrentUserResponse


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=CurrentUserResponse)
def get_me(current_user: Usuario = Depends(get_current_user)) -> CurrentUserResponse:
    """Alias 2.0 para consultar el perfil autenticado."""
    return CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        nombre=current_user.nombre,
        rol=current_user.rol.value,
        organizacion_id=current_user.organizacion_id,
        organizacion=current_user.organizacion.nombre if current_user.organizacion else None,
    )
