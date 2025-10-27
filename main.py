# main.py - VERSIÓN ACTUALIZADA CON SCHEDULER

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.init_db import init_db
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.middlewares.error_handler import ErrorHandler
from app.db.seed_db import create_admin_user
import os
import logging

# Importar los routers
from app.routers import (
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
    jornada_laboral_router
)

# ✅ NUEVO: Importar scheduler
from app.tasks.jornada_scheduler import iniciar_scheduler

# ✅ NUEVO: Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ✅ NUEVO: Variable global para el scheduler
scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    ✅ Gestión del ciclo de vida de la aplicación
    - Startup: Inicializar BD y scheduler
    - Shutdown: Detener scheduler
    """
    global scheduler
    
    # ========== STARTUP ==========
    logger.info("🚀 Iniciando aplicación Kedikian...")
    
    # Inicializar base de datos
    await init_db()
    logger.info("✅ Base de datos inicializada")
    
    # Crear usuario admin
    create_admin_user()
    logger.info("✅ Usuario admin verificado")
    
    # ✅ NUEVO: Iniciar scheduler de jornadas
    try:
        logger.info("⏰ Iniciando scheduler de jornadas laborales...")
        scheduler = iniciar_scheduler()
        logger.info("✅ Scheduler iniciado correctamente")
    except Exception as e:
        logger.error(f"❌ Error iniciando scheduler: {str(e)}")
        # No detener la aplicación si falla el scheduler
    
    logger.info("✅ Aplicación Kedikian iniciada correctamente")
    
    yield
    
    # ========== SHUTDOWN ==========
    logger.info("🛑 Deteniendo aplicación...")
    
    # ✅ NUEVO: Detener scheduler
    if scheduler:
        try:
            logger.info("⏰ Deteniendo scheduler...")
            scheduler.shutdown(wait=False)
            logger.info("✅ Scheduler detenido correctamente")
        except Exception as e:
            logger.error(f"❌ Error deteniendo scheduler: {str(e)}")
    
    logger.info("✅ Aplicación detenida correctamente")

# Crear aplicación con lifespan actualizado
app = FastAPI(
    lifespan=lifespan,  # ✅ MANTENER lifespan
    title="Kedikian API",
    version="1.0.0",
    openapi_version="3.0.2",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    root_path="/api"
)

app.add_middleware(ErrorHandler)

# Configuración de CORS y middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",           # Desarrollo local
        "http://localhost:3000",           # Desarrollo alternativo
        "http://168.197.50.82",            # Tu servidor de producción
        "https://168.197.50.82",           # HTTPS si aplica
        "http://kedikian.site",            # Tu dominio
        "https://kedikian.site"
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Métodos permitidos
    allow_headers=["*"],  # Headers permitidos
)

# Montar la carpeta static para servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar directorio de uploads
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Middleware para servir archivos estáticos de uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Incluir todos los routers
app.include_router(usuarios_router.router, prefix="/v1")
app.include_router(maquinas_router.router, prefix="/v1")
app.include_router(proyectos_router.router, prefix="/v1")
app.include_router(contratos_router.router, prefix="/v1")
app.include_router(gastos_router.router, prefix="/v1")
app.include_router(pagos_router.router, prefix="/v1")
app.include_router(productos_router.router, prefix="/v1")
app.include_router(arrendamientos_router.router, prefix="/v1")
app.include_router(movimientos_inventario_router.router, prefix="/v1")
app.include_router(reportes_laborales_router.router, prefix="/v1")
app.include_router(excel_router.router, prefix="/v1")
app.include_router(entrega_arido_router.router, prefix="/v1")
app.include_router(login_router.router, prefix="/v1")
app.include_router(aridos_router.router, prefix="/v1")
app.include_router(mantenimiento_router.router, prefix="/v1")
app.include_router(jornada_laboral_router.router, prefix="/v1")

# Debug al final del archivo, después de incluir routers
def debug_routes():
    print("🚀 RUTAS REGISTRADAS:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            print(f"  {route.methods} {route.path}")
        elif hasattr(route, 'path'):
            print(f"  [STATIC] {route.path}")

# Llamar debug después de configurar todo
debug_routes()

@app.get("/")
def read_root():
    """✅ Endpoint raíz"""
    return {
        "message": "API Kedikian funcionando correctamente",
        "version": "1.0.0",
        "scheduler": "active" if scheduler and scheduler.running else "inactive"
    }

# ✅ NUEVO: Health check con información del scheduler
@app.get("/health")
def health_check():
    """✅ Health check para monitoreo"""
    return {
        "status": "healthy",
        "api": "Kedikian API v1.0.0",
        "scheduler_running": scheduler.running if scheduler else False,
        "scheduler_jobs": len(scheduler.get_jobs()) if scheduler else 0
    }

@app.get("/debug-openapi")
def debug_openapi():
    return app.openapi()
