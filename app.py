from flask import Flask, request
import requests
from bs4 import BeautifulSoup
from groq import Groq
import json
from datetime import datetime
import uuid
import os
import html

app = Flask(__name__)

# =========================
# 🔑 API KEY SEGURA (desde Render)
# =========================
api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    raise ValueError("Falta la API KEY de Groq en Render")

client = Groq(api_key=api_key)

# =========================
# ⚙️ CONFIGURACIÓN
# =========================
MODEL_NAME = "openai/gpt-oss-20b"

GOOGLE_SCRIPT_URL = os.environ.get(
    "GOOGLE_SCRIPT_URL",
    "https://script.google.com/macros/s/AKfycbybOrZVzoZYjIvagGcb7wfQwevVM93wIq4AMijPdLG82HXwXwxuC0p8pK4m-p4LACEYPg/exec"
)

# Almacenamiento temporal
quizzes = {}

# =========================
# 🎨 ESTILO VISUAL GENERAL
# =========================
BASE_STYLE = """
<style>
    :root {
        --bg-1: #d7c8bb;
        --bg-2: #b8a99c;
        --glass: rgba(255,255,255,0.20);
        --glass-strong: rgba(255,255,255,0.32);
        --border: rgba(255,255,255,0.34);
        --text: #2f2c2a;
        --muted: #6d655f;
        --shadow: 0 20px 60px rgba(67, 53, 44, 0.20);
        --radius: 24px;
        --accent: rgba(58, 52, 48, 0.88);
        --accent-hover: rgba(40, 36, 33, 0.96);
        --success: rgba(209, 238, 218, 0.75);
        --danger: rgba(248, 215, 218, 0.78);
        --warning: rgba(255, 243, 205, 0.78);
    }

    * {
        box-sizing: border-box;
    }

    html {
        scroll-behavior: smooth;
    }

    body {
        margin: 0;
        min-height: 100vh;
        font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                     "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: var(--text);
        background:
            radial-gradient(circle at 15% 20%, rgba(255,255,255,0.65), transparent 32%),
            radial-gradient(circle at 86% 14%, rgba(196,176,158,0.72), transparent 34%),
            radial-gradient(circle at 54% 92%, rgba(244,225,208,0.58), transparent 38%),
            linear-gradient(135deg, var(--bg-1), var(--bg-2));
        background-attachment: fixed;
        position: relative;
    }

    body::before,
    body::after {
        content: "";
        position: fixed;
        pointer-events: none;
        border-radius: 999px;
        filter: blur(70px);
        opacity: 0.45;
        z-index: 0;
    }

    body::before {
        width: 310px;
        height: 310px;
        background: rgba(255, 235, 214, 0.85);
        top: 7%;
        left: -70px;
    }

    body::after {
        width: 360px;
        height: 360px;
        background: rgba(168, 151, 138, 0.74);
        right: -90px;
        bottom: 2%;
    }

    .page-shell {
        position: relative;
        z-index: 1;
        width: min(920px, calc(100% - 28px));
        margin: 0 auto;
        padding: 42px 0 64px;
    }

    .glass {
        background: var(--glass);
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border-radius: var(--radius);
    }

    .hero {
        padding: 28px;
        margin-bottom: 20px;
    }

    .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 7px 11px;
        border-radius: 999px;
        background: rgba(255,255,255,0.24);
        border: 1px solid rgba(255,255,255,0.34);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: .08em;
        text-transform: uppercase;
        color: var(--muted);
        margin-bottom: 13px;
    }

    h1, h2, h3, p {
        margin-top: 0;
    }

    h1 {
        font-size: clamp(28px, 5vw, 44px);
        line-height: 1.04;
        margin-bottom: 10px;
        letter-spacing: -0.035em;
    }

    h2 {
        font-size: 23px;
        margin-bottom: 8px;
    }

    h3 {
        font-size: 17px;
    }

    .subtitle,
    .muted {
        color: var(--muted);
        line-height: 1.55;
    }

    .card {
        padding: 24px;
        margin-bottom: 16px;
    }

    .form-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
    }

    .field {
        margin-bottom: 15px;
    }

    .field.full {
        grid-column: 1 / -1;
    }

    label {
        display: block;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 7px;
        color: rgba(47, 44, 42, 0.88);
    }

    input[type="text"],
    input[type="email"],
    textarea {
        width: 100%;
        border: 1px solid rgba(255,255,255,0.38);
        outline: none;
        background: rgba(255,255,255,0.34);
        color: var(--text);
        border-radius: 15px;
        padding: 13px 14px;
        font: inherit;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.26);
        transition: .2s ease;
    }

    textarea {
        min-height: 170px;
        resize: vertical;
        line-height: 1.5;
    }

    input:focus,
    textarea:focus {
        background: rgba(255,255,255,0.48);
        border-color: rgba(255,255,255,0.75);
        box-shadow: 0 0 0 4px rgba(255,255,255,0.12);
    }

    .btn {
        appearance: none;
        border: 0;
        cursor: pointer;
        width: 100%;
        min-height: 50px;
        padding: 13px 18px;
        border-radius: 16px;
        background: var(--accent);
        color: white;
        font-weight: 750;
        font-size: 15px;
        letter-spacing: .01em;
        transition: transform .15s ease, background .15s ease, box-shadow .15s ease;
        box-shadow: 0 12px 30px rgba(45, 39, 35, 0.18);
    }

    .btn:hover {
        background: var(--accent-hover);
        transform: translateY(-1px);
    }

    .btn:active {
        transform: translateY(0);
    }

    a {
        color: #403a36;
        font-weight: 700;
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }

    .quiz-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 14px;
    }

    .pill {
        border: 1px solid rgba(255,255,255,0.36);
        background: rgba(255,255,255,0.23);
        border-radius: 999px;
        padding: 7px 11px;
        font-size: 12px;
        font-weight: 700;
        color: var(--muted);
    }

    .question-card {
        padding: 22px;
        margin-bottom: 14px;
    }

    .question-number {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: .1em;
        font-weight: 800;
        color: var(--muted);
        margin-bottom: 8px;
    }

    .question-text {
        font-size: 17px;
        line-height: 1.5;
        font-weight: 760;
        margin-bottom: 15px;
    }

    .option {
        position: relative;
        display: flex;
        align-items: flex-start;
        gap: 11px;
        padding: 12px 13px;
        margin: 8px 0;
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.28);
        background: rgba(255,255,255,0.20);
        cursor: pointer;
        transition: .16s ease;
        line-height: 1.38;
    }

    .option:hover {
        background: rgba(255,255,255,0.34);
        transform: translateX(2px);
    }

    .option input[type="radio"] {
        margin-top: 3px;
        accent-color: #4c4540;
        transform: scale(1.08);
        flex: 0 0 auto;
    }

    .result-summary {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 18px;
        align-items: center;
    }

    .score {
        display: inline-flex;
        align-items: baseline;
        gap: 4px;
        font-size: clamp(34px, 7vw, 54px);
        font-weight: 850;
        letter-spacing: -0.05em;
    }

    .score small {
        font-size: 16px;
        color: var(--muted);
        letter-spacing: 0;
    }

    .result-card {
        padding: 20px;
        margin-bottom: 12px;
    }

    .result-card.correcta {
        background: var(--success);
    }

    .result-card.incorrecta {
        background: var(--danger);
    }

    .result-card.blanco {
        background: var(--warning);
    }

    .answer-line {
        margin-bottom: 6px;
        line-height: 1.48;
    }

    .created-box {
        text-align: center;
        padding: 32px 24px;
    }

    .created-link {
        display: block;
        padding: 12px 14px;
        margin: 14px 0;
        border-radius: 14px;
        word-break: break-all;
        background: rgba(255,255,255,0.28);
        border: 1px solid rgba(255,255,255,0.34);
    }

    .footer-note {
        text-align: center;
        color: var(--muted);
        font-size: 12px;
        margin-top: 18px;
    }

    @media (max-width: 700px) {
        .page-shell {
            width: min(100% - 18px, 920px);
            padding: 18px 0 36px;
        }

        .hero,
        .card,
        .question-card {
            padding: 18px;
        }

        .form-grid {
            grid-template-columns: 1fr;
        }

        .field.full {
            grid-column: auto;
        }

        .result-summary {
            grid-template-columns: 1fr;
        }

        h1 {
            font-size: 30px;
        }
    }
</style>
"""


def page_html(title, content):
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{html.escape(title)}</title>
        {BASE_STYLE}
    </head>
    <body>
        <main class="page-shell">
            {content}
        </main>
    </body>
    </html>
    """


# =========================
# 🧑‍💼 ADMIN
# =========================
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        content = request.form["content"].strip()
        marca = request.form["marca"].strip()
        modelo = request.form["modelo"].strip()

        if content.startswith("http"):
            try:
                response = requests.get(content, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                text = soup.get_text(" ", strip=True)
            except Exception as e:
                error_content = f"""
                <section class="glass hero">
                    <span class="eyebrow">Error de lectura</span>
                    <h1>No pude leer esa URL</h1>
                    <p class="subtitle">{html.escape(str(e))}</p>
                    <a href="/admin">← Volver al panel</a>
                </section>
                """
                return page_html("Error", error_content)
        else:
            text = content

        prompt = f"""
Respondé EXCLUSIVAMENTE en JSON válido.
No escribas explicaciones, títulos, comentarios ni texto fuera del JSON.

Formato obligatorio:

[
{{
"pregunta": "texto",
"opciones": ["texto de opción 1", "texto de opción 2", "texto de opción 3", "texto de opción 4"],
"correcta": "texto exacto de una de las opciones"
}}
]

INSTRUCCIONES IMPORTANTES:

1. Basate ÚNICAMENTE en la información proporcionada. No inventes datos, características, versiones, motorizaciones, potencias ni equipamiento.

2. Generá exactamente 15 preguntas.

3. Cada pregunta debe tener EXACTAMENTE 4 opciones.

4. El campo "correcta" debe contener EXACTAMENTE el mismo texto que una de las cuatro opciones del arreglo "opciones".
No uses letras (A, B, C, D), números de índice ni referencias como "opción 1".

5. El examen debe evaluar tanto conocimientos básicos como conocimientos técnicos y específicos del vehículo.

6. NO te limites a utilizar solamente la información más simple o evidente del documento. Debés buscar activamente información técnica y generar preguntas sobre ella cuando esté disponible.

7. Priorizá una distribución variada de las preguntas entre las diferentes categorías de información presentes en el material.

Cuando exista información suficiente, incluí preguntas sobre:

- Motorización
- Tipo de motor
- Cilindrada
- Potencia
- Torque
- Tipo y cantidad de marchas
- Transmisión
- Tipo de tracción
- Suspensión
- Dirección
- Frenos
- Consumo
- Capacidad del tanque
- Velocidad máxima
- Aceleración
- Dimensiones
- Capacidad del baúl
- Equipamiento
- Tecnología
- Seguridad
- Airbags
- ADAS y sistemas de asistencia a la conducción
- Iluminación
- Confort
- Diseño
- Diferencias entre versiones

No es obligatorio utilizar todas estas categorías. Utilizá únicamente las que estén realmente presentes en la información proporcionada.

8. Evitá generar demasiadas preguntas sobre una misma categoría. Por ejemplo, no generes 8 preguntas sobre iluminación dejando de lado la motorización, seguridad o transmisión si esa información está disponible.

9. Si existe información técnica sobre la motorización, DEBE haber al menos una pregunta relacionada con el motor o el sistema de propulsión.

10. Si existe información sobre potencia, torque, transmisión o suspensión, intentá incluir preguntas sobre esas características antes de utilizar nuevamente características de equipamiento.

11. Si el material contiene UN SOLO modelo o versión, generá preguntas variadas sobre ese modelo, incluyendo tanto características generales como información técnica.

12. Si el material contiene DOS O MÁS modelos o versiones, distribuí las preguntas entre TODOS los modelos de manera equilibrada.

13. Cuando existan varios modelos o versiones, generá también preguntas COMPARATIVAS que permitan diferenciarlos.

Por ejemplo:

- ¿Qué versión incorpora techo panorámico?
- ¿Qué versión tiene mayor potencia?
- ¿Qué versiones utilizan el motor T200?
- ¿Qué versión incorpora cámara 360°?
- ¿Qué versiones cuentan con determinado sistema de seguridad?

14. Cuando una característica pertenezca a MÁS DE UN modelo, la respuesta correcta puede contener una combinación de modelos.

Por ejemplo, si Active y Allure tienen determinada característica:

"opciones": [
    "Active",
    "Allure",
    "GT",
    "Active y Allure"
],
"correcta": "Active y Allure"

15. Si una característica pertenece a TODOS los modelos, podés utilizar una respuesta que incluya todos los modelos.

Por ejemplo:

"opciones": [
    "Active",
    "Allure",
    "GT",
    "Active, Allure y GT"
],
"correcta": "Active, Allure y GT"

16. Las combinaciones de modelos deben basarse ÚNICAMENTE en la información proporcionada. No inventes que dos o tres versiones comparten una característica si el documento no lo indica.

17. Cuando una característica pertenezca únicamente a una versión, la respuesta correcta debe ser esa versión.

18. Las opciones incorrectas deben ser plausibles y estar basadas en información real del documento. No inventes especificaciones para crear distractores.

19. Evitá repetir preguntas sobre la misma característica.

20. Variá la dificultad de las preguntas.

Incluí preguntas de:

- Conocimiento directo: identificar una característica concreta.
- Diferenciación: distinguir entre dos o más versiones.
- Comparación: determinar qué versión o versiones poseen determinada característica.
- Conocimiento técnico: interpretar correctamente datos de motor, potencia, torque, transmisión, suspensión, seguridad u otras especificaciones.

21. Cuando existan datos numéricos importantes, utilizalos para generar preguntas. Por ejemplo, potencia, torque, cilindrada, capacidad de baúl, capacidad de tanque, dimensiones, velocidad máxima, cantidad de marchas, etc.

22. No descartes una información técnica simplemente porque sea más compleja. Si está presente en el material, debe considerarse para la generación del examen.

23. Las preguntas deben estar redactadas de manera clara y profesional, como un examen de capacitación para vendedores de vehículos.

24. Antes de generar el JSON final, verificá internamente que:

- Hay exactamente 15 preguntas.
- Cada pregunta tiene exactamente 4 opciones.
- "correcta" coincide exactamente con una de las 4 opciones.
- No hay preguntas repetidas.
- Se utilizaron diferentes categorías de información cuando están disponibles.
- Si existen varios modelos, todos fueron considerados.
- Si una característica pertenece a varios modelos, se consideró la posibilidad de una respuesta combinada.
- Si existe información de motorización, se incluyeron preguntas técnicas sobre ella.
- No se inventó ninguna información.

Material:

{text[:5500]}
"""

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=6000
            )
        except Exception as e:
            error_content = f"""
            <section class="glass hero">
                <span class="eyebrow">Error de IA</span>
                <h1>No pude generar el quiz</h1>
                <p class="subtitle">{html.escape(str(e))}</p>
                <a href="/admin">← Volver al panel</a>
            </section>
            """
            return page_html("Error de IA", error_content)

        quiz_json = response.choices[0].message.content.strip()

        # Limpieza automática: toma solamente el array JSON.
        start = quiz_json.find("[")
        end = quiz_json.rfind("]") + 1

        if start == -1 or end <= start:
            safe_output = html.escape(quiz_json)
            error_content = f"""
            <section class="glass hero">
                <span class="eyebrow">Formato inesperado</span>
                <h1>La IA no devolvió el quiz en el formato esperado</h1>
                <p class="subtitle">Volvé a intentarlo. Si se repite, revisá el material ingresado.</p>
            </section>
            <section class="glass card">
                <pre style="white-space:pre-wrap;overflow:auto;">{safe_output}</pre>
            </section>
            """
            return page_html("Error de formato", error_content)

        quiz_json = quiz_json[start:end]

        try:
            quiz = json.loads(quiz_json)
        except Exception:
            safe_output = html.escape(quiz_json)
            error_content = f"""
            <section class="glass hero">
                <span class="eyebrow">Error JSON</span>
                <h1>No pude interpretar las preguntas generadas</h1>
                <p class="subtitle">Volvé a generar la evaluación.</p>
            </section>
            <section class="glass card">
                <pre style="white-space:pre-wrap;overflow:auto;">{safe_output}</pre>
            </section>
            """
            return page_html("Error JSON", error_content)

        # Validación mínima para evitar publicar un quiz roto.
        if not isinstance(quiz, list) or len(quiz) != 15:
            error_content = f"""
            <section class="glass hero">
                <span class="eyebrow">Validación</span>
                <h1>El quiz no salió completo</h1>
                <p class="subtitle">Se generaron {len(quiz) if isinstance(quiz, list) else 0} preguntas en lugar de 15. Probá nuevamente.</p>
                <a href="/admin">← Volver al panel</a>
            </section>
            """
            return page_html("Quiz incompleto", error_content)

        for q in quiz:
            if (
                not isinstance(q, dict)
                or not isinstance(q.get("opciones"), list)
                or len(q.get("opciones", [])) != 4
                or q.get("correcta") not in q.get("opciones", [])
                or not q.get("pregunta")
            ):
                error_content = """
                <section class="glass hero">
                    <span class="eyebrow">Validación</span>
                    <h1>Una pregunta salió con un formato inválido</h1>
                    <p class="subtitle">No se publicó el quiz para evitar errores. Volvé a generarlo.</p>
                    <a href="/admin">← Volver al panel</a>
                </section>
                """
                return page_html("Quiz inválido", error_content)

        quiz_id = str(uuid.uuid4())

        try:
            requests.post(
                GOOGLE_SCRIPT_URL,
                json={
                    "tipo": "quiz",
                    "quiz_id": quiz_id,
                    "marca": marca,
                    "modelo": modelo,
                    "quiz_json": json.dumps(quiz, ensure_ascii=False)
                },
                timeout=10
            )
        except Exception as e:
            print("ERROR GUARDANDO QUIZ EN SHEETS:", e)

        link = f"{request.url_root}quiz/{quiz_id}"

        created_content = f"""
        <section class="glass created-box">
            <span class="eyebrow">Quiz listo</span>
            <h1>Evaluación creada</h1>
            <p class="subtitle">Tu evaluación de <b>{html.escape(marca)} {html.escape(modelo)}</b> ya está lista para compartir.</p>
            <a class="created-link" href="{html.escape(link)}" target="_blank">{html.escape(link)}</a>
            <p><a href="{html.escape(link)}" target="_blank">Abrir evaluación →</a></p>
            <p><a href="/admin">Crear otra evaluación</a></p>
        </section>
        """
        return page_html("Quiz creado", created_content)

    admin_content = """
    <section class="glass hero">
        <span class="eyebrow">Quiz Generator</span>
        <h1>Creá una evaluación en minutos</h1>
        <p class="subtitle">
            Pegá una URL o el contenido técnico del vehículo. La IA genera 15 preguntas
            y deja el quiz listo para compartir.
        </p>
    </section>

    <section class="glass card">
        <form method="post">
            <div class="form-grid">
                <div class="field">
                    <label>Marca</label>
                    <input type="text" name="marca" placeholder="Ej. Peugeot" required>
                </div>

                <div class="field">
                    <label>Modelo</label>
                    <input type="text" name="modelo" placeholder="Ej. 2008 Allure" required>
                </div>

                <div class="field full">
                    <label>Información para generar el quiz</label>
                    <textarea
                        name="content"
                        placeholder="Pegá aquí el texto técnico o una URL..."
                        required
                    ></textarea>
                </div>
            </div>

            <button class="btn" type="submit">Generar evaluación</button>
        </form>
    </section>

    <p class="footer-note">La información del quiz se genera únicamente a partir del material ingresado.</p>
    """

    return page_html("Panel Admin - Quiz Generator", admin_content)


# =========================
# 👤 USER
# =========================
@app.route("/quiz/<quiz_id>", methods=["GET"])
def quiz(quiz_id):
    try:
        r = requests.get(
            GOOGLE_SCRIPT_URL,
            params={"quiz_id": quiz_id},
            timeout=10
        )
    except Exception as e:
        return page_html(
            "Error",
            f"""
            <section class="glass hero">
                <span class="eyebrow">Error de conexión</span>
                <h1>No pude abrir esta evaluación</h1>
                <p class="subtitle">{html.escape(str(e))}</p>
            </section>
            """
        )

    if r.text == "NOT_FOUND":
        return page_html(
            "Quiz no encontrado",
            """
            <section class="glass hero">
                <span class="eyebrow">No encontrado</span>
                <h1>Este quiz no está disponible</h1>
                <p class="subtitle">Revisá el enlace o solicitá uno nuevo.</p>
            </section>
            """
        )

    try:
        data = r.json()
    except Exception:
        return page_html(
            "Error",
            """
            <section class="glass hero">
                <span class="eyebrow">Error</span>
                <h1>No pude leer esta evaluación</h1>
                <p class="subtitle">Intentá nuevamente en unos instantes.</p>
            </section>
            """
        )

    marca = data["marca"]
    modelo = data["modelo"]
    quiz_data = data["quiz"]

    questions_html = ""

    for i, q in enumerate(quiz_data):
        pregunta = html.escape(str(q["pregunta"]))
        options_html = ""

        for op in q["opciones"]:
            safe_op = html.escape(str(op), quote=True)
            options_html += f"""
            <label class="option">
                <input type="radio" name="q{i}" value="{safe_op}" required>
                <span>{safe_op}</span>
            </label>
            """

        questions_html += f"""
        <section class="glass question-card">
            <div class="question-number">Pregunta {i + 1} de {len(quiz_data)}</div>
            <div class="question-text">{pregunta}</div>
            {options_html}
        </section>
        """

    quiz_content = f"""
    <section class="glass hero">
        <span class="eyebrow">Evaluación</span>
        <h1>{html.escape(str(marca))} · {html.escape(str(modelo))}</h1>
        <p class="subtitle">Completá tus datos y respondé las {len(quiz_data)} preguntas.</p>
        <div class="quiz-meta">
            <span class="pill">{len(quiz_data)} preguntas</span>
            <span class="pill">Una respuesta por pregunta</span>
        </div>
    </section>

    <form method="post" action="/submit">
        <section class="glass card">
            <div class="form-grid">
                <div class="field">
                    <label>Email</label>
                    <input type="email" name="email" placeholder="nombre@empresa.com" required>
                </div>

                <div class="field">
                    <label>Nombre</label>
                    <input type="text" name="nombre" placeholder="Tu nombre" required>
                </div>

                <div class="field full">
                    <label>Equipo</label>
                    <input type="text" name="equipo" placeholder="Ej. Ventas / Sucursal / Equipo" required>
                </div>
            </div>
        </section>

        {questions_html}

        <input type="hidden" name="quiz_id" value="{html.escape(str(quiz_id), quote=True)}">

        <section class="glass card">
            <button class="btn" type="submit">Enviar respuestas</button>
        </section>
    </form>
    """

    return page_html(f"Evaluación - {marca} {modelo}", quiz_content)


# =========================
# 📊 RESULTADOS
# =========================
@app.route("/submit", methods=["POST"])
def submit():
    nombre = request.form["nombre"]
    email = request.form["email"]
    equipo = request.form["equipo"]
    quiz_id = request.form["quiz_id"]

    try:
        r = requests.get(
            GOOGLE_SCRIPT_URL,
            params={"quiz_id": quiz_id},
            timeout=10
        )
    except Exception as e:
        return page_html(
            "Error",
            f"""
            <section class="glass hero">
                <span class="eyebrow">Error de conexión</span>
                <h1>No pude calcular el resultado</h1>
                <p class="subtitle">{html.escape(str(e))}</p>
            </section>
            """
        )

    if r.text == "NOT_FOUND":
        return page_html(
            "Quiz no encontrado",
            """
            <section class="glass hero">
                <span class="eyebrow">No encontrado</span>
                <h1>Este quiz ya no está disponible</h1>
            </section>
            """
        )

    data = r.json()

    marca = data["marca"]
    modelo = data["modelo"]
    quiz_data = data["quiz"]

    score = 0
    detalle = ""

    for i, q in enumerate(quiz_data):
        respuesta_usuario = request.form.get(f"q{i}")
        correcta = q["correcta"]
        texto_correcto = correcta

        if not respuesta_usuario:
            estado = "blanco"
            icono = "🟡"
            titulo_estado = "Sin responder"
        elif respuesta_usuario == texto_correcto:
            score += 1
            estado = "correcta"
            icono = "🟢"
            titulo_estado = "Correcta"
        else:
            estado = "incorrecta"
            icono = "🔴"
            titulo_estado = "Incorrecta"

        detalle += f"""
        <section class="glass result-card {estado}">
            <div class="question-number">{icono} Pregunta {i + 1} · {titulo_estado}</div>
            <div class="question-text">{html.escape(str(q["pregunta"]))}</div>

            <div class="answer-line">
                <b>Tu respuesta:</b>
                {html.escape(str(respuesta_usuario)) if respuesta_usuario else "Sin responder"}
            </div>

            <div class="answer-line">
                <b>Respuesta correcta:</b>
                {html.escape(str(texto_correcto))}
            </div>
        </section>
        """

    total = len(quiz_data)
    porcentaje_num = round((score / total) * 100, 2) if total else 0
    porcentaje = f"{porcentaje_num}%"

    result_data = {
        "Nombre": nombre,
        "Email": email,
        "Equipo": equipo,
        "Marca": marca,
        "Modelo": modelo,
        "Puntaje": score,
        "Total": total,
        "Porcentaje": porcentaje,
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    try:
        r = requests.post(
            GOOGLE_SCRIPT_URL,
            json={
                "fecha": result_data["Fecha"],
                "marca": result_data["Marca"],
                "modelo": result_data["Modelo"],
                "nombre": result_data["Nombre"],
                "email": result_data["Email"],
                "equipo": result_data["Equipo"],
                "puntaje": result_data["Puntaje"],
                "total": result_data["Total"],
                "porcentaje": result_data["Porcentaje"]
            },
            timeout=10
        )

        print("GOOGLE STATUS:", r.status_code)
        print("GOOGLE RESPONSE:", r.text)

    except Exception as e:
        print("ERROR SHEETS:", e)

    summary_content = f"""
    <section class="glass hero">
        <span class="eyebrow">Resultado</span>

        <div class="result-summary">
            <div>
                <h1>{html.escape(nombre)}</h1>
                <p class="subtitle">{html.escape(str(marca))} · {html.escape(str(modelo))}</p>
            </div>

            <div class="score">
                {score}/{total}
                <small>{porcentaje}</small>
            </div>
        </div>

        <div class="quiz-meta">
            <span class="pill">{html.escape(equipo)}</span>
            <span class="pill">{html.escape(email)}</span>
        </div>
    </section>

    {detalle}

    <p class="footer-note">Resultado registrado · {html.escape(result_data["Fecha"])}</p>
    """

    return page_html("Resultado del examen", summary_content)


# =========================
# 🚀 START
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
