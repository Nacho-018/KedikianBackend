from app.db.models import Usuario
from app.schemas.schemas import UsuarioSchema, UsuarioOut, UsuarioCreate
from sqlalchemy.orm import Session
from typing import List, Optional

# Servicio para operaciones de Usuario

def get_usuarios(db: Session) -> List[UsuarioOut]:
    usuarios = db.query(Usuario).all()
    return [UsuarioOut(
        id=u.id,
        nombre=u.nombre,
        email=u.email,
        estado=u.estado,
        roles=u.roles.split(',') if u.roles else [],
        fecha_creacion=u.fecha_creacion
    ) for u in usuarios]

def get_usuario(db: Session, usuario_id: int) -> Optional[UsuarioOut]:
    u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if u:
        return UsuarioOut(
            id=u.id,
            nombre=u.nombre,
            email=u.email,
            estado=u.estado,
            roles=u.roles.split(',') if u.roles else [],
            fecha_creacion=u.fecha_creacion
        )
    return None

def create_usuario(db: Session, usuario: UsuarioCreate) -> UsuarioOut:
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
    return UsuarioOut(
        id=nuevo_usuario.id,
        nombre=nuevo_usuario.nombre,
        email=nuevo_usuario.email,
        estado=nuevo_usuario.estado,
        roles=nuevo_usuario.roles.split(',') if nuevo_usuario.roles else [],
        fecha_creacion=nuevo_usuario.fecha_creacion
    )

def update_usuario(db: Session, usuario_id: int, usuario: UsuarioSchema) -> Optional[UsuarioOut]:
    existing_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if existing_usuario:
        data = usuario.model_dump()
        # Convertir lista de roles a string si existe
        if 'roles' in data and isinstance(data['roles'], list):
            data['roles'] = ','.join(data['roles'])
        for field, value in data.items():
            setattr(existing_usuario, field, value)
        db.commit()
        db.refresh(existing_usuario)
        return UsuarioOut(
            id=existing_usuario.id,
            nombre=existing_usuario.nombre,
            email=existing_usuario.email,
            estado=existing_usuario.estado,
            roles=existing_usuario.roles.split(',') if existing_usuario.roles else [],
            fecha_creacion=existing_usuario.fecha_creacion
        )
    return None

def delete_usuario(db: Session, usuario_id: int) -> bool:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario:
        db.delete(usuario)
        db.commit()
        return True
    return False

def get_usuario_by_email(db: Session, email: str) -> Optional[UsuarioOut]:
    u = db.query(Usuario).filter(Usuario.email == email).first()
    if u:
        return UsuarioOut(
            id=u.id,
            nombre=u.nombre,
            email=u.email,
            estado=u.estado,
            roles=u.roles.split(',') if u.roles else [],
            fecha_creacion=u.fecha_creacion,
            hash_contrasena=u.hash_contrasena
        )
    return None