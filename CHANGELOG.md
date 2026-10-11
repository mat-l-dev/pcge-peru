# Historial de cambios

## Sin publicar

- Corrección de los nombres de `60931` (Transporte) y `68714` (Cuentas por cobrar
  diversas – Terceros) en PCGE 2026: se eliminan palabras de la entrada anterior
  arrastradas al inicio de una nueva página. Respaldo: [PDF oficial 2026](https://cdn.www.gob.pe/uploads/document/file/10567153/8559148-plan-contable-general-empresarial-pcge-2026%282%29.pdf?v=1788535543),
  páginas PDF 40 y 46 (impresas 38 y 44).
- Corrección del localizador documental de `61 VARIACIÓN DE INVENTARIOS` en las
  anomalías de PCGE 2019: página PDF 49 e impresa 48, conforme al
  [PDF oficial 2019](https://www.mef.gob.pe/contenidos/conta_publ/pcge/PCGE_2019.pdf).
- Rechazo de consultas de búsqueda que quedan vacías o solo con espacios tras
  normalizar acentos, evitando coincidencias sin un término de búsqueda.
- Rechazo de espacios alrededor de códigos de anomalías para mantener consultas
  coherentes con los valores admitidos por el modelo.
- Esquemas JSON más estrictos para códigos, textos vacíos y fechas calendáricas.
- Nombres normalizados una sola vez al construir el catálogo para agilizar las
  búsquedas repetidas, conservando textos y orden documental.
- Ruff sincronizado entre desarrollo y pre-commit, con verificación automática.
- CI en Ubuntu y Windows y comprobación de paquetes después de subirlos y
  descargarlos como artefactos.
- Verificación de la instalación aislada del wheel original y del reconstruido
  desde la distribución fuente.

Ambos snapshots pasan a `dataset_revision = 2`. Se actualiza el `dataset_sha256`
de PCGE 2026 por la corrección de nombres. En PCGE 2019 solo cambia el localizador
de una anomalía: `entries.json` y su `dataset_sha256` permanecen idénticos.
Las versiones normativas, los códigos, la jerarquía y los hashes de los PDF
fuente no cambian.
