from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional
from datetime import datetime
from app.db.dependencies import get_db
from app.schemas.schemas import (
    ClienteCreate,
    ClienteOut,
    CotizacionCreate,
    CotizacionUpdate,
    CotizacionOut,
    CotizacionItemCreate,
    ServiciosPredefinidosOut
)
from sqlalchemy.orm import Session
from app.services import cotizacion_service
from app.security.auth import get_current_user
import io
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
import os

router = APIRouter(
    prefix="/cotizaciones",
    tags=["Cotizaciones"],
    dependencies=[Depends(get_current_user)]
)

# ============= Endpoints de Clientes =============

@router.get("/clientes", response_model=List[ClienteOut])
def get_clientes(session: Session = Depends(get_db)):
    """
    Obtiene todos los clientes registrados en el sistema.
    """
    return cotizacion_service.get_clientes(session)

@router.post("/clientes", response_model=ClienteOut, status_code=201)
def create_cliente(
    cliente_data: ClienteCreate,
    session: Session = Depends(get_db)
):
    """
    Crea un nuevo cliente.
    El nombre es obligatorio, los demás campos son opcionales.
    """
    try:
        return cotizacion_service.create_cliente(session, cliente_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear cliente: {str(e)}")

# ============= Endpoints de Servicios Predefinidos =============

@router.get("/servicios-predefinidos", response_model=ServiciosPredefinidosOut)
def get_servicios_predefinidos():
    """
    Obtiene la lista de servicios predefinidos con sus precios por defecto.
    Incluye áridos (Arena Fina, Granza, etc.) y máquinas (BOBCAT, EXCAVADORA, etc.)
    con los mismos precios que se usan en Cuenta Corriente.
    """
    return cotizacion_service.get_servicios_predefinidos()

# ============= Endpoints de Cotizaciones CRUD =============

@router.get("/cotizaciones", response_model=List[CotizacionOut])
def get_cotizaciones(
    cliente_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    session: Session = Depends(get_db)
):
    """
    Lista todas las cotizaciones generadas.
    Opcionalmente filtra por cliente.
    Incluye los items y datos del cliente en cada cotización.
    """
    return cotizacion_service.get_cotizaciones(session, cliente_id)

@router.get("/cotizaciones/{cotizacion_id}", response_model=CotizacionOut)
def get_cotizacion(
    cotizacion_id: int,
    session: Session = Depends(get_db)
):
    """
    Obtiene una cotización específica por su ID.
    Incluye todos los items y datos del cliente.
    """
    cotizacion = cotizacion_service.get_cotizacion(session, cotizacion_id)

    if not cotizacion:
        raise HTTPException(
            status_code=404,
            detail=f"Cotización con ID {cotizacion_id} no encontrada"
        )

    return cotizacion

@router.post("/cotizaciones", response_model=CotizacionOut, status_code=201)
def create_cotizacion(
    cotizacion_data: CotizacionCreate,
    session: Session = Depends(get_db)
):
    """
    Crea una nueva cotización con sus items.

    Calcula automáticamente:
    - Subtotal de cada item (cantidad × precio_unitario)
    - Importe total de la cotización (suma de subtotales)

    El estado inicial es "borrador".
    """
    try:
        return cotizacion_service.create_cotizacion(session, cotizacion_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear cotización: {str(e)}")

@router.put("/cotizaciones/{cotizacion_id}", response_model=CotizacionOut)
def update_cotizacion(
    cotizacion_id: int,
    cotizacion_update: CotizacionUpdate,
    session: Session = Depends(get_db)
):
    """
    Actualiza el estado, observaciones o fecha de validez de una cotización.

    Estados permitidos: "borrador", "enviada", "aprobada"

    No modifica los items (usar PUT /cotizaciones/{id}/items para eso).
    """
    cotizacion = cotizacion_service.update_cotizacion(
        session,
        cotizacion_id,
        cotizacion_update
    )

    if not cotizacion:
        raise HTTPException(
            status_code=404,
            detail=f"Cotización con ID {cotizacion_id} no encontrada"
        )

    return cotizacion

@router.put("/cotizaciones/{cotizacion_id}/items", response_model=CotizacionOut)
def update_cotizacion_items(
    cotizacion_id: int,
    items: List[CotizacionItemCreate],
    session: Session = Depends(get_db)
):
    """
    Reemplaza todos los items de una cotización.

    Útil cuando el usuario edita precios, cantidades o agrega/elimina items.
    Recalcula automáticamente los subtotales y el importe total.
    """
    try:
        cotizacion = cotizacion_service.update_cotizacion_items(
            session,
            cotizacion_id,
            items
        )

        if not cotizacion:
            raise HTTPException(
                status_code=404,
                detail=f"Cotización con ID {cotizacion_id} no encontrada"
            )

        return cotizacion
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar items: {str(e)}")

@router.delete("/cotizaciones/{cotizacion_id}", status_code=204)
def delete_cotizacion(
    cotizacion_id: int,
    session: Session = Depends(get_db)
):
    """
    Elimina una cotización.
    Los items se eliminan automáticamente en cascada.
    """
    success = cotizacion_service.delete_cotizacion(session, cotizacion_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Cotización con ID {cotizacion_id} no encontrada"
        )

    return JSONResponse(
        status_code=204,
        content={"message": "Cotización eliminada exitosamente"}
    )

# ============= Endpoints de Exportación =============

@router.get("/cotizaciones/{cotizacion_id}/excel")
def exportar_cotizacion_excel(
    cotizacion_id: int,
    session: Session = Depends(get_db)
):
    """
    Exporta una cotización a formato Excel (.xlsx)

    Contiene hojas:
    - Información: Datos generales de la cotización
    - Servicios: Detalle de items con precios
    - Totales: Importe total
    """
    # Obtener la cotización
    cotizacion = cotizacion_service.get_cotizacion(session, cotizacion_id)
    if not cotizacion:
        raise HTTPException(
            status_code=404,
            detail=f"Cotización con ID {cotizacion_id} no encontrada"
        )

    # Crear el archivo Excel en memoria
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Hoja de Información
        info_data = {
            'Campo': ['Cliente', 'Fecha Creación', 'Fecha Validez', 'Estado', 'Observaciones'],
            'Valor': [
                cotizacion.cliente.nombre,
                cotizacion.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
                cotizacion.fecha_validez.strftime("%d/%m/%Y") if cotizacion.fecha_validez else 'N/A',
                cotizacion.estado.upper(),
                cotizacion.observaciones or 'N/A'
            ]
        }
        df_info = pd.DataFrame(info_data)
        df_info.to_excel(writer, sheet_name='Información', index=False)

        # Hoja de Servicios
        if cotizacion.items:
            servicios_data = {
                'Servicio': [item.nombre_servicio for item in cotizacion.items],
                'Cantidad': [item.cantidad for item in cotizacion.items],
                'Unidad': [item.unidad for item in cotizacion.items],
                'Precio Unitario': [float(item.precio_unitario) for item in cotizacion.items],
                'Subtotal': [float(item.subtotal) for item in cotizacion.items]
            }
            df_servicios = pd.DataFrame(servicios_data)
            df_servicios.to_excel(writer, sheet_name='Servicios', index=False)

        # Hoja de Totales
        totales_data = {
            'Concepto': ['IMPORTE TOTAL'],
            'Valor': [float(cotizacion.importe_total)]
        }
        df_totales = pd.DataFrame(totales_data)
        df_totales.to_excel(writer, sheet_name='Totales', index=False)

    output.seek(0)

    filename = f"cotizacion_{cotizacion_id}_{cotizacion.cliente.nombre.replace(' ', '_')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/cotizaciones/{cotizacion_id}/pdf")
def exportar_cotizacion_pdf(
    cotizacion_id: int,
    session: Session = Depends(get_db)
):
    """
    Exporta una cotización a formato PDF

    Estructura similar al PDF de cuenta corriente:
    - Logo (si existe)
    - Título "COTIZACIÓN"
    - Información general del cliente
    - Tabla de servicios
    - Tabla de totales
    - Observaciones
    """
    # Obtener la cotización
    cotizacion = cotizacion_service.get_cotizacion(session, cotizacion_id)
    if not cotizacion:
        raise HTTPException(
            status_code=404,
            detail=f"Cotización con ID {cotizacion_id} no encontrada"
        )

    # Crear el PDF en memoria
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Logo en el encabezado (si existe)
    logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'assets', 'logo-kedikian.png')
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=120, height=120)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 0.2*inch))
        except Exception as e:
            print(f"Advertencia: No se pudo cargar el logo: {e}")

    # Título
    title = Paragraph(f"<b>COTIZACIÓN</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))

    # Información general
    info_text = f"""
    <b>Cliente:</b> {cotizacion.cliente.nombre}<br/>
    <b>Fecha de Creación:</b> {cotizacion.fecha_creacion.strftime("%d/%m/%Y %H:%M")}<br/>
    <b>Válida hasta:</b> {cotizacion.fecha_validez.strftime("%d/%m/%Y") if cotizacion.fecha_validez else 'N/A'}<br/>
    <b>Estado:</b> {cotizacion.estado.upper()}<br/>
    """
    if cotizacion.cliente.email:
        info_text += f"<b>Email:</b> {cotizacion.cliente.email}<br/>"
    if cotizacion.cliente.telefono:
        info_text += f"<b>Teléfono:</b> {cotizacion.cliente.telefono}<br/>"

    info_para = Paragraph(info_text, styles['Normal'])
    elements.append(info_para)
    elements.append(Spacer(1, 0.3*inch))

    # Tabla de servicios
    if cotizacion.items:
        servicios_title = Paragraph("<b>DETALLE DE SERVICIOS</b>", styles['Heading2'])
        elements.append(servicios_title)
        elements.append(Spacer(1, 0.1*inch))

        servicios_data = [['Servicio', 'Cantidad', 'Unidad', 'Precio Unit.', 'Subtotal']]
        for item in cotizacion.items:
            servicios_data.append([
                item.nombre_servicio,
                f"{item.cantidad:.2f}",
                item.unidad,
                f"${float(item.precio_unitario):,.2f}",
                f"${float(item.subtotal):,.2f}"
            ])

        servicios_table = Table(servicios_data)
        servicios_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(servicios_table)
        elements.append(Spacer(1, 0.3*inch))

    # Totales
    totales_title = Paragraph("<b>TOTALES</b>", styles['Heading2'])
    elements.append(totales_title)
    elements.append(Spacer(1, 0.1*inch))

    totales_data = [
        ['Concepto', 'Valor'],
        ['IMPORTE TOTAL', f"${float(cotizacion.importe_total):,.2f}"]
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
    if cotizacion.observaciones:
        elements.append(Spacer(1, 0.3*inch))
        obs_title = Paragraph("<b>OBSERVACIONES</b>", styles['Heading2'])
        elements.append(obs_title)
        obs_text = Paragraph(cotizacion.observaciones, styles['Normal'])
        elements.append(obs_text)

    # Generar PDF
    doc.build(elements)
    buffer.seek(0)

    filename = f"cotizacion_{cotizacion_id}_{cotizacion.cliente.nombre.replace(' ', '_')}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
