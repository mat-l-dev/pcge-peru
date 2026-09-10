# pcge-peru

Librería open source en Python para representar, consultar y validar el catálogo oficial del Plan Contable General Empresarial (PCGE) del Perú.

El propósito de `pcge-peru` es brindar una representación tipada y programáticamente accesible de las entradas del catálogo contable peruano, facilitando su navegación jerárquica y búsqueda en proyectos de software.

> **Alcance del proyecto**:
> - `pcge-peru` **no es un ERP**.
> - No implementa asientos contables, libro diario, mayor, cálculo de impuestos ni facturación electrónica.
> - El proyecto se enfoca exclusivamente en el catálogo de cuentas del **Capítulo II** de los planes contables soportados (snapshots para PCGE 2019 y PCGE 2026).
> - El **Capítulo III** (dinámica contable, descripciones narrativas y comentarios por cuenta) no forma parte del modelo público en esta versión.

---

## Estado del proyecto

El proyecto se encuentra en **etapa de desarrollo inicial** (`v0.1.0`). La API pública puede recibir ajustes y mejoras antes de alcanzar una versión de estabilidad definitiva.

El paquete se encuentra disponible públicamente en [PyPI](https://pypi.org/project/pcge-peru/).

---

## Requisitos e instalación

### Requisitos

- **Python**: `>=3.14,<3.15` (probado en Python 3.14).

### Instalación

Instale el paquete desde PyPI:

```bash
pip install pcge-peru
```

### Instalación desde código fuente (desarrollo)

Para clonar e instalar el proyecto en un entorno virtual:

```bash
git clone https://github.com/mat-l-dev/pcge-peru.git
cd pcge-peru
```

Crear y activar el entorno virtual:

En Linux / macOS:
```bash
python3.14 -m venv .venv
source .venv/bin/activate
```

En Windows (PowerShell):
```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
```

Instalar el paquete en modo editable y las herramientas de desarrollo:

```bash
python -m pip install --upgrade pip
pip install -e .
pip install --group dev
```

---

## Inicio rápido

La función principal para comenzar es `load_catalog`, que carga el catálogo oficial empaquetado como un objeto `PCGECatalog` con una interfaz pública de consulta de solo lectura. Dado que cada snapshot representa una edición normativa distinta, la versión debe indicarse siempre de forma explícita:

```python
from pcge import available_versions, load_catalog

# Listar las versiones normativas disponibles
print(available_versions())
# ("2019", "2026")

# Cargar explícitamente la versión requerida
catalog = load_catalog("2026")

# O cargar la versión 2019:
catalog_2019 = load_catalog("2019")

# 1. Longitud del catálogo
print(len(catalog))
# 1636

# 2. Acceso directo por código (retorna PCGEEntry o lanza KeyError)
entry = catalog["10"]
print(entry.code)  # 10
print(entry.name)  # EFECTIVO Y EQUIVALENTES AL EFECTIVO
print(entry.pcge_level)  # account
print(entry.parent_code)  # "1"

# 3. Acceso seguro con get (retorna None si no existe)
print(catalog.get("101"))  # PCGEEntry(code='101', name='Caja', parent_code='10')
print(catalog.get("9999"))  # None

# 4. Comprobación de pertenencia
print("10" in catalog)  # True
print("9999" in catalog)  # False

# 5. Navegación: entrada padre inmediata (retorna PCGEEntry o None para elementos raíz)
parent = catalog.parent("101")
print(parent.code, parent.name)
# 10 EFECTIVO Y EQUIVALENTES AL EFECTIVO

# 6. Navegación: hijos directos (retorna tupla inmutable de PCGEEntry)
children = catalog.children("10")
for child in children:
    print(child.code, child.name)
# 101 Caja
# 102 Fondos fijos
# 103 Efectivo y cheques en tránsito
# 104 Cuentas corrientes en instituciones financieras
# 105 Otros equivalentes al efectivo
# 106 Depósitos en instituciones financieras
# 107 Fondos sujetos a restricción

# 7. Navegación: ancestros (desde el padre inmediato hasta el elemento raíz)
ancestors = catalog.ancestors("1041")
for anc in ancestors:
    print(anc.code, anc.name)
# 104 Cuentas corrientes en instituciones financieras
# 10 EFECTIVO Y EQUIVALENTES AL EFECTIVO
# 1 ACTIVO DISPONIBLE Y EXIGIBLE

# 8. Navegación: todos los descendientes en profundidad
descendants = catalog.descendants("9")
for desc in descendants:
    print(desc.code, desc.name)
# 91 GASTOS DE OPERACIÓN
# 92 GASTOS DE INVERSIÓN
# 93 GASTOS DE FINANCIAMIENTO

# 9. Búsqueda por texto normalizado (ignora mayúsculas, minúsculas y acentos)
results = catalog.search("consultoria")
for res in results:
    print(res.code, res.name)
# 4942 Contrato de consultoría TI
# 632 Asesoría y consultoría
# 70992 Contrato de consultoría TI

# 10. Metadatos del catálogo
meta = catalog.metadata
print(meta.pcge_version)  # 2026
print(meta.entry_count)  # 1636

# 11. Procedencia normativa del catálogo
prov = catalog.provenance
print(prov.authority)  # Consejo Normativo de Contabilidad
print(prov.resolution)  # Resolución N.° 002-2026-EF/30
print(prov.mandatory_effective_date)  # 2028-01-01
print(prov.source_sha256)  # Hash SHA-256 del documento normativo original
print(
    prov.dataset_sha256
)  # Hash SHA-256 canónico del dataset empaquetado (verificado en carga)

# 12. Anomalías documentales auditadas
for anomaly in catalog.anomalies:
    print(f"[{anomaly.id}] {anomaly.type} ({anomaly.status})")

# Consultar anomalías asociadas a un código contable específico
anomalies_709 = catalog.anomalies_for("70992")
for a in anomalies_709:
    print(a.id, a.description)
```

### Reglas clave de uso

- **Selección explícita de versión obligatoria**: La función `load_catalog(version)` requiere indicar explícitamente la versión a cargar (`"2019"` o `"2026"`). Dado que cada snapshot corresponde a una norma contable distinta, la librería no asume ninguna versión por defecto.
- **Códigos como cadenas de texto (`str`)**: Los códigos contables se manejan siempre como `str` (por ejemplo, `"10"`, `"101"`), nunca como enteros `int`.
- **Manejo de códigos inexistentes**: `catalog[code]` lanza `KeyError` si el código no forma parte del catálogo. Para evitar excepciones, utilice `catalog.get(code)` o la verificación `"code" in catalog`.
- **Estructuras inmutables**: `catalog.children()`, `catalog.ancestors()` y `catalog.descendants()` devuelven tuplas inmutables (`tuple[PCGEEntry, ...]`).
- **Búsqueda insensible a tildes y caja**: El método `catalog.search()` normaliza los caracteres de entrada, de modo que términos como `"mercaderias"`, `"MERCADERÍAS"` y `"mercaderías"` devuelven los mismos resultados.

---

## Modelo de dominio

El paquete expone las siguientes clases y funciones públicas principales:

- **`PCGEEntry`**: Modelo inmutable (`frozen`, `slots`) que representa una entrada del catálogo con las propiedades `code: str`, `name: str`, `parent_code: str | None`, y las propiedades calculadas `code_length: int` y `pcge_level: PCGELevel | None`.
- **`PCGELevel`**: Enumeración (`StrEnum`) con los cinco niveles jerárquicos normativos:
  - `ELEMENT` (1 dígito)
  - `ACCOUNT` (2 dígitos)
  - `SUBACCOUNT` (3 dígitos)
  - `DIVISIONARY` (4 dígitos)
  - `SUBDIVISIONARY` (5 dígitos)
- **`PCGEMetadata`**: Modelo inmutable con la información de versión y revisión del dataset (`pcge_version`, `schema_version`, `dataset_revision`, `entry_count`).
- **`PCGEProvenance`**: Modelo inmutable (`frozen`, `slots`) que representa la procedencia y respaldo documental normativo del snapshot (`title`, `authority`, `resolution`, `resolution_date`, `publication_date`, `mandatory_effective_date`, `resolution_url`, `source_filename`, `source_sha256`, `catalog_chapter`, `catalog_pdf_pages`, `catalog_printed_pages`, `dataset_sha256`).
- **`PCGEAnomaly`**: Modelo inmutable (`frozen`, `slots`) que documenta una anomalía editorial oficial auditada (`id`, `type`, `codes`, `status`, `description`, `decision`, `confirmation_no_invented_code`, `occurrences`).
- **`PCGEAnomalyOccurrence`**: Modelo inmutable (`frozen`, `slots`) que describe una aparición textual dentro del documento oficial (`occurrence_index`, `pdf_page`, `printed_page`, `printed_code`, `printed_name`, `printed_parent_code`, `disposition`).
- **`PCGECatalog`**: Catálogo en memoria indexado por código, con una interfaz pública de consulta de solo lectura. Ofrece acceso por clave, comprobación de pertenencia, iteración en orden documental, conteo de entradas, consultas jerárquicas (`parent`, `children`, `ancestors`, `descendants`), búsqueda de texto (`search`), metadatos (`metadata`), procedencia (`provenance`), anomalías globales (`anomalies`) y consulta de anomalías por código (`anomalies_for`).
- **`available_versions()`**: Función que retorna una tupla inmutable con las versiones normativas soportadas en el paquete (`("2019", "2026")`).
- **`load_catalog(version)`**: Función de alto nivel que localiza, valida y construye el catálogo para la versión solicitada (`str` obligatorio) a partir de los recursos empaquetados mediante `importlib.resources`.
- **`PCGEDataError`**: Subclase de `ValueError` emitida ante problemas de lectura de recursos empaquetados, formato JSON mal formado, metadatos incompatibles o inconsistencias estructurales del dataset.

### Códigos oficiales de seis dígitos

Tanto el PCGE 2019 como el PCGE 2026 incluyen códigos oficiales de seis dígitos en sus catálogos impresos:
- En **PCGE 2019**: se preservan 20 detalles oficiales de seis dígitos, concentrados en las cuentas 682 y 683, relacionados con la depreciación de activos por derecho de uso.
- En **PCGE 2026**: se incluyen 12 códigos oficiales (`655111` a `655162`), correspondientes a desgloses de *Operación* e *Inversión* subordinados al costo neto de enajenación de activos inmovilizados.

En el modelo de `pcge-peru`:
- Se preservan con su código completo de seis dígitos.
- Su longitud es `code_length == 6`.
- Tienen `pcge_level is None`, dado que la normativa contable oficial no define un sexto nivel jerárquico formal.
- No se introducen niveles artificiales ni se clasifican erróneamente como extensiones empresariales libres.

---

## Datasets y procedencia

La librería distribuye snapshots canónicos e inmutables de los catálogos normativos del Plan Contable General Empresarial emitidos por el Consejo Normativo de Contabilidad (CNC). Cada consumidor es responsable de seleccionar la versión del catálogo contable correspondiente a sus requerimientos operativos o de auditoría.

### PCGE 2019

- **Cantidad de entradas**: 1,757 entradas canónicas.
- **Alcance documental**: Capítulo II (Catálogo de Cuentas), páginas PDF 21 a 62 (numeración impresa 20 a 61).
- **Autoridad normativa**: Consejo Normativo de Contabilidad (CNC).
- **Dispositivo legal**: [Resolución N.° 002-2019-EF/30](https://busquedas.elperuano.pe/dispositivo/NL/1772236-1), emitida el 16 de mayo de 2019 y publicada el 24 de mayo de 2019 en el Diario Oficial El Peruano.
- **Vigencia obligatoria**: A partir del 01 de enero de 2020.
- **Procedencia registrada**: Los metadatos de la fuente original, el hash SHA-256 del documento primario y el hash canónico del dataset se conservan en [`src/pcge/data/2019/source.json`](src/pcge/data/2019/source.json).
- **Anomalías documentadas**: Las inconsistencias editoriales auditadas en la fuente oficial (grupos A a I) y los criterios canónicos aplicados están documentados formalmente en [`src/pcge/data/2019/anomalies.json`](src/pcge/data/2019/anomalies.json).

### PCGE 2026

- **Cantidad de entradas**: 1,636 entradas canónicas.
- **Alcance documental**: Capítulo II (Catálogo de Cuentas), páginas PDF 19 a 52 (numeración impresa 17 a 50).
- **Autoridad normativa**: Consejo Normativo de Contabilidad (CNC).
- **Dispositivo legal**: [Resolución N.° 002-2026-EF/30](https://busquedas.elperuano.pe/dispositivo/NL/2550786-1), publicada el 04 de septiembre de 2026 en el Diario Oficial El Peruano.
- **Vigencia obligatoria**: A partir del 01 de enero de 2028 (con aplicación anticipada permitida).
- **Procedencia registrada**: Los metadatos de la fuente original, el hash SHA-256 del documento primario y el hash canónico del dataset se conservan en [`src/pcge/data/2026/source.json`](src/pcge/data/2026/source.json).
- **Anomalías documentadas**: Las inconsistencias editoriales auditadas en la fuente oficial se conservan en [`src/pcge/data/2026/anomalies.json`](src/pcge/data/2026/anomalies.json).

### Integridad y reproducibilidad de los snapshots

Cada snapshot registra dos hashes SHA-256 con propósitos distintos:

- **`source_sha256`**: fingerprint SHA-256 del documento normativo fuente
  utilizado para preparar y auditar el snapshot. El PDF fuente no se distribuye
  con el paquete, por lo que este valor sirve como referencia de procedencia
  para compararlo con una copia externa del documento.
- **`dataset_sha256`**: SHA-256 de los bytes exactos del `entries.json`
  canónico distribuido. `load_catalog()` recalcula este valor en cada carga y
  comprueba que coincida con el hash registrado, detectando inconsistencias
  byte-a-byte dentro del snapshot empaquetado.

Estos hashes facilitan la trazabilidad, la comprobación de integridad y la
reproducibilidad del dataset. No constituyen por sí solos una firma digital ni
una garantía de autenticidad frente a la sustitución simultánea de los datos y
sus hashes.

#### Tratamiento de la anomalía documental 70992 en PCGE 2026

En el documento oficial impreso se detectó una doble aparición del código `70992`:

1. En la página PDF 48 (impresa 46), aparece impreso `70992 Relacionadas` bajo la divisionaria `7090` (*Mercaderías - Venta de exportación*).
2. En la página PDF 49 (impresa 47), aparece impreso `70992 Contrato de consultoría TI` bajo la divisionaria `7099` (*Otros*).

La fuente utilizada para este snapshot no incluye una corrección oficial de esa duplicidad, por lo que se aplicaron los siguientes criterios documentales estrictos:

- Se retuvo en el catálogo canónico la aparición de la página 49 (`70992 Contrato de consultoría TI`), por ser internamente consistente con su código y el prefijo de su cuenta padre (`7099`).
- Se excluyó del catálogo canónico la primera aparición (`70992 Relacionadas`) y se registró formalmente en [`src/pcge/data/2026/anomalies.json`](src/pcge/data/2026/anomalies.json).
- **No se inventó ni incorporó el código `70902`**: No se realizan correcciones silenciosas ni inferencias de códigos sin respaldo expreso en una norma o fe de erratas oficial.

---

## Desarrollo

Para ejecutar las verificaciones de calidad de código y pruebas del proyecto:

```bash
# Análisis estático de código
ruff check .

# Comprobación de formato
ruff format --check .

# Ejecución de pruebas
pytest

# Construcción de paquetes (wheel y sdist)
python -m build
```

---

## Licencia

El código fuente de este proyecto se distribuye bajo los términos de la **Apache License 2.0**. Consulte el archivo [LICENSE](LICENSE) para más detalles.

El contenido normativo del Plan Contable General Empresarial corresponde a disposiciones de carácter público emitidas por el Estado Peruano a través del Consejo Normativo de Contabilidad y el Ministerio de Economía y Finanzas. La documentación de procedencia se mantiene separada y no atribuye la licencia Apache 2.0 a los textos oficiales del Estado.
