from app.db.models import Cliente, Cotizacion, CotizacionItem
from app.schemas.schemas import (
    ClienteCreate,
    ClienteOut,
    CotizacionCreate,
    CotizacionUpdate,
    CotizacionOut,
    CotizacionItemCreate,
    ServicioPredefinido,
    ServiciosPredefinidosOut
)
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

# Importar precios y tarifas desde cuenta_corriente_service
from app.services.cuenta_corriente_service import PRECIOS_ARIDOS, TARIFAS_MAQUINAS

# ============= FUNCIONES DE CLIENTES =============

def get_clientes(db: Session) -> List[ClienteOut]:
    """Obtiene todos los clientes"""
    clientes = db.query(Cliente).order_by(Cliente.nombre).all()
    return [ClienteOut.model_validate(c) for c in clientes]

def create_cliente(db: Session, cliente_data: ClienteCreate) -> ClienteOut:
    """Crea un nuevo cliente"""
    nuevo_cliente = Cliente(
        nombre=cliente_data.nombre,
        email=cliente_data.email,
        telefono=cliente_data.telefono,
        direccion=cliente_data.direccion
    )

    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)

    return ClienteOut.model_validate(nuevo_cliente)

# ============= FUNCIONES DE SERVICIOS PREDEFINIDOS =============

def get_servicios_predefinidos() -> ServiciosPredefinidosOut:
    """
    Obtiene la lista de servicios predefinidos con precios por defecto.
    Combina áridos y máquinas de cuenta_corriente_service.
    """
    servicios = []

    # Agregar áridos
    for tipo_arido, precio in PRECIOS_ARIDOS.items():
        servicios.append(ServicioPredefinido(
            nombre=tipo_arido,
            precio_por_defecto=precio,
            unidad="m³",
            categoria="arido"
        ))

    # Agregar máquinas (excluir "default")
    for maquina_nombre, tarifa in TARIFAS_MAQUINAS.items():
        if maquina_nombre != "default":
            servicios.append(ServicioPredefinido(
                nombre=maquina_nombre,
                precio_por_defecto=tarifa,
                unidad="hora",
                categoria="maquina"
            ))

    return ServiciosPredefinidosOut(servicios=servicios)

# ============= FUNCIONES DE COTIZACIONES =============

def get_cotizaciones(db: Session, cliente_id: Optional[int] = None) -> List[CotizacionOut]:
    """
    Obtiene todas las cotizaciones, opcionalmente filtradas por cliente.
    Incluye items y datos del cliente.
    """
    query = db.query(Cotizacion).options(
        joinedload(Cotizacion.cliente),
        joinedload(Cotizacion.items)
    )

    if cliente_id:
        query = query.filter(Cotizacion.cliente_id == cliente_id)

    cotizaciones = query.order_by(Cotizacion.fecha_creacion.desc()).all()

    return [CotizacionOut.model_validate(c) for c in cotizaciones]

def get_cotizacion(db: Session, cotizacion_id: int) -> Optional[CotizacionOut]:
    """Obtiene una cotización específica por ID con sus items y cliente"""
    cotizacion = db.query(Cotizacion).options(
        joinedload(Cotizacion.cliente),
        joinedload(Cotizacion.items)
    ).filter(Cotizacion.id == cotizacion_id).first()

    if cotizacion:
        return CotizacionOut.model_validate(cotizacion)
    return None

def create_cotizacion(db: Session, cotizacion_data: CotizacionCreate) -> CotizacionOut:
    """
    Crea una nueva cotización con sus items.
    Calcula automáticamente los subtotales y el importe total.
    """
    # Validar que el cliente existe
    cliente = db.query(Cliente).filter(Cliente.id == cotizacion_data.cliente_id).first()
    if not cliente:
        raise ValueError(f"No se encontró el cliente con ID {cotizacion_data.cliente_id}")

    # Validar que hay items
    if not cotizacion_data.items or len(cotizacion_data.items) == 0:
        raise ValueError("La cotización debe tener al menos un item")

    # Calcular importe total
    importe_total = 0.0
    for item in cotizacion_data.items:
        subtotal = item.cantidad * item.precio_unitario
        importe_total += subtotal

    # Crear la cotización
    nueva_cotizacion = Cotizacion(
        cliente_id=cotizacion_data.cliente_id,
        fecha_creacion=datetime.now(),
        fecha_validez=cotizacion_data.fecha_validez,
        estado="borrador",
        observaciones=cotizacion_data.observaciones,
        importe_total=Decimal(str(importe_total))
    )

    db.add(nueva_cotizacion)
    db.flush()  # Para obtener el ID de la cotización

    # Crear los items
    for item_data in cotizacion_data.items:
        subtotal = item_data.cantidad * item_data.precio_unitario

        item = CotizacionItem(
            cotizacion_id=nueva_cotizacion.id,
            nombre_servicio=item_data.nombre_servicio,
            unidad=item_data.unidad,
            cantidad=item_data.cantidad,
            precio_unitario=Decimal(str(item_data.precio_unitario)),
            subtotal=Decimal(str(subtotal))
        )
        db.add(item)

    db.commit()
    db.refresh(nueva_cotizacion)

    # Obtener la cotización completa con relaciones cargadas
    cotizacion_completa = db.query(Cotizacion).options(
        joinedload(Cotizacion.cliente),
        joinedload(Cotizacion.items)
    ).filter(Cotizacion.id == nueva_cotizacion.id).first()

    return CotizacionOut.model_validate(cotizacion_completa)

def update_cotizacion(
    db: Session,
    cotizacion_id: int,
    cotizacion_update: CotizacionUpdate
) -> Optional[CotizacionOut]:
    """
    Actualiza el estado, observaciones o fecha de validez de una cotización.
    No modifica los items (usar update_cotizacion_items para eso).
    """
    cotizacion = db.query(Cotizacion).filter(
        Cotizacion.id == cotizacion_id
    ).first()

    if not cotizacion:
        return None

    # Actualizar solo los campos proporcionados
    update_data = cotizacion_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(cotizacion, field, value)

    db.commit()
    db.refresh(cotizacion)

    # Obtener la cotización completa con relaciones
    cotizacion_completa = db.query(Cotizacion).options(
        joinedload(Cotizacion.cliente),
        joinedload(Cotizacion.items)
    ).filter(Cotizacion.id == cotizacion_id).first()

    return CotizacionOut.model_validate(cotizacion_completa)

def update_cotizacion_items(
    db: Session,
    cotizacion_id: int,
    items_data: List[CotizacionItemCreate]
) -> Optional[CotizacionOut]:
    """
    Reemplaza todos los items de una cotización con nuevos items.
    Útil cuando el usuario edita precios o cantidades.
    Recalcula el importe total automáticamente.
    """
    cotizacion = db.query(Cotizacion).filter(
        Cotizacion.id == cotizacion_id
    ).first()

    if not cotizacion:
        return None

    # Validar que hay items
    if not items_data or len(items_data) == 0:
        raise ValueError("La cotización debe tener al menos un item")

    # Eliminar items existentes
    db.query(CotizacionItem).filter(
        CotizacionItem.cotizacion_id == cotizacion_id
    ).delete()

    # Crear nuevos items y calcular importe total
    importe_total = 0.0
    for item_data in items_data:
        subtotal = item_data.cantidad * item_data.precio_unitario
        importe_total += subtotal

        item = CotizacionItem(
            cotizacion_id=cotizacion_id,
            nombre_servicio=item_data.nombre_servicio,
            unidad=item_data.unidad,
            cantidad=item_data.cantidad,
            precio_unitario=Decimal(str(item_data.precio_unitario)),
            subtotal=Decimal(str(subtotal))
        )
        db.add(item)

    # Actualizar importe total
    cotizacion.importe_total = Decimal(str(importe_total))

    db.commit()

    # Obtener la cotización completa con relaciones
    cotizacion_completa = db.query(Cotizacion).options(
        joinedload(Cotizacion.cliente),
        joinedload(Cotizacion.items)
    ).filter(Cotizacion.id == cotizacion_id).first()

    return CotizacionOut.model_validate(cotizacion_completa)

def delete_cotizacion(db: Session, cotizacion_id: int) -> bool:
    """Elimina una cotización (los items se eliminan en cascada)"""
    cotizacion = db.query(Cotizacion).filter(
        Cotizacion.id == cotizacion_id
    ).first()

    if not cotizacion:
        return False

    db.delete(cotizacion)
    db.commit()
    return True
