-- ============================================================
-- Script para Diagnosticar y Limpiar Duplicados de Clientes
-- ============================================================
-- IMPORTANTE: Hacer BACKUP de la base de datos antes de ejecutar DELETE

-- ============================================================
-- 1. DIAGNÓSTICO - Ver todos los clientes duplicados
-- ============================================================

-- Ver registros de "Claudio Peisina" específicamente
SELECT
    id,
    nombre,
    email,
    telefono,
    direccion,
    created,
    updated
FROM cliente
WHERE nombre LIKE '%Claudio Peisina%'
ORDER BY id;

-- Ver TODOS los clientes duplicados por nombre
SELECT
    nombre,
    COUNT(*) as cantidad,
    GROUP_CONCAT(id) as ids
FROM cliente
GROUP BY nombre
HAVING COUNT(*) > 1
ORDER BY cantidad DESC;

-- Ver clientes duplicados por nombre + email
SELECT
    nombre,
    email,
    COUNT(*) as cantidad,
    GROUP_CONCAT(id) as ids
FROM cliente
GROUP BY nombre, email
HAVING COUNT(*) > 1
ORDER BY cantidad DESC;

-- Ver clientes completamente idénticos (nombre, email, teléfono)
SELECT
    nombre,
    email,
    telefono,
    COUNT(*) as cantidad,
    GROUP_CONCAT(id) as ids
FROM cliente
GROUP BY nombre, email, telefono
HAVING COUNT(*) > 1
ORDER BY cantidad DESC;

-- ============================================================
-- 2. ANÁLISIS - Ver si los duplicados tienen cotizaciones
-- ============================================================

-- Ver cuántas cotizaciones tiene cada cliente duplicado
SELECT
    c.id,
    c.nombre,
    c.email,
    COUNT(cot.id) as num_cotizaciones,
    c.created,
    c.updated
FROM cliente c
LEFT JOIN cotizacion cot ON c.id = cot.cliente_id
WHERE c.nombre IN (
    SELECT nombre
    FROM cliente
    GROUP BY nombre
    HAVING COUNT(*) > 1
)
GROUP BY c.id
ORDER BY c.nombre, c.created;

-- ============================================================
-- 3. LIMPIEZA - Eliminar duplicados (CUIDADO!)
-- ============================================================

-- OPCIÓN A: Mantener el registro más ANTIGUO (menor ID)
-- Esto eliminará los duplicados más recientes

-- PRIMERO: Ver qué se va a eliminar (NO elimina, solo muestra)
SELECT
    c.id,
    c.nombre,
    c.email,
    c.telefono,
    c.created,
    'SE ELIMINARÁ' as accion
FROM cliente c
WHERE c.id NOT IN (
    -- Subquery que obtiene el ID más pequeño (más antiguo) de cada grupo
    SELECT MIN(id)
    FROM cliente
    GROUP BY nombre, COALESCE(email, '')
)
ORDER BY c.nombre, c.id;

-- LUEGO: Ejecutar el DELETE (¡HACER BACKUP PRIMERO!)
-- Descomentar para ejecutar:
/*
DELETE FROM cliente
WHERE id NOT IN (
    SELECT * FROM (
        SELECT MIN(id)
        FROM cliente
        GROUP BY nombre, COALESCE(email, '')
    ) as temp
);
*/

-- OPCIÓN B: Mantener el registro más RECIENTE (mayor ID)
-- Esto eliminará los duplicados más antiguos

-- PRIMERO: Ver qué se va a eliminar
SELECT
    c.id,
    c.nombre,
    c.email,
    c.telefono,
    c.created,
    'SE ELIMINARÁ' as accion
FROM cliente c
WHERE c.id NOT IN (
    SELECT MAX(id)
    FROM cliente
    GROUP BY nombre, COALESCE(email, '')
)
ORDER BY c.nombre, c.id;

-- LUEGO: Ejecutar el DELETE (¡HACER BACKUP PRIMERO!)
-- Descomentar para ejecutar:
/*
DELETE FROM cliente
WHERE id NOT IN (
    SELECT * FROM (
        SELECT MAX(id)
        FROM cliente
        GROUP BY nombre, COALESCE(email, '')
    ) as temp
);
*/

-- OPCIÓN C: Mantener el que tiene MÁS COTIZACIONES
-- Más complejo pero preserva el cliente con más datos relacionados

-- Ver cuál se mantendría de cada grupo
WITH RankedClientes AS (
    SELECT
        c.id,
        c.nombre,
        c.email,
        c.telefono,
        c.created,
        COUNT(cot.id) as num_cotizaciones,
        ROW_NUMBER() OVER (
            PARTITION BY c.nombre, COALESCE(c.email, '')
            ORDER BY COUNT(cot.id) DESC, c.created ASC
        ) as rn
    FROM cliente c
    LEFT JOIN cotizacion cot ON c.id = cot.cliente_id
    GROUP BY c.id, c.nombre, c.email, c.telefono, c.created
)
SELECT
    id,
    nombre,
    email,
    num_cotizaciones,
    created,
    CASE WHEN rn = 1 THEN 'SE MANTIENE' ELSE 'SE ELIMINA' END as accion
FROM RankedClientes
WHERE nombre IN (
    SELECT nombre
    FROM cliente
    GROUP BY nombre
    HAVING COUNT(*) > 1
)
ORDER BY nombre, rn;

-- ============================================================
-- 4. VERIFICACIÓN POST-LIMPIEZA
-- ============================================================

-- Verificar que no quedan duplicados
SELECT
    nombre,
    email,
    COUNT(*) as cantidad
FROM cliente
GROUP BY nombre, COALESCE(email, '')
HAVING COUNT(*) > 1;

-- Debe retornar 0 filas si la limpieza fue exitosa

-- ============================================================
-- 5. CASO ESPECÍFICO: Limpiar solo "Claudio Peisina"
-- ============================================================

-- Ver todos los registros de Claudio Peisina
SELECT
    c.id,
    c.nombre,
    c.email,
    c.telefono,
    COUNT(cot.id) as num_cotizaciones,
    c.created
FROM cliente c
LEFT JOIN cotizacion cot ON c.id = cot.cliente_id
WHERE c.nombre LIKE '%Claudio Peisina%'
GROUP BY c.id
ORDER BY c.created;

-- Eliminar duplicados de Claudio Peisina manteniendo el más antiguo
-- Descomentar para ejecutar (¡BACKUP PRIMERO!):
/*
DELETE FROM cliente
WHERE nombre LIKE '%Claudio Peisina%'
AND id NOT IN (
    SELECT * FROM (
        SELECT MIN(id)
        FROM cliente
        WHERE nombre LIKE '%Claudio Peisina%'
    ) as temp
);
*/
