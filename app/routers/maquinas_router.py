from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.dependencies import get_db
from app.schemas.schemas import (
    MaquinaSchema, MaquinaCreate, RegistroHorasMaquinaCreate,
    HistorialHorasOut, EstadisticasHorasOut, UsuarioOut,
    NotaMaquinaOut, NotaMaquinaCreate, ProximoMantenimientoUpdate
)
from app.services.maquina_service import (
    get_maquinas as service_get_maquinas,
    get_maquina as service_get_maquina,
    create_maquina as service_create_maquina,
    update_maquina as service_update_maquina,
    delete_maquina as service_delete_maquina,
    get_all_maquinas_paginated,
    registrar_horas_maquina,
    obtener_historial_horas_maquina,
    obtener_estadisticas_horas_maquina
)
from app.services.nota_maquina_service import (
    listar_notas_maquina,
    crear_nota_maquina,
    eliminar_nota_maquina
)
from app.db.models import ReporteLaboral, Maquina, HorometroHistorial
from app.security.auth import get_current_user
from app.schemas.schemas import UsuarioOut as Usuario

router = APIRouter(prefix="/maquinas", tags=["Maquinas"])

# ==================== CRUD MÁQUINAS ====================

@router.get("/", response_model=List[MaquinaSchema])
def get_maquinas(session: Session = Depends(get_db)):
    return service_get_maquinas(session)

@router.get("/paginado")
def maquinas_paginado(skip: int = 0, limit: int = 15, session: Session = Depends(get_db)):
    return get_all_maquinas_paginated(session, skip=skip, limit=limit)

# ==================== HORÓMETRO INICIAL (ACTUALIZADO) ====================

@router.get("/horometro-inicial")
def obtener_horometro_inicial_todas(session: Session = Depends(get_db)):
    """
    Obtiene el horómetro inicial de todas las máquinas desde la tabla maquina
    """
    maquinas = session.query(Maquina).all()
    resultado = {}
    
    for maquina in maquinas:
        # Ahora tomamos el horometro_inicial directamente de la tabla maquina
        resultado[maquina.id] = float(maquina.horometro_inicial or 0)
    
    return resultado

@router.get("/{id}", response_model=MaquinaSchema)
def get_maquina(id: int, session: Session = Depends(get_db)):
    maquina = service_get_maquina(session, id)
    if maquina:
        return maquina
    return JSONResponse(content={"error": "Maquina no encontrada"}, status_code=404)

@router.get("/{maquina_id}/horometro-inicial")
def obtener_horometro_inicial_maquina(
    maquina_id: int,
    session: Session = Depends(get_db)
):
    """
    Obtiene el horómetro inicial de una máquina específica desde la tabla maquina
    """
    maquina = session.query(Maquina).filter(Maquina.id == maquina_id).first()
    
    if not maquina:
        return JSONResponse(content={"error": "Máquina no encontrada"}, status_code=404)
    
    return {"horometro_inicial": float(maquina.horometro_inicial or 0)}

@router.put("/{maquina_id}/horometro-inicial")
def actualizar_horometro_inicial(
    maquina_id: int,
    datos: dict,
    session: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza el horómetro inicial de una máquina específica
    ⚠️ ADVERTENCIA: Este endpoint debe usarse solo en casos especiales
    El horometro_inicial se actualiza automáticamente al crear reportes laborales
    """
    maquina = session.query(Maquina).filter(Maquina.id == maquina_id).first()

    if not maquina:
        return JSONResponse(content={"error": "Máquina no encontrada"}, status_code=404)

    nuevo_horometro = datos.get('horometro_inicial')

    if nuevo_horometro is None:
        return JSONResponse(content={"error": "El campo 'horometro_inicial' es requerido"}, status_code=400)

    if nuevo_horometro < 0:
        return JSONResponse(content={"error": "El horómetro no puede ser negativo"}, status_code=400)

    valor_anterior = maquina.horometro_inicial
    valor_nuevo = float(nuevo_horometro)

    # ✅ Validación: el horómetro solo puede aumentar, no retroceder
    # (Solo se permite si el usuario envía explícitamente 'permitir_retroceso': true)
    if valor_nuevo < valor_anterior and not datos.get('permitir_retroceso', False):
        return JSONResponse(
            content={
                "error": f"El horómetro no puede retroceder. Valor actual: {valor_anterior}, Valor nuevo: {valor_nuevo}",
                "valor_anterior": valor_anterior,
                "valor_nuevo": valor_nuevo,
                "sugerencia": "Si realmente necesitas reducir el valor, envía 'permitir_retroceso': true en el payload"
            },
            status_code=400
        )

    # Solo actualizar si el valor cambió
    if valor_anterior != valor_nuevo:
        # Actualizar el horómetro inicial en la tabla maquina
        maquina.horometro_inicial = valor_nuevo

        # ✅ Registrar el cambio en el historial de auditoría
        historial = HorometroHistorial(
            maquina_id=maquina.id,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            usuario_id=current_user.id,
            motivo="manual",
            reporte_laboral_id=None
        )
        session.add(historial)
        session.commit()
        session.refresh(maquina)

        return {
            "message": f"Horómetro actualizado correctamente",
            "maquina_id": maquina.id,
            "valor_anterior": valor_anterior,
            "horometro_inicial": valor_nuevo,
            "actualizado_por": current_user.nombre,
            "registrado_en_historial": True
        }
    else:
        return {
            "message": "El valor del horómetro no ha cambiado",
            "maquina_id": maquina.id,
            "horometro_inicial": valor_anterior
        }
    
@router.get("/{maquina_id}/horas-restantes")
def obtener_horas_restantes(
    maquina_id: int,
    session: Session = Depends(get_db)
):
    """
    Calcula las horas restantes para el próximo mantenimiento
    Fórmula: horometro_inicial - proximo_mantenimiento

    Nota: Si la máquina no tiene configurado 'proximo_mantenimiento',
    retorna None. Use PUT /{maquina_id}/proximo-mantenimiento para configurarlo.
    """
    maquina = session.query(Maquina).filter(Maquina.id == maquina_id).first()

    if not maquina:
        return JSONResponse(content={"error": "Máquina no encontrada"}, status_code=404)

    # Verificar si tiene el campo proximo_mantenimiento
    proximo_mantenimiento = getattr(maquina, 'proximo_mantenimiento', None)

    if proximo_mantenimiento is None:
        return {
            "maquina_id": maquina.id,
            "nombre": maquina.nombre,
            "horometro_inicial": float(maquina.horometro_inicial or 0),
            "proximo_mantenimiento": None,
            "horas_restantes": None,
            "mensaje": "La máquina no tiene configurado el próximo mantenimiento"
        }

    # Calcular horas restantes según la fórmula del usuario
    horas_restantes = float(maquina.horometro_inicial or 0) - float(proximo_mantenimiento)

    return {
        "maquina_id": maquina.id,
        "nombre": maquina.nombre,
        "horometro_inicial": float(maquina.horometro_inicial or 0),
        "proximo_mantenimiento": float(proximo_mantenimiento),
        "horas_restantes": horas_restantes,
        "estado": "normal" if horas_restantes >= 0 else "excedido"
    }

@router.post("/", response_model=MaquinaSchema, status_code=201)
def create_maquina(maquina: MaquinaCreate, session: Session = Depends(get_db)):
    return service_create_maquina(session, maquina)

@router.put("/{id}", response_model=MaquinaSchema)
def update_maquina(id: int, maquina: MaquinaSchema, session: Session = Depends(get_db)):
    updated = service_update_maquina(session, id, maquina)
    if updated:
        return updated
    return JSONResponse(content={"error": "Maquina no encontrada"}, status_code=404)

@router.delete("/{id}")
def delete_maquina(id: int, session: Session = Depends(get_db)):
    deleted = service_delete_maquina(session, id)
    if deleted:
        return {"message": "Maquina eliminada"}
    return JSONResponse(content={"error": "Maquina no encontrada"}, status_code=404)

# ==================== HORAS ====================

@router.post("/{maquina_id}/horas", status_code=201)
def registrar_horas(
    maquina_id: int,
    registro: RegistroHorasMaquinaCreate,
    session: Session = Depends(get_db),
    current_user: UsuarioOut = Depends(get_current_user)
):
    """
    Registrar horas de uso de una máquina
    """
    try:
        return registrar_horas_maquina(
            db=session,
            maquina_id=maquina_id,
            registro=registro,
            usuario_id=current_user.id
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

@router.get("/{maquina_id}/horas/historial", response_model=List[HistorialHorasOut])
def historial_horas(maquina_id: int, session: Session = Depends(get_db)):
    """
    Historial completo de horas de una máquina
    """
    return obtener_historial_horas_maquina(session, maquina_id)

# ==================== CRUD DE REGISTROS DE HORAS ====================

@router.put("/{maquina_id}/horas/{registro_id}")
def actualizar_registro_horas(
    maquina_id: int,
    registro_id: int,
    datos: RegistroHorasMaquinaCreate,
    session: Session = Depends(get_db)
):
    registro = session.query(ReporteLaboral).filter(
        ReporteLaboral.id == registro_id,
        ReporteLaboral.maquina_id == maquina_id
    ).first()

    if not registro:
        return JSONResponse(content={"error": "Registro no encontrado"}, status_code=404)

    registro.horas_turno = datos.horas
    registro.fecha_asignacion = datos.fecha
    session.commit()
    session.refresh(registro)

    return {
        "message": f"Registro {registro_id} actualizado correctamente",
        "registro": {
            "id": registro.id,
            "maquina_id": registro.maquina_id,
            "horas": registro.horas_turno,
            "fecha": registro.fecha_asignacion
        }
    }

@router.delete("/{maquina_id}/horas/{registro_id}")
def eliminar_registro_horas(
    maquina_id: int,
    registro_id: int,
    session: Session = Depends(get_db)
):
    registro = session.query(ReporteLaboral).filter(
        ReporteLaboral.id == registro_id,
        ReporteLaboral.maquina_id == maquina_id
    ).first()

    if not registro:
        return JSONResponse(content={"error": "Registro no encontrado"}, status_code=404)

    session.delete(registro)
    session.commit()
    return {"message": f"Registro {registro_id} eliminado correctamente"}

# ==================== NOTAS DE MÁQUINAS ====================

@router.get("/{maquina_id}/notas", response_model=List[NotaMaquinaOut])
def obtener_notas_maquina(
    maquina_id: int,
    session: Session = Depends(get_db)
):
    """
    Obtiene todas las notas de una máquina específica, ordenadas por fecha descendente
    """
    try:
        return listar_notas_maquina(session, maquina_id)
    except ValueError as e:
        return JSONResponse(content={"message": str(e)}, status_code=404)
    except Exception as e:
        return JSONResponse(content={"message": f"Error al obtener notas: {str(e)}"}, status_code=500)

@router.post("/{maquina_id}/notas", response_model=NotaMaquinaOut, status_code=201)
def crear_nota(
    maquina_id: int,
    nota: NotaMaquinaCreate,
    session: Session = Depends(get_db),
    current_user: UsuarioOut = Depends(get_current_user)
):
    """
    Crea una nueva nota para una máquina específica
    """
    try:
        # Usar el nombre del usuario autenticado en lugar de 'Usuario' por defecto
        usuario = current_user.nombre if current_user and current_user.nombre else "Usuario"
        return crear_nota_maquina(session, maquina_id, nota.texto, usuario)
    except ValueError as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"message": f"Error al crear nota: {str(e)}"}, status_code=500)

@router.delete("/notas/{nota_id}", status_code=204)
def eliminar_nota(
    nota_id: int,
    session: Session = Depends(get_db),
    current_user: UsuarioOut = Depends(get_current_user)
):
    """
    Elimina una nota específica
    """
    try:
        eliminar_nota_maquina(session, nota_id)
        return JSONResponse(content=None, status_code=204)
    except ValueError as e:
        return JSONResponse(content={"message": str(e)}, status_code=404)
    except Exception as e:
        return JSONResponse(content={"message": f"Error al eliminar nota: {str(e)}"}, status_code=500)

# ==================== PRÓXIMO MANTENIMIENTO ====================

@router.put("/{maquina_id}/proximo-mantenimiento", response_model=MaquinaSchema)
def actualizar_proximo_mantenimiento(
    maquina_id: int,
    datos: ProximoMantenimientoUpdate,
    session: Session = Depends(get_db)
):
    """
    Actualiza las horas del próximo mantenimiento de una máquina.

    - Si se envía un valor numérico, se establece como próximo mantenimiento personalizado
    - Si se envía null, se resetea al cálculo automático
    """
    maquina = session.query(Maquina).filter(Maquina.id == maquina_id).first()

    if not maquina:
        return JSONResponse(content={"message": "Máquina no encontrada"}, status_code=404)

    # Actualizar el campo proximo_mantenimiento
    maquina.proximo_mantenimiento = datos.horas

    session.commit()
    session.refresh(maquina)

    return maquina