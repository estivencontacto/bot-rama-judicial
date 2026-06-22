from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Cliente, Radicado, Usuario, UsuarioRol
from backend.app.routers.dependencies import get_current_user, require_roles
from backend.app.schemas.clientes import ClienteCreate, ClienteRead


router = APIRouter(prefix="/clientes", tags=["clientes"])


def _normalizar_nombre(nombre: str) -> str:
    valor = " ".join(nombre.strip().split())
    if not valor:
        raise HTTPException(status_code=400, detail="El nombre del cliente es obligatorio")
    return valor


def ensure_cliente(db: Session, usuario: Usuario, nombre: str | None) -> Cliente | None:
    """Crea el cliente/carpeta si no existe y retorna la entidad."""
    if not nombre:
        return None
    nombre_limpio = _normalizar_nombre(nombre)
    item = (
        db.query(Cliente)
        .filter(Cliente.organizacion_id == usuario.organizacion_id, Cliente.nombre == nombre_limpio)
        .first()
    )
    if item:
        return item
    item = Cliente(organizacion_id=usuario.organizacion_id, nombre=nombre_limpio)
    db.add(item)
    db.flush()
    return item


@router.get("", response_model=list[ClienteRead])
def list_clientes(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Cliente]:
    clientes = (
        db.query(Cliente)
        .filter(Cliente.organizacion_id == current_user.organizacion_id)
        .order_by(Cliente.nombre.asc())
        .all()
    )
    nombres_guardados = {item.nombre for item in clientes}
    etiquetas = (
        db.query(Radicado.etiqueta)
        .filter(Radicado.organizacion_id == current_user.organizacion_id, Radicado.etiqueta.isnot(None))
        .distinct()
        .all()
    )
    for row in etiquetas:
        if row.etiqueta and row.etiqueta not in nombres_guardados:
            item = Cliente(organizacion_id=current_user.organizacion_id, nombre=row.etiqueta)
            db.add(item)
            clientes.append(item)
            nombres_guardados.add(row.etiqueta)
    if etiquetas:
        db.commit()
    return sorted(clientes, key=lambda item: item.nombre.lower())


@router.post("", response_model=ClienteRead)
def create_cliente(
    payload: ClienteCreate,
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin, UsuarioRol.operador)),
    db: Session = Depends(get_db),
) -> Cliente:
    nombre = _normalizar_nombre(payload.nombre)
    existing = (
        db.query(Cliente)
        .filter(Cliente.organizacion_id == current_user.organizacion_id, Cliente.nombre == nombre)
        .first()
    )
    if existing:
        if payload.descripcion is not None:
            existing.descripcion = payload.descripcion
        existing.activo = True
        db.commit()
        db.refresh(existing)
        return existing
    item = Cliente(
        organizacion_id=current_user.organizacion_id,
        nombre=nombre,
        descripcion=payload.descripcion,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{cliente_id}")
def delete_cliente(
    cliente_id: int,
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin, UsuarioRol.operador)),
    db: Session = Depends(get_db),
) -> dict:
    item = (
        db.query(Cliente)
        .filter(Cliente.id == cliente_id, Cliente.organizacion_id == current_user.organizacion_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db.delete(item)
    db.commit()
    return {"ok": True}
