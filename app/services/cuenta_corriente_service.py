from app.db.models import (
    ReporteCuentaCorriente,
    Proyecto,
    EntregaArido,
    ReporteLaboral,
    Maquina,
    ReporteItemArido,
    ReporteItemHora,
    PagoReporte,
    PrecioAridoProyecto,
    TarifaMaquinaProyecto,
)
from app.schemas.schemas import (
    ReporteCuentaCorrienteCreate,
    ReporteCuentaCorrienteUpdate,
    ReporteCuentaCorrientePatchRequest,
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
    ActualizarItemsPagoResponse,
    ReporteCuentaCorrienteConDetalleOut,
    PagoReporteCreate,
    PagoReporteOut,
    RegistrarPagoResponse
)
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal
import unicodedata

# Los precios de árido y tarifas de máquina viven en las tablas
# precio_arido_proyecto y tarifa_maquina_proyecto (por proyecto).
# No hay defaults hardcodeados: si no está configurado, el importe es 0
# y el registro se marca como precio_configurado=False para que el admin lo vea.

# Constantes vacías dejadas por compatibilidad con módulos que aún las importan
# (ej. cotizacion_service). No se usan para calcular importes de cuenta corriente.
PRECIOS_ARIDOS: Dict[str, float] = {}
TARIFAS_MAQUINAS: Dict[str, float] = {}


def _normalizar(texto: str) -> str:
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8').lower().strip()


def get_precio_arido(tipo_arido: str) -> float:
    """Compat: sin catálogo global de precios. Devuelve 0."""
    return 0.0


def get_tarifa_maquina(maquina_nombre: str) -> float:
    """Compat: sin catálogo global de tarifas. Devuelve 0."""
    return 0.0


def get_precio_arido_proyecto(db: Session, proyecto_id: int, tipo_arido: str) -> Optional[float]:
    """Retorna precio unitario configurado para (proyecto, tipo_arido) o None."""
    row = db.query(PrecioAridoProyecto).filter(
        PrecioAridoProyecto.proyecto_id == proyecto_id,
        PrecioAridoProyecto.tipo_arido == tipo_arido,
    ).first()
    return float(row.precio_unitario) if row else None


def get_tarifa_maquina_proyecto(db: Session, proyecto_id: int, maquina_id: int) -> Optional[float]:
    """Retorna tarifa por hora configurada para (proyecto, maquina) o None."""
    row = db.query(TarifaMaquinaProyecto).filter(
        TarifaMaquinaProyecto.proyecto_id == proyecto_id,
        TarifaMaquinaProyecto.maquina_id == maquina_id,
    ).first()
    return float(row.tarifa_hora) if row else None


def upsert_precio_arido_proyecto(db: Session, proyecto_id: int, tipo_arido: str, precio: float) -> PrecioAridoProyecto:
    row = db.query(PrecioAridoProyecto).filter(
        PrecioAridoProyecto.proyecto_id == proyecto_id,
        PrecioAridoProyecto.tipo_arido == tipo_arido,
    ).first()
    if row:
        row.precio_unitario = precio
    else:
        row = PrecioAridoProyecto(proyecto_id=proyecto_id, tipo_arido=tipo_arido, precio_unitario=precio)
        db.add(row)
    db.flush()
    return row


def upsert_tarifa_maquina_proyecto(db: Session, proyecto_id: int, maquina_id: int, tarifa: float) -> TarifaMaquinaProyecto:
    row = db.query(TarifaMaquinaProyecto).filter(
        TarifaMaquinaProyecto.proyecto_id == proyecto_id,
        TarifaMaquinaProyecto.maquina_id == maquina_id,
    ).first()
    if row:
        row.tarifa_hora = tarifa
    else:
        row = TarifaMaquinaProyecto(proyecto_id=proyecto_id, maquina_id=maquina_id, tarifa_hora=tarifa)
        db.add(row)
    db.flush()
    return row

def get_resumen_proyecto(
    db: Session,
    proyecto_id: int,
    periodo_inicio: date,
    periodo_fin: date,
    tipos_aridos: Optional[List[str]] = None,
    maquinas_ids: Optional[List[int]] = None
) -> Optional[ResumenProyectoSchema]:
    """
    Obtiene el resumen de áridos y horas de un proyecto con sus precios calculados
    para un período determinado.

    IMPORTANTE: Lee los precios y tarifas desde la base de datos (precio_unitario y tarifa_hora)
    en lugar de usar valores predeterminados.

    Args:
        db: Sesión de base de datos
        proyecto_id: ID del proyecto
        periodo_inicio: Fecha de inicio del período
        periodo_fin: Fecha de fin del período
        tipos_aridos: Lista opcional de tipos de áridos a incluir (filtro)
        maquinas_ids: Lista opcional de IDs de máquinas a incluir (filtro)
    """
    # Verificar que el proyecto existe
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        return None

    # IDs de entregas ya incluidas en un reporte pagado (se excluyen del pendiente)
    aridos_pagados_subq = db.query(ReporteItemArido.entrega_arido_id).join(
        ReporteCuentaCorriente, ReporteCuentaCorriente.id == ReporteItemArido.reporte_id
    ).filter(ReporteCuentaCorriente.estado == 'pagado').subquery()

    # Entregas de árido individuales del período
    query_aridos = db.query(EntregaArido).filter(
        EntregaArido.proyecto_id == proyecto_id,
        EntregaArido.fecha_entrega >= periodo_inicio,
        EntregaArido.fecha_entrega <= periodo_fin,
        EntregaArido.id.notin_(aridos_pagados_subq),
    )
    if tipos_aridos:
        query_aridos = query_aridos.filter(EntregaArido.tipo_arido.in_(tipos_aridos))
    entregas_aridos = query_aridos.order_by(EntregaArido.fecha_entrega.asc(), EntregaArido.id.asc()).all()

    # Cache de precios configurados por proyecto (evita 1 query por fila)
    precios_por_tipo: Dict[str, float] = {}
    for row in db.query(PrecioAridoProyecto).filter(PrecioAridoProyecto.proyecto_id == proyecto_id).all():
        precios_por_tipo[row.tipo_arido] = float(row.precio_unitario)

    detalles_aridos: List[DetalleAridoConPrecio] = []
    total_aridos_m3 = 0.0
    total_importe_aridos = 0.0

    for entrega in entregas_aridos:
        cantidad = float(entrega.cantidad or 0)
        # Precio efectivo: el guardado en el registro (histórico) tiene prioridad;
        # si es NULL, usar catálogo por proyecto; si tampoco hay, 0.
        precio_registro = entrega.precio_unitario
        precio_catalogo = precios_por_tipo.get(entrega.tipo_arido)
        if precio_registro is not None:
            precio_efectivo = float(precio_registro)
            configurado = True
        elif precio_catalogo is not None:
            precio_efectivo = precio_catalogo
            configurado = True
        else:
            precio_efectivo = 0.0
            configurado = False
        importe = cantidad * precio_efectivo

        detalles_aridos.append(DetalleAridoConPrecio(
            id=entrega.id,
            entrega_arido_id=entrega.id,
            tipo_arido=entrega.tipo_arido,
            cantidad=cantidad,
            precio_unitario=precio_efectivo,
            importe=importe,
            fecha=entrega.fecha_entrega.date() if hasattr(entrega.fecha_entrega, 'date') else entrega.fecha_entrega,
            precio_configurado=configurado,
        ))
        total_aridos_m3 += cantidad
        total_importe_aridos += importe

    # IDs de reportes laborales ya incluidos en un reporte pagado
    horas_pagadas_subq = db.query(ReporteItemHora.reporte_laboral_id).join(
        ReporteCuentaCorriente, ReporteCuentaCorriente.id == ReporteItemHora.reporte_id
    ).filter(ReporteCuentaCorriente.estado == 'pagado').subquery()

    query_horas = db.query(ReporteLaboral, Maquina.nombre.label('maquina_nombre')).join(
        Maquina, Maquina.id == ReporteLaboral.maquina_id
    ).filter(
        ReporteLaboral.proyecto_id == proyecto_id,
        ReporteLaboral.fecha_asignacion >= periodo_inicio,
        ReporteLaboral.fecha_asignacion <= periodo_fin,
        ReporteLaboral.id.notin_(horas_pagadas_subq),
    )
    if maquinas_ids:
        query_horas = query_horas.filter(ReporteLaboral.maquina_id.in_(maquinas_ids))
    reportes_labor = query_horas.order_by(ReporteLaboral.fecha_asignacion.asc(), ReporteLaboral.id.asc()).all()

    # Cache de tarifas configuradas por proyecto
    tarifas_por_maquina: Dict[int, float] = {}
    for row in db.query(TarifaMaquinaProyecto).filter(TarifaMaquinaProyecto.proyecto_id == proyecto_id).all():
        tarifas_por_maquina[row.maquina_id] = float(row.tarifa_hora)

    detalles_horas: List[DetalleHorasConTarifa] = []
    total_horas = 0.0
    total_importe_horas = 0.0

    for reporte_laboral, maquina_nombre in reportes_labor:
        horas = float(reporte_laboral.horas_turno or 0)
        tarifa_registro = reporte_laboral.tarifa_hora
        tarifa_catalogo = tarifas_por_maquina.get(reporte_laboral.maquina_id)
        if tarifa_registro is not None:
            tarifa_efectiva = float(tarifa_registro)
            configurado = True
        elif tarifa_catalogo is not None:
            tarifa_efectiva = tarifa_catalogo
            configurado = True
        else:
            tarifa_efectiva = 0.0
            configurado = False
        importe = horas * tarifa_efectiva

        detalles_horas.append(DetalleHorasConTarifa(
            id=reporte_laboral.id,
            reporte_laboral_id=reporte_laboral.id,
            maquina_id=reporte_laboral.maquina_id,
            maquina_nombre=maquina_nombre,
            total_horas=horas,
            tarifa_hora=tarifa_efectiva,
            importe=importe,
            fecha=reporte_laboral.fecha_asignacion.date() if hasattr(reporte_laboral.fecha_asignacion, 'date') else reporte_laboral.fecha_asignacion,
            precio_configurado=configurado,
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

def _enrich_reporte(reporte) -> ReporteCuentaCorrienteOut:
    monto_pagado = float(sum(p.monto for p in reporte.pagos))
    importe_total = float(reporte.importe_total or 0)
    reporte.monto_pagado = monto_pagado
    reporte.saldo_pendiente = importe_total - monto_pagado
    return ReporteCuentaCorrienteOut.model_validate(reporte)

def get_reportes(db: Session, proyecto_id: Optional[int] = None) -> List[ReporteCuentaCorrienteOut]:
    """Obtiene todos los reportes de cuenta corriente, opcionalmente filtrados por proyecto"""
    query = db.query(ReporteCuentaCorriente).options(joinedload(ReporteCuentaCorriente.pagos))

    if proyecto_id:
        query = query.filter(ReporteCuentaCorriente.proyecto_id == proyecto_id)

    reportes = query.order_by(ReporteCuentaCorriente.fecha_generacion.desc()).all()

    return [_enrich_reporte(r) for r in reportes]

def get_reporte(db: Session, reporte_id: int) -> Optional[ReporteCuentaCorrienteOut]:
    """Obtiene un reporte específico por ID"""
    reporte = db.query(ReporteCuentaCorriente).options(
        joinedload(ReporteCuentaCorriente.pagos)
    ).filter(ReporteCuentaCorriente.id == reporte_id).first()

    if reporte:
        return _enrich_reporte(reporte)
    return None

def create_reporte(db: Session, reporte_data: ReporteCuentaCorrienteCreate):
    """
    Crea un nuevo reporte de cuenta corriente calculando automáticamente
    los totales e importes del período especificado.

    Soporta selección de items específicos mediante:
    - aridos_seleccionados: Lista de tipos de áridos a incluir
    - maquinas_seleccionadas: Lista de IDs de máquinas a incluir

    Si no se especifican, se incluyen todos los items del período.
    """
    # Validar que el proyecto existe
    proyecto = db.query(Proyecto).filter(Proyecto.id == reporte_data.proyecto_id).first()
    if not proyecto:
        raise ValueError(f"No se encontró el proyecto con ID {reporte_data.proyecto_id}")

    # Validar tipos de áridos si se especificaron
    if reporte_data.aridos_seleccionados is not None and len(reporte_data.aridos_seleccionados) > 0:
        tipos_existentes = db.query(EntregaArido.tipo_arido).filter(
            EntregaArido.proyecto_id == reporte_data.proyecto_id,
            EntregaArido.fecha_entrega >= reporte_data.periodo_inicio,
            EntregaArido.fecha_entrega <= reporte_data.periodo_fin
        ).distinct().all()
        tipos_existentes = [t[0] for t in tipos_existentes]

        tipos_invalidos = [t for t in reporte_data.aridos_seleccionados if t not in tipos_existentes]
        if tipos_invalidos:
            raise ValueError(f"Tipos de áridos no encontrados en el período: {', '.join(tipos_invalidos)}")

    # Validar máquinas si se especificaron
    if reporte_data.maquinas_seleccionadas is not None and len(reporte_data.maquinas_seleccionadas) > 0:
        maquinas_existentes = db.query(ReporteLaboral.maquina_id).filter(
            ReporteLaboral.proyecto_id == reporte_data.proyecto_id,
            ReporteLaboral.fecha_asignacion >= reporte_data.periodo_inicio,
            ReporteLaboral.fecha_asignacion <= reporte_data.periodo_fin
        ).distinct().all()
        maquinas_existentes = [m[0] for m in maquinas_existentes]

        maquinas_invalidas = [m for m in reporte_data.maquinas_seleccionadas if m not in maquinas_existentes]
        if maquinas_invalidas:
            raise ValueError(f"Máquinas no encontradas en el período: {', '.join(map(str, maquinas_invalidas))}")

    # Obtener resumen del proyecto para el período con filtros opcionales
    resumen = get_resumen_proyecto(
        db,
        reporte_data.proyecto_id,
        reporte_data.periodo_inicio,
        reporte_data.periodo_fin,
        tipos_aridos=reporte_data.aridos_seleccionados,
        maquinas_ids=reporte_data.maquinas_seleccionadas
    )

    if not resumen:
        raise ValueError(f"No se encontró el proyecto con ID {reporte_data.proyecto_id}")

    # Validar que haya al menos un item para generar el reporte
    if resumen.total_aridos_m3 == 0 and resumen.total_horas == 0:
        raise ValueError("No se puede generar un reporte sin items. Debe seleccionar al menos un árido o máquina.")

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

    # Obtener los registros de áridos que pertenecen a este reporte
    query_aridos = db.query(EntregaArido).filter(
        EntregaArido.proyecto_id == reporte_data.proyecto_id,
        EntregaArido.fecha_entrega >= reporte_data.periodo_inicio,
        EntregaArido.fecha_entrega <= reporte_data.periodo_fin
    )
    if reporte_data.aridos_seleccionados and len(reporte_data.aridos_seleccionados) > 0:
        query_aridos = query_aridos.filter(EntregaArido.tipo_arido.in_(reporte_data.aridos_seleccionados))

    entregas_aridos = query_aridos.all()

    # Guardar relaciones de áridos
    for entrega in entregas_aridos:
        item_rel = ReporteItemArido(
            reporte_id=nuevo_reporte.id,
            entrega_arido_id=entrega.id
        )
        db.add(item_rel)

    # Obtener los reportes laborales que pertenecen a este reporte
    query_horas = db.query(ReporteLaboral).filter(
        ReporteLaboral.proyecto_id == reporte_data.proyecto_id,
        ReporteLaboral.fecha_asignacion >= reporte_data.periodo_inicio,
        ReporteLaboral.fecha_asignacion <= reporte_data.periodo_fin
    )
    if reporte_data.maquinas_seleccionadas and len(reporte_data.maquinas_seleccionadas) > 0:
        query_horas = query_horas.filter(ReporteLaboral.maquina_id.in_(reporte_data.maquinas_seleccionadas))

    reportes_horas = query_horas.all()

    # Guardar relaciones de horas
    for reporte_hora in reportes_horas:
        item_rel = ReporteItemHora(
            reporte_id=nuevo_reporte.id,
            reporte_laboral_id=reporte_hora.id
        )
        db.add(item_rel)

    # Commit de las relaciones
    db.commit()

    # Obtener items individuales filtrados para el response
    items_aridos = _get_items_aridos_filtrados(
        db,
        reporte_data.proyecto_id,
        reporte_data.periodo_inicio,
        reporte_data.periodo_fin,
        reporte_data.aridos_seleccionados
    )

    items_horas = _get_items_horas_filtrados(
        db,
        reporte_data.proyecto_id,
        reporte_data.periodo_inicio,
        reporte_data.periodo_fin,
        reporte_data.maquinas_seleccionadas
    )

    # Construir response con items incluidos
    return ReporteCuentaCorrienteConDetalleOut(
        **ReporteCuentaCorrienteOut.model_validate(nuevo_reporte).model_dump(),
        items_aridos=items_aridos,
        items_horas=items_horas
    )

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

def actualizar_reporte(
    db: Session,
    reporte_id: int,
    datos_actualizacion
) -> Optional['ReporteCuentaCorrienteOut']:
    """
    Actualiza campos editables de un reporte de cuenta corriente.

    Solo permite actualizar:
    - observaciones
    - numero_factura
    - fecha_pago (con validación de que sea >= fecha_generacion)

    Args:
        db: Sesión de base de datos
        reporte_id: ID del reporte a actualizar
        datos_actualizacion: Datos a actualizar (ReporteCuentaCorrientePatchRequest)

    Returns:
        Reporte actualizado o None si no existe

    Raises:
        ValueError: Si la fecha_pago es anterior a la fecha_generacion
    """
    # Buscar el reporte
    reporte = db.query(ReporteCuentaCorriente).filter(
        ReporteCuentaCorriente.id == reporte_id
    ).first()

    if not reporte:
        return None

    # Validar fecha_pago si se proporciona
    if datos_actualizacion.fecha_pago:
        fecha_pago_dt = datetime.strptime(datos_actualizacion.fecha_pago, '%Y-%m-%d').date()
        fecha_generacion_dt = reporte.fecha_generacion.date()

        if fecha_pago_dt < fecha_generacion_dt:
            raise ValueError(
                "La fecha de pago no puede ser anterior a la fecha de generación del reporte"
            )

        reporte.fecha_pago = fecha_pago_dt

    # Actualizar solo los campos proporcionados
    if datos_actualizacion.observaciones is not None:
        reporte.observaciones = datos_actualizacion.observaciones

    if datos_actualizacion.numero_factura is not None:
        reporte.numero_factura = datos_actualizacion.numero_factura

    # Actualizar timestamp
    reporte.updated = datetime.now()

    # Guardar en base de datos
    db.commit()
    db.refresh(reporte)

    # Retornar reporte actualizado
    return ReporteCuentaCorrienteOut.model_validate(reporte)

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

def _get_items_aridos_filtrados(
    db: Session,
    proyecto_id: int,
    periodo_inicio: date,
    periodo_fin: date,
    tipos_aridos: Optional[List[str]] = None
) -> List[ItemAridoDetalle]:
    """
    Obtiene los items individuales de áridos con filtros opcionales.
    Función auxiliar privada para create_reporte.
    """
    query = db.query(EntregaArido).filter(
        EntregaArido.proyecto_id == proyecto_id,
        EntregaArido.fecha_entrega >= periodo_inicio,
        EntregaArido.fecha_entrega <= periodo_fin
    )

    # Aplicar filtro de tipos si se especifica
    if tipos_aridos and len(tipos_aridos) > 0:
        query = query.filter(EntregaArido.tipo_arido.in_(tipos_aridos))

    entregas_aridos = query.all()

    items_aridos = []
    for arido in entregas_aridos:
        if arido.precio_unitario is not None:
            precio_unitario = float(arido.precio_unitario)
        else:
            catalogo = get_precio_arido_proyecto(db, arido.proyecto_id, arido.tipo_arido)
            precio_unitario = catalogo if catalogo is not None else 0.0
        importe = float(arido.cantidad or 0) * precio_unitario

        items_aridos.append(ItemAridoDetalle(
            id=arido.id,
            tipo_arido=arido.tipo_arido,
            cantidad=arido.cantidad,
            precio_unitario=precio_unitario,
            importe=importe,
            pagado=arido.pagado if arido.pagado is not None else False,
            fecha=arido.fecha_entrega.date()
        ))

    return items_aridos

def _get_items_horas_filtrados(
    db: Session,
    proyecto_id: int,
    periodo_inicio: date,
    periodo_fin: date,
    maquinas_ids: Optional[List[int]] = None
) -> List[ItemHoraDetalle]:
    """
    Obtiene los items individuales de horas con filtros opcionales.
    Función auxiliar privada para create_reporte.
    """
    query = db.query(ReporteLaboral).options(
        joinedload(ReporteLaboral.maquina),
        joinedload(ReporteLaboral.usuario)
    ).filter(
        ReporteLaboral.proyecto_id == proyecto_id,
        ReporteLaboral.fecha_asignacion >= periodo_inicio,
        ReporteLaboral.fecha_asignacion <= periodo_fin
    )

    # Aplicar filtro de máquinas si se especifica
    if maquinas_ids and len(maquinas_ids) > 0:
        query = query.filter(ReporteLaboral.maquina_id.in_(maquinas_ids))

    reportes_horas = query.all()

    items_horas = []
    for reporte_hora in reportes_horas:
        if reporte_hora.tarifa_hora is not None:
            tarifa_hora = float(reporte_hora.tarifa_hora)
        else:
            catalogo = get_tarifa_maquina_proyecto(db, reporte_hora.proyecto_id, reporte_hora.maquina_id)
            tarifa_hora = catalogo if catalogo is not None else 0.0
        importe = float(reporte_hora.horas_turno or 0) * tarifa_hora

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

    return items_horas

def get_detalle_reporte(
    db: Session,
    reporte_id: int
) -> Optional[DetalleReporteResponse]:
    """
    Obtiene el detalle de items individuales de áridos y horas de un reporte.

    IMPORTANTE: Lee los items desde las tablas relacionales (reporte_items_aridos, reporte_items_horas)
    para obtener SOLO los items que fueron seleccionados al crear el reporte.
    """
    # Obtener el reporte
    reporte = db.query(ReporteCuentaCorriente).filter(
        ReporteCuentaCorriente.id == reporte_id
    ).first()

    if not reporte:
        return None

    # Obtener items de áridos desde la tabla relacional
    items_aridos_rel = db.query(ReporteItemArido).filter(
        ReporteItemArido.reporte_id == reporte_id
    ).all()

    # Obtener las entregas de áridos correspondientes
    entregas_aridos = []
    for item_rel in items_aridos_rel:
        arido = db.query(EntregaArido).filter(EntregaArido.id == item_rel.entrega_arido_id).first()
        if arido:
            entregas_aridos.append(arido)

    # Convertir áridos a ItemAridoDetalle
    items_aridos = []
    for arido in entregas_aridos:
        if arido.precio_unitario is not None:
            precio_unitario = float(arido.precio_unitario)
        else:
            catalogo = get_precio_arido_proyecto(db, arido.proyecto_id, arido.tipo_arido)
            precio_unitario = catalogo if catalogo is not None else 0.0
        importe = float(arido.cantidad or 0) * precio_unitario

        items_aridos.append(ItemAridoDetalle(
            id=arido.id,
            tipo_arido=arido.tipo_arido,
            cantidad=arido.cantidad,
            precio_unitario=precio_unitario,
            importe=importe,
            pagado=arido.pagado if arido.pagado is not None else False,
            fecha=arido.fecha_entrega.date()
        ))

    # Obtener items de horas desde la tabla relacional
    items_horas_rel = db.query(ReporteItemHora).filter(
        ReporteItemHora.reporte_id == reporte_id
    ).all()

    # Obtener los reportes laborales correspondientes
    reportes_horas = []
    for item_rel in items_horas_rel:
        reporte_hora = db.query(ReporteLaboral).options(
            joinedload(ReporteLaboral.maquina),
            joinedload(ReporteLaboral.usuario)
        ).filter(ReporteLaboral.id == item_rel.reporte_laboral_id).first()
        if reporte_hora:
            reportes_horas.append(reporte_hora)

    # Convertir horas a ItemHoraDetalle
    items_horas = []
    for reporte_hora in reportes_horas:
        if reporte_hora.tarifa_hora is not None:
            tarifa_hora = float(reporte_hora.tarifa_hora)
        else:
            catalogo = get_tarifa_maquina_proyecto(db, reporte_hora.proyecto_id, reporte_hora.maquina_id)
            tarifa_hora = catalogo if catalogo is not None else 0.0
        importe = float(reporte_hora.horas_turno or 0) * tarifa_hora

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
    # Obtener SOLO los items de áridos que pertenecen a este reporte (desde tabla relacional)
    items_aridos_rel = db.query(ReporteItemArido).filter(
        ReporteItemArido.reporte_id == reporte_id
    ).all()

    todos_aridos = []
    for item_rel in items_aridos_rel:
        arido = db.query(EntregaArido).filter(EntregaArido.id == item_rel.entrega_arido_id).first()
        if arido:
            todos_aridos.append(arido)

    # Obtener SOLO los items de horas que pertenecen a este reporte (desde tabla relacional)
    items_horas_rel = db.query(ReporteItemHora).filter(
        ReporteItemHora.reporte_id == reporte_id
    ).all()

    todos_reportes_horas = []
    for item_rel in items_horas_rel:
        reporte_hora = db.query(ReporteLaboral).filter(ReporteLaboral.id == item_rel.reporte_laboral_id).first()
        if reporte_hora:
            todos_reportes_horas.append(reporte_hora)

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

def registrar_pago(
    db: Session,
    reporte_id: int,
    pago_data: PagoReporteCreate
) -> Optional[RegistrarPagoResponse]:
    """
    Registra un pago para un reporte y actualiza automáticamente el estado del reporte.

    Lógica de actualización de estado:
    - Si total_pagado >= importe_total → estado = PAGADO
    - Si total_pagado > 0 → estado = PARCIAL
    - Si total_pagado = 0 → estado = PENDIENTE

    Args:
        db: Sesión de base de datos
        reporte_id: ID del reporte
        pago_data: Datos del pago a crear

    Returns:
        Respuesta con el pago creado, reporte actualizado, total pagado y saldo pendiente
    """
    # Verificar que el reporte existe
    reporte = db.query(ReporteCuentaCorriente).filter(
        ReporteCuentaCorriente.id == reporte_id
    ).first()

    if not reporte:
        return None

    # Crear el nuevo pago
    nuevo_pago = PagoReporte(
        reporte_id=reporte_id,
        monto=Decimal(str(pago_data.monto)),
        fecha=pago_data.fecha,
        observaciones=pago_data.observaciones
    )

    db.add(nuevo_pago)
    db.flush()  # Para obtener el ID sin hacer commit todavía

    # Calcular total pagado (sumar todos los pagos del reporte)
    total_pagado = db.query(func.sum(PagoReporte.monto)).filter(
        PagoReporte.reporte_id == reporte_id
    ).scalar() or Decimal('0.0')

    # Actualizar estado del reporte según el total pagado
    importe_total = reporte.importe_total or Decimal('0.0')

    if total_pagado >= importe_total:
        reporte.estado = "pagado"
        # Si el reporte se marca como pagado y no tiene fecha_pago, asignarla
        if not reporte.fecha_pago:
            reporte.fecha_pago = pago_data.fecha
    elif total_pagado > 0:
        reporte.estado = "parcial"
    else:
        reporte.estado = "pendiente"

    # Guardar cambios
    db.commit()
    db.refresh(nuevo_pago)
    db.refresh(reporte)

    # Calcular saldo pendiente
    saldo_pendiente = float(importe_total - total_pagado)

    return RegistrarPagoResponse(
        pago=PagoReporteOut.model_validate(nuevo_pago),
        reporte_actualizado=ReporteCuentaCorrienteOut.model_validate(reporte),
        total_pagado=float(total_pagado),
        saldo_pendiente=saldo_pendiente
    )

def listar_pagos_reporte(
    db: Session,
    reporte_id: int
) -> Optional[List[PagoReporteOut]]:
    """
    Lista todos los pagos asociados a un reporte específico.

    Args:
        db: Sesión de base de datos
        reporte_id: ID del reporte

    Returns:
        Lista de pagos del reporte ordenados por fecha de registro (más recientes primero)
    """
    # Verificar que el reporte existe
    reporte = db.query(ReporteCuentaCorriente).filter(
        ReporteCuentaCorriente.id == reporte_id
    ).first()

    if not reporte:
        return None

    # Obtener todos los pagos del reporte
    pagos = db.query(PagoReporte).filter(
        PagoReporte.reporte_id == reporte_id
    ).order_by(PagoReporte.fecha_registro.desc()).all()

    return [PagoReporteOut.model_validate(p) for p in pagos]
