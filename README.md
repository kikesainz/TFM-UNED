<p align="center">
  <img src="assets/sello-uned-logo.jpg" alt="Logotipo de la UNED" width="180" />
</p>

<h1 align="center">Generación semiautomática de bancos de preguntas desde apuntes en Jupyter/MyST</h1>

<p align="center">
  <strong>Trabajo de Fin de Máster</strong><br/>
  Máster Universitario en Ingeniería de las Tecnologías Educativas · UNED
</p>

<p align="center">
  <strong>Autor:</strong> Enrique Sainz-Terrones Peña<br/>
  <strong>Tutor:</strong> José Luis Fernández Vindel
</p>

<p align="center">
  <em>LLMs · Jupyter · MyST · Moodle GIFT · Evaluación · Teacher-in-the-loop</em>
</p>

---

## Descripción general

Este repositorio contiene el prototipo desarrollado como parte del Trabajo de Fin de Máster titulado **“Generación semiautomática de bancos de preguntas desde apuntes en Jupyter/MyST con LLMs y control de calidad”**.

El proyecto aborda un problema habitual en la práctica docente: la creación de bancos de preguntas exige una inversión considerable de tiempo y no puede reducirse únicamente a generar ítems de forma automática. Para que las preguntas puedan incorporarse a un contexto educativo real, deben ser revisables, trazables, estructuralmente correctas e importables en una plataforma de aprendizaje como Moodle.

El prototipo permite marcar fragmentos de materiales docentes mediante semillas `qseed`, generar preguntas con ayuda de un modelo de lenguaje, validar la estructura de los ítems, comprobar que cada pregunta contiene una evidencia literal presente en la fuente y exportar el resultado final en formato **Moodle GIFT**.

El enfoque general es **teacher-in-the-loop**: la IA ayuda a generar propuestas de preguntas, pero el sistema incorpora controles automáticos y mantiene la revisión final en manos del docente.

---

## Índice

- [Descripción general](#descripción-general)
- [Contexto académico](#contexto-académico)
- [Objetivo del prototipo](#objetivo-del-prototipo)
- [Flujo de trabajo](#flujo-de-trabajo)
- [Funcionalidades principales](#funcionalidades-principales)
- [Resultados del caso piloto](#resultados-del-caso-piloto)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración de la API de OpenAI](#configuración-de-la-api-de-openai)
- [Formato de las semillas qseed](#formato-de-las-semillas-qseed)
- [Ejecución](#ejecución)
- [Salidas generadas](#salidas-generadas)
- [Importación en Moodle](#importación-en-moodle)
- [Revisión docente](#revisión-docente)
- [Estructura recomendada del repositorio](#estructura-recomendada-del-repositorio)
- [Buenas prácticas de seguridad](#buenas-prácticas-de-seguridad)
- [Limitaciones](#limitaciones)
- [Líneas de trabajo futuro](#líneas-de-trabajo-futuro)
- [Licencia](#licencia)

---

## Contexto académico

Este trabajo se desarrolla en el marco del **Máster Universitario en Ingeniería de las Tecnologías Educativas de la Universidad Nacional de Educación a Distancia (UNED)**.

- **Autor:** Enrique Sainz-Terrones Peña
- **Tutor:** José Luis Fernández Vindel
- **Institución:** Universidad Nacional de Educación a Distancia (UNED)
- **Ámbito:** inteligencia artificial generativa aplicada a la creación de recursos de evaluación
- **Escenario de uso:** materiales docentes en Jupyter/MyST y exportación de bancos de preguntas a Moodle

---

## Objetivo del prototipo

El objetivo del prototipo es explorar un flujo de trabajo reproducible para generar bancos de preguntas a partir de materiales docentes propios, manteniendo tres principios fundamentales:

1. **Control docente:** el profesor decide qué fragmentos del material son evaluables mediante semillas `qseed`.
2. **Trazabilidad:** cada pregunta debe estar respaldada por una evidencia literal presente en el texto fuente.
3. **Interoperabilidad:** el resultado se exporta en formato Moodle GIFT para poder incorporarse a un banco de preguntas real.

El trabajo no pretende sustituir al docente ni delegar la evaluación completamente en un LLM. La finalidad es construir un sistema de apoyo que genere propuestas revisables, auditables e integrables en un entorno educativo.

---

## Flujo de trabajo

```text
Material docente (.md / .myst.md / .ipynb)
        ↓
Extracción de semillas qseed
        ↓
Construcción del contexto de generación
        ↓
Generación de preguntas con LLM
        ↓
Salida estructurada en JSON
        ↓
Validación estructural
        ↓
Comprobación de evidencia literal
        ↓
Reintento si falla la evidencia
        ↓
Emisión de warnings no bloqueantes
        ↓
Exportación a Moodle GIFT
        ↓
Generación de report.json
```

La aportación principal no está únicamente en generar preguntas, sino en articular un pipeline controlado alrededor del modelo de lenguaje. El LLM actúa como motor de generación, pero el programa se encarga de validar, verificar, registrar y exportar los resultados.

---

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

---

## Resultados del caso piloto

El caso piloto se realizó con materiales docentes sobre DNS en el contexto de 2.º de ASIR. El documento de entrada contenía 30 semillas `qseed`, cada una de ellas orientada a generar preguntas a partir de fragmentos concretos del material.

| Métrica | Resultado |
|---|---:|
| Semillas detectadas | 30 |
| Preguntas exportadas | 60 |
| Preguntas de opción múltiple | 50 |
| Preguntas de verdadero/falso | 10 |
| Semillas con reintento por evidencia | 16 |
| Porcentaje de semillas con reintento | 53,3 % |
| Warnings registrados | 131 |
| Media de warnings por pregunta | 2,18 |

El fichero `banco.gift` generado pudo importarse correctamente en Moodle. Este resultado valida la interoperabilidad técnica del prototipo, aunque la calidad pedagógica final de los ítems sigue requiriendo revisión docente.

---

## Requisitos

Se recomienda utilizar **Python 3.11** o superior.

Dependencias principales:

```bash
pip install openai python-dotenv nbformat pandas matplotlib
```

Si el repositorio incluye un fichero `requirements.txt`, la instalación puede hacerse con:

```bash
pip install -r requirements.txt
```

---

## Instalación

Clona el repositorio:

```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_REPOSITORIO>
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

---

## Configuración de la API de OpenAI

El programa utiliza la API de OpenAI para generar las preguntas. Para ello es necesario configurar una clave de API mediante la variable de entorno `OPENAI_API_KEY`.

### Opción recomendada: fichero `.env`

Crea un fichero llamado `.env` en la raíz del proyecto:

```env
OPENAI_API_KEY=TU_CLAVE_DE_OPENAI
```

El fichero `.env` no debe subirse al repositorio. Debe incluirse en `.gitignore`.

Como plantilla pública puede añadirse un fichero `.env.example`:

```env
OPENAI_API_KEY=TU_CLAVE_DE_OPENAI
```

---

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

---

## Ejecución

La ejecución se realiza desde consola mediante `main.py`.

Ejemplo de ejecución:

```bash
python main.py --input apuntes/apuntes_dns_2asir_con_30_qseeds.ipynb --output outputs/banco.gift --report outputs/banco.report.json --model gpt-4o-mini
```

Parámetros habituales:

- `--input`: ruta del fichero de entrada (`.md`, `.myst.md` o `.ipynb`).
- `--output`: ruta del fichero GIFT generado.
- `--report`: ruta del fichero JSON de instrumentación.
- `--model`: modelo utilizado para la generación, si el programa permite configurarlo.

> Si la versión actual del script utiliza rutas fijas en el código en lugar de argumentos por consola, edita las variables correspondientes en `main.py` antes de ejecutar el programa.

---

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

---

## Importación en Moodle

Para importar el banco generado en Moodle:

1. Accede al curso de Moodle.
2. Entra en el banco de preguntas.
3. Selecciona la opción de importar preguntas.
4. Elige el formato `GIFT`.
5. Sube el fichero `banco.gift`.
6. Ejecuta la importación.
7. Revisa que las preguntas aparecen correctamente en la categoría seleccionada.

La importación en Moodle valida la interoperabilidad técnica del fichero, pero no garantiza por sí sola la calidad pedagógica de las preguntas.

---

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

El sistema ayuda a generar, filtrar y priorizar la revisión de preguntas, pero la decisión final sobre su validez corresponde al docente.

---

## Estructura recomendada del repositorio

```text
.
├── README.md
├── main.py
├── requirements.txt
├── .gitignore
├── .env.example
├── assets/
│   └── sello-uned-logo.jpg
├── apuntes/
│   ├── apuntes_dns_2asir_con_30_qseeds.ipynb
│   └── apuntes_dns_2asir_myst.md
└── outputs/
    ├── banco.gift
    └── banco.report.json
```

---

## Buenas prácticas de seguridad

- No incluyas claves de API en el código fuente.
- No subas el fichero `.env` al repositorio.
- No pegues claves reales en el `README.md`.
- Usa `.env.example` como plantilla pública.
- Revisa `git status` antes de hacer `commit`.
- Si una clave se ha expuesto por error, revócala y crea una nueva.
- Revisa el historial de Git si sospechas que una clave pudo subirse en algún commit anterior.

Ejemplo recomendado de `.gitignore`:

```gitignore
.env
.venv/
venv/
__pycache__/
*.pyc
outputs/*.json
outputs/*.gift
```

> Puedes eliminar las dos últimas líneas si quieres versionar los resultados generados como parte del repositorio.

---

## Limitaciones

La versión actual del prototipo se centra en la generación semiautomática de preguntas de opción múltiple y verdadero/falso a partir de semillas marcadas en materiales docentes.

No incorpora todavía:

- una interfaz integrada en Jupyter mediante plugin, botón o widget;
- una base local incremental de preguntas revisadas;
- detección avanzada de duplicados semánticos entre convocatorias;
- modelización semántica intermedia de conceptos;
- generación de otros tipos de pregunta como emparejamiento, respuesta corta o rellenado de huecos;
- validación psicométrica con datos reales del alumnado.

---

## Líneas de trabajo futuro

Entre las posibles líneas de evolución se encuentran:

- integración operacional en Jupyter mediante botón, widget o extensión;
- creación de una base local incremental de preguntas;
- incorporación de embeddings para detectar similitud semántica y duplicados;
- modelización semántica ligera mediante relaciones sujeto–relación–objeto;
- ampliación a nuevos tipos de preguntas compatibles con Moodle;
- comparación de modelos de lenguaje bajo las mismas semillas y métricas;
- evaluación empírica de los ítems con docentes y alumnado.

---

## Licencia

Apache 2.0.

---

## Aviso

Este repositorio recoge un prototipo académico desarrollado en el marco de un Trabajo de Fin de Máster. Las preguntas generadas deben considerarse borradores revisables y no deben utilizarse en evaluaciones formales sin supervisión docente.
