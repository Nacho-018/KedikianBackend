from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.init_db import init_db
from app.db.database import SessionLocal
from fastapi.staticfiles import StaticFiles
# Importar los routers
from routers import (
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
def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "API funcionando correctamente"}

# Lineas de código para debuggear
import uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app")
