from app.db.database import Base, engine
from sqlalchemy import text
from app.db.models import (
    Usuario,
    Maquina,
    Proyecto,
    Contrato,
    Gasto,
    Pago,
    Producto,
    Arrendamiento,
    MovimientoInventario,
    ReporteLaboral,
)

async def add_proyecto_id_column():
    """
    Agrega la columna proyecto_id a la tabla reporte_laboral si no existe
    """
    with engine.begin() as connection:
        try:
            # Usar DO $$ BEGIN ... END $$ para asegurar que la operación es atómica
            connection.execute(text("""
                DO $$ 
                BEGIN
                    -- Verificar si la columna existe
                    IF NOT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name='reporte_laboral' 
                        AND column_name='proyecto_id'
                    ) THEN
                        -- Si no existe, la agregamos
                        ALTER TABLE reporte_laboral 
                        ADD COLUMN proyecto_id INTEGER;
                        
                        -- Agregar la restricción de clave foránea
                        ALTER TABLE reporte_laboral
                        ADD CONSTRAINT fk_reporte_proyecto 
                        FOREIGN KEY (proyecto_id) 
                        REFERENCES proyecto(id);
                        
                        RAISE NOTICE 'Columna proyecto_id agregada exitosamente';
                    END IF;
                END $$;
            """))
            print("✅ Verificación/creación de columna proyecto_id completada")
            
        except Exception as e:
            print(f"❌ Error al verificar/agregar la columna: {str(e)}")
            # Intentar obtener más información sobre el error
            try:
                connection.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.tables 
                        WHERE table_name = 'reporte_laboral'
                    );
                """))
                print("La tabla reporte_laboral existe")
                
                connection.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'reporte_laboral';
                """))
                print("Columnas actuales en reporte_laboral:", result.fetchall())
            except Exception as debug_e:
                print(f"Error al intentar debuggear: {str(debug_e)}")
            raise e

async def init_db():
    """
    Inicializa la base de datos y asegura que exista la columna proyecto_id
    """
    try:
        print("🚀 Iniciando configuración de la base de datos...")
        
        # Crear todas las tablas si no existen
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas base creadas")
        
        # Verificar la estructura actual de la tabla
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'reporte_laboral'
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            print("📊 Estructura actual de reporte_laboral:", columns)
        
        # Agregar la columna proyecto_id
        await add_proyecto_id_column()
        print("✅ Proceso de inicialización completado")
        
    except Exception as e:
        print(f"❌ Error durante la inicialización: {str(e)}")
        raise e
