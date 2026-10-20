-- TODO: reemplazar por las tablas reales del legacy (extracción cruda, sin CASE WHEN).
SELECT
    CAST(g.ID_Alumno AS VARCHAR(9))                 AS ID_Alumno,
    g.Cod_Grado_Sipan                               AS Cod_Grado_Sipan,
    CONVERT(VARCHAR(10), g.Fecha_Emision, 23)       AS Fecha_Emision   -- YYYY-MM-DD
FROM dbo.TABLA_GRADOS AS g;
