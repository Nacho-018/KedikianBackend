from app.db.database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime

class Usuario(Base):
    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True, auto_increment=True)
    nombre = Column(String)
    email = Column(String, unique=True)
    hash_contrasena = Column(String)
    estado = Column(Boolean, default=True)
    roles = Column(String)
    fecha_creacion = Column(DateTime)

class Maquina(Base):
    __tablename__ = "maquina"
    id = Column(Integer, primary_key=True, auto_increment=True)
    nombre = Column(String)
    estado = Column(Boolean, default=True)
    horas_uso = Column(Integer, default=0)

class Maquina_Usuario(Base):
    __tablename__="maquina_usuario"
    id = Column(Integer, primary_key=True, auto_increment=True)
    maquina_id = Column(Integer, foreign_key="maquina.id")
    usuario_id = Column(Integer, foreign_key="usuario.id")
    fecha_asignacion = Column(DateTime)
    horas_turno = Column(DateTime)

class Proyecto(Base):
    __tablename__ = "proyecto"
    id = Column(Integer, primary_key=True, auto_increment=True)
    nombre = Column(String)
    estado = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime)
    contrato_id = Column(Integer, foreign_key="contrato.id")
    ubicacion = Column(String)

class Proyecto_Maquina(Base):
    __tablename__ = "proyecto_maquina"
    id = Column(Integer, primary_key=True, auto_increment=True)
    proyecto_id = Column(Integer, foreign_key="proyecto.id")
    maquina_id = Column(Integer, foreign_key="maquina.id")
    horas_uso = Column(Integer, default=0)
    fecha_asignacion = Column(DateTime)

class Contrato(Base):
    __tablename__ = "contrato"
    id = Column(Integer, primary_key=True, auto_increment=True)
    proyecto_id = Column(Integer, foreign_key="proyecto.id")
    detalle = Column(String)
    cliente = Column(String)
    importe_total = Column(Integer)
    fecha_inicio = Column(DateTime)
    fecha_terminacion = Column(DateTime)

class Gasto(Base):
    __tablename__ = "gasto"
    id = Column(Integer, primary_key=True, auto_increment=True)
    usuario_id = Column(Integer, foreign_key="usuario.id")
    maquina_id = Column(Integer, foreign_key="maquina.id")
    tipo = Column(String)
    importe_total = Column(Integer)
    fecha = Column(DateTime)
    descripcion = Column(String)
    imagen = Column(String)

class Pago(Base):
    __tablename__ = "pago"
    id = Column(Integer, primary_key=True, auto_increment=True)
    proyecto_id = Column(Integer, foreign_key="proyecto.id")
    producto_id = Column(Integer, foreign_key="producto.id")
    monto = Column(Integer)
    fecha = Column(DateTime)
    descripcion = Column(String)

class Producto(Base):
    __tablename__ = "producto"
    id = Column(Integer, primary_key=True, auto_increment=True)
    nombre = Column(String)
    codigo_producto = Column(String)
    inventario = Column(Integer)

class Producto_Usuario(Base):
    __tablename__ = "producto_usuario"
    id = Column(Integer, primary_key=True, auto_increment=True)
    producto_id = Column(Integer, foreign_key="producto.id")
    usuario_id = Column(Integer, foreign_key="usuario.id")
    cantidad = Column(Integer)
    fecha = Column(DateTime)
    tipo_transaccion = Column(String)  # "entrada" o "salida"
