from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from main import get_db
from models import Maquina
from app.schemas.schemas import MaquinaSchema

router = APIRouter()

# Endpoints Maquinas
@router.get("/maquinas", tags=["Maquinas"], response_model=List[MaquinaSchema])
def get_maquinas(session = Depends(get_db)):
    maquinas = session.query(Maquina).all()
    return maquinas

@router.get("/maquinas/{id}", tags=["Maquinas"], response_model=MaquinaSchema)
def get_maquina(id: int, session = Depends(get_db)):
    maquina = session.query(Maquina).filter(Maquina.id == id).first()
    if maquina:
        return maquina
    else:
        return JSONResponse(content={"error": "Maquina no encontrada"}, status_code=404)

@router.post("/maquinas", tags=["Maquinas"], response_model=MaquinaSchema, status_code=201)
def create_maquina(maquina: MaquinaSchema, session = Depends(get_db)):
    nueva_maquina = Maquina(**maquina.model_dump())
    session.add(nueva_maquina)
    session.commit()
    session.refresh(nueva_maquina)
    return nueva_maquina

@router.put("/maquinas/{id}", tags=["Maquinas"], response_model=MaquinaSchema)
def update_maquina(id: int, maquina: MaquinaSchema, session = Depends(get_db)):
    existing_maquina = session.query(Maquina).filter(Maquina.id == id).first()
    if existing_maquina:
        for field, value in maquina.model_dump().items():
            setattr(existing_maquina, field, value)
        session.commit()
        session.refresh(existing_maquina)
        return existing_maquina
    else:
        return JSONResponse(content={"error": "Maquina no encontrada"}, status_code=404)

@router.delete("/maquinas/{id}", tags=["Maquinas"])
def delete_maquina(id: int, session = Depends(get_db)):
    maquina = session.query(Maquina).filter(Maquina.id == id).first()
    if maquina:
        session.delete(maquina)
        session.commit()
        return {"message": "Maquina eliminada"}
    else:
        return JSONResponse(content={"error": "Maquina no encontrada"}, status_code=404)