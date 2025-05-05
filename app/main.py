from fastapi import FastAPI
from app.db.init_db import init_db  # Llama a la función que crea las tablas

app = FastAPI()

# Inicializar la base de datos
@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def read_root():
    return {"message": "API funcionando correctamente"}
