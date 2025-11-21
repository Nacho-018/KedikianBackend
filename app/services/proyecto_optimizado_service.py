"""
Servicio optimizado para proyectos que elimina N+1 queries usando eager loading.
Implementa endpoints que retornan proyectos con todas sus relaciones en una sola query.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict, Any
from collections import defaultdict

from app.db.models import Proyecto, ReporteLaboral, EntregaArido, ContratoArchivo, Maquina, Usuario
from app.schemas.schemas import (
    ProyectoConDetallesResponse,
    MaquinaConHorasSchema,
    AridoDetalladoSchema,
    ReporteLaboralDetalladoSchema,
    UsuarioDetalladoSchema,
    MaquinaOut,
    ContratoArchivoResponse
)


def get_proyecto_con_detalles_optimizado(
    db: Session,
    proyecto_id: int
) -> Optional[ProyectoConDetallesResponse]:
    """
    Obtiene un proyecto específico con todas sus relaciones en UNA SOLA QUERY optimizada.

    Elimina el problema de N+1 usando joinedload() para pre-cargar:
    - Reportes laborales con máquinas y usuarios
    - Entregas de áridos con usuarios
    - Archivos de contrato

    Args:
        db: Sesión de base de datos
        proyecto_id: ID del proyecto a buscar

    Returns:
        ProyectoConDetallesResponse con todas las relaciones cargadas, o None si no existe
    """
    try:
        # QUERY OPTIMIZADA: Usa joinedload para pre-cargar TODAS las relaciones
        # Esto ejecuta 1-2 queries con JOINs en lugar de N queries individuales
        proyecto = (
            db.query(Proyecto)
            .filter(Proyecto.id == proyecto_id)
            .options(
                # Pre-cargar reportes laborales con sus relaciones anidadas
                joinedload(Proyecto.reportes_laborales)
                    .joinedload(ReporteLaboral.maquina),
                joinedload(Proyecto.reportes_laborales)
                    .joinedload(ReporteLaboral.usuario),
                # Pre-cargar áridos con usuario
                joinedload(Proyecto.entrega_arido)
                    .joinedload(EntregaArido.usuario),
                # Pre-cargar archivos de contrato
                joinedload(Proyecto.contrato_archivos)
            )
            .first()
        )

        if not proyecto:
            return None

        # Procesar máquinas: agrupar por ID y sumar horas totales
        maquinas_dict: Dict[int, Dict[str, Any]] = {}

        for reporte in proyecto.reportes_laborales:
            # IMPORTANTE: reporte.maquina ya está cargada en memoria (no genera query adicional)
            if reporte.maquina:
                maquina = reporte.maquina

                if maquina.id not in maquinas_dict:
                    # Primera vez que vemos esta máquina
                    maquinas_dict[maquina.id] = {
                        "id": maquina.id,
                        "nombre": maquina.nombre,
                        "horas_uso": maquina.horas_uso or 0,
                        "horas_maquina": maquina.horas_maquina or 0,
                        "horometro_inicial": maquina.horometro_inicial,
                        "proximo_mantenimiento": maquina.proximo_mantenimiento,
                        "horas_totales": 0,
                        "created": maquina.created,
                        "updated": maquina.updated
                    }

                # Sumar horas del turno a las horas totales (solo si tiene valor)
                if reporte.horas_turno is not None:
                    maquinas_dict[maquina.id]["horas_totales"] += reporte.horas_turno

        # Convertir máquinas a lista de schemas
        maquinas_list = [
            MaquinaConHorasSchema(**maquina_data)
            for maquina_data in maquinas_dict.values()
        ]

        # Procesar áridos con usuario completo
        aridos_list = []
        for arido in proyecto.entrega_arido:
            if arido.usuario:
                aridos_list.append(AridoDetalladoSchema(
                    id=arido.id,
                    tipo_arido=arido.tipo_arido,
                    nombre=arido.nombre or arido.tipo_arido,
                    cantidad=arido.cantidad,
                    fecha_entrega=arido.fecha_entrega,
                    usuario=UsuarioDetalladoSchema(
                        id=arido.usuario.id,
                        nombre=arido.usuario.nombre,
                        email=arido.usuario.email,
                        estado=arido.usuario.estado,
                        roles=arido.usuario.roles.split(',') if arido.usuario.roles else [],
                        fecha_creacion=arido.usuario.fecha_creacion
                    ),
                    created=arido.created,
                    updated=arido.updated
                ))

        # Procesar reportes laborales con máquina y usuario completos
        reportes_list = []
        for reporte in proyecto.reportes_laborales:
            # Construir schema de usuario si existe
            usuario_schema = None
            if reporte.usuario:
                usuario_schema = UsuarioDetalladoSchema(
                    id=reporte.usuario.id,
                    nombre=reporte.usuario.nombre,
                    email=reporte.usuario.email,
                    estado=reporte.usuario.estado,
                    roles=reporte.usuario.roles.split(',') if reporte.usuario.roles else [],
                    fecha_creacion=reporte.usuario.fecha_creacion
                )

            # Construir schema de máquina
            maquina_schema = None
            if reporte.maquina:
                maquina_schema = MaquinaOut(
                    id=reporte.maquina.id,
                    nombre=reporte.maquina.nombre,
                    horas_uso=reporte.maquina.horas_uso or 0,
                    horas_maquina=reporte.maquina.horas_maquina or 0,
                    horometro_inicial=reporte.maquina.horometro_inicial,
                    proximo_mantenimiento=reporte.maquina.proximo_mantenimiento,
                    created=reporte.maquina.created,
                    updated=reporte.maquina.updated
                )

            reportes_list.append(ReporteLaboralDetalladoSchema(
                id=reporte.id,
                maquina_id=reporte.maquina_id,
                usuario_id=reporte.usuario_id,
                proyecto_id=reporte.proyecto_id,
                fecha_asignacion=reporte.fecha_asignacion,
                horas_turno=reporte.horas_turno,
                horometro_inicial=reporte.horometro_inicial,
                maquina=maquina_schema,
                usuario=usuario_schema,
                created=reporte.created,
                updated=reporte.updated
            ))

        # Procesar archivos de contrato
        archivos_list = [
            ContratoArchivoResponse(
                id=archivo.id,
                proyecto_id=archivo.proyecto_id,
                nombre_archivo=archivo.nombre_archivo,
                ruta_archivo=archivo.ruta_archivo,
                tipo_archivo=archivo.tipo_archivo,
                tamaño_archivo=archivo.tamaño_archivo,
                fecha_subida=archivo.fecha_subida
            )
            for archivo in proyecto.contrato_archivos
        ]

        # Construir respuesta final
        return ProyectoConDetallesResponse(
            id=proyecto.id,
            nombre=proyecto.nombre,
            descripcion=proyecto.descripcion,
            estado=proyecto.estado,
            fecha_creacion=proyecto.fecha_creacion,
            fecha_inicio=proyecto.fecha_inicio,
            fecha_fin=proyecto.fecha_fin,
            progreso=proyecto.progreso,
            gerente=proyecto.gerente,
            contrato_id=proyecto.contrato_id,
            ubicacion=proyecto.ubicacion,
            contrato_url=proyecto.contrato_url,
            contrato_nombre=proyecto.contrato_nombre,
            contrato_tipo=proyecto.contrato_tipo,
            maquinas=maquinas_list,
            aridos=aridos_list,
            reportes_laborales=reportes_list,
            contrato_archivos=archivos_list
        )

    except SQLAlchemyError as e:
        print(f"[ERROR] get_proyecto_con_detalles_optimizado (proyecto_id={proyecto_id}): {e}")
        raise Exception(f"Error al obtener proyecto con detalles: {str(e)}")


def get_proyectos_con_detalles_optimizado(
    db: Session,
    solo_activos: bool = True
) -> List[ProyectoConDetallesResponse]:
    """
    Obtiene TODOS los proyectos con todas sus relaciones optimizadas.

    Similar a get_proyecto_con_detalles_optimizado pero para múltiples proyectos.
    Usa eager loading para evitar N+1 queries.

    Args:
        db: Sesión de base de datos
        solo_activos: Si True, solo retorna proyectos activos (estado=True)

    Returns:
        Lista de ProyectoConDetallesResponse con todas las relaciones cargadas
    """
    try:
        # Construir query base
        query = db.query(Proyecto)

        # Aplicar filtro de estado si es necesario
        if solo_activos:
            query = query.filter(Proyecto.estado == True)

        # QUERY OPTIMIZADA: Pre-cargar todas las relaciones
        proyectos = (
            query.options(
                joinedload(Proyecto.reportes_laborales)
                    .joinedload(ReporteLaboral.maquina),
                joinedload(Proyecto.reportes_laborales)
                    .joinedload(ReporteLaboral.usuario),
                joinedload(Proyecto.entrega_arido)
                    .joinedload(EntregaArido.usuario),
                joinedload(Proyecto.contrato_archivos)
            )
            .all()
        )

        # Procesar cada proyecto
        resultado = []

        for proyecto in proyectos:
            # Procesar máquinas: agrupar por ID y sumar horas
            maquinas_dict: Dict[int, Dict[str, Any]] = {}

            for reporte in proyecto.reportes_laborales:
                if reporte.maquina:
                    maquina = reporte.maquina

                    if maquina.id not in maquinas_dict:
                        maquinas_dict[maquina.id] = {
                            "id": maquina.id,
                            "nombre": maquina.nombre,
                            "horas_uso": maquina.horas_uso or 0,
                            "horas_maquina": maquina.horas_maquina or 0,
                            "horometro_inicial": maquina.horometro_inicial,
                            "proximo_mantenimiento": maquina.proximo_mantenimiento,
                            "horas_totales": 0,
                            "created": maquina.created,
                            "updated": maquina.updated
                        }

                    # Sumar horas del turno a las horas totales (solo si tiene valor)
                    if reporte.horas_turno is not None:
                        maquinas_dict[maquina.id]["horas_totales"] += reporte.horas_turno

            maquinas_list = [
                MaquinaConHorasSchema(**maquina_data)
                for maquina_data in maquinas_dict.values()
            ]

            # Procesar áridos
            aridos_list = []
            for arido in proyecto.entrega_arido:
                if arido.usuario:
                    aridos_list.append(AridoDetalladoSchema(
                        id=arido.id,
                        tipo_arido=arido.tipo_arido,
                        nombre=arido.nombre or arido.tipo_arido,
                        cantidad=arido.cantidad,
                        fecha_entrega=arido.fecha_entrega,
                        usuario=UsuarioDetalladoSchema(
                            id=arido.usuario.id,
                            nombre=arido.usuario.nombre,
                            email=arido.usuario.email,
                            estado=arido.usuario.estado,
                            roles=arido.usuario.roles.split(',') if arido.usuario.roles else [],
                            fecha_creacion=arido.usuario.fecha_creacion
                        ),
                        created=arido.created,
                        updated=arido.updated
                    ))

            # Procesar reportes laborales
            reportes_list = []
            for reporte in proyecto.reportes_laborales:
                usuario_schema = None
                if reporte.usuario:
                    usuario_schema = UsuarioDetalladoSchema(
                        id=reporte.usuario.id,
                        nombre=reporte.usuario.nombre,
                        email=reporte.usuario.email,
                        estado=reporte.usuario.estado,
                        roles=reporte.usuario.roles.split(',') if reporte.usuario.roles else [],
                        fecha_creacion=reporte.usuario.fecha_creacion
                    )

                maquina_schema = None
                if reporte.maquina:
                    maquina_schema = MaquinaOut(
                        id=reporte.maquina.id,
                        nombre=reporte.maquina.nombre,
                        horas_uso=reporte.maquina.horas_uso or 0,
                        horas_maquina=reporte.maquina.horas_maquina or 0,
                        horometro_inicial=reporte.maquina.horometro_inicial,
                        proximo_mantenimiento=reporte.maquina.proximo_mantenimiento,
                        created=reporte.maquina.created,
                        updated=reporte.maquina.updated
                    )

                reportes_list.append(ReporteLaboralDetalladoSchema(
                    id=reporte.id,
                    maquina_id=reporte.maquina_id,
                    usuario_id=reporte.usuario_id,
                    proyecto_id=reporte.proyecto_id,
                    fecha_asignacion=reporte.fecha_asignacion,
                    horas_turno=reporte.horas_turno,
                    horometro_inicial=reporte.horometro_inicial,
                    maquina=maquina_schema,
                    usuario=usuario_schema,
                    created=reporte.created,
                    updated=reporte.updated
                ))

            # Procesar archivos
            archivos_list = [
                ContratoArchivoResponse(
                    id=archivo.id,
                    proyecto_id=archivo.proyecto_id,
                    nombre_archivo=archivo.nombre_archivo,
                    ruta_archivo=archivo.ruta_archivo,
                    tipo_archivo=archivo.tipo_archivo,
                    tamaño_archivo=archivo.tamaño_archivo,
                    fecha_subida=archivo.fecha_subida
                )
                for archivo in proyecto.contrato_archivos
            ]

            # Agregar proyecto procesado a la lista
            resultado.append(ProyectoConDetallesResponse(
                id=proyecto.id,
                nombre=proyecto.nombre,
                descripcion=proyecto.descripcion,
                estado=proyecto.estado,
                fecha_creacion=proyecto.fecha_creacion,
                fecha_inicio=proyecto.fecha_inicio,
                fecha_fin=proyecto.fecha_fin,
                progreso=proyecto.progreso,
                gerente=proyecto.gerente,
                contrato_id=proyecto.contrato_id,
                ubicacion=proyecto.ubicacion,
                contrato_url=proyecto.contrato_url,
                contrato_nombre=proyecto.contrato_nombre,
                contrato_tipo=proyecto.contrato_tipo,
                maquinas=maquinas_list,
                aridos=aridos_list,
                reportes_laborales=reportes_list,
                contrato_archivos=archivos_list
            ))

        return resultado

    except SQLAlchemyError as e:
        print(f"[ERROR] get_proyectos_con_detalles_optimizado: {e}")
        raise Exception(f"Error al obtener proyectos con detalles: {str(e)}")
