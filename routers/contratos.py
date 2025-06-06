from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from main import get_db
from models import Contrato
from app.schemas.schemas import ContratoSchema

router = APIRouter()

# Endpoints Contratos
@router.get("/contratos", tags=["Contratos"], response_model=List[ContratoSchema])
def get_contratos(session = Depends(get_db)):
    contratos = session.query(Contrato).all()
    return contratos

@router.get("/contratos/{id}", tags=["Contratos"], response_model=ContratoSchema)
def get_contrato(id: int, session = Depends(get_db)):
    contrato = session.query(Contrato).filter(Contrato.id == id).first()
    if contrato:
        return contrato
    else:
        return JSONResponse(content={"error": "Contrato no encontrado"}, status_code=404)

@router.post("/contratos", tags=["Contratos"], response_model=ContratoSchema, status_code=201)
def create_contrato(contrato: ContratoSchema, session = Depends(get_db)):
    nuevo_contrato = Contrato(**contrato.model_dump())
    session.add(nuevo_contrato)
    session.commit()
    session.refresh(nuevo_contrato)
    return nuevo_contrato

@router.put("/contratos/{id}", tags=["Contratos"], response_model=ContratoSchema)
def update_contrato(id: int, contrato: ContratoSchema, session = Depends(get_db)):
    existing_contrato = session.query(Contrato).filter(Contrato.id == id).first()
    if existing_contrato:
        for field, value in contrato.model_dump().items():
            setattr(existing_contrato, field, value)
        session.commit()
        session.refresh(existing_contrato)
        return existing_contrato
    else:
        return JSONResponse(content={"error": "Contrato no encontrado"}, status_code=404)

@router.delete("/contratos/{id}", tags=["Contratos"])
def delete_contrato(id: int, session = Depends(get_db)):
    contrato = session.query(Contrato).filter(Contrato.id == id).first()
    if contrato:
        session.delete(contrato)
        session.commit()
        return {"message": "Contrato eliminado"}
    else:
        return JSONResponse(content={"error": "Contrato no encontrado"}, status_code=404)