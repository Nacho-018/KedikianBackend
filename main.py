from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.init_db import init_db
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.middlewares.error_handler import ErrorHandler
# Importar los routers
from app.routers import (
    usuarios,
    maquinas,
    proyectos,
    contratos,
    gastos,
    pagos,
    productos,
    arrendamientos,
    movimientos_inventario,
    reportes_laborales,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(ErrorHandler)
# Configuración de CORS y middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Permite solicitudes desde cualquier origen
    allow_credentials=True,
    allow_methods=["*"],  # Métodos permitidos
    allow_headers=["*"],  # Headers permitidos
)

# Montar la carpeta static para servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(usuarios.router, prefix="/api/v1")
app.include_router(maquinas.router, prefix="/api/v1")
app.include_router(proyectos.router, prefix="/api/v1")
app.include_router(contratos.router, prefix="/api/v1")
app.include_router(gastos.router, prefix="/api/v1")
app.include_router(pagos.router, prefix="/api/v1")
app.include_router(productos.router, prefix="/api/v1")
app.include_router(arrendamientos.router, prefix="/api/v1")
app.include_router(movimientos_inventario.router, prefix="/api/v1")
app.include_router(reportes_laborales.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "API funcionando correctamente"}

# Lineas de código para debuggear
import uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app")
