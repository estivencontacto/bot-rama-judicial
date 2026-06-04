import argparse

from backend.app.core.security import get_password_hash
from backend.app.database.session import SessionLocal
from backend.app.models import Organizacion, Usuario, UsuarioRol


def create_admin(email: str, password: str, nombre: str) -> None:
    db = SessionLocal()
    try:
        org = db.query(Organizacion).order_by(Organizacion.id.asc()).first()
        if not org:
            org = Organizacion(nombre="Organizacion Demo")
            db.add(org)
            db.commit()
            db.refresh(org)

        user = db.query(Usuario).filter(Usuario.email == email).first()
        if user:
            user.password_hash = get_password_hash(password)
            user.nombre = nombre
            user.is_admin = True
            user.is_active = True
            user.rol = UsuarioRol.admin
            user.organizacion_id = org.id
        else:
            db.add(
                Usuario(
                    organizacion_id=org.id,
                    email=email,
                    nombre=nombre,
                    password_hash=get_password_hash(password),
                    rol=UsuarioRol.admin,
                    is_admin=True,
                )
            )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--nombre", default="Administrador")
    args = parser.parse_args()
    create_admin(args.email, args.password, args.nombre)
