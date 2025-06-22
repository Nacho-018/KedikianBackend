from app.db.models import Usuario
from app.schemas.schemas import UsuarioSchema, UserOut, UsuarioCreate
from sqlalchemy.orm import Session
from typing import List, Optional

# Servicio para operaciones de Usuario

def get_usuarios(db: Session) -> List[Usuario]:
    return db.query(Usuario).all()

def get_usuario(db: Session, usuario_id: int) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()

def create_usuario(db: Session, usuario: UsuarioCreate) -> UserOut:
    # Convertir la lista de roles a string para guardar en la base de datos
    roles_str = ','.join(usuario.roles)
    nuevo_usuario = Usuario(
        nombre=usuario.nombre,
        email=usuario.email,
        hash_contrasena=usuario.hash_contrasena,
        estado=usuario.estado,
        roles=roles_str,
        fecha_creacion=usuario.fecha_creacion
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    # Convertir roles de string a lista para la salida
    return UserOut(
        id=nuevo_usuario.id,
        nombre=nuevo_usuario.nombre,
        email=nuevo_usuario.email,
        estado=nuevo_usuario.estado,
        roles=nuevo_usuario.roles.split(',') if nuevo_usuario.roles else [],
        fecha_creacion=nuevo_usuario.fecha_creacion
    )

def update_usuario(db: Session, usuario_id: int, usuario: UsuarioSchema) -> Optional[Usuario]:
    existing_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if existing_usuario:
        for field, value in usuario.model_dump().items():
            setattr(existing_usuario, field, value)
        db.commit()
        db.refresh(existing_usuario)
        return existing_usuario
    return None

def delete_usuario(db: Session, usuario_id: int) -> bool:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario:
        db.delete(usuario)
        db.commit()
        return True
    return False
