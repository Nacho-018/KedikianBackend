from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from app.db.dependencies import get_db
from app.db.models import Usuario
from app.schemas.schemas import UsuarioSchema, UserOut

router = APIRouter()

# Endpoints Usuarios
@router.get("/usuarios", tags=["Usuarios"], response_model=List[UsuarioSchema])
def get_usuarios(session = Depends(get_db)):
    usuarios = session.query(Usuario).all()
    return usuarios

@router.get("/usuarios/{id}", tags=["Usuarios"], response_model=UsuarioSchema)
def get_usuario(id: int, session = Depends(get_db)):
    usuario = session.query(Usuario).filter(Usuario.id == id).first()
    if usuario:
        return usuario
    else:
        return JSONResponse(content={"error": "Usuario no encontrado"}, status_code=404)

@router.post("/usuarios", tags=["Usuarios"], response_model=UsuarioSchema, status_code=201)
def create_usuario(usuario: UsuarioSchema, session = Depends(get_db)):
    nuevo_usuario = Usuario(**usuario.model_dump())
    session.add(nuevo_usuario)
    session.commit()
    session.refresh(nuevo_usuario)
    return nuevo_usuario

@router.put("/usuarios/{id}", tags=["Usuarios"], response_model=UsuarioSchema)
def update_usuario(id: int, usuario: UsuarioSchema, session = Depends(get_db)):
    existing_usuario = session.query(Usuario).filter(Usuario.id == id).first()
    if existing_usuario:
        for field, value in usuario.model_dump().items():
            setattr(existing_usuario, field, value)
        session.commit()
        session.refresh(existing_usuario)
        return existing_usuario
    else:
        return JSONResponse(content={"error": "Usuario no encontrado"}, status_code=404)

@router.delete("/usuarios/{id}", tags=["Usuarios"])
def delete_usuario(id: int, session = Depends(get_db)):
    usuario = session.query(Usuario).filter(Usuario.id == id).first()
    if usuario:
        session.delete(usuario)
        session.commit()
        return {"message": "Usuario eliminado"}
    else:
        return JSONResponse(content={"error": "Usuario no encontrado"}, status_code=404)