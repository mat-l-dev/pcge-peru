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

Si propones cambios o adiciones en la información del catálogo contable, debes cumplir estrictamente los siguientes requisitos:

- **Evidencia oficial obligatoria**: No corrijas, infieras ni completes datos contables sin una fuente normativa oficial verificable.
- **Registro de procedencia**: Es obligatorio registrar o actualizar `src/pcge/data/<versión>/source.json` indicando título, autoridad normativa, resolución oficial, fecha, SHA-256 y páginas correspondientes.
- **Documentación de anomalías**: Si el documento fuente presenta erratas, duplicidades o inconsistencias, no las corrijas silenciosamente; documéntalas de forma estructurada en `src/pcge/data/<versión>/anomalies.json` detallando apariciones, disposición y estado.
- **Consistencia y metadatos**: Actualiza `metadata.json` (incluyendo `entry_count` exacto) y comprueba que las entradas respeten los esquemas de `schemas/` y la jerarquía canónica de prefijos.
- **Pruebas automatizadas**: Añade o actualiza pruebas en `tests/` para verificar la carga e integridad del dataset modificado.

## Pull requests

Los pull requests deben cumplir los siguientes criterios:

- Tener un objetivo claro.
- Incluir pruebas cuando corresponda.
- Mantener el estilo del proyecto.
- No incluir cambios no relacionados.