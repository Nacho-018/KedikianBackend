from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
import logging

from app.db.models import NotaMaquina, Maquina
from app.schemas.schemas import NotaMaquinaOut, NotaMaquinaCreate

logger = logging.getLogger(__name__)


def listar_notas_maquina(db: Session, maquina_id: int) -> List[NotaMaquinaOut]:
    """
    Obtiene todas las notas de una máquina específica, ordenadas por fecha descendente
    """
    # Verificar que la máquina existe
    maquina = db.query(Maquina).filter(Maquina.id == maquina_id).first()
    if not maquina:
        raise ValueError(f"Máquina con ID {maquina_id} no encontrada")

    # Obtener notas ordenadas por fecha descendente
    notas = db.query(NotaMaquina).filter(
        NotaMaquina.maquina_id == maquina_id
    ).order_by(desc(NotaMaquina.fecha)).all()

    return [NotaMaquinaOut.model_validate(nota) for nota in notas]


def crear_nota_maquina(
    db: Session,
    maquina_id: int,
    texto: str,
    usuario: str = "Usuario"
) -> NotaMaquinaOut:
    """
    Crea una nueva nota para una máquina específica
    """
    # Verificar que la máquina existe
    maquina = db.query(Maquina).filter(Maquina.id == maquina_id).first()
    if not maquina:
        raise ValueError(f"Máquina con ID {maquina_id} no encontrada")

    # Validar que el texto no esté vacío
    if not texto or len(texto.strip()) < 3:
        raise ValueError("El texto de la nota debe tener al menos 3 caracteres")

    # Crear la nota
    nueva_nota = NotaMaquina(
        maquina_id=maquina_id,
        texto=texto.strip(),
        usuario=usuario,
        fecha=datetime.utcnow()
    )

    db.add(nueva_nota)
    db.commit()
    db.refresh(nueva_nota)

    logger.info(f"Nota creada para máquina {maquina_id} por usuario {usuario}")

    return NotaMaquinaOut.model_validate(nueva_nota)


def eliminar_nota_maquina(db: Session, nota_id: int) -> bool:
    """
    Elimina una nota específica por su ID
    """
    nota = db.query(NotaMaquina).filter(NotaMaquina.id == nota_id).first()

    if not nota:
        raise ValueError(f"Nota con ID {nota_id} no encontrada")

    db.delete(nota)
    db.commit()

    logger.info(f"Nota {nota_id} eliminada correctamente")

    return True
