"""Utilidades criptograficas y JWT.

Este modulo concentra hashing de passwords, emision de tokens y validacion de
access tokens para que los routers no manejen detalles criptograficos.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.app.core.settings import get_settings


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Valida una password plana contra el hash almacenado."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Genera un hash seguro para persistir passwords."""
    return pwd_context.hash(password)


def create_access_token(subject: str) -> str:
    """Crea un JWT corto con el email del usuario como sujeto."""
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token() -> str:
    """Genera un token opaco para renovar sesiones sin reingresar password."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Guarda refresh tokens como hash para no persistir secretos en texto plano."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_access_token(token: str) -> str:
    """Decodifica el JWT y devuelve el sujeto autenticado."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        subject = payload.get("sub")
    except JWTError as exc:
        raise ValueError("Token invalido o expirado") from exc

    if not subject:
        raise ValueError("Token sin sujeto")
    return str(subject)
