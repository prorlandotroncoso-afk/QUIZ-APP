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
MODEL_NAME = "qwen/qwen3.6-27b"

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
        
        # Generamos el quiz en 3 bloques de 5 preguntas.
        # Esto reduce el tamaño de cada respuesta y evita que Qwen corte el JSON.
        quiz = []
        preguntas_previas = []

        for bloque in range(3):
            previas_texto = "\n".join(
                f"- {q['pregunta']}" for q in preguntas_previas
            ) if preguntas_previas else "Ninguna."

            prompt = f"""
Respondé EXCLUSIVAMENTE con JSON válido.
No uses Markdown, títulos, comentarios ni texto fuera del JSON.

Formato obligatorio:
{{
  "preguntas": [
    {{
      "pregunta": "texto",
      "opciones": ["opción 1", "opción 2", "opción 3", "opción 4"],
      "correcta": "texto exacto de una de las opciones"
    }}
  ]
}}

REGLAS:
1. Generá EXACTAMENTE 5 preguntas nuevas usando ÚNICAMENTE el material proporcionado.
2. Cada pregunta debe tener EXACTAMENTE 4 opciones.
3. "correcta" debe coincidir EXACTAMENTE con una de las 4 opciones.
4. No inventes datos, especificaciones, versiones, equipamiento ni combinaciones.
5. No repitas ninguna pregunta de la lista de preguntas ya generadas.
6. Distribuí las preguntas entre categorías distintas cuando el material lo permita.
7. Priorizá información técnica disponible: motor, cilindrada, potencia, torque, transmisión, marchas, tracción, suspensión, dirección, frenos, consumo, tanque, velocidad, aceleración, dimensiones, baúl, seguridad, airbags, ADAS, tecnología, equipamiento, iluminación, confort y diseño.
8. Usá datos numéricos relevantes cuando estén presentes.
9. Si hay varias versiones/modelos, repartí las preguntas entre ellas y comparalas cuando el material lo permita.
10. Las opciones incorrectas deben ser plausibles y basarse en información del material.
11. Variá la dificultad entre conocimiento directo, diferenciación, comparación y conocimiento técnico.
12. Antes de responder verificá: exactamente 5 preguntas, 4 opciones por pregunta, "correcta" incluida entre las opciones, sin repeticiones y sin información inventada.

Preguntas ya generadas que NO debés repetir:
{previas_texto}

Material:
{text[:4000]}
"""

            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=1800,
                )
            except Exception as e:
                error_content = f"""
                <section class="glass hero">
                    <span class="eyebrow">Error de IA</span>
                    <h1>No pude generar el bloque {bloque + 1} del quiz</h1>
                    <p class="subtitle">{html.escape(str(e))}</p>
                    <a href="/admin">← Volver al panel</a>
                </section>
                """
                return page_html("Error de IA", error_content)

            raw_output = response.choices[0].message.content.strip()

            try:
                bloque_data = json.loads(raw_output)
                preguntas_bloque = bloque_data.get("preguntas", [])
            except Exception:
                safe_output = html.escape(raw_output)
                error_content = f"""
                <section class="glass hero">
                    <span class="eyebrow">Error JSON</span>
                    <h1>No pude interpretar el bloque {bloque + 1}</h1>
                    <p class="subtitle">La IA no devolvió JSON válido. Volvé a generar la evaluación.</p>
                </section>
                <section class="glass card">
                    <pre style="white-space:pre-wrap;overflow:auto;">{safe_output}</pre>
                </section>
                """
                return page_html("Error JSON", error_content)

            if not isinstance(preguntas_bloque, list) or len(preguntas_bloque) != 5:
                error_content = f"""
                <section class="glass hero">
                    <span class="eyebrow">Validación</span>
                    <h1>El bloque {bloque + 1} salió incompleto</h1>
                    <p class="subtitle">Se generaron {len(preguntas_bloque) if isinstance(preguntas_bloque, list) else 0} preguntas en lugar de 5. Probá nuevamente.</p>
                    <a href="/admin">← Volver al panel</a>
                </section>
                """
                return page_html("Bloque incompleto", error_content)

            for q in preguntas_bloque:
                if (
                    not isinstance(q, dict)
                    or not q.get("pregunta")
                    or not isinstance(q.get("opciones"), list)
                    or len(q.get("opciones", [])) != 4
                    or q.get("correcta") not in q.get("opciones", [])
                ):
                    error_content = f"""
                    <section class="glass hero">
                        <span class="eyebrow">Validación</span>
                        <h1>Una pregunta del bloque {bloque + 1} salió con formato inválido</h1>
                        <p class="subtitle">No se publicó el quiz para evitar errores. Volvé a generarlo.</p>
                        <a href="/admin">← Volver al panel</a>
                    </section>
                    """
                    return page_html("Quiz inválido", error_content)

            quiz.extend(preguntas_bloque)
            preguntas_previas.extend(preguntas_bloque)

        # Validación final antes de crear el link compartible.
        if len(quiz) != 15:
            error_content = f"""
            <section class="glass hero">
                <span class="eyebrow">Validación final</span>
                <h1>El quiz no salió completo</h1>
                <p class="subtitle">Se generaron {len(quiz)} preguntas en lugar de 15. Probá nuevamente.</p>
                <a href="/admin">← Volver al panel</a>
            </section>
            """
            return page_html("Quiz incompleto", error_content)

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
