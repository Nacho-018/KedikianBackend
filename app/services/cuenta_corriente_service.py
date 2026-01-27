from app.db.models import ReporteCuentaCorriente, Proyecto, EntregaArido, ReporteLaboral, Maquina
from app.schemas.schemas import (
    ReporteCuentaCorrienteCreate,
    ReporteCuentaCorrienteUpdate,
    ReporteCuentaCorrienteOut,
    ResumenProyectoSchema,
    DetalleAridoConPrecio,
    DetalleHorasConTarifa,
    PrecioAridoSchema,
    TarifaMaquinaSchema
)
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal

# Diccionario de precios de áridos por tipo (precio por m³)
# Estos valores pueden moverse a una tabla de configuración en el futuro
PRECIOS_ARIDOS: Dict[str, float] = {
    "Arena Fina": 8500.0,
    "Granza": 7500.0,
    "Arena Común": 7000.0,
    "Relleno": 6000.0,
    "Tierra Negra": 9000.0,
    "Piedra": 12000.0,
    "0.20": 8000.0,
    "Blinder": 10000.0,
    "Arena Lavada": 8800.0
}

# Diccionario de tarifas por hora de máquinas
# Estos valores pueden moverse a una tabla de configuración en el futuro
TARIFAS_MAQUINAS: Dict[str, float] = {
    # Por defecto, todas las máquinas tienen una tarifa base
    # Se puede personalizar por nombre de máquina
    "default": 15000.0,  # Tarifa por defecto por hora
    "Excavadora": 18000.0,
    "Retroexcavadora": 16000.0,
    "Cargadora": 17000.0,
    "Motoniveladora": 20000.0,
    "Compactadora": 14000.0,
    "Camión": 12000.0,
}

def get_precio_arido(tipo_arido: str) -> float:
    """Obtiene el precio por m³ de un tipo de árido"""
    return PRECIOS_ARIDOS.get(tipo_arido, 0.0)

def get_tarifa_maquina(maquina_nombre: str) -> float:
    """Obtiene la tarifa por hora de una máquina"""
    # Primero intenta buscar por nombre específico, si no usa la tarifa default
    return TARIFAS_MAQUINAS.get(maquina_nombre, TARIFAS_MAQUINAS["default"])

def get_resumen_proyecto(
    db: Session,
    proyecto_id: int,
    periodo_inicio: date,
    periodo_fin: date
) -> Optional[ResumenProyectoSchema]:
    """
    Obtiene el resumen de áridos y horas de un proyecto con sus precios calculados
    para un período determinado.
    """
    # Verificar que el proyecto existe
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        return None

    # Obtener entregas de áridos en el período
    entregas_aridos = db.query(
        EntregaArido.tipo_arido,
        func.sum(EntregaArido.cantidad).label('total_cantidad')
    ).filter(
        EntregaArido.proyecto_id == proyecto_id,
        EntregaArido.fecha_entrega >= periodo_inicio,
        EntregaArido.fecha_entrega <= periodo_fin
    ).group_by(EntregaArido.tipo_arido).all()

    # Calcular detalles de áridos con precios
    detalles_aridos = []
    total_aridos_m3 = 0.0
    total_importe_aridos = 0.0

    for tipo_arido, cantidad in entregas_aridos:
        precio_unitario = get_precio_arido(tipo_arido)
        importe = cantidad * precio_unitario

        detalles_aridos.append(DetalleAridoConPrecio(
            tipo_arido=tipo_arido,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            importe=importe
        ))

        total_aridos_m3 += cantidad
        total_importe_aridos += importe

    # Obtener horas de máquinas en el período
    horas_maquinas = db.query(
        Maquina.id,
        Maquina.nombre,
        func.sum(ReporteLaboral.horas_turno).label('total_horas')
    ).join(
        ReporteLaboral, ReporteLaboral.maquina_id == Maquina.id
    ).filter(
        ReporteLaboral.proyecto_id == proyecto_id,
        ReporteLaboral.fecha_asignacion >= periodo_inicio,
        ReporteLaboral.fecha_asignacion <= periodo_fin
    ).group_by(Maquina.id, Maquina.nombre).all()

    # Calcular detalles de horas con tarifas
    detalles_horas = []
    total_horas = 0.0
    total_importe_horas = 0.0

    for maquina_id, maquina_nombre, horas in horas_maquinas:
        tarifa_hora = get_tarifa_maquina(maquina_nombre)
        importe = horas * tarifa_hora

        detalles_horas.append(DetalleHorasConTarifa(
            maquina_id=maquina_id,
            maquina_nombre=maquina_nombre,
            total_horas=horas,
            tarifa_hora=tarifa_hora,
            importe=importe
        ))

        total_horas += horas
        total_importe_horas += importe

    # Calcular importe total
    importe_total = total_importe_aridos + total_importe_horas

    return ResumenProyectoSchema(
        proyecto_id=proyecto_id,
        proyecto_nombre=proyecto.nombre,
        periodo_inicio=periodo_inicio,
        periodo_fin=periodo_fin,
        aridos=detalles_aridos,
        total_aridos_m3=total_aridos_m3,
        total_importe_aridos=total_importe_aridos,
        horas_maquinas=detalles_horas,
        total_horas=total_horas,
        total_importe_horas=total_importe_horas,
        importe_total=importe_total
    )

def get_reportes(db: Session, proyecto_id: Optional[int] = None) -> List[ReporteCuentaCorrienteOut]:
    """Obtiene todos los reportes de cuenta corriente, opcionalmente filtrados por proyecto"""
    query = db.query(ReporteCuentaCorriente)

    if proyecto_id:
        query = query.filter(ReporteCuentaCorriente.proyecto_id == proyecto_id)

    reportes = query.order_by(ReporteCuentaCorriente.fecha_generacion.desc()).all()

    return [ReporteCuentaCorrienteOut.model_validate(r) for r in reportes]

def get_reporte(db: Session, reporte_id: int) -> Optional[ReporteCuentaCorrienteOut]:
    """Obtiene un reporte específico por ID"""
    reporte = db.query(ReporteCuentaCorriente).filter(
        ReporteCuentaCorriente.id == reporte_id
    ).first()

    if reporte:
        return ReporteCuentaCorrienteOut.model_validate(reporte)
    return None

def create_reporte(db: Session, reporte_data: ReporteCuentaCorrienteCreate) -> ReporteCuentaCorrienteOut:
    """
    Crea un nuevo reporte de cuenta corriente calculando automáticamente
    los totales e importes del período especificado
    """
    # Obtener resumen del proyecto para el período
    resumen = get_resumen_proyecto(
        db,
        reporte_data.proyecto_id,
        reporte_data.periodo_inicio,
        reporte_data.periodo_fin
    )

    if not resumen:
        raise ValueError(f"No se encontró el proyecto con ID {reporte_data.proyecto_id}")

    # Crear el reporte con los datos calculados
    nuevo_reporte = ReporteCuentaCorriente(
        proyecto_id=reporte_data.proyecto_id,
        periodo_inicio=reporte_data.periodo_inicio,
        periodo_fin=reporte_data.periodo_fin,
        total_aridos=resumen.total_aridos_m3,
        total_horas=resumen.total_horas,
        importe_aridos=Decimal(str(resumen.total_importe_aridos)),
        importe_horas=Decimal(str(resumen.total_importe_horas)),
        importe_total=Decimal(str(resumen.importe_total)),
        estado="pendiente",
        fecha_generacion=datetime.now(),
        observaciones=reporte_data.observaciones
    )

    db.add(nuevo_reporte)
    db.commit()
    db.refresh(nuevo_reporte)

    return ReporteCuentaCorrienteOut.model_validate(nuevo_reporte)

def update_reporte_estado(
    db: Session,
    reporte_id: int,
    reporte_update: ReporteCuentaCorrienteUpdate
) -> Optional[ReporteCuentaCorrienteOut]:
    """Actualiza el estado y otros campos de un reporte"""
    reporte = db.query(ReporteCuentaCorriente).filter(
        ReporteCuentaCorriente.id == reporte_id
    ).first()

    if not reporte:
        return None

    # Actualizar solo los campos proporcionados
    update_data = reporte_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(reporte, field, value)

    # Si se marca como pagado y no tiene fecha de pago, asignarla
    if reporte_update.estado == "pagado" and not reporte.fecha_pago:
        reporte.fecha_pago = date.today()

    db.commit()
    db.refresh(reporte)

    return ReporteCuentaCorrienteOut.model_validate(reporte)

def delete_reporte(db: Session, reporte_id: int) -> bool:
    """Elimina un reporte de cuenta corriente"""
    reporte = db.query(ReporteCuentaCorriente).filter(
        ReporteCuentaCorriente.id == reporte_id
    ).first()

    if not reporte:
        return False

    db.delete(reporte)
    db.commit()
    return True

def get_todos_precios_aridos() -> List[PrecioAridoSchema]:
    """Obtiene todos los precios de áridos disponibles"""
    return [
        PrecioAridoSchema(tipo_arido=tipo, precio_m3=precio)
        for tipo, precio in PRECIOS_ARIDOS.items()
    ]

def get_tarifa_maquina_por_id(db: Session, maquina_id: int) -> Optional[TarifaMaquinaSchema]:
    """Obtiene la tarifa por hora de una máquina específica"""
    maquina = db.query(Maquina).filter(Maquina.id == maquina_id).first()

    if not maquina:
        return None

    tarifa = get_tarifa_maquina(maquina.nombre)

    return TarifaMaquinaSchema(
        maquina_id=maquina.id,
        maquina_nombre=maquina.nombre,
        tarifa_hora=tarifa
    )
