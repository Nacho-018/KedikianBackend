from fastapi import FastAPI
from app.db.init_db import init_db  # Llama a la función que crea las tablas
from app.db.models import (
    Usuario,
    Maquina,
    Proyecto,
    Contrato,
    Gasto,
    Pago,
    Producto,
    Arrendamiento,
    MovimientoInventario,
    ReporteLaboral,
)
from app.db.session import session  # Importa la sesión de la base de datos

app = FastAPI()

# Inicializar la base de datos
@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def read_root():
    return {"message": "API funcionando correctamente"}

@app.get("/usuarios", tags=["Usuarios"])
def getUSuarios():
    return session.query(Usuario).all()

@app.get("/usuarios/{id}", tags=["Usuarios"])
def get_usuario(id: int):
    usuario = session.query(Usuario).filter(Usuario.id == id).first()
    if usuario:
        return usuario
    else:
        return {"error": "Usuario no encontrado"}
    
@app.post("/usuarios", tags=["Usuarios"])
def create_usuario(usuario: Usuario):
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario

@app.put("/usuarios/{id}", tags=["Usuarios"])
def update_usuario(id: int, usuario: Usuario):
    existing_usuario = session.query(Usuario).filter(Usuario.id == id).first()
    if existing_usuario:
        existing_usuario.nombre = usuario.nombre
        existing_usuario.email = usuario.email
        existing_usuario.hash_contrasena = usuario.hash_contrasena
        existing_usuario.estado = usuario.estado
        existing_usuario.roles = usuario.roles
        existing_usuario.fecha_creacion = usuario.fecha_creacion
        session.commit()
        return existing_usuario
    else:
        return {"error": "Usuario no encontrado"}
    
@app.delete("/usuarios/{id}", tags=["Usuarios"])
def delete_usuario(id: int):
    usuario = session.query(Usuario).filter(Usuario.id == id).first()
    if usuario:
        session.delete(usuario)
        session.commit()
        return {"message": "Usuario eliminado"}
    else:
        return {"error": "Usuario no encontrado"}
    
@app.get("/maquinas", tags=["Maquinas"])
def get_maquinas():
    return session.query(Maquina).all()

@app.get("/maquinas/{id}", tags=["Maquinas"])
def get_maquina(id: int):
    maquina = session.query(Maquina).filter(Maquina.id == id).first()
    if maquina:
        return maquina
    else:
        return {"error": "Maquina no encontrada"}
    
@app.post("/maquinas", tags=["Maquinas"])
def create_maquina(maquina: Maquina):
    session.add(maquina)
    session.commit()
    session.refresh(maquina)
    return maquina

@app.put("/maquinas/{id}", tags=["Maquinas"])
def update_maquina(id: int, maquina: Maquina):
    existing_maquina = session.query(Maquina).filter(Maquina.id == id).first()
    if existing_maquina:
        existing_maquina.nombre = maquina.nombre
        existing_maquina.estado = maquina.estado
        existing_maquina.horas_uso = maquina.horas_uso
        session.commit()
        return existing_maquina
    else:
        return {"error": "Maquina no encontrada"}
    
@app.delete("/maquinas/{id}", tags=["Maquinas"])
def delete_maquina(id: int):
    maquina = session.query(Maquina).filter(Maquina.id == id).first()
    if maquina:
        session.delete(maquina)
        session.commit()
        return {"message": "Maquina eliminada"}
    else:
        return {"error": "Maquina no encontrada"}
    
@app.get("/proyectos", tags=["Proyectos"])
def get_proyectos():
    return session.query(Proyecto).all()

@app.get("/proyectos/{id}", tags=["Proyectos"])
def get_proyecto(id: int):
    proyecto = session.query(Proyecto).filter(Proyecto.id == id).first()
    if proyecto:
        return proyecto
    else:
        return {"error": "Proyecto no encontrado"}
    
@app.post("/proyectos", tags=["Proyectos"])
def create_proyecto(proyecto: Proyecto):
    session.add(proyecto)
    session.commit()
    session.refresh(proyecto)
    return proyecto

@app.put("/proyectos/{id}", tags=["Proyectos"])
def update_proyecto(id: int, proyecto: Proyecto):
    existing_proyecto = session.query(Proyecto).filter(Proyecto.id == id).first()
    if existing_proyecto:
        existing_proyecto.nombre = proyecto.nombre
        existing_proyecto.estado = proyecto.estado
        existing_proyecto.ubicacion = proyecto.ubicacion
        session.commit()
        return existing_proyecto
    else:
        return {"error": "Proyecto no encontrado"}
    
@app.delete("/proyectos/{id}", tags=["Proyectos"])
def delete_proyecto(id: int):
    proyecto = session.query(Proyecto).filter(Proyecto.id == id).first()
    if proyecto:
        session.delete(proyecto)
        session.commit()
        return {"message": "Proyecto eliminado"}
    else:
        return {"error": "Proyecto no encontrado"}
    
@app.get("/contratos", tags=["Contratos"])
def get_contratos():
    return session.query(Contrato).all()

@app.get("/contratos/{id}", tags=["Contratos"])
def get_contrato(id: int):
    contrato = session.query(Contrato).filter(Contrato.id == id).first()
    if contrato:
        return contrato
    else:
        return {"error": "Contrato no encontrado"}
    
@app.post("/contratos", tags=["Contratos"])
def create_contrato(contrato: Contrato):
    session.add(contrato)
    session.commit()
    session.refresh(contrato)
    return contrato

@app.put("/contratos/{id}", tags=["Contratos"])
def update_contrato(id: int, contrato: Contrato):
    existing_contrato = session.query(Contrato).filter(Contrato.id == id).first()
    if existing_contrato:
        existing_contrato.detalle = contrato.detalle
        existing_contrato.fecha_terminacion = contrato.fecha_terminacion
        session.commit()
        return existing_contrato
    else:
        return {"error": "Contrato no encontrado"}
    
@app.delete("/contratos/{id}", tags=["Contratos"])
def delete_contrato(id: int):
    contrato = session.query(Contrato).filter(Contrato.id == id).first()
    if contrato:
        session.delete(contrato)
        session.commit()
        return {"message": "Contrato eliminado"}
    else:
        return {"error": "Contrato no encontrado"}
    
@app.get("/gastos", tags=["Gastos"])
def get_gastos():
    return session.query(Gasto).all()

@app.get("/gastos/{id}", tags=["Gastos"])
def get_gasto(id: int):
    gasto = session.query(Gasto).filter(Gasto.id == id).first()
    if gasto:
        return gasto
    else:
        return {"error": "Gasto no encontrado"}
    
@app.post("/gastos", tags=["Gastos"])
def create_gasto(gasto: Gasto):
    session.add(gasto)
    session.commit()
    session.refresh(gasto)
    return gasto

@app.put("/gastos/{id}", tags=["Gastos"])
def update_gasto(id: int, gasto: Gasto):
    existing_gasto = session.query(Gasto).filter(Gasto.id == id).first()
    if existing_gasto:
        existing_gasto.importe_total = gasto.importe_total
        existing_gasto.descripcion = gasto.descripcion
        existing_gasto.imagen = gasto.imagen
        session.commit()
        return existing_gasto
    else:
        return {"error": "Gasto no encontrado"}
    
@app.delete("/gastos/{id}", tags=["Gastos"])
def delete_gasto(id: int):
    gasto = session.query(Gasto).filter(Gasto.id == id).first()
    if gasto:
        session.delete(gasto)
        session.commit()
        return {"message": "Gasto eliminado"}
    else:
        return {"error": "Gasto no encontrado"}
    
@app.get("/pagos", tags=["Pagos"])
def get_pagos():
    return session.query(Pago).all()

@app.get("/pagos/{id}", tags=["Pagos"])
def get_pago(id: int):
    pago = session.query(Pago).filter(Pago.id == id).first()
    if pago:
        return pago
    else:
        return {"error": "Pago no encontrado"}
    
@app.post("/pagos", tags=["Pagos"])
def create_pago(pago: Pago):
    session.add(pago)
    session.commit()
    session.refresh(pago)
    return pago

@app.put("/pagos/{id}", tags=["Pagos"])
def update_pago(id: int, pago: Pago):
    existing_pago = session.query(Pago).filter(Pago.id == id).first()
    if existing_pago:
        existing_pago.importe_total = pago.importe_total
        existing_pago.descripcion = pago.descripcion
        session.commit()
        return existing_pago
    else:
        return {"error": "Pago no encontrado"}
    
@app.delete("/pagos/{id}", tags=["Pagos"])
def delete_pago(id: int):
    pago = session.query(Pago).filter(Pago.id == id).first()
    if pago:
        session.delete(pago)
        session.commit()
        return {"message": "Pago eliminado"}
    else:
        return {"error": "Pago no encontrado"}
    
@app.get("/productos", tags=["Productos"])
def get_productos():
    return session.query(Producto).all()

@app.get("/productos/{id}", tags=["Productos"])
def get_producto(id: int):
    producto = session.query(Producto).filter(Producto.id == id).first()
    if producto:
        return producto
    else:
        return {"error": "Producto no encontrado"}
    
@app.post("/productos", tags=["Productos"])
def create_producto(producto: Producto):
    session.add(producto)
    session.commit()
    session.refresh(producto)
    return producto

@app.put("/productos/{id}", tags=["Productos"])
def update_producto(id: int, producto: Producto):
    existing_producto = session.query(Producto).filter(Producto.id == id).first()
    if existing_producto:
        existing_producto.nombre = producto.nombre
        existing_producto.inventario = producto.inventario
        session.commit()
        return existing_producto
    else:
        return {"error": "Producto no encontrado"}
    
@app.delete("/productos/{id}", tags=["Productos"])
def delete_producto(id: int):
    producto = session.query(Producto).filter(Producto.id == id).first()
    if producto:
        session.delete(producto)
        session.commit()
        return {"message": "Producto eliminado"}
    else:
        return {"error": "Producto no encontrado"}
    
@app.get("/arrendamientos", tags=["Arrendamientos"])
def get_arrendamientos():
    return session.query(Arrendamiento).all()

@app.get("/arrendamientos/{id}", tags=["Arrendamientos"])
def get_arrendamiento(id: int):
    arrendamiento = session.query(Arrendamiento).filter(Arrendamiento.id == id).first()
    if arrendamiento:
        return arrendamiento
    else:
        return {"error": "Arrendamiento no encontrado"}
    
@app.post("/arrendamientos", tags=["Arrendamientos"])
def create_arrendamiento(arrendamiento: Arrendamiento):
    session.add(arrendamiento)
    session.commit()
    session.refresh(arrendamiento)
    return arrendamiento

@app.put("/arrendamientos/{id}", tags=["Arrendamientos"])
def update_arrendamiento(id: int, arrendamiento: Arrendamiento):
    existing_arrendamiento = session.query(Arrendamiento).filter(Arrendamiento.id == id).first()
    if existing_arrendamiento:
        existing_arrendamiento.horas_uso = arrendamiento.horas_uso
        session.commit()
        return existing_arrendamiento
    else:
        return {"error": "Arrendamiento no encontrado"}
    
@app.delete("/arrendamientos/{id}", tags=["Arrendamientos"])
def delete_arrendamiento(id: int):
    arrendamiento = session.query(Arrendamiento).filter(Arrendamiento.id == id).first()
    if arrendamiento:
        session.delete(arrendamiento)
        session.commit()
        return {"message": "Arrendamiento eliminado"}
    else:
        return {"error": "Arrendamiento no encontrado"}
    
@app.get("/movimientos_inventario", tags=["Movimientos de Inventario"])
def get_movimientos_inventario():
    return session.query(MovimientoInventario).all()

@app.get("/movimientos_inventario/{id}", tags=["Movimientos de Inventario"])
def get_movimiento_inventario(id: int):
    movimiento_inventario = session.query(MovimientoInventario).filter(MovimientoInventario.id == id).first()
    if movimiento_inventario:
        return movimiento_inventario
    else:
        return {"error": "Movimiento de inventario no encontrado"}
    
@app.post("/movimientos_inventario", tags=["Movimientos de Inventario"])
def create_movimiento_inventario(movimiento_inventario: MovimientoInventario):
    session.add(movimiento_inventario)
    session.commit()
    session.refresh(movimiento_inventario)
    return movimiento_inventario

@app.put("/movimientos_inventario/{id}", tags=["Movimientos de Inventario"])
def update_movimiento_inventario(id: int, movimiento_inventario: MovimientoInventario):
    existing_movimiento_inventario = session.query(MovimientoInventario).filter(MovimientoInventario.id == id).first()
    if existing_movimiento_inventario:
        existing_movimiento_inventario.cantidad = movimiento_inventario.cantidad
        existing_movimiento_inventario.tipo_transaccion = movimiento_inventario.tipo_transaccion
        session.commit()
        return existing_movimiento_inventario
    else:
        return {"error": "Movimiento de inventario no encontrado"}
    
@app.delete("/movimientos_inventario/{id}", tags=["Movimientos de Inventario"])
def delete_movimiento_inventario(id: int):
    movimiento_inventario = session.query(MovimientoInventario).filter(MovimientoInventario.id == id).first()
    if movimiento_inventario:
        session.delete(movimiento_inventario)
        session.commit()
        return {"message": "Movimiento de inventario eliminado"}
    else:
        return {"error": "Movimiento de inventario no encontrado"}
    



