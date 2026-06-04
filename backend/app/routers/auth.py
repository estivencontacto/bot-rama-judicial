"""Endpoints de autenticacion y sesion.

Implementa login, refresh token rotativo, logout, perfil actual y cambio de
password con auditoria de eventos relevantes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    hash_token,
    verify_password,
)
from backend.app.core.settings import get_settings
from backend.app.database.session import get_db
from backend.app.models import RefreshToken, Usuario, utcnow
from backend.app.routers.dependencies import get_current_user
from backend.app.schemas.auth import (
    ChangePasswordRequest,
    CurrentUserResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from backend.app.services.audit_service import registrar_auditoria


router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(db: Session, user: Usuario) -> TokenResponse:
    """Emite access token corto y refresh token persistido como hash."""
    settings = get_settings()
    refresh_token = create_refresh_token()
    db.add(
        RefreshToken(
            usuario_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=utcnow() + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    db.commit()
    return TokenResponse(access_token=create_access_token(user.email), refresh_token=refresh_token)


def _is_locked(user: Usuario) -> bool:
    """Indica si el usuario esta bloqueado por intentos fallidos."""
    return bool(user.locked_until and _as_aware(user.locked_until) > utcnow())


def _as_aware(value: datetime) -> datetime:
    """Normaliza datetimes naive a UTC para comparaciones seguras."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Autentica usuario, aplica bloqueo por fallos y registra auditoria."""
    settings = get_settings()
    user = db.query(Usuario).filter(Usuario.email == payload.email).first()

    if not user:
        registrar_auditoria(db, None, "auth.login_fallido", f"Login fallido para email no registrado: {payload.email}", "usuario")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas")

    if _is_locked(user):
        registrar_auditoria(db, user, "auth.login_bloqueado", "Intento de login con usuario bloqueado", "usuario", str(user.id))
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Usuario bloqueado temporalmente")

    if not verify_password(payload.password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.max_failed_login_attempts:
            user.locked_until = utcnow() + timedelta(minutes=settings.login_lock_minutes)
        db.commit()
        registrar_auditoria(db, user, "auth.login_fallido", "Login fallido por password incorrecto", "usuario", str(user.id))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas")

    if not user.is_active:
        registrar_auditoria(db, user, "auth.login_inactivo", "Intento de login con usuario inactivo", "usuario", str(user.id))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = utcnow()
    db.commit()
    registrar_auditoria(db, user, "auth.login_exitoso", "Login exitoso", "usuario", str(user.id))
    return _issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Rota refresh token y entrega una nueva pareja de tokens."""
    token_hash = hash_token(payload.refresh_token)
    item = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if not item or item.revoked_at or _as_aware(item.expires_at) <= utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalido")

    user = db.query(Usuario).filter(Usuario.id == item.usuario_id, Usuario.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario invalido")

    item.revoked_at = utcnow()
    db.commit()
    return _issue_tokens(db, user)


@router.post("/logout")
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> dict:
    """Revoca el refresh token activo."""
    token_hash = hash_token(payload.refresh_token)
    item = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if item and not item.revoked_at:
        item.revoked_at = utcnow()
        db.commit()
    return {"ok": True}


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: Usuario = Depends(get_current_user)) -> CurrentUserResponse:
    """Devuelve informacion minima del usuario autenticado."""
    return CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        nombre=current_user.nombre,
        rol=current_user.rol.value,
        organizacion_id=current_user.organizacion_id,
        organizacion=current_user.organizacion.nombre if current_user.organizacion else None,
    )


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Actualiza password y revoca refresh tokens existentes."""
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="La nueva password debe tener minimo 8 caracteres")
    if not verify_password(payload.current_password, current_user.password_hash):
        registrar_auditoria(db, current_user, "auth.password_fallido", "Intento fallido de cambio de password", "usuario", str(current_user.id))
        raise HTTPException(status_code=401, detail="Password actual incorrecta")

    current_user.password_hash = get_password_hash(payload.new_password)
    current_user.password_changed_at = utcnow()
    db.query(RefreshToken).filter(RefreshToken.usuario_id == current_user.id, RefreshToken.revoked_at.is_(None)).update(
        {"revoked_at": utcnow()}
    )
    db.commit()
    registrar_auditoria(db, current_user, "auth.password_actualizado", "Password actualizada", "usuario", str(current_user.id))
    return {"ok": True}
