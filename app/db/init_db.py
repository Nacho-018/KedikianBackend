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

async def add_es_feriado_column():
    """
    Agrega la columna es_feriado a la tabla jornada_laboral si no existe
    """
    with engine.begin() as connection:
        try:
            connection.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name='jornada_laboral'
                          AND column_name='es_feriado'
                    ) THEN
                        ALTER TABLE jornada_laboral
                        ADD COLUMN es_feriado BOOLEAN DEFAULT FALSE;
                        RAISE NOTICE 'Columna es_feriado agregada exitosamente';
                    END IF;
                END $$;
            """))
            print("✅ Verificación/creación de columna es_feriado completada")
        except Exception as e:
            print(f"❌ Error al verificar/agregar la columna es_feriado: {str(e)}")
            raise e

async def ensure_jornada_laboral_columns():
    """
    Asegura que todas las columnas usadas por el modelo JornadaLaboral existan.
    Opera de forma idempotente con IF NOT EXISTS.
    """
    statements = [
        # Campos principales ya deberían existir: id, usuario_id, fecha
        # Control de tiempo
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS hora_inicio TIMESTAMP NOT NULL;",
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS hora_fin TIMESTAMP NULL;",
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS tiempo_descanso INTEGER DEFAULT 0;",
        # Cálculos
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS horas_regulares DOUBLE PRECISION DEFAULT 0.0;",
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS horas_extras DOUBLE PRECISION DEFAULT 0.0;",
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS total_horas DOUBLE PRECISION DEFAULT 0.0;",
        # Estado y control
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS estado VARCHAR(20) DEFAULT 'activa';",
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS es_feriado BOOLEAN DEFAULT FALSE;",
        # Control específico de horas extras
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS limite_regular_alcanzado BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS hora_limite_regular TIMESTAMP NULL;",
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS overtime_solicitado BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS overtime_confirmado BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS overtime_iniciado TIMESTAMP NULL;",
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS pausa_automatica BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS finalizacion_forzosa BOOLEAN DEFAULT FALSE;",
        # Información adicional
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS notas_inicio TEXT NULL;",
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS notas_fin TEXT NULL;",
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS motivo_finalizacion VARCHAR(100) NULL;",
        # Geolocalización
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS ubicacion_inicio TEXT NULL;",
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS ubicacion_fin TEXT NULL;",
        # Control de advertencias
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS advertencia_8h_mostrada BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS advertencia_limite_mostrada BOOLEAN DEFAULT FALSE;",
        # Timestamps
        # created y updated pueden existir ya; si no, los creamos sin default de zona horaria
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS created TIMESTAMP NULL;",
        "ALTER TABLE jornada_laboral ADD COLUMN IF NOT EXISTS updated TIMESTAMP NULL;",
    ]

    with engine.begin() as connection:
        try:
            for stmt in statements:
                connection.execute(text(stmt))
            print("✅ Verificación/creación de columnas de jornada_laboral completada")
        except Exception as e:
            print(f"❌ Error asegurando columnas de jornada_laboral: {str(e)}")
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
        # Agregar la columna es_feriado en jornada_laboral
        await add_es_feriado_column()
        # Asegurar todas las columnas del modelo jornada_laboral
        await ensure_jornada_laboral_columns()
        print("✅ Proceso de inicialización completado")
        
    except Exception as e:
        print(f"❌ Error durante la inicialización: {str(e)}")
        raise e
