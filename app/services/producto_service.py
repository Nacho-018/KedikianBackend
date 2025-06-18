from app.db.models import Producto
from app.schemas.schemas import ProductoSchema
from sqlalchemy.orm import Session
from typing import List, Optional
import os

UPLOAD_DIR = "static/productos/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Servicio para operaciones de Producto

def get_productos(db: Session) -> List[Producto]:
    return db.query(Producto).all()

def get_producto(db: Session, producto_id: int) -> Optional[Producto]:
    return db.query(Producto).filter(Producto.id == producto_id).first()

def create_producto(db: Session, nombre: str, codigo_producto: str, inventario: int, imagen) -> Producto:
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
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    return nuevo_producto

def update_producto(db: Session, producto_id: int, nombre: str, codigo_producto: str, inventario: int, imagen=None) -> Optional[Producto]:
    existing_producto = db.query(Producto).filter(Producto.id == producto_id).first()
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
        db.commit()
        db.refresh(existing_producto)
        return existing_producto
    return None

def delete_producto(db: Session, producto_id: int) -> bool:
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if producto:
        db.delete(producto)
        db.commit()
        return True
    return False
