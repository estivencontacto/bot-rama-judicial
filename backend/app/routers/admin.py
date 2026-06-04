from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.security import get_password_hash
from backend.app.database.session import get_db
from backend.app.models import AuditoriaEvento, Organizacion, Usuario, UsuarioRol
from backend.app.routers.dependencies import require_roles
from backend.app.schemas.admin import OrganizacionRead, OrganizacionUpdate, UsuarioCreate, UsuarioRead, UsuarioUpdate
from backend.app.schemas.auditoria import AuditoriaRead
from backend.app.services.audit_service import registrar_auditoria


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/organizacion", response_model=OrganizacionRead)
def get_organizacion(
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin)),
    db: Session = Depends(get_db),
) -> Organizacion:
    if not current_user.organizacion_id:
        raise HTTPException(status_code=400, detail="Usuario sin organizacion asignada")
    organizacion = db.query(Organizacion).filter(Organizacion.id == current_user.organizacion_id).first()
    if not organizacion:
        raise HTTPException(status_code=404, detail="Organizacion no encontrada")
    return organizacion


@router.put("/organizacion", response_model=OrganizacionRead)
def update_organizacion(
    payload: OrganizacionUpdate,
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin)),
    db: Session = Depends(get_db),
) -> Organizacion:
    organizacion = db.query(Organizacion).filter(Organizacion.id == current_user.organizacion_id).first()
    if not organizacion:
        raise HTTPException(status_code=404, detail="Organizacion no encontrada")

    organizacion.nombre = payload.nombre
    organizacion.limite_radicados = payload.limite_radicados
    organizacion.activa = payload.activa
    db.commit()
    db.refresh(organizacion)
    registrar_auditoria(db, current_user, "organizacion.actualizada", "Organizacion actualizada", "organizacion", str(organizacion.id))
    return organizacion


@router.get("/usuarios", response_model=list[UsuarioRead])
def list_usuarios(
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin)),
    db: Session = Depends(get_db),
) -> list[Usuario]:
    return (
        db.query(Usuario)
        .filter(Usuario.organizacion_id == current_user.organizacion_id)
        .order_by(Usuario.created_at.desc())
        .all()
    )


@router.post("/usuarios", response_model=UsuarioRead)
def create_usuario(
    payload: UsuarioCreate,
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin)),
    db: Session = Depends(get_db),
) -> Usuario:
    exists = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=409, detail="Email ya registrado")

    try:
        rol = UsuarioRol(payload.rol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Rol invalido") from exc

    usuario = Usuario(
        organizacion_id=current_user.organizacion_id,
        email=payload.email,
        nombre=payload.nombre,
        password_hash=get_password_hash(payload.password),
        rol=rol,
        is_admin=rol == UsuarioRol.admin,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    registrar_auditoria(db, current_user, "usuario.creado", f"Usuario creado: {usuario.email}", "usuario", str(usuario.id))
    return usuario


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioRead)
def update_usuario(
    usuario_id: int,
    payload: UsuarioUpdate,
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin)),
    db: Session = Depends(get_db),
) -> Usuario:
    usuario = (
        db.query(Usuario)
        .filter(Usuario.id == usuario_id, Usuario.organizacion_id == current_user.organizacion_id)
        .first()
    )
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if payload.nombre is not None:
        usuario.nombre = payload.nombre
    if payload.rol is not None:
        try:
            usuario.rol = UsuarioRol(payload.rol)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Rol invalido") from exc
        usuario.is_admin = usuario.rol == UsuarioRol.admin
    if payload.is_active is not None:
        usuario.is_active = payload.is_active

    db.commit()
    db.refresh(usuario)
    registrar_auditoria(db, current_user, "usuario.actualizado", f"Usuario actualizado: {usuario.email}", "usuario", str(usuario.id))
    return usuario


@router.get("/auditoria", response_model=list[AuditoriaRead])
def list_auditoria(
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin)),
    db: Session = Depends(get_db),
) -> list[AuditoriaEvento]:
    return (
        db.query(AuditoriaEvento)
        .filter(AuditoriaEvento.organizacion_id == current_user.organizacion_id)
        .order_by(AuditoriaEvento.created_at.desc())
        .limit(100)
        .all()
    )
