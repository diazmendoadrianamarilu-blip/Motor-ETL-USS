-- Extracción CRUDA de Docentes desde Sipán. Sin CASE WHEN: la homologación la hace el motor.
-- TODO: reemplazar dbo.<TABLA_DOCENTES> (y joins) por las tablas reales del legacy.
-- Los alias deben coincidir EXACTAMENTE con DEFINICION.columnas_legacy.
SELECT
    CAST(d.ID_LEGADO AS VARCHAR(15))                       AS ID_LEGADO,
    d.AUD_Unidad_BDSipan                                   AS AUD_Unidad_BDSipan,
    d.AUD_Cargo_BDSipan                                    AS AUD_Cargo_BDSipan,
    d.AUD_Dedicacion_BDSipan                               AS AUD_Dedicacion_BDSipan,
    d.[ESCUELA PROCEDENCIA REAL BD]                        AS [ESCUELA PROCEDENCIA REAL BD],
    d.[GRADO USS]                                          AS [GRADO USS],
    CONVERT(VARCHAR(8), d.[FECHA OBTENCION GRADO], 112)    AS [FECHA OBTENCION GRADO]  -- YYYYMMDD
FROM dbo.TABLA_DOCENTES AS d;
