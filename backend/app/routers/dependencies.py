from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.security import decode_access_token
from backend.app.database.session import get_db
from backend.app.models import Usuario, UsuarioRol


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        subject = decode_access_token(token)
    except ValueError as exc:
        raise credentials_error from exc

    user = db.query(Usuario).filter(Usuario.email == subject, Usuario.is_active.is_(True)).first()
    if not user:
        raise credentials_error
    return user


def require_roles(*roles: UsuarioRol):
    def checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.rol not in roles and not current_user.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")
        return current_user

    return checker
