# pcge-peru

Librería open source en Python para representar, consultar y validar el catálogo oficial del Plan Contable General Empresarial (PCGE) del Perú.

El propósito de `pcge-peru` es brindar una representación tipada y programáticamente accesible de las entradas del catálogo contable peruano, facilitando su navegación jerárquica y búsqueda en proyectos de software.

> **Alcance del proyecto**:
> - `pcge-peru` **no es un ERP**.
> - No implementa asientos contables, libro diario, mayor, cálculo de impuestos ni facturación electrónica.
> - La versión actual se enfoca exclusivamente en el catálogo de cuentas del **Capítulo II** del PCGE 2026.
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

La función principal para comenzar es `load_catalog`, que carga el catálogo oficial empaquetado como un objeto `PCGECatalog` con una interfaz pública de consulta de solo lectura:

```python
from pcge import load_catalog

# Carga la versión por defecto ("2026")
catalog = load_catalog()

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
```

### Reglas clave de uso

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
- **`PCGECatalog`**: Catálogo en memoria indexado por código, con una interfaz pública de consulta de solo lectura. Ofrece acceso por clave, comprobación de pertenencia, iteración en orden documental, conteo de entradas, consultas jerárquicas (`parent`, `children`, `ancestors`, `descendants`) y búsqueda de texto (`search`).
- **`load_catalog(version="2026")`**: Función de alto nivel que localiza, valida y construye el catálogo a partir de los recursos empaquetados mediante `importlib.resources`.
- **`PCGEDataError`**: Subclase de `ValueError` emitida ante problemas de lectura de recursos empaquetados, formato JSON mal formado, metadatos incompatibles o inconsistencias estructurales del dataset.

### Códigos oficiales de seis dígitos

El PCGE 2026 incluye doce códigos oficiales de seis dígitos (`655111` a `655162`). Son desgloses de *Operación* e *Inversión* subordinados a los códigos `65511` a `65516`, dentro del costo neto de enajenación de activos inmovilizados.

En el modelo de `pcge-peru`:
- Se preservan con su código completo de seis dígitos.
- Su longitud es `code_length == 6`.
- Tienen `pcge_level is None`, dado que la normativa contable oficial no define un sexto nivel jerárquico formal.
- No se introducen niveles artificiales ni se clasifican erróneamente como extensiones empresariales libres.

---

## Dataset y procedencia

El catálogo integrado corresponde a la actualización oficial del Plan Contable General Empresarial publicada en 2026:

- **Cantidad de entradas**: 1,636 entradas canónicas.
- **Alcance documental**: Capítulo II (Catálogo de Cuentas), páginas PDF 19 a 52 (numeración impresa 17 a 50).
- **Autoridad normativa**: Consejo Normativo de Contabilidad (CNC).
- **Dispositivo legal**: [Resolución N.° 002-2026-EF/30](https://busquedas.elperuano.pe/dispositivo/NL/2550786-1), publicada el 04 de septiembre de 2026 en el Diario Oficial El Peruano.
- **Vigencia obligatoria**: A partir del 01 de enero de 2028 (con aplicación anticipada permitida).
- **Procedencia registrada**: Los metadatos de la fuente original y el hash SHA-256 del documento primario se conservan en [`sources/2026/source.json`](sources/2026/source.json).

### Tratamiento de la anomalía documental 70992

En el documento oficial impreso se detectó una doble aparición del código `70992`:

1. En la página PDF 48 (impresa 46), aparece impreso `70992 Relacionadas` bajo la divisionaria `7090` (*Mercaderías - Venta de exportación*).
2. En la página PDF 49 (impresa 47), aparece impreso `70992 Contrato de consultoría TI` bajo la divisionaria `7099` (*Otros*).

La fuente utilizada para este snapshot no incluye una corrección oficial de esa duplicidad, por lo que se aplicaron los siguientes criterios documentales estrictos:

- Se retuvo en el catálogo canónico la aparición de la página 49 (`70992 Contrato de consultoría TI`), por ser internamente consistente con su código y el prefijo de su cuenta padre (`7099`).
- Se excluyó del catálogo canónico la primera aparición (`70992 Relacionadas`) y se registró formalmente en [`sources/2026/anomalies.json`](sources/2026/anomalies.json).
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
