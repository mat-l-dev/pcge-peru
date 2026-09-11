# Guía de contribución

Gracias por tu interés en contribuir al proyecto PCGE Perú. Esta guía describe los requisitos y procedimientos básicos para realizar cambios en el repositorio.

## Antes de empezar

- Utiliza Python 3.14.x.
- Crea una rama independiente para tus cambios.
- No realices cambios directamente sobre `main`.
- Mantén cada contribución enfocada en un objetivo específico.

## Configuración local

Crea y activa un entorno virtual con los siguientes comandos:

```bash
py -3.14 -m venv .venv
```

En PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Actualiza `pip`:

```powershell
python -m pip install --upgrade pip
```

Instala el proyecto en modo editable y las herramientas de desarrollo:

```bash
pip install -e .
pip install --group dev
```

Instala los hooks de `pre-commit`:

```bash
pre-commit install
```

## Antes de enviar un pull request

Ejecuta las comprobaciones del proyecto:

```bash
ruff check .
ruff format --check .
pytest
python -m build
```

Todos los comandos deben finalizar correctamente y sin errores.

## Cambios en los datos del PCGE

El catálogo contable distribuido en `pcge-peru` reproduce con fidelidad los textos normativos oficiales emitidos por el Consejo Normativo de Contabilidad (CNC). Si propones cambios o adiciones en la información del catálogo contable, debes cumplir estrictamente los siguientes principios y procedimientos.

### Jerarquía y distinción de información

En todo momento se debe distinguir con claridad entre tres categorías:

1. **Datos oficiales**: Información textualmente respaldada por la fuente oficial primaria (códigos impresos, denominaciones, jerarquía documental). La fuente oficial primaria es la única autoridad normativa.
2. **Datos derivados**: Información calculada de manera determinística por la librería a partir de los datos oficiales (relaciones de parentesco derivadas del prefijo numérico, longitud de código, identificación de raíces y hojas). No deben presentarse como definiciones explícitas del CNC.
3. **Metadatos de librería**: Información técnica propia de `pcge-peru` para control de versiones y esquemas (`schema_version`, `dataset_revision`, `entry_count`). No forman parte de la norma contable.

### Flujo de trazabilidad del catálogo

Cualquier incorporación o actualización de un catálogo debe seguir el flujo determinístico de mantenimiento:

1. **Identificación de la fuente oficial primaria**: Identificar y verificar la resolución oficial en el Diario Oficial El Peruano y el documento técnico en la sede digital del Ministerio de Economía y Finanzas (gob.pe/mef).
2. **Verificación de procedencia**: Registrar en `src/pcge/data/<versión>/source.json` los metadatos documentales: título oficial, autoridad emisora, dispositivo legal, fechas (emisión, publicación, vigencia obligatoria), URL de consulta, nombre del archivo fuente, hash SHA-256 de la fuente descargada y rango de páginas del Capítulo II (Catálogo de Cuentas).
3. **Extracción y normalización**: Procesar el texto oficial preservando la denominación documental exacta, eliminando espacios superfluos y respetando mayúsculas/minúsculas oficiales.
4. **Auditoría documental de anomalías**: Si el documento oficial contiene erratas, duplicidades o discordancias (por ejemplo, códigos duplicados o incoherencias de jerarquía), no se corrigen silenciosamente ni se inventan códigos inexistentes. Se documentan formalmente en `src/pcge/data/<versión>/anomalies.json` indicando páginas, texto impreso, disposición adoptada y justificación.
5. **Generación del dataset canónico**: Generar `src/pcge/data/<versión>/entries.json` en orden documental estricto, cumpliendo las reglas estructurales (código numérico ASCII de 1 a 6 dígitos, prefijo canónico de parentesco, unicidad).
6. **Cálculo de integridad criptográfica**: Calcular el hash SHA-256 (64 caracteres hexadecimales en mayúsculas) de los bytes exactos de `entries.json` y registrarlo en `source.json` bajo el campo `dataset_sha256`.
7. **Actualización de metadatos**: Registrar en `metadata.json` la versión (`pcge_version`), el esquema (`schema_version`), la revisión (`dataset_revision`) y el conteo exacto de entradas (`entry_count`).
8. **Verificación automatizada**: Comprobar que los datos validen contra los esquemas JSON (`schemas/`), pasen la suite de pruebas (`pytest`) y superen la verificación de empaquetado (`scripts/verify_distribution.py`).

### Política de corrección de datasets y revisiones

Para mantener la estabilidad y predictibilidad de los consumidores de la librería, se aplica la siguiente política de versionado y corrección de datos:

- **Edición oficial del catálogo (`pcge_version`)**: Corresponde a la edición normativa oficial aprobada por el Consejo Normativo de Contabilidad (por ejemplo, `"2019"`, `"2026"`). Una corrección en la transcripción o representación interna de un catálogo existente **no crea una nueva versión de PCGE**.
- **Revisión del dataset (`dataset_revision`)**: Entero incremental (`>= 1`) administrado por `pcge-peru` que refleja la edición del snapshot empaquetado. Si se subsana una errata interna de transcripción o se ajusta la representación canónica con respaldo normativo oficial, se incrementa `dataset_revision` (por ejemplo, de `1` a `2`), actualizando simultáneamente `dataset_sha256` en `source.json`.
- **Inmutabilidad de `entries.json`**: El archivo `entries.json` solo puede ser modificado si existe evidencia oficial fehaciente que demuestre un error en la transcripción de la librería respecto a la fuente oficial o ante la publicación de una fe de erratas oficial por parte del CNC.
- **Prohibición de invención de códigos**: Bajo ninguna circunstancia se introducirán códigos contables ausentes en el documento oficial ("cuentas puente", "correcciones lógicas" o inferencias no promulgadas). Las inconsistencias editoriales oficiales deben canalizarse exclusivamente a través de `anomalies.json`.

## Pull requests

Los pull requests deben cumplir los siguientes criterios:

- Tener un objetivo claro.
- Incluir pruebas cuando corresponda.
- Mantener el estilo del proyecto.
- No incluir cambios no relacionados.