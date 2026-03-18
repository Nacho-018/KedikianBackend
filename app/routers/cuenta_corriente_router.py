from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional
from datetime import date, datetime
from app.db.dependencies import get_db
from app.db.models import Proyecto, EntregaArido, ReporteLaboral
from app.schemas.schemas import (
    ReporteCuentaCorrienteCreate,
    ReporteCuentaCorrienteUpdate,
    ReporteCuentaCorrientePatchRequest,
    ReporteCuentaCorrienteOut,
    ResumenProyectoSchema,
    PrecioAridoSchema,
    TarifaMaquinaSchema,
    ActualizarPrecioAridoRequest,
    ActualizarPrecioAridoResponse,
    ActualizarTarifaMaquinaRequest,
    ActualizarTarifaMaquinaResponse,
    DetalleReporteResponse,
    ActualizarItemsPagoRequest,
    ActualizarItemsPagoResponse,
    ReporteCuentaCorrienteConDetalleOut,
    PagoReporteCreate,
    PagoReporteOut,
    RegistrarPagoResponse
)
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.services import cuenta_corriente_service
from app.security.auth import get_current_user
from app.db.models.pago_reporte import PagoReporte
from decimal import Decimal
import io
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
import os

router = APIRouter(
    prefix="/cuenta-corriente",
    tags=["Cuenta Corriente"],
    dependencies=[Depends(get_current_user)]
)

# ============= Endpoints de Precios y Tarifas =============

@router.get("/aridos/precios", response_model=List[PrecioAridoSchema])
def get_precios_aridos(session: Session = Depends(get_db)):
    """
    Obtiene todos los precios de áridos disponibles por m³
    """
    return cuenta_corriente_service.get_todos_precios_aridos()

@router.get("/maquinas/{maquina_id}/tarifa", response_model=TarifaMaquinaSchema)
def get_tarifa_maquina(
    maquina_id: int,
    session: Session = Depends(get_db)
):
    """
    Obtiene la tarifa por hora de una máquina específica
    """
    tarifa = cuenta_corriente_service.get_tarifa_maquina_por_id(session, maquina_id)

    if not tarifa:
        raise HTTPException(status_code=404, detail=f"Máquina con ID {maquina_id} no encontrada")

    return tarifa

# ============= Endpoints de Resumen de Proyecto =============

@router.get("/proyectos/{proyecto_id}/resumen", response_model=ResumenProyectoSchema)
def get_resumen_proyecto(
    proyecto_id: int,
    periodo_inicio: date = Query(..., description="Fecha de inicio del período"),
    periodo_fin: date = Query(..., description="Fecha de fin del período"),
    session: Session = Depends(get_db)
):
    """
    Obtiene el resumen de áridos y horas de un proyecto con precios calculados
    para un período determinado.

    Retorna:
    - Detalle de áridos entregados con sus precios por m³
    - Detalle de horas de máquinas con sus tarifas por hora
    - Totales e importes calculados
    """
    resumen = cuenta_corriente_service.get_resumen_proyecto(
        session,
        proyecto_id,
        periodo_inicio,
        periodo_fin
    )

    if not resumen:
        raise HTTPException(
            status_code=404,
            detail=f"Proyecto con ID {proyecto_id} no encontrado"
        )

    return resumen

# ============= Endpoints de Reportes =============

@router.get("/reportes", response_model=List[ReporteCuentaCorrienteOut])
def get_reportes(
    proyecto_id: Optional[int] = Query(None, description="Filtrar por proyecto"),
    session: Session = Depends(get_db)
):
    """
    Lista todos los reportes de cuenta corriente generados.
    Opcionalmente filtra por proyecto.
    """
    return cuenta_corriente_service.get_reportes(session, proyecto_id)

@router.get("/reportes/{reporte_id}", response_model=ReporteCuentaCorrienteOut)
def get_reporte(
    reporte_id: int,
    session: Session = Depends(get_db)
):
    """
    Obtiene un reporte específico por su ID
    """
    reporte = cuenta_corriente_service.get_reporte(session, reporte_id)

    if not reporte:
        raise HTTPException(
            status_code=404,
            detail=f"Reporte con ID {reporte_id} no encontrado"
        )

    return reporte

@router.get("/reportes/{reporte_id}/detalle", response_model=DetalleReporteResponse)
def get_detalle_reporte(
    reporte_id: int,
    session: Session = Depends(get_db)
):
    """
    Obtiene el detalle de items individuales (áridos y horas) de un reporte.

    Retorna:
    - items_aridos: Lista de entregas de áridos con id, tipo, cantidad, precio, importe, pagado, fecha
    - items_horas: Lista de reportes de horas con id, maquina_id, nombre, horas, tarifa, importe, pagado, fecha, usuario
    """
    detalle = cuenta_corriente_service.get_detalle_reporte(session, reporte_id)

    if not detalle:
        raise HTTPException(
            status_code=404,
            detail=f"Reporte con ID {reporte_id} no encontrado"
        )

    return detalle

@router.put("/reportes/{reporte_id}/items-pago", response_model=ActualizarItemsPagoResponse)
def actualizar_items_pago(
    reporte_id: int,
    items_data: ActualizarItemsPagoRequest,
    session: Session = Depends(get_db)
):
    """
    Actualiza el estado de pago de items individuales (áridos y horas) de un reporte.

    Permite marcar items específicos como pagados o no pagados, actualizando las columnas
    'pagado' en las tablas entrega_arido y reporte_laboral.

    Args:
        reporte_id: ID del reporte
        items_data: Lista de items de áridos y horas con sus estados de pago

    Returns:
        Resumen de actualización con número de items actualizados y reporte actualizado
    """
    resultado = cuenta_corriente_service.actualizar_items_pago(
        session,
        reporte_id,
        items_data
    )

    if not resultado:
        raise HTTPException(
            status_code=404,
            detail=f"Reporte con ID {reporte_id} no encontrado"
        )

    return resultado

@router.post("/reportes", response_model=ReporteCuentaCorrienteConDetalleOut, status_code=201)
def create_reporte(
    reporte_data: ReporteCuentaCorrienteCreate,
    session: Session = Depends(get_db)
):
    """
    Genera un nuevo reporte de cuenta corriente para un proyecto y período específico.

    El reporte calculará automáticamente:
    - Total de áridos entregados (m³)
    - Total de horas de máquinas
    - Importes según precios y tarifas configurados

    Soporta selección de items específicos mediante:
    - aridos_seleccionados: Lista de tipos de áridos a incluir (opcional)
    - maquinas_seleccionadas: Lista de IDs de máquinas a incluir (opcional)

    Si no se especifican, se incluyen todos los items del período.
    """
    try:
        return cuenta_corriente_service.create_reporte(session, reporte_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el reporte: {str(e)}")

@router.put("/reportes/{reporte_id}/estado", response_model=ReporteCuentaCorrienteOut)
def update_estado_reporte(
    reporte_id: int,
    reporte_update: ReporteCuentaCorrienteUpdate,
    session: Session = Depends(get_db)
):
    """
    Actualiza el estado de un reporte (pendiente/pagado) y otros campos opcionales.

    Permite actualizar:
    - Estado (pendiente/pagado)
    - Observaciones
    - Número de factura
    - Fecha de pago
    """
    reporte = cuenta_corriente_service.update_reporte_estado(
        session,
        reporte_id,
        reporte_update
    )

    if not reporte:
        raise HTTPException(
            status_code=404,
            detail=f"Reporte con ID {reporte_id} no encontrado"
        )

    return reporte

@router.patch("/reportes/{reporte_id}", response_model=ReporteCuentaCorrienteOut)
def actualizar_reporte(
    reporte_id: int,
    datos: ReporteCuentaCorrientePatchRequest,
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Actualiza campos editables de un reporte de cuenta corriente.

    Solo administradores pueden usar este endpoint.

    Campos editables:
    - observaciones: Observaciones del reporte
    - numero_factura: Número de factura asociada
    - fecha_pago: Fecha de pago (debe ser >= fecha_generacion)

    Todos los campos son opcionales. Solo se actualizan los campos proporcionados.
    """
    # Verificar permisos de administrador
    if not current_user.roles or "administrador" not in current_user.roles:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos de administrador para realizar esta acción"
        )

    try:
        reporte = cuenta_corriente_service.actualizar_reporte(
            session,
            reporte_id,
            datos
        )

        if not reporte:
            raise HTTPException(
                status_code=404,
                detail="Reporte no encontrado"
            )

        return reporte

    except ValueError as e:
        # Errores de validación (ej: fecha_pago anterior a fecha_generacion)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        # Otros errores
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar reporte: {str(e)}"
        )

@router.delete("/reportes/{reporte_id}", status_code=204)
def delete_reporte(
    reporte_id: int,
    session: Session = Depends(get_db)
):
    """
    Elimina un reporte de cuenta corriente
    """
    success = cuenta_corriente_service.delete_reporte(session, reporte_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Reporte con ID {reporte_id} no encontrado"
        )

    return JSONResponse(
        status_code=204,
        content={"message": "Reporte eliminado exitosamente"}
    )

# ============= Endpoints de Pagos de Reportes =============

@router.post("/reportes/{reporte_id}/pagos", response_model=RegistrarPagoResponse, status_code=201)
def registrar_pago(
    reporte_id: int,
    pago_data: PagoReporteCreate,
    session: Session = Depends(get_db)
):
    """
    Registra un pago para un reporte de cuenta corriente.

    Al registrar el pago, el sistema:
    1. Inserta el pago en la base de datos
    2. Calcula el total pagado sumando todos los pagos del reporte
    3. Actualiza automáticamente el estado del reporte:
       - PAGADO: si total_pagado >= importe_total
       - PARCIAL: si total_pagado > 0 pero < importe_total
       - PENDIENTE: si total_pagado = 0
    4. Retorna el pago creado junto con el estado actualizado del reporte

    Args:
        reporte_id: ID del reporte
        pago_data: Datos del pago (monto, fecha, observaciones)

    Returns:
        Pago creado, reporte actualizado, total pagado y saldo pendiente
    """
    resultado = cuenta_corriente_service.registrar_pago(
        session,
        reporte_id,
        pago_data
    )

    if not resultado:
        raise HTTPException(
            status_code=404,
            detail=f"Reporte con ID {reporte_id} no encontrado"
        )

    return resultado

@router.get("/reportes/{reporte_id}/pagos", response_model=List[PagoReporteOut])
def listar_pagos(
    reporte_id: int,
    session: Session = Depends(get_db)
):
    """
    Lista todos los pagos asociados a un reporte de cuenta corriente.

    Los pagos se retornan ordenados por fecha de registro (más recientes primero).

    Args:
        reporte_id: ID del reporte

    Returns:
        Lista de pagos del reporte
    """
    pagos = cuenta_corriente_service.listar_pagos_reporte(session, reporte_id)

    if pagos is None:
        raise HTTPException(
            status_code=404,
            detail=f"Reporte con ID {reporte_id} no encontrado"
        )

    return pagos

# ============= Endpoints de Exportación =============

@router.get("/reportes/{reporte_id}/excel")
def exportar_reporte_excel(
    reporte_id: int,
    session: Session = Depends(get_db)
):
    """
    Exporta un reporte de cuenta corriente a formato Excel (.xlsx)
    """
    # Obtener el reporte
    reporte = cuenta_corriente_service.get_reporte(session, reporte_id)
    if not reporte:
        raise HTTPException(
            status_code=404,
            detail=f"Reporte con ID {reporte_id} no encontrado"
        )

    # Obtener el resumen detallado
    resumen = cuenta_corriente_service.get_resumen_proyecto(
        session,
        reporte.proyecto_id,
        reporte.periodo_inicio,
        reporte.periodo_fin
    )

    if not resumen:
        raise HTTPException(status_code=404, detail="No se pudo obtener el resumen del proyecto")

    # Obtener todos los pagos del reporte
    pagos = session.query(PagoReporte).filter(
        PagoReporte.reporte_id == reporte_id
    ).order_by(PagoReporte.fecha.desc()).all()

    # Calcular total pagado
    total_pagado = session.query(func.sum(PagoReporte.monto)).filter(
        PagoReporte.reporte_id == reporte_id
    ).scalar() or Decimal('0.0')

    # Calcular saldo pendiente
    saldo_pendiente = (reporte.importe_total or Decimal('0.0')) - total_pagado

    # Crear el archivo Excel en memoria
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Información general
        info_data = {
            'Campo': ['Proyecto', 'Período', 'Fecha Generación', 'Estado', 'N° Factura', 'Total Pagado', 'Saldo Pendiente'],
            'Valor': [
                resumen.proyecto_nombre,
                f"{reporte.periodo_inicio} - {reporte.periodo_fin}",
                reporte.fecha_generacion.strftime("%d/%m/%Y %H:%M"),
                reporte.estado,
                reporte.numero_factura or 'N/A',
                f"${float(total_pagado):,.2f}",
                f"${float(saldo_pendiente):,.2f}"
            ]
        }
        df_info = pd.DataFrame(info_data)
        df_info.to_excel(writer, sheet_name='Información', index=False)

        # Detalle de áridos
        if resumen.aridos:
            aridos_data = {
                'Tipo Árido': [a.tipo_arido for a in resumen.aridos],
                'Cantidad (m³)': [a.cantidad for a in resumen.aridos],
                'Precio Unitario': [a.precio_unitario for a in resumen.aridos],
                'Importe': [a.importe for a in resumen.aridos]
            }
            df_aridos = pd.DataFrame(aridos_data)
            df_aridos.to_excel(writer, sheet_name='Áridos', index=False)

        # Detalle de horas de máquinas
        if resumen.horas_maquinas:
            horas_data = {
                'Máquina': [h.maquina_nombre for h in resumen.horas_maquinas],
                'Total Horas': [h.total_horas for h in resumen.horas_maquinas],
                'Tarifa/Hora': [h.tarifa_hora for h in resumen.horas_maquinas],
                'Importe': [h.importe for h in resumen.horas_maquinas]
            }
            df_horas = pd.DataFrame(horas_data)
            df_horas.to_excel(writer, sheet_name='Horas Máquinas', index=False)

        # Detalle de pagos (si hay pagos)
        if pagos:
            pagos_data = {
                'Fecha de Pago': [p.fecha.strftime("%d/%m/%Y") for p in pagos],
                'Monto': [f"${float(p.monto):,.2f}" for p in pagos],
                'Observaciones': [p.observaciones or 'Sin observaciones' for p in pagos],
                'Fecha de Registro': [p.fecha_registro.strftime("%d/%m/%Y %H:%M") if p.fecha_registro else 'N/A' for p in pagos]
            }
            df_pagos = pd.DataFrame(pagos_data)
            df_pagos.to_excel(writer, sheet_name='Pagos', index=False)

        # Resumen de totales
        totales_data = {
            'Concepto': [
                'Total Áridos (m³)',
                'Importe Áridos',
                'Total Horas',
                'Importe Horas',
                'IMPORTE TOTAL',
                '--- Pagos ---',
                'Total Pagado',
                'Saldo Pendiente'
            ],
            'Valor': [
                resumen.total_aridos_m3,
                resumen.total_importe_aridos,
                resumen.total_horas,
                resumen.total_importe_horas,
                resumen.importe_total,
                '',
                f"${float(total_pagado):,.2f}",
                f"${float(saldo_pendiente):,.2f}"
            ]
        }
        df_totales = pd.DataFrame(totales_data)
        df_totales.to_excel(writer, sheet_name='Totales', index=False)

    output.seek(0)

    filename = f"reporte_cuenta_corriente_{reporte_id}_{resumen.proyecto_nombre.replace(' ', '_')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/reportes/{reporte_id}/pdf")
def exportar_reporte_pdf(
    reporte_id: int,
    session: Session = Depends(get_db)
):
    """
    Exporta un reporte de cuenta corriente a formato PDF
    """
    # Obtener el reporte
    reporte = cuenta_corriente_service.get_reporte(session, reporte_id)
    if not reporte:
        raise HTTPException(
            status_code=404,
            detail=f"Reporte con ID {reporte_id} no encontrado"
        )

    # Obtener el resumen detallado
    resumen = cuenta_corriente_service.get_resumen_proyecto(
        session,
        reporte.proyecto_id,
        reporte.periodo_inicio,
        reporte.periodo_fin
    )

    if not resumen:
        raise HTTPException(status_code=404, detail="No se pudo obtener el resumen del proyecto")

    # Obtener todos los pagos del reporte
    pagos = session.query(PagoReporte).filter(
        PagoReporte.reporte_id == reporte_id
    ).order_by(PagoReporte.fecha.desc()).all()

    # Calcular total pagado
    total_pagado = session.query(func.sum(PagoReporte.monto)).filter(
        PagoReporte.reporte_id == reporte_id
    ).scalar() or Decimal('0.0')

    # Calcular saldo pendiente
    saldo_pendiente = (reporte.importe_total or Decimal('0.0')) - total_pagado

    # Crear el PDF en memoria
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Logo en el encabezado (si existe)
    logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'assets', 'logo-kedikian.png')
    if os.path.exists(logo_path):
        try:
            # El logo es casi cuadrado (536x528), mantener proporción 1:1
            logo = Image(logo_path, width=120, height=120)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 0.2*inch))
        except Exception as e:
            # Si hay error al cargar la imagen, continuar sin logo
            print(f"Advertencia: No se pudo cargar el logo: {e}")

    # Título
    title = Paragraph(f"<b>REPORTE DE CUENTA CORRIENTE</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))

    # Información general
    info_text = f"""
    <b>Proyecto:</b> {resumen.proyecto_nombre}<br/>
    <b>Período:</b> {reporte.periodo_inicio} al {reporte.periodo_fin}<br/>
    <b>Fecha de Generación:</b> {reporte.fecha_generacion.strftime("%d/%m/%Y %H:%M")}<br/>
    <b>Estado:</b> {reporte.estado.upper()}<br/>
    <b>N° Factura:</b> {reporte.numero_factura or 'N/A'}<br/>
    <b>Total Pagado:</b> ${float(total_pagado):,.2f}<br/>
    <b>Saldo Pendiente:</b> ${float(saldo_pendiente):,.2f}
    """
    info_para = Paragraph(info_text, styles['Normal'])
    elements.append(info_para)
    elements.append(Spacer(1, 0.3*inch))

    # Tabla de áridos
    if resumen.aridos:
        aridos_title = Paragraph("<b>DETALLE DE ÁRIDOS</b>", styles['Heading2'])
        elements.append(aridos_title)
        elements.append(Spacer(1, 0.1*inch))

        aridos_data = [['Tipo Árido', 'Cantidad (m³)', 'Precio/m³', 'Importe']]
        for arido in resumen.aridos:
            aridos_data.append([
                arido.tipo_arido,
                f"{arido.cantidad:.2f}",
                f"${arido.precio_unitario:,.2f}",
                f"${arido.importe:,.2f}"
            ])

        aridos_table = Table(aridos_data)
        aridos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(aridos_table)
        elements.append(Spacer(1, 0.3*inch))

    # Tabla de horas de máquinas
    if resumen.horas_maquinas:
        horas_title = Paragraph("<b>DETALLE DE HORAS DE MÁQUINAS</b>", styles['Heading2'])
        elements.append(horas_title)
        elements.append(Spacer(1, 0.1*inch))

        horas_data = [['Máquina', 'Total Horas', 'Tarifa/Hora', 'Importe']]
        for hora in resumen.horas_maquinas:
            horas_data.append([
                hora.maquina_nombre,
                f"{hora.total_horas:.2f}",
                f"${hora.tarifa_hora:,.2f}",
                f"${hora.importe:,.2f}"
            ])

        horas_table = Table(horas_data)
        horas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(horas_table)
        elements.append(Spacer(1, 0.3*inch))

    # Tabla de pagos (si hay pagos)
    if pagos:
        pagos_title = Paragraph("<b>HISTORIAL DE PAGOS</b>", styles['Heading2'])
        elements.append(pagos_title)
        elements.append(Spacer(1, 0.1*inch))

        pagos_data = [['Fecha de Pago', 'Monto', 'Observaciones', 'Fecha de Registro']]
        for pago in pagos:
            pagos_data.append([
                pago.fecha.strftime("%d/%m/%Y"),
                f"${float(pago.monto):,.2f}",
                pago.observaciones or 'Sin observaciones',
                pago.fecha_registro.strftime("%d/%m/%Y %H:%M") if pago.fecha_registro else 'N/A'
            ])

        pagos_table = Table(pagos_data)
        pagos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(pagos_table)
        elements.append(Spacer(1, 0.3*inch))

    # Totales
    totales_title = Paragraph("<b>TOTALES</b>", styles['Heading2'])
    elements.append(totales_title)
    elements.append(Spacer(1, 0.1*inch))

    totales_data = [
        ['Concepto', 'Valor'],
        ['Total Áridos (m³)', f"{resumen.total_aridos_m3:.2f}"],
        ['Importe Áridos', f"${resumen.total_importe_aridos:,.2f}"],
        ['Total Horas', f"{resumen.total_horas:.2f}"],
        ['Importe Horas', f"${resumen.total_importe_horas:,.2f}"],
        ['IMPORTE TOTAL', f"${resumen.importe_total:,.2f}"],
        ['--- Pagos ---', ''],
        ['Total Pagado', f"${float(total_pagado):,.2f}"],
        ['Saldo Pendiente', f"${float(saldo_pendiente):,.2f}"]
    ]

    totales_table = Table(totales_data)
    totales_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(totales_table)

    # Observaciones
    if reporte.observaciones:
        elements.append(Spacer(1, 0.3*inch))
        obs_title = Paragraph("<b>OBSERVACIONES</b>", styles['Heading2'])
        elements.append(obs_title)
        obs_text = Paragraph(reporte.observaciones, styles['Normal'])
        elements.append(obs_text)

    # Generar PDF
    doc.build(elements)
    buffer.seek(0)

    filename = f"reporte_cuenta_corriente_{reporte_id}_{resumen.proyecto_nombre.replace(' ', '_')}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ============= ENDPOINTS PARA ACTUALIZACIÓN DE PRECIOS Y TARIFAS =============

@router.put("/proyectos/{proyecto_id}/aridos/actualizar-precio", response_model=ActualizarPrecioAridoResponse)
async def actualizar_precio_arido(
    proyecto_id: int,
    data: ActualizarPrecioAridoRequest,
    db: Session = Depends(get_db)
):
    """
    Actualiza el precio unitario de todos los registros de áridos
    de un tipo específico en un período determinado.

    Args:
        proyecto_id: ID del proyecto
        data: Datos de actualización (tipo_arido, nuevo_precio, periodo_inicio, periodo_fin)
        db: Sesión de base de datos

    Returns:
        Resumen de la actualización con información de precios e importes

    Raises:
        HTTPException 404: Si el proyecto no existe
        HTTPException 400: Si no hay registros que actualizar o el precio no es válido
    """
    try:
        # Verificar que el proyecto existe
        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

        # Validar nuevo precio
        if data.nuevo_precio <= 0:
            raise HTTPException(status_code=400, detail="El precio debe ser mayor a 0")

        # Validar fechas
        if data.periodo_inicio > data.periodo_fin:
            raise HTTPException(
                status_code=400,
                detail="La fecha de inicio debe ser anterior a la fecha de fin"
            )

        # Buscar todos los registros de áridos que coinciden con los criterios
        registros = db.query(EntregaArido).filter(
            EntregaArido.proyecto_id == proyecto_id,
            EntregaArido.tipo_arido == data.tipo_arido,
            EntregaArido.fecha_entrega >= datetime.combine(data.periodo_inicio, datetime.min.time()),
            EntregaArido.fecha_entrega <= datetime.combine(data.periodo_fin, datetime.max.time())
        ).all()

        if not registros:
            raise HTTPException(
                status_code=400,
                detail=f"No se encontraron registros de árido '{data.tipo_arido}' en el período especificado"
            )

        # Calcular estadísticas anteriores
        registros_actualizados = len(registros)

        # Calcular precio anterior promedio (solo de los registros que tienen precio)
        precios_anteriores = [r.precio_unitario for r in registros if r.precio_unitario is not None]
        precio_anterior = sum(precios_anteriores) / len(precios_anteriores) if precios_anteriores else 0.0

        # Calcular importe anterior (suma de cantidad * precio_unitario)
        importe_anterior = sum(
            (r.cantidad * r.precio_unitario) if r.precio_unitario is not None else 0.0
            for r in registros
        )

        # Actualizar precio_unitario de cada registro
        for registro in registros:
            registro.precio_unitario = data.nuevo_precio

        # Calcular importe nuevo
        importe_nuevo = sum(r.cantidad * data.nuevo_precio for r in registros)

        # Calcular diferencia
        diferencia = importe_nuevo - importe_anterior

        # Guardar cambios
        db.commit()

        return ActualizarPrecioAridoResponse(
            registros_actualizados=registros_actualizados,
            precio_anterior=round(precio_anterior, 2),
            precio_nuevo=round(data.nuevo_precio, 2),
            importe_anterior=round(importe_anterior, 2),
            importe_nuevo=round(importe_nuevo, 2),
            diferencia=round(diferencia, 2)
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar precio de áridos: {str(e)}"
        )

@router.put("/proyectos/{proyecto_id}/maquinas/actualizar-tarifa", response_model=ActualizarTarifaMaquinaResponse)
async def actualizar_tarifa_maquina(
    proyecto_id: int,
    data: ActualizarTarifaMaquinaRequest,
    db: Session = Depends(get_db)
):
    """
    Actualiza la tarifa por hora de todos los registros de horas
    de una máquina específica en un período determinado.

    Args:
        proyecto_id: ID del proyecto
        data: Datos de actualización (maquina_id, nueva_tarifa, periodo_inicio, periodo_fin)
        db: Sesión de base de datos

    Returns:
        Resumen de la actualización con información de tarifas e importes

    Raises:
        HTTPException 404: Si el proyecto no existe
        HTTPException 400: Si no hay registros que actualizar o la tarifa no es válida
    """
    try:
        # Verificar que el proyecto existe
        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

        # Validar nueva tarifa
        if data.nueva_tarifa <= 0:
            raise HTTPException(status_code=400, detail="La tarifa debe ser mayor a 0")

        # Validar fechas
        if data.periodo_inicio > data.periodo_fin:
            raise HTTPException(
                status_code=400,
                detail="La fecha de inicio debe ser anterior a la fecha de fin"
            )

        # Buscar todos los registros de reportes laborales que coinciden con los criterios
        registros = db.query(ReporteLaboral).filter(
            ReporteLaboral.proyecto_id == proyecto_id,
            ReporteLaboral.maquina_id == data.maquina_id,
            ReporteLaboral.fecha_asignacion >= datetime.combine(data.periodo_inicio, datetime.min.time()),
            ReporteLaboral.fecha_asignacion <= datetime.combine(data.periodo_fin, datetime.max.time())
        ).all()

        if not registros:
            raise HTTPException(
                status_code=400,
                detail=f"No se encontraron registros de horas para la máquina {data.maquina_id} en el período especificado"
            )

        # Calcular estadísticas anteriores
        registros_actualizados = len(registros)

        # Calcular tarifa anterior promedio (solo de los registros que tienen tarifa)
        tarifas_anteriores = [r.tarifa_hora for r in registros if r.tarifa_hora is not None]
        tarifa_anterior = sum(tarifas_anteriores) / len(tarifas_anteriores) if tarifas_anteriores else 0.0

        # Calcular importe anterior (suma de horas_turno * tarifa_hora)
        importe_anterior = sum(
            (r.horas_turno * r.tarifa_hora) if r.tarifa_hora is not None else 0.0
            for r in registros
        )

        # Actualizar tarifa_hora de cada registro
        for registro in registros:
            registro.tarifa_hora = data.nueva_tarifa

        # Calcular importe nuevo
        importe_nuevo = sum(r.horas_turno * data.nueva_tarifa for r in registros)

        # Calcular diferencia
        diferencia = importe_nuevo - importe_anterior

        # Guardar cambios
        db.commit()

        return ActualizarTarifaMaquinaResponse(
            registros_actualizados=registros_actualizados,
            tarifa_anterior=round(tarifa_anterior, 2),
            tarifa_nueva=round(data.nueva_tarifa, 2),
            importe_anterior=round(importe_anterior, 2),
            importe_nuevo=round(importe_nuevo, 2),
            diferencia=round(diferencia, 2)
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar tarifa de máquina: {str(e)}"
        )
