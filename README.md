# Generación semiautomática de bancos de preguntas desde apuntes en Jupyter/MyST

Este repositorio contiene el prototipo desarrollado como parte del Trabajo de Fin de Máster del Máster Universitario en Ingeniería de las Tecnologías Educativas de la UNED. El TFM se titula **“Generación semiautomática de bancos de preguntas desde apuntes en Jupyter/MyST con LLMs y control de calidad”** y tiene como objetivo explorar un flujo de trabajo para generar bancos de preguntas a partir de materiales docentes en Markdown/MyST o cuadernos Jupyter (`.ipynb`).

Este repositorio contiene un prototipo en Python para generar de forma semiautomática un banco de preguntas a partir de materiales docentes escritos en Markdown/MyST o en cuadernos Jupyter (`.ipynb`).

El sistema permite marcar fragmentos del material mediante semillas `qseed`, generar preguntas con ayuda de un modelo de lenguaje, validar la estructura de los ítems, comprobar que cada pregunta contiene una evidencia literal presente en la fuente y exportar el resultado final en formato Moodle GIFT.

## Índice

- [Descripción general](#descripción-general)
- [Funcionalidades principales](#funcionalidades-principales)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración de la API de OpenAI](#configuración-de-la-api-de-openai)
- [Formato de las semillas qseed](#formato-de-las-semillas-qseed)
- [Ejecución](#ejecución)
- [Salidas generadas](#salidas-generadas)
- [Importación en Moodle](#importación-en-moodle)
- [Estructura recomendada del repositorio](#estructura-recomendada-del-repositorio)
- [Buenas prácticas de seguridad](#buenas-prácticas-de-seguridad)
- [Limitaciones](#limitaciones)
- [Licencia](#licencia)

## Descripción general

El objetivo del prototipo es apoyar al docente en la creación de bancos de preguntas reutilizables a partir de materiales propios. El flujo general es el siguiente:

```text
Material docente (.md / .myst.md / .ipynb)
        ↓
Extracción de semillas qseed
        ↓
Construcción del contexto de generación
        ↓
Generación de preguntas con LLM
        ↓
Validación estructural
        ↓
Comprobación de evidencia literal
        ↓
Emisión de warnings no bloqueantes
        ↓
Exportación a Moodle GIFT
        ↓
Generación de report.json
```

El enfoque es `teacher-in-the-loop`: el sistema automatiza parte del proceso de creación de ítems, pero el docente conserva la revisión final antes de utilizar las preguntas en una evaluación real.

## Funcionalidades principales

- Lectura de materiales docentes en formato:
  - Markdown (`.md`);
  - MyST Markdown (`.myst.md`);
  - cuadernos Jupyter (`.ipynb`).
- Extracción automática de semillas de evaluación marcadas como `qseed`.
- Generación de preguntas de:
  - opción múltiple de respuesta única (`mcq`);
  - verdadero/falso (`tf`).
- Generación con salida estructurada en JSON.
- Validación automática de requisitos mínimos de estructura.
- Comprobación de evidencia literal contra el texto fuente.
- Reintento automático cuando falla la evidencia literal.
- Emisión de avisos no bloqueantes (`warnings`) para priorizar revisión docente.
- Exportación del banco de preguntas a formato Moodle GIFT.
- Generación de un fichero `report.json` con métricas, trazabilidad y resultados de ejecución.

## Requisitos

Se recomienda utilizar Python 3.11 o superior.

Dependencias principales:

```bash
pip install openai python-dotenv nbformat pandas matplotlib
```

Si el repositorio incluye un fichero `requirements.txt`, la instalación puede hacerse con:

```bash
pip install -r requirements.txt
```

## Instalación

Clona el repositorio:

```bash
git clone https://github.com/usuario/nombre-del-repositorio.git
cd nombre-del-repositorio
```

Crea un entorno virtual:

```bash
python -m venv .venv
```

Activa el entorno virtual.

En Windows:

```bash
.venv\Scripts\activate
```

En Linux/macOS:

```bash
source .venv/bin/activate
```

Instala las dependencias:

```bash
pip install -r requirements.txt
```

Si no existe `requirements.txt`, instala manualmente las dependencias principales:

```bash
pip install openai python-dotenv nbformat pandas matplotlib
```

## Configuración de la API de OpenAI

El programa utiliza la API de OpenAI para generar las preguntas. Para ello es necesario configurar una clave de API mediante la variable de entorno `OPENAI_API_KEY`.

### Opción recomendada: fichero `.env`

Crea un fichero llamado `.env` en la raíz del proyecto:

```env
OPENAI_API_KEY=pon_aquí_tu_clave_sk-XXX
```

Ejemplo:

```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```


```


## Formato de las semillas qseed

El sistema detecta bloques marcados como `qseed`. Cada semilla incluye metadatos y un texto fuente que servirá de base para generar las preguntas.

Ejemplo de semilla en Markdown:

````markdown
```qseed
id: dns-a-record
type: mcq
n: 2
difficulty: media
objective: Comprender la función del registro A en DNS
---
El registro A asocia un nombre de dominio con una dirección IPv4. Se utiliza para resolver nombres como www.ejemplo.com a direcciones IP que puedan ser usadas por los clientes.
```
````

Campos principales:

- `id`: identificador único de la semilla.
- `type`: tipo de pregunta a generar (`mcq` o `tf`).
- `n`: número de preguntas que se desean generar a partir de la semilla.
- `difficulty`: dificultad prevista (`baja`, `media`, `alta`).
- `objective`: objetivo didáctico de la pregunta.
- Texto tras `---`: fragmento fuente del que deben derivarse las preguntas.

## Ejecución

La ejecución se realiza desde consola mediante `main.py`.


Ejemplo indicando modelo:

```bash
python main.py --input apuntes/apuntes_dns_2asir_con_30_qseeds.ipynb  outputs/banco.gift  gpt-4o-mini
```

Parámetros habituales:

- `--input`: ruta del fichero de entrada (`.md`, `.myst.md` o `.ipynb`).
- `--output`: ruta del fichero GIFT generado.
- `--report`: ruta del fichero JSON de instrumentación.
- `--model`: modelo utilizado para la generación, si el programa permite configurarlo.

> Si la versión actual del script utiliza rutas fijas en el código en lugar de argumentos por consola, edita las variables correspondientes en `main.py` antes de ejecutar el programa.

## Salidas generadas

Tras la ejecución, el programa genera principalmente dos artefactos.

### `banco.gift`

Fichero en formato Moodle GIFT con las preguntas generadas. Puede importarse en Moodle desde el banco de preguntas.

### `banco.report.json`

Fichero de trazabilidad e instrumentación que registra información sobre la ejecución, por ejemplo:

- número de semillas detectadas;
- número de preguntas exportadas;
- modelo utilizado;
- umbrales aplicados;
- warnings emitidos;
- métricas de similitud;
- incidencias o rechazos;
- información útil para análisis posterior.

## Importación en Moodle

Para importar el banco generado en Moodle:

1. Accede al curso de Moodle.
2. Entra en el banco de preguntas.
3. Selecciona la opción de importar preguntas.
4. Elige el formato `GIFT`.
5. Sube el fichero `banco.gift`.
6. Ejecuta la importación.
7. Revisa que las preguntas aparecen correctamente en la categoría seleccionada.

## Revisión docente

Las preguntas generadas no deben utilizarse directamente en una evaluación formal sin revisión humana.

Antes de usar el banco, se recomienda revisar:

- claridad del enunciado;
- unicidad de la respuesta correcta;
- plausibilidad de los distractores;
- adecuación al nivel del alumnado;
- coherencia con el material fuente;
- ausencia de ambigüedades;
- adecuación de la retroalimentación;
- avisos (`warnings`) registrados en `report.json`.

El sistema ayuda a generar y filtrar preguntas, pero la decisión final sobre su validez corresponde al docente.

## Estructura recomendada del repositorio

```text
.
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── apuntes/
│   ├── apuntes_dns_2asir_con_30_qseeds.ipynb
│   └── apuntes_dns_2asir_myst.md
├── outputs/
│   ├── banco.gift
│   └── banco.report.json

```



## Buenas prácticas de seguridad

- No incluyas claves de API en el código fuente.
- No subas el fichero `.env` al repositorio.
- No pegues claves reales en el `README.md`.
- Usa `.env.example` como plantilla pública.
- Revisa `git status` antes de hacer `commit`.
- Si una clave se ha expuesto por error, revócala y crea una nueva.
- Revisa el historial de Git si sospechas que una clave pudo subirse en algún commit anterior.

## Limitaciones

La versión actual del prototipo se centra en la generación semiautomática de preguntas de opción múltiple y verdadero/falso a partir de semillas marcadas en materiales docentes.

No incorpora todavía:

- una interfaz integrada en Jupyter mediante plugin, botón o widget;
- una base local incremental de preguntas revisadas;
- detección avanzada de duplicados semánticos entre convocatorias;
- modelización semántica intermedia de conceptos;
- generación de otros tipos de pregunta como matching, respuesta corta o rellenado de huecos;
- validación psicométrica con datos reales del alumnado.

Estas funcionalidades se consideran posibles líneas de trabajo futuro.

## Licencia

Indicar aquí la licencia del proyecto, por ejemplo MIT, Apache 2.0 o la que se considere adecuada.
