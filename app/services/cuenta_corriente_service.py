from app.db.models import ReporteCuentaCorriente, Proyecto, EntregaArido, ReporteLaboral, Maquina
from app.schemas.schemas import (
    ReporteCuentaCorrienteCreate,
    ReporteCuentaCorrienteUpdate,
    ReporteCuentaCorrienteOut,
    ResumenProyectoSchema,
    DetalleAridoConPrecio,
    DetalleHorasConTarifa,
    PrecioAridoSchema,
    TarifaMaquinaSchema,
    DetalleReporteResponse,
    ItemAridoDetalle,
    ItemHoraDetalle,
    ActualizarItemsPagoRequest,
    ActualizarItemsPagoResponse
)
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal

# ============= PRECIOS DE ÁRIDOS POR M³ =============
# Estos son valores por defecto que se usan como fallback
# Si el registro tiene precio_unitario en la BD, se usa ese valor
PRECIOS_ARIDOS: Dict[str, float] = {
    "Arena Fina": 54000.0,
    "Granza": 54000.0,
    "Arena Común": 33680.0,
    "Relleno": 16000.0,
    "Tierra Negra": 16000.0,
    "Piedra": 12000.0,
    "0.20": 8000.0,
    "Blinder": 10000.0,
    "Arena Lavada": 33680.0
}


# ============= TARIFAS DE MÁQUINAS POR HORA =============
# IMPORTANTE: Usa los nombres EXACTOS de las máquinas como aparecen en la BD
# Para obtener los nombres: SELECT id, nombre FROM maquina;
#
# Formato: "Nombre_Exacto_Maquina": tarifa_por_hora
#
# INSTRUCCIONES:
# 1. Consulta tus máquinas en la BD
# 2. Reemplaza estos ejemplos con tus máquinas reales
# 3. Usa el nombre EXACTO (case-sensitive)
# 4. La tarifa "default" se usa si la máquina no está en la lista

TARIFAS_MAQUINAS: Dict[str, float] = {
    # ===== TARIFA POR DEFECTO =====
    "default": 15000.0,  # Se usa si la máquina no está en la lista
    "BOBCAT 2018 S650.": 700000,
    "BOBCAT S530 2017": 700000,
    "EXCAVADORA 2020 SANY EU50.": 100000,
    "EXCAVADORA 2023 XCMG E60.": 100000,
    "EXCAVADORA 2022 LONKING 6150.": 150000,
    "EXCAVADORA 2015 LONKING 6150.": 150000,
    "PALA 2022 SINOMACH 933.": 100000
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

    IMPORTANTE: Lee los precios y tarifas desde la base de datos (precio_unitario y tarifa_hora)
    en lugar de usar valores predeterminados.
    """
    # Verificar que el proyecto existe
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        return None

    # Obtener entregas de áridos en el período con precio_unitario desde la BD
    entregas_aridos = db.query(
        EntregaArido.tipo_arido,
        func.sum(EntregaArido.cantidad).label('total_cantidad'),
        func.avg(EntregaArido.precio_unitario).label('precio_promedio')
    ).filter(
        EntregaArido.proyecto_id == proyecto_id,
        EntregaArido.fecha_entrega >= periodo_inicio,
        EntregaArido.fecha_entrega <= periodo_fin
    ).group_by(EntregaArido.tipo_arido).all()

    # Calcular detalles de áridos con precios REALES de la BD
    detalles_aridos = []
    total_aridos_m3 = 0.0
    total_importe_aridos = 0.0

    for tipo_arido, cantidad, precio_promedio in entregas_aridos:
        # Usar el precio de la BD, si es None usar el diccionario como fallback
        precio_unitario = precio_promedio if precio_promedio is not None else get_precio_arido(tipo_arido)
        importe = cantidad * precio_unitario

        detalles_aridos.append(DetalleAridoConPrecio(
            tipo_arido=tipo_arido,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            importe=importe
        ))

        total_aridos_m3 += cantidad
        total_importe_aridos += importe

    # Obtener horas de máquinas en el período con tarifa_hora desde la BD
    horas_maquinas = db.query(
        Maquina.id,
        Maquina.nombre,
        func.sum(ReporteLaboral.horas_turno).label('total_horas'),
        func.avg(ReporteLaboral.tarifa_hora).label('tarifa_promedio')
    ).join(
        ReporteLaboral, ReporteLaboral.maquina_id == Maquina.id
    ).filter(
        ReporteLaboral.proyecto_id == proyecto_id,
        ReporteLaboral.fecha_asignacion >= periodo_inicio,
        ReporteLaboral.fecha_asignacion <= periodo_fin
    ).group_by(Maquina.id, Maquina.nombre).all()

    # Calcular detalles de horas con tarifas REALES de la BD
    detalles_horas = []
    total_horas = 0.0
    total_importe_horas = 0.0

    for maquina_id, maquina_nombre, horas, tarifa_promedio in horas_maquinas:
        # Usar la tarifa de la BD, si es None usar el diccionario como fallback
        tarifa_hora = tarifa_promedio if tarifa_promedio is not None else get_tarifa_maquina(maquina_nombre)
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

def get_detalle_reporte(
    db: Session,
    reporte_id: int
) -> Optional[DetalleReporteResponse]:
    """
    Obtiene el detalle de items individuales de áridos y horas de un reporte
    """
    # Obtener el reporte
    reporte = db.query(ReporteCuentaCorriente).filter(
        ReporteCuentaCorriente.id == reporte_id
    ).first()

    if not reporte:
        return None

    # Obtener items individuales de áridos en el período
    entregas_aridos = db.query(EntregaArido).filter(
        EntregaArido.proyecto_id == reporte.proyecto_id,
        EntregaArido.fecha_entrega >= reporte.periodo_inicio,
        EntregaArido.fecha_entrega <= reporte.periodo_fin
    ).all()

    # Convertir áridos a ItemAridoDetalle
    items_aridos = []
    for arido in entregas_aridos:
        precio_unitario = arido.precio_unitario if arido.precio_unitario is not None else get_precio_arido(arido.tipo_arido)
        importe = arido.cantidad * precio_unitario

        items_aridos.append(ItemAridoDetalle(
            id=arido.id,
            tipo_arido=arido.tipo_arido,
            cantidad=arido.cantidad,
            precio_unitario=precio_unitario,
            importe=importe,
            pagado=arido.pagado if arido.pagado is not None else False,
            fecha=arido.fecha_entrega.date()
        ))

    # Obtener items individuales de horas en el período con información de máquina y usuario
    reportes_horas = db.query(ReporteLaboral).options(
        joinedload(ReporteLaboral.maquina),
        joinedload(ReporteLaboral.usuario)
    ).filter(
        ReporteLaboral.proyecto_id == reporte.proyecto_id,
        ReporteLaboral.fecha_asignacion >= reporte.periodo_inicio,
        ReporteLaboral.fecha_asignacion <= reporte.periodo_fin
    ).all()

    # Convertir horas a ItemHoraDetalle
    items_horas = []
    for reporte_hora in reportes_horas:
        tarifa_hora = reporte_hora.tarifa_hora if reporte_hora.tarifa_hora is not None else get_tarifa_maquina(reporte_hora.maquina.nombre)
        importe = reporte_hora.horas_turno * tarifa_hora

        items_horas.append(ItemHoraDetalle(
            id=reporte_hora.id,
            maquina_id=reporte_hora.maquina_id,
            maquina_nombre=reporte_hora.maquina.nombre,
            total_horas=reporte_hora.horas_turno,
            tarifa_hora=tarifa_hora,
            importe=importe,
            pagado=reporte_hora.pagado if reporte_hora.pagado is not None else False,
            fecha=reporte_hora.fecha_asignacion.date(),
            usuario_nombre=reporte_hora.usuario.nombre if reporte_hora.usuario else None
        ))

    return DetalleReporteResponse(
        items_aridos=items_aridos,
        items_horas=items_horas
    )

def actualizar_items_pago(
    db: Session,
    reporte_id: int,
    items_data: ActualizarItemsPagoRequest
) -> Optional[ActualizarItemsPagoResponse]:
    """
    Actualiza el estado de pago de items individuales (áridos y horas) de un reporte.

    Args:
        db: Sesión de base de datos
        reporte_id: ID del reporte
        items_data: Lista de items a actualizar con sus estados de pago

    Returns:
        Respuesta con el número de items actualizados y el reporte actualizado
    """
    # Verificar que el reporte existe
    reporte = db.query(ReporteCuentaCorriente).filter(
        ReporteCuentaCorriente.id == reporte_id
    ).first()

    if not reporte:
        return None

    aridos_actualizados = 0
    horas_actualizadas = 0

    # Actualizar items de áridos
    for item in items_data.items_aridos:
        arido = db.query(EntregaArido).filter(
            EntregaArido.id == item.item_id,
            EntregaArido.proyecto_id == reporte.proyecto_id
        ).first()

        if arido:
            arido.pagado = item.pagado
            aridos_actualizados += 1

    # Actualizar items de horas
    for item in items_data.items_horas:
        reporte_hora = db.query(ReporteLaboral).filter(
            ReporteLaboral.id == item.item_id,
            ReporteLaboral.proyecto_id == reporte.proyecto_id
        ).first()

        if reporte_hora:
            reporte_hora.pagado = item.pagado
            horas_actualizadas += 1

    # Guardar cambios de items individuales
    db.commit()

    # ============= CALCULAR ESTADO GENERAL DEL REPORTE =============
    # Obtener TODOS los items de áridos del período del reporte
    todos_aridos = db.query(EntregaArido).filter(
        EntregaArido.proyecto_id == reporte.proyecto_id,
        EntregaArido.fecha_entrega >= reporte.periodo_inicio,
        EntregaArido.fecha_entrega <= reporte.periodo_fin
    ).all()

    # Obtener TODOS los items de horas del período del reporte
    todos_reportes_horas = db.query(ReporteLaboral).filter(
        ReporteLaboral.proyecto_id == reporte.proyecto_id,
        ReporteLaboral.fecha_asignacion >= reporte.periodo_inicio,
        ReporteLaboral.fecha_asignacion <= reporte.periodo_fin
    ).all()

    # Calcular totales
    total_items = len(todos_aridos) + len(todos_reportes_horas)

    if total_items == 0:
        # Si no hay items, mantener el estado pendiente
        reporte.estado = "pendiente"
    else:
        # Contar items pagados
        aridos_pagados = sum(1 for arido in todos_aridos if arido.pagado)
        horas_pagadas = sum(1 for hora in todos_reportes_horas if hora.pagado)
        total_pagados = aridos_pagados + horas_pagadas

        # Determinar estado del reporte basándose en items pagados
        if total_pagados == 0:
            # Ningún item pagado
            reporte.estado = "pendiente"
        elif total_pagados == total_items:
            # Todos los items pagados
            reporte.estado = "pagado"
        else:
            # Algunos items pagados (pago parcial)
            reporte.estado = "parcial"

    # Guardar cambios del estado del reporte
    db.commit()
    db.refresh(reporte)

    return ActualizarItemsPagoResponse(
        aridos_actualizados=aridos_actualizados,
        horas_actualizadas=horas_actualizadas,
        reporte=ReporteCuentaCorrienteOut.model_validate(reporte)
    )
