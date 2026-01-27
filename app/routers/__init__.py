# Exportar todos los routers para facilitar su importación
from . import (
    usuarios_router,
    maquinas_router,
    proyectos_router,
    contratos_router,
    gastos_router,
    pagos_router,
    productos_router,
    arrendamientos_router,
    movimientos_inventario_router,
    reportes_laborales_router,
    excel_router,
    entrega_arido_router,
    login_router,
    aridos_router,
    mantenimiento_router,
    jornada_laboral_router,
    cuenta_corriente_router
)

__all__ = [
    "usuarios_router",
    "maquinas_router",
    "proyectos_router",
    "contratos_router",
    "gastos_router",
    "pagos_router",
    "productos_router",
    "arrendamientos_router",
    "movimientos_inventario_router",
    "reportes_laborales_router",
    "excel_router",
    "entrega_arido_router",
    "login_router",
    "aridos_router",
    "mantenimiento_router",
    "jornada_laboral_router",
    "cuenta_corriente_router"
]
