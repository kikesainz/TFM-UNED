<div align="center">

<img src="assets/sello-uned-logo.jpg" alt="Logotipo de la UNED" width="180"/>

# Generación semiautomática de bancos de preguntas desde apuntes en Jupyter/MyST

## LLMs, control de calidad y exportación a Moodle GIFT

**Trabajo de Fin de Máster**
Máster Universitario en Ingeniería de las Tecnologías Máster**
Máster Universitario en Ingeniería de las Tecnologías Educativas
Universidad Nacional de Educación a Distancia — UNED

**Autor:** Enrique Sainz-Terrones Peña
**Tutor:** José Luis Fernández Vindel

</div>

---

## Descripción general

Este repositorio contiene el prototipo desarrollado como parte del Trabajo de Fin de Máster titulado **“Generación semiautomática de bancos de preguntas desde apuntes en Jupyter/MyST con LLMs y control de calidad”**.

El trabajo parte de un problema habitual en la práctica docente: la creación de bancos de preguntas exige una inversión considerable de tiempo y no puede reducirse únicamente a generar ítems de forma automática. Para que esas preguntas puedan incorporarse a un contexto educativo real, deben ser revisables, trazables, estructuralmente correctas e importables en una plataforma de aprendizaje como Moodle.

El prototipo propone un flujo de trabajo en el que el docente marca fragmentos relevantes de sus materiales mediante semillas `qseed`, el sistema genera preguntas con ayuda de un modelo de lenguaje, valida automáticamente la estructura de los ítems, comprueba que cada pregunta contiene una evidencia literal presente en la fuente y exporta el resultado final en formato Moodle GIFT.

El enfoque general es **teacher-in-the-loop**: la IA ayuda a generar preguntas, el sistema aplica controles automáticos y el docente conserva la responsabilidad final sobre la revisión y aceptación de los ítems.

---

## Memoria del TFM

La memoria completa del Trabajo de Fin de Máster puede consultarse en el siguiente enlace:

[Consultar memoria del TFM](docs/Memoria.TFM-Enrique.Sainz-Terrones.Peña.pdf)

---

## Índice

* [Descripción general](#descripción-general)
* [Memoria del TFM](#memoria-del-tfm)
* [Objetivos del prototipo](#objetivos-del-prototipo)
* [Flujo de funcionamiento](#flujo-de-funcionamiento)
* [Funcionalidades principales](#funcionalidades-principales)
* [Formato de las semillas qseed](#formato-de-las-semillas-qseed)
* [Resultados del caso piloto](#resultados-del-caso-piloto)
* [Requisitos](#requisitos)
* [Instalación](#instalación)
* [Configuración de la API de OpenAI](#configuración-de-la-api-de-openai)
* [Ejecución](#ejecución)
* [Salidas generadas](#salidas-generadas)
* [Importación en Moodle](#importación-en-moodle)
* [Revisión docente](#revisión-docente)
* [Estructura recomendada del repositorio](#estructura-recomendada-del-repositorio)
* [Buenas prácticas de seguridad](#buenas-prácticas-de-seguridad)
* [Limitaciones](#limitaciones)
* [Trabajo futuro](#trabajo-futuro)
* [Licencia](#licencia)

---

## Objetivos del prototipo

El objetivo principal del prototipo es explorar un flujo reproducible para generar bancos de preguntas a partir de materiales docentes en Markdown/MyST o cuadernos Jupyter.

De forma más concreta, el sistema busca:

* permitir que el docente marque fragmentos evaluables dentro de sus propios apuntes;
* generar preguntas de opción múltiple y verdadero/falso mediante un modelo de lenguaje;
* forzar una salida estructurada mediante JSON;
* validar automáticamente requisitos mínimos de los ítems;
* exigir evidencia literal verificable en el texto fuente;
* emitir avisos no bloqueantes para priorizar la revisión docente;
* exportar las preguntas generadas a formato Moodle GIFT;
* producir un informe `report.json` con métricas, trazabilidad y resultados de ejecución.

---

## Flujo de funcionamiento

El flujo general del sistema es el siguiente:

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

La idea central no es simplemente pedir preguntas a un modelo de lenguaje, sino envolver esa generación en un pipeline controlado, trazable y orientado a un uso docente real.

---

## Funcionalidades principales

* Lectura de materiales docentes en formato:

  * Markdown (`.md`);
  * MyST Markdown (`.myst.md`);
  * cuadernos Jupyter (`.ipynb`).
* Extracción automática de semillas de evaluación marcadas como `qseed`.
* Generación de preguntas de:

  * opción múltiple de respuesta única (`mcq`);
  * verdadero/falso (`tf`).
* Generación con salida estructurada en JSON.
* Validación automática de requisitos mínimos de estructura.
* Comprobación de evidencia literal contra el texto fuente.
* Reintento automático cuando falla la evidencia literal.
* Emisión de avisos no bloqueantes (`warnings`) para priorizar la revisión docente.
* Exportación del banco de preguntas a formato Moodle GIFT.
* Generación de un fichero `report.json` con métricas, trazabilidad y resultados de ejecución.

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

* `id`: identificador único de la semilla.
* `type`: tipo de pregunta a generar (`mcq` o `tf`).
* `n`: número de preguntas que se desean generar a partir de la semilla.
* `difficulty`: dificultad prevista (`baja`, `media`, `alta`).
* `objective`: objetivo didáctico de la pregunta.
* Texto tras `---`: fragmento fuente del que deben derivarse las preguntas.

---

## Resultados del caso piloto

El prototipo se probó sobre un conjunto de apuntes de DNS preparados en formato Jupyter/MyST.

En la ejecución piloto:

* se detectaron correctamente **30 semillas qseed**;
* se generaron y exportaron **60 preguntas**;
* **50 preguntas** fueron de opción múltiple;
* **10 preguntas** fueron de verdadero/falso;
* **16 de las 30 semillas** requirieron al menos un reintento por evidencia literal;
* se registraron **131 warnings** no bloqueantes;
* el banco generado pudo exportarse en formato Moodle GIFT;
* el fichero `banco.gift` se importó correctamente en Moodle.

Estos resultados muestran la viabilidad técnica del enfoque, pero también refuerzan la necesidad de mantener controles automáticos y revisión docente antes de utilizar las preguntas en una evaluación formal.

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

---

## Configuración de la API de OpenAI

El programa utiliza la API de OpenAI para generar las preguntas. Para ello es necesario configurar una clave de API mediante la variable de entorno `OPENAI_API_KEY`.

### Opción recomendada: fichero `.env`

Crea un fichero llamado `.env` en la raíz del proyecto:

```env
OPENAI_API_KEY=pon_aqui_tu_clave
```

También puede incluirse un fichero `.env.example` como plantilla pública:

```env
OPENAI_API_KEY=tu_clave_aqui
```

El fichero `.env` real no debe subirse al repositorio.

---

## Ejecución

La ejecución se realiza desde consola mediante `main.py`.

Ejemplo:

```bash
python main.py --input apuntes/apuntes_dns_2asir_con_30_qseeds.ipynb --output outputs/banco.gift --report outputs/banco.report.json --model gpt-4o-mini
```

Parámetros habituales:

* `--input`: ruta del fichero de entrada (`.md`, `.myst.md` o `.ipynb`);
* `--output`: ruta del fichero GIFT generado;
* `--report`: ruta del fichero JSON de instrumentación;
* `--model`: modelo utilizado para la generación.

Si la versión actual del script utiliza rutas fijas en el código en lugar de argumentos por consola, edita las variables correspondientes en `main.py` antes de ejecutar el programa.

---

## Salidas generadas

Tras la ejecución, el programa genera principalmente dos artefactos.

### `banco.gift`

Fichero en formato Moodle GIFT con las preguntas generadas. Puede importarse en Moodle desde el banco de preguntas.

### `banco.report.json`

Fichero de trazabilidad e instrumentación que registra información sobre la ejecución, por ejemplo:

* número de semillas detectadas;
* número de preguntas exportadas;
* modelo utilizado;
* umbrales aplicados;
* warnings emitidos;
* métricas de similitud;
* incidencias o rechazos;
* información útil para análisis posterior.

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

* claridad del enunciado;
* unicidad de la respuesta correcta;
* plausibilidad de los distractores;
* adecuación al nivel del alumnado;
* coherencia con el material fuente;
* ausencia de ambigüedades;
* adecuación de la retroalimentación;
* avisos (`warnings`) registrados en `report.json`.

El sistema ayuda a generar y filtrar preguntas, pero la decisión final sobre su validez corresponde al docente.

---

## Estructura recomendada del repositorio

```text
.
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── assets/
│   └── sello-uned-logo.jpg
├── docs/
│   └── memoria-tfm-enrique-sainz-terrones.pdf
├── apuntes/
│   ├── apuntes_dns_2asir_con_30_qseeds.ipynb
│   └── apuntes_dns_2asir_myst.md
└── outputs/
    ├── banco.gift
    └── banco.report.json
```

---

## Buenas prácticas de seguridad

* No incluyas claves de API en el código fuente.
* No subas el fichero `.env` al repositorio.
* No pegues claves reales en el `README.md`.
* Usa `.env.example` como plantilla pública.
* Revisa `git status` antes de hacer `commit`.
* Si una clave se ha expuesto por error, revócala y crea una nueva.
* Revisa el historial de Git si sospechas que una clave pudo subirse en algún commit anterior.

Ejemplo recomendado de `.gitignore`:

```gitignore
.env
.venv/
venv/
__pycache__/
*.pyc
.ipynb_checkpoints/
```

---

## Limitaciones

La versión actual del prototipo se centra en la generación semiautomática de preguntas de opción múltiple y verdadero/falso a partir de semillas marcadas en materiales docentes.

No incorpora todavía:

* una interfaz integrada en Jupyter mediante plugin, botón o widget;
* una base local incremental de preguntas revisadas;
* detección avanzada de duplicados semánticos entre convocatorias;
* modelización semántica intermedia de conceptos;
* generación de otros tipos de pregunta como emparejamiento, respuesta corta o rellenado de huecos;
* validación psicométrica con datos reales del alumnado.

Estas limitaciones no invalidan el prototipo, sino que delimitan su alcance como prueba funcional de un pipeline controlado, trazable e interoperable.

---

## Trabajo futuro

Entre las principales líneas de trabajo futuro se plantean:

* incorporar una base local incremental de preguntas;
* registrar versiones revisadas y estados de aceptación o descarte;
* detectar duplicados semánticos mediante embeddings;
* enriquecer las semillas `qseed` con relaciones semánticas ligeras de tipo sujeto-relación-objeto;
* ampliar los tipos de preguntas generables;
* mejorar la instrumentación de los reintentos mediante un campo `attempts[]`;
* integrar el sistema directamente en Jupyter mediante un botón, widget o extensión;
* añadir exportación a otros formatos, como Moodle XML o QTI;
* realizar una evaluación empírica con docentes y alumnado.

---

## Licencia

Apache 2.0.

---

## Autoría y contexto académico

Este repositorio forma parte del Trabajo de Fin de Máster de **Enrique Sainz-Terrones Peña**, desarrollado en el marco del **Máster Universitario en Ingeniería de las Tecnologías Educativas** de la **Universidad Nacional de Educación a Distancia — UNED**.

El trabajo ha sido tutorizado por **José Luis Fernández Vindel**.

El prototipo se ofrece con finalidad académica, experimental y docente.
