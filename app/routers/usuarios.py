from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from app.db.dependencies import get_db
from app.schemas.schemas import UsuarioSchema, UserOut
from sqlalchemy.orm import Session
from services.usuario_service import (
    get_usuarios as service_get_usuarios,
    get_usuario as service_get_usuario,
    create_usuario as service_create_usuario,
    update_usuario as service_update_usuario,
    delete_usuario as service_delete_usuario,
)

router = APIRouter()

# Endpoints Usuarios
@router.get("/usuarios", tags=["Usuarios"], response_model=List[UsuarioSchema])
def get_usuarios(session: Session = Depends(get_db)):
    return service_get_usuarios(session)

@router.get("/usuarios/{id}", tags=["Usuarios"], response_model=UsuarioSchema)
def get_usuario(id: int, session: Session = Depends(get_db)):
    usuario = service_get_usuario(session, id)
    if usuario:
        return usuario
    else:
        return JSONResponse(content={"error": "Usuario no encontrado"}, status_code=404)

@router.post("/usuarios", tags=["Usuarios"], response_model=UsuarioSchema, status_code=201)
def create_usuario(usuario: UsuarioSchema, session: Session = Depends(get_db)):
    return service_create_usuario(session, usuario)

@router.put("/usuarios/{id}", tags=["Usuarios"], response_model=UsuarioSchema)
def update_usuario(id: int, usuario: UsuarioSchema, session: Session = Depends(get_db)):
    updated = service_update_usuario(session, id, usuario)
    if updated:
        return updated
    else:
        return JSONResponse(content={"error": "Usuario no encontrado"}, status_code=404)

@router.delete("/usuarios/{id}", tags=["Usuarios"])
def delete_usuario(id: int, session: Session = Depends(get_db)):
    deleted = service_delete_usuario(session, id)
    if deleted:
        return {"message": "Usuario eliminado"}
    else:
        return JSONResponse(content={"error": "Usuario no encontrado"}, status_code=404)