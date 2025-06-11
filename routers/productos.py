from fastapi import APIRouter, Depends, File, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
from app.db.dependencies import get_db
from app.db.models import Producto
from app.schemas.schemas import ProductoSchema
import os

router = APIRouter()

UPLOAD_DIR = "static/productos/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Endpoints Productos
@router.get("/productos", tags=["Productos"], response_model=List[ProductoSchema])
def get_productos(session = Depends(get_db)):
    productos = session.query(Producto).all()
    return productos

@router.get("/productos/{id}", tags=["Productos"], response_model=ProductoSchema)
def get_producto(id: int, session = Depends(get_db)):
    producto = session.query(Producto).filter(Producto.id == id).first()
    if producto:
        return producto
    else:
        return JSONResponse(content={"error": "Producto no encontrado"}, status_code=404)

@router.post("/productos", tags=["Productos"], response_model=ProductoSchema, status_code=201)
def create_producto(
    nombre: str = Form(...),
    codigo_producto: str = Form(...),
    inventario: int = Form(...),
    imagen: UploadFile = File(...),
    session = Depends(get_db)
):
    filename = f"{codigo_producto}_{imagen.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(imagen.file.read())
    url_imagen = f"/static/productos/{filename}"
    nuevo_producto = Producto(
        nombre=nombre,
        codigo_producto=codigo_producto,
        inventario=inventario,
        url_imagen=url_imagen
    )
    session.add(nuevo_producto)
    session.commit()
    session.refresh(nuevo_producto)
    return nuevo_producto

@router.put("/productos/{id}", tags=["Productos"], response_model=ProductoSchema)
def update_producto(
    id: int,
    nombre: str = Form(...),
    codigo_producto: str = Form(...),
    inventario: int = Form(...),
    imagen: Optional[UploadFile] = File(None),
    session = Depends(get_db)
):
    existing_producto = session.query(Producto).filter(Producto.id == id).first()
    if existing_producto:
        existing_producto.nombre = nombre
        existing_producto.codigo_producto = codigo_producto
        existing_producto.inventario = inventario
        if imagen:
            filename = f"{codigo_producto}_{imagen.filename}"
            file_path = os.path.join(UPLOAD_DIR, filename)
            with open(file_path, "wb") as f:
                f.write(imagen.file.read())
            existing_producto.url_imagen = f"/static/productos/{filename}"
        session.commit()
        session.refresh(existing_producto)
        return existing_producto
    else:
        return JSONResponse(content={"error": "Producto no encontrado"}, status_code=404)

@router.delete("/productos/{id}", tags=["Productos"])
def delete_producto(id: int, session = Depends(get_db)):
    producto = session.query(Producto).filter(Producto.id == id).first()
    if producto:
        session.delete(producto)
        session.commit()
        return {"message": "Producto eliminado"}
    else:
        return JSONResponse(content={"error": "Producto no encontrado"}, status_code=404)