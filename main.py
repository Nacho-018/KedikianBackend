from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.init_db import init_db
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.middlewares.error_handler import ErrorHandler
from app.db.seed_db import create_admin_user
from app.routers import jornada_laboral_router
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan, title="Kedikian API", version="1.0.0",
openapi_version="3.0.2",    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json", root_path="/api")

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
        "https://kedikian.site"],
    allow_credentials=True,
    allow_methods=["*"],  # Métodos permitidos
    allow_headers=["*"],  # Headers permitidos
)

# Montar la carpeta static para servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

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

create_admin_user()

@app.get("/")
def read_root():
    return {"message": "API funcionando correctamente"}

app.get("/debug-openapi")
def debug_openapi():
    return app.openapi()
