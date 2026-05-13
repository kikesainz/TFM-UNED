# main.py
# Uso:
#   python main.py <entrada.md|entrada.ipynb> <salida.gift> <modelo>
#
# Ejemplo (PowerShell):
#   python main.py "C:\Users\kikes\OneDrive - Educacyl\Varios\Pruebas\Untitled.ipynb" banco.gift gpt-4o-mini

from __future__ import annotations

import os
import re
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone


import nbformat
from openai import OpenAI, RateLimitError, APIError, APITimeoutError
from dotenv import load_dotenv
load_dotenv()


# ============================================================
# Configuración (umbrales y parámetros)
# ============================================================

# --- Warnings heurísticos (domain-agnostic) ---
JACCARD_DISTRACTOR_CORRECT_MAX = 0.75   # distractor demasiado parecido a la correcta
JACCARD_DISTRACTOR_STEM_MIN = 0.10      # distractor poco relacionado con el enunciado
CHOICE_LENGTH_RATIO_MAX = 2.5           # max(len)/min(len) permitido
RATIONALE_MIN_CHARS = 12                # rationale demasiado corta (warning)
DISTRACTOR_RATIONALES_EXPECTED = 3      # nº de rationales esperadas (MCQ)

# --- Evidence retry ---
EVIDENCE_RETRY_MAX_ATTEMPTS = 3
EVIDENCE_CANDIDATES_MAX_ITEMS = 6
EVIDENCE_CANDIDATE_MIN_CHARS = 10
EVIDENCE_FALLBACK_SOURCE_MAX_CHARS = 500

# --- LLM retry/backoff (429/timeouts/5xx) ---
LLM_RETRY_ATTEMPTS = 4
LLM_RETRY_BASE_WAIT_SEC = 2.0


# Palabras frecuentes en español (stopwords) para tokenización simple
STOP = {
    "el", "la", "los", "las", "un", "una", "de", "del", "y", "o", "a", "en", "por", "para",
    "que", "es", "son", "se"
}

# Separador de meta/cuerpo en qseed (acepta --- y variantes Unicode)
DASH_LINE_RE = re.compile(r"^[\s\-–—]{3,}$")


# ============================================================
# Modelos de datos
# ============================================================

@dataclass
class QSeed:
    sid: str
    qtype: str          # "mcq" | "tf"
    n: int
    difficulty: str     # "baja" | "media" | "alta"
    objective: str
    body: str           # texto semilla (FUENTE)


# ============================================================
# Utilidades
# ============================================================

def normalize_text(s: str) -> str:
    return " ".join((s or "").lower().split())


def tokens(text: str) -> set[str]:
    """
    Tokenización simple para similitud Jaccard:
    - regex \\w+
    - minúsculas
    - quitar stopwords
    - quitar tokens muy cortos (<=2)
    """
    ws = re.findall(r"\w+", (text or "").lower())
    return {w for w in ws if w not in STOP and len(w) > 2}


def jaccard(a: set[str], b: set[str]) -> float:
    """Similitud Jaccard: |A∩B| / |A∪B|"""
    return len(a & b) / max(1, len(a | b))


# ============================================================
# Entrada: lectura de .md o .ipynb
# ============================================================

def load_text_from_file(path: str, read_all_cells: bool = False) -> str:
    """
    Carga texto desde:
    - .md -> contenido completo
    - .ipynb -> concatenación de celdas markdown/raw (por defecto)
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No existe el archivo: {p}")

    if p.suffix.lower() == ".ipynb":
        nb = nbformat.read(p, as_version=4)
        parts: List[str] = []
        for cell in nb.cells:
            if read_all_cells or cell.cell_type in ("markdown", "raw"):
                parts.append(cell.source)
        return "\n\n".join(parts)

    return p.read_text(encoding="utf-8")


# ============================================================
# Extracción de bloques qseed (robusta, por líneas)
# ============================================================

def parse_meta(meta_text: str) -> Dict[str, str]:
    """
    Meta en formato:
      id: ...
      type: mcq|tf
      n: 2
      difficulty: media
      objective: ...
    """
    meta: Dict[str, str] = {}
    for line in meta_text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        k, v = line.split(":", 1)
        meta[k.strip().lower()] = v.strip().strip('"').strip("'")
    return meta


def extract_qseeds(text: str) -> List[QSeed]:
    """
    Busca bloques:
    ```qseed
    id: ...
    type: ...
    n: ...
    difficulty: ...
    objective: ...
    ---
    texto semilla...
    ```
    """
    seeds: List[QSeed] = []
    lines = text.replace("\r\n", "\n").split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip().lower()

        if line.startswith("```qseed"):
            i += 1
            meta_lines: List[str] = []
            body_lines: List[str] = []
            in_body = False

            while i < len(lines):
                cur_raw = lines[i]
                cur = cur_raw.strip()

                if cur.startswith("```"):  # cierre del bloque
                    break

                if not in_body and (cur == "---" or cur == "..." or DASH_LINE_RE.match(cur)):
                    in_body = True
                else:
                    (body_lines if in_body else meta_lines).append(cur_raw)

                i += 1

            meta_text = "\n".join(meta_lines).strip()
            body_text = "\n".join(body_lines).strip()

            if not meta_text or not body_text:
                raise ValueError("Bloque qseed incompleto: faltan metadatos o cuerpo")

            meta = parse_meta(meta_text)
            sid = meta.get("id")
            if not sid:
                raise ValueError("Bloque qseed sin 'id:'")

            qtype = meta.get("type", "mcq").lower()
            if qtype not in ("mcq", "tf"):
                raise ValueError(f"Tipo no soportado en {sid}: {qtype}")

            n = int(meta.get("n", "1"))

            difficulty = meta.get("difficulty", "media").lower()
            if difficulty not in ("baja", "media", "alta"):
                difficulty = "media"

            objective = meta.get("objective", "")

            seeds.append(QSeed(
                sid=sid,
                qtype=qtype,
                n=n,
                difficulty=difficulty,
                objective=objective,
                body=body_text
            ))

        i += 1

    return seeds


# ============================================================
# JSON Schema (Structured Outputs strict)
# ============================================================

def question_schema() -> dict:
    """
    Schema compatible con strict=True:
    - additionalProperties=False
    - required incluye TODAS las claves de properties (en cada object)
    - sin oneOf/anyOf (no permitido)
    """
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"type": "string", "enum": ["mcq", "tf"]},
                        "stem": {"type": "string", "minLength": 10},
                        "difficulty": {"type": "string", "enum": ["baja", "media", "alta"]},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "explanation": {"type": "string", "minLength": 10},
                        "evidence": {"type": "string", "minLength": 10},

                        "answer_type": {
                            "type": "string",
                            "enum": [
                                "definicion", "funcion", "proceso_paso", "comparacion",
                                "causa_efecto", "ejemplo", "clasificacion", "valor_unidad", "otro"
                            ]
                        },

                        # Siempre presentes (neutros si no aplican)
                        "choices": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 0,
                            "maxItems": 4
                        },
                        "correct_index": {"type": "integer", "minimum": 0, "maximum": 3},
                        "answer": {"type": "boolean"},

                        "distractor_rationales": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 0,
                            "maxItems": 3
                        }
                    },
                    "required": [
                        "id", "type", "stem", "difficulty", "tags",
                        "explanation", "evidence", "answer_type",
                        "choices", "correct_index", "answer",
                        "distractor_rationales"
                    ]
                }
            }
        },
        "required": ["questions"]
    }


# ============================================================
# Llamadas a IA (con prompt mejorado + retries)
# ============================================================

def build_context(seed: QSeed) -> str:
    return (
        f"OBJETIVO: {seed.objective}\n"
        f"DIFICULTAD: {seed.difficulty}\n"
        f"TIPO: {seed.qtype}\n\n"
        f"FUENTE (texto base):\n{seed.body}\n"
    )


def build_prompt(seed: QSeed, extra_rules: str = "") -> str:
    """
    Prompt generalista y consistente con schema strict.
    Incluye reglas de:
    - fidelidad a la fuente + evidencia literal
    - neutral fields por tipo (mcq/tf)
    - distractores near-miss (sin depender del tema)
    - variedad cuando n>1
    """
    return f"""
Genera EXACTAMENTE {seed.n} preguntas a partir de la FUENTE.

SALIDA
- Devuelve SOLO JSON válido conforme al esquema (sin texto extra).
- No añadas claves distintas de las del esquema.
- Incluye SIEMPRE estos campos:
  id, type, stem, difficulty, tags, explanation, evidence, answer_type,
  choices, correct_index, answer, distractor_rationales.

FIDELIDAD A LA FUENTE
- Usa SOLO información presente en la FUENTE.
- 'evidence' debe ser una cita LITERAL copiada de la FUENTE (frase o fragmento exacto).
- No inventes datos, definiciones ni ejemplos que no estén en la FUENTE.

PARAMETROS DE LA SEMILLA
- El campo "difficulty" debe ser exactamente "{seed.difficulty}".
- El campo "type" debe ser "{seed.qtype}" en todas las preguntas.

VARIEDAD (IMPORTANTE si n>1)
- Las preguntas deben ser realmente diferentes (no paráfrasis).
- Si es posible, usa 'answer_type' diferente en cada pregunta.

answer_type (elige una)
definicion | funcion | proceso_paso | comparacion | causa_efecto | ejemplo | clasificacion | valor_unidad | otro

TAGS
- tags: 1–3 palabras clave cortas presentes en la FUENTE (sin stopwords). Si no procede, usa [].

REGLAS POR TIPO
1) Si type="mcq":
- choices: EXACTAMENTE 4 opciones (strings), longitudes similares.
- correct_index: 0..3 indicando la correcta.
- answer: false (neutro).
- distractor_rationales: EXACTAMENTE 3 textos (uno por distractor, en el mismo orden que aparecen).
- Distractores: deben ser "near-miss" (plausibles), incorrectos por un detalle.
  Para construirlos, modifica SOLO UN detalle de la idea correcta/evidence
  (atributo, relación, orden, unidad, cuantificador, etc.).
- Evita opciones absurdas y evita "Todas/Ninguna de las anteriores".

2) Si type="tf":
- answer: true/false.
- choices: [] (neutro), correct_index: 0 (neutro), distractor_rationales: [] (neutro).

IDs
- Usa IDs: "{seed.sid}-q1", "{seed.sid}-q2", etc.

{extra_rules}
""".strip()


def call_llm_generate(client: OpenAI, seed: QSeed, model: str, extra_rules: str = "") -> Dict[str, Any]:
    schema = question_schema()
    prompt = build_prompt(seed, extra_rules=extra_rules)

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": "Eres un generador de preguntas para Moodle. Responde con JSON estricto."},
            {"role": "user", "content": build_context(seed)},
            {"role": "user", "content": prompt},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "question_bank",
                "strict": True,
                "schema": schema
            }
        }
    )
    return json.loads(resp.output_text)


def call_llm_generate_with_retry(
    client: OpenAI,
    seed: QSeed,
    model: str,
    extra_rules: str = "",
    attempts: int = LLM_RETRY_ATTEMPTS,
    base_wait: float = LLM_RETRY_BASE_WAIT_SEC
) -> Dict[str, Any]:
    """
    Reintenta la llamada a la IA ante errores temporales (429, timeouts, 5xx).
    Nota: 'insufficient_quota' no se soluciona reintentando; se relanza.
    """
    last_err: Optional[Exception] = None

    for attempt in range(1, attempts + 1):
        try:
            return call_llm_generate(client, seed, model=model, extra_rules=extra_rules)

        except (RateLimitError, APITimeoutError, APIError) as e:
            # Si es falta de cuota, reintentar no ayuda
            if "insufficient_quota" in str(e).lower():
                raise

            last_err = e
            wait = base_wait * (2 ** (attempt - 1))
            print(f"[RETRY] {seed.sid}: intento {attempt}/{attempts} ({type(e).__name__}). Esperando {wait:.1f}s...")
            time.sleep(wait)

    raise last_err if last_err else RuntimeError("Error desconocido en call_llm_generate_with_retry")


# ============================================================
# Validación hard + warnings
# ============================================================

def validate_question(q: dict, source_text: str) -> List[str]:
    errors: List[str] = []
    qtype = q.get("type")

    # Evidence: obligatorio y literal en fuente
    evidence = (q.get("evidence") or "").strip()
    if not evidence:
        errors.append("Falta evidence")
    elif normalize_text(evidence) not in normalize_text(source_text):
        errors.append("Evidence no aparece literalmente en la fuente")

    # Stem/explanation mínimos
    stem = (q.get("stem") or "").strip()
    expl = (q.get("explanation") or "").strip()
    if len(stem) < 10:
        errors.append("stem demasiado corto")
    if len(expl) < 10:
        errors.append("explanation demasiado corta")

    # Validación por tipo
    if qtype == "mcq":
        choices = q.get("choices", [])
        ci = q.get("correct_index", None)
        rats = q.get("distractor_rationales", [])

        if not isinstance(choices, list) or len(choices) != 4:
            errors.append("MCQ debe tener 4 opciones")
        if not isinstance(ci, int) or not (0 <= ci <= 3):
            errors.append("correct_index inválido")
        if isinstance(choices, list):
            norm = [normalize_text(c) for c in choices]
            if len(set(norm)) != len(norm):
                errors.append("opciones duplicadas")

        # No bloqueante en hard (puede ser warning), pero si quieres hacerlo hard, muévelo
        if not isinstance(rats, list) or len(rats) != DISTRACTOR_RATIONALES_EXPECTED:
            # lo dejamos en warning, no en error
            pass

    elif qtype == "tf":
        ans = q.get("answer", None)
        if not isinstance(ans, bool):
            errors.append("TF debe tener answer boolean")
    else:
        errors.append("type inválido (mcq o tf)")

    return errors


def distractor_warnings(q: dict) -> List[str]:
    warns: List[str] = []

    if q.get("type") != "mcq":
        return warns

    choices = q.get("choices", [])
    ci = q.get("correct_index", None)

    if not isinstance(choices, list) or len(choices) != 4 or not isinstance(ci, int) or not (0 <= ci <= 3):
        return warns  # la validación hard ya se encargará

    stem_t = tokens(q.get("stem", ""))
    correct_t = tokens(choices[ci])
    distractors = [c for i, c in enumerate(choices) if i != ci]

    # 1) Rationales
    rats = q.get("distractor_rationales", [])
    if not isinstance(rats, list) or len(rats) != DISTRACTOR_RATIONALES_EXPECTED:
        warns.append(f"WARNING: distractor_rationales debería tener {DISTRACTOR_RATIONALES_EXPECTED} elementos.")
    else:
        if any(len((r or "").strip()) < RATIONALE_MIN_CHARS for r in rats):
            warns.append(f"WARNING: alguna distractor_rationale es demasiado corta (<{RATIONALE_MIN_CHARS}).")

    # 2) Distractor ~ correcta
    for d in distractors:
        sim = jaccard(tokens(d), correct_t)
        if sim > JACCARD_DISTRACTOR_CORRECT_MAX:
            warns.append(f"WARNING: distractor muy parecido a la correcta (sim={sim:.2f}): '{d}'")

    # 3) Distractor ~ enunciado
    for d in distractors:
        sim = jaccard(tokens(d), stem_t)
        if sim < JACCARD_DISTRACTOR_STEM_MIN:
            warns.append(f"WARNING: distractor poco relacionado con el enunciado (sim={sim:.2f}): '{d}'")

    # 4) Longitudes dispares
    lens = [len(c.strip()) for c in choices]
    if min(lens) > 0 and (max(lens) / min(lens)) > CHOICE_LENGTH_RATIO_MAX:
        warns.append(f"WARNING: longitudes de opciones muy dispares (ratio>{CHOICE_LENGTH_RATIO_MAX}): {lens}")

    return warns


# ============================================================
# Evidence retry (regeneración si falla evidence)
# ============================================================

def evidence_candidates(source: str, max_items: int = EVIDENCE_CANDIDATES_MAX_ITEMS) -> List[str]:
    """
    Devuelve frases candidatas (literales) para evidence.
    """
    s = " ".join(source.replace("\r", " ").split())
    parts = re.split(r"(?<=[\.\;\:])\s+|\n+", s)
    parts = [p.strip() for p in parts if len(p.strip()) >= EVIDENCE_CANDIDATE_MIN_CHARS]
    if not parts:
        return [s[:EVIDENCE_FALLBACK_SOURCE_MAX_CHARS]]
    return parts[:max_items]


def evidence_strict_instructions(source: str) -> str:
    cands = evidence_candidates(source)
    bullets = "\n".join([f"- {c}" for c in cands])
    return f"""
EVIDENCIA (MODO ESTRICTO)
- El campo "evidence" DEBE ser COPIA EXACTA de UNA de las siguientes frases (elige una y pégala tal cual):
{bullets}
- Si ninguna encaja, usa como "evidence" la FUENTE COMPLETA (copiada literalmente).
- No parafrasees la evidencia.
""".strip()


def generate_questions_with_evidence_retry(
    client: OpenAI,
    seed: QSeed,
    model: str,
    max_attempts: int = EVIDENCE_RETRY_MAX_ATTEMPTS
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Devuelve (preguntas_validas, mensajes_rechazo).
    Reintenta si los fallos son SOLO de evidence.
    """
    rejected: List[str] = []

    for attempt in range(1, max_attempts + 1):
        extra = ""
        if attempt >= 2:
            extra = "\n\n" + evidence_strict_instructions(seed.body)

        payload = call_llm_generate_with_retry(
            client, seed, model=model, extra_rules=extra
        )

        questions = payload.get("questions", [])
        if not isinstance(questions, list) or not questions:
            rejected.append(f"[{seed.sid}] IA devolvió 0 preguntas (intento {attempt})")
            continue

        valid: List[Dict[str, Any]] = []
        errors_for_attempt: List[str] = []

        for q in questions:
            errs = validate_question(q, seed.body)
            if errs:
                errors_for_attempt.append(f"{q.get('id','(sin id)')}: " + "; ".join(errs))
            else:
                valid.append(q)

        if len(valid) == len(questions):
            return valid, rejected

        # Si hay errores no-evidence, no merece reintentar
        non_evidence = [e for e in errors_for_attempt if "evidence" not in e.lower()]
        if non_evidence:
            rejected.append(f"[{seed.sid}] Fallos no-evidence (no reintento): " + " | ".join(non_evidence))
            return valid, rejected

        rejected.append(
            f"[{seed.sid}] Intento {attempt} falló solo por evidence -> reintento. Detalles: " +
            " | ".join(errors_for_attempt)
        )

    return [], rejected


# ============================================================
# Exportación Moodle GIFT
# ============================================================

def escape_gift(text: str) -> str:
    """
    Escapes básicos para GIFT.
    """
    t = (text or "").replace("\r", " ").replace("\n", " ").strip()
    t = t.replace("\\", "\\\\")
    for ch in ["{", "}", "~", "=", "#"]:
        t = t.replace(ch, f"\\{ch}")
    return t


def to_gift(q: Dict[str, Any]) -> str:
    qid = escape_gift(q["id"])
    stem = escape_gift(q["stem"])
    expl = escape_gift(q["explanation"])

    if q["type"] == "mcq":
        choices = [escape_gift(c) for c in q["choices"]]
        ci = q["correct_index"]
        parts = []
        for i, c in enumerate(choices):
            parts.append(("=" if i == ci else "~") + c)
        body = " ".join(parts)
        return f"::{qid}::\n{stem}\n{{{body} #### {expl}}}\n"

    ans = "T" if q["answer"] else "F"
    return f"::{qid}::\n{stem}\n{{{ans} #### {expl}}}\n"
def compute_mcq_metrics(q: dict) -> dict:
    """
    Calcula métricas cuantitativas (domain-agnostic) para análisis y reporting.

    Esta función resume, en un diccionario plano, varias métricas útiles para:
      - generar figuras del Capítulo 4 (Resultados),
      - emitir *warnings* de calidad,
      - y documentar el comportamiento del pipeline de generación.

    Las métricas se calculan SOLO si la pregunta es de tipo 'mcq'. En caso contrario
    se devuelven valores neutros (listas vacías / None), para mantener una estructura
    homogénea en el report.

    Métricas que produce (para MCQ):
    ------------------------------
    1) jaccard_distractor_correct : list[float]
       Lista de 3 valores (uno por distractor), donde cada valor es:
         Jaccard(tokens(distractor), tokens(opción_correcta))
       Interpretación: valores altos sugieren distractores demasiado parecidos a la correcta.

    2) jaccard_distractor_stem : list[float]
       Lista de 3 valores (uno por distractor), donde cada valor es:
         Jaccard(tokens(distractor), tokens(enunciado))
       Interpretación: valores bajos sugieren distractores poco relacionados con el enunciado
       (ojo: puede dar falsos positivos en enunciados cortos).

    3) choice_len_ratio : float | None
       Ratio max_len/min_len sobre las 4 opciones (longitud en caracteres tras strip).
       Interpretación: valores altos indican desbalance de longitudes (posibles "pistas").

    4) rationale_lengths : list[int]
       Lista con la longitud (en caracteres) de cada elemento en 'distractor_rationales'.
       Sirve para auditar si las rationales son informativas (p.ej. si son demasiado cortas).

    Parámetros
    ----------
    q : dict
        Estructura de la pregunta generada (un item del JSON del LLM). Se espera que contenga,
        al menos, 'type', 'stem', 'choices', 'correct_index' y opcionalmente 'distractor_rationales'.

    Retorna
    -------
    dict
        Diccionario con las claves:
          - jaccard_distractor_correct (list[float] o [])
          - jaccard_distractor_stem (list[float] o [])
          - choice_len_ratio (float o None)
          - rationale_lengths (list[int] o [])
    """
    # Si no es MCQ, devolvemos estructura neutra para report homogéneo.
    if q.get("type") != "mcq":
        return {
            "jaccard_distractor_correct": [],
            "jaccard_distractor_stem": [],
            "choice_len_ratio": None,
            "rationale_lengths": []
        }

    # Validación básica de estructura MCQ
    choices = q.get("choices", [])
    ci = q.get("correct_index", None)
    if not isinstance(choices, list) or len(choices) != 4 or not isinstance(ci, int) or not (0 <= ci <= 3):
        # Si llega aquí con estructura inválida, no calculamos métricas.
        return {
            "jaccard_distractor_correct": [],
            "jaccard_distractor_stem": [],
            "choice_len_ratio": None,
            "rationale_lengths": []
        }

    # Tokenización de enunciado y correcta para comparaciones Jaccard
    stem_t = tokens(q.get("stem", ""))
    correct_t = tokens(choices[ci])

    # Lista de distractores (3 opciones que no son la correcta)
    distractors = [c for i, c in enumerate(choices) if i != ci]

    # Jaccard distractor vs correcta (3 valores)
    jac_dc = [jaccard(tokens(d), correct_t) for d in distractors]

    # Jaccard distractor vs enunciado (3 valores)
    jac_ds = [jaccard(tokens(d), stem_t) for d in distractors]

    # Desbalance de longitudes de opciones: max/min
    lens = [len((c or "").strip()) for c in choices]
    choice_ratio = (max(lens) / min(lens)) if min(lens) > 0 else None

    # Longitudes de rationales (si existen)
    rats = q.get("distractor_rationales", [])
    rat_lens = [len((r or "").strip()) for r in rats] if isinstance(rats, list) else []

    return {
        "jaccard_distractor_correct": jac_dc,
        "jaccard_distractor_stem": jac_ds,
        "choice_len_ratio": choice_ratio,
        "rationale_lengths": rat_lens
    }

# ============================================================
# Main
# ============================================================

def main(input_path: str, out_gift: str, model: str, read_all_cells: bool = False, debug: bool = True):
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Falta OPENAI_API_KEY en el entorno (variable de entorno).")

    # Contenedores para el reporte
    report_questions: List[Dict[str, Any]] = []
    report_rejections: List[Dict[str, Any]] = []

    text = load_text_from_file(input_path, read_all_cells=read_all_cells)

    if debug:
        print("DEBUG: contiene ```qseed ? ", "```qseed" in text)

    seeds = extract_qseeds(text)

    if debug:
        print(f"DEBUG: semillas encontradas: {len(seeds)}")
        for s in seeds[:10]:
            print(f" - {s.sid} | {s.qtype} | n={s.n} | diff={s.difficulty}")

    if not seeds:
        raise RuntimeError("No se encontraron bloques ```qseed ... ```")

    client = OpenAI()

    all_questions: List[Dict[str, Any]] = []
    rejected: List[str] = []

    for seed in seeds:
        try:
            valid_questions, rej = generate_questions_with_evidence_retry(
                client, seed, model=model, max_attempts=EVIDENCE_RETRY_MAX_ATTEMPTS
            )

            # Guarda rechazos en dos formatos: texto y estructurado (para el report)
            rejected.extend(rej)
            for msg in rej:
                report_rejections.append({"seed_id": seed.sid, "message": msg})

            # Procesa cada pregunta válida: warnings + métricas + registro
            for q in valid_questions:
                warns = distractor_warnings(q)
                if warns:
                    print(f"[WARN] {q.get('id')} -> " + " | ".join(warns))

                metrics = compute_mcq_metrics(q)

                report_questions.append({
                    "question_id": q.get("id"),
                    "seed_id": seed.sid,
                    "type": q.get("type"),
                    "difficulty": q.get("difficulty"),
                    "answer_type": q.get("answer_type"),
                    "warnings": warns,
                    **metrics
                })

            all_questions.extend(valid_questions)

        except Exception as e:
            msg = f"[{seed.sid}] ERROR llamada IA: {e}"
            rejected.append(msg)
            report_rejections.append({"seed_id": seed.sid, "message": msg})
            continue

    # Exportación GIFT
    out_lines: List[str] = []
    for q in all_questions:
        out_lines.append(to_gift(q))
        out_lines.append("")

    Path(out_gift).write_text("\n".join(out_lines), encoding="utf-8")

    print(f"\nOK: exportadas {len(all_questions)} preguntas a {out_gift}")
    if rejected:
        print("\nRechazadas (para revisión o regeneración):")
        for r in rejected:
            print(" -", r)

    # -------- Report JSON (se genera aquí, donde existen seeds/all_questions/input_path/out_gift/model) --------
    report = {
        "run": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "input_path": input_path,
            "output_gift": out_gift,
            "model": model,
            "seeds_found": len(seeds),
            "questions_exported": len(all_questions),
        },
        "thresholds": {
            "jaccard_distractor_correct_max": JACCARD_DISTRACTOR_CORRECT_MAX,
            "jaccard_distractor_stem_min": JACCARD_DISTRACTOR_STEM_MIN,
            "choice_length_ratio_max": CHOICE_LENGTH_RATIO_MAX,
            "rationale_min_chars": RATIONALE_MIN_CHARS,
            "rationales_expected": DISTRACTOR_RATIONALES_EXPECTED,
            "evidence_retry_max_attempts": EVIDENCE_RETRY_MAX_ATTEMPTS,
        },
        "questions": report_questions,
        "rejections": report_rejections,
    }

    report_path = Path(out_gift).with_suffix(".report.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Reporte guardado en: {report_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Uso:")
        print("  python main.py <entrada.md|entrada.ipynb> <salida.gift> <modelo>")
        print("")
        print("Ejemplo:")
        print('  python main.py "C:\\ruta\\archivo.ipynb" banco.gift gpt-4o-mini')
        raise SystemExit(1)

    input_path = sys.argv[1]
    out_gift = sys.argv[2]
    model = sys.argv[3]

    main(input_path, out_gift, model=model, read_all_cells=False, debug=True)