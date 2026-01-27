from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional
from datetime import date
from app.db.dependencies import get_db
from app.schemas.schemas import (
    ReporteCuentaCorrienteCreate,
    ReporteCuentaCorrienteUpdate,
    ReporteCuentaCorrienteOut,
    ResumenProyectoSchema,
    PrecioAridoSchema,
    TarifaMaquinaSchema
)
from sqlalchemy.orm import Session
from app.services import cuenta_corriente_service
from app.security.auth import get_current_user
import io
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

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

@router.post("/reportes", response_model=ReporteCuentaCorrienteOut, status_code=201)
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

    # Crear el archivo Excel en memoria
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Información general
        info_data = {
            'Campo': ['Proyecto', 'Período', 'Fecha Generación', 'Estado', 'N° Factura'],
            'Valor': [
                resumen.proyecto_nombre,
                f"{reporte.periodo_inicio} - {reporte.periodo_fin}",
                reporte.fecha_generacion.strftime("%d/%m/%Y %H:%M"),
                reporte.estado,
                reporte.numero_factura or 'N/A'
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

        # Resumen de totales
        totales_data = {
            'Concepto': [
                'Total Áridos (m³)',
                'Importe Áridos',
                'Total Horas',
                'Importe Horas',
                'IMPORTE TOTAL'
            ],
            'Valor': [
                resumen.total_aridos_m3,
                resumen.total_importe_aridos,
                resumen.total_horas,
                resumen.total_importe_horas,
                resumen.importe_total
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

    # Crear el PDF en memoria
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

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
    <b>N° Factura:</b> {reporte.numero_factura or 'N/A'}
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
        ['IMPORTE TOTAL', f"${resumen.importe_total:,.2f}"]
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
