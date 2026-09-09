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
```

Todos los comandos deben finalizar correctamente.

## Cambios en los datos del PCGE

Si modificas información contable, debes cumplir los siguientes requisitos:

- Indica la fuente oficial.
- Incluye la página, sección o referencia correspondiente cuando sea posible.
- Explica el motivo del cambio.
- No agregues información sin una fuente verificable.

## Pull requests

Los pull requests deben cumplir los siguientes criterios:

- Tener un objetivo claro.
- Incluir pruebas cuando corresponda.
- Mantener el estilo del proyecto.
- No incluir cambios no relacionados.