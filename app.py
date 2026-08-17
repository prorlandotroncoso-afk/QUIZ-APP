from flask import Flask, request
import requests
from bs4 import BeautifulSoup
from groq import Groq
import json
import pandas as pd
from datetime import datetime
import uuid
import os

app = Flask(__name__)

# =========================
# 🔑 API KEY SEGURA (desde Render)
# =========================
api_key = xxxxxx

if not api_key:
    raise ValueError("Falta la API KEY de Groq en Render")

client = Groq(xxxxxx)

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbybOrZVzoZYjIvagGcb7wfQwevVM93wIq4AMijPdLG82HXwXwxuC0p8pK4m-p4LACEYPg/exec"
# almacenamiento temporal
quizzes = {}

# =========================
# 🧑‍💼 ADMIN
# =========================

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        content = request.form["content"]
        marca = request.form["marca"]
        modelo = request.form["modelo"]

        if content.startswith("http"):
            response = requests.get(content)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()
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

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}]
        )

        quiz_json = response.choices[0].message.content.strip()

        # limpieza automática
        start = quiz_json.find("[")
        end = quiz_json.rfind("]") + 1
        quiz_json = quiz_json[start:end]

        try:
            quiz = json.loads(quiz_json)
        except:
            return f"<pre>Error JSON:\n{quiz_json}</pre>"
            
        quiz_id = str(uuid.uuid4())
        requests.post(
            GOOGLE_SCRIPT_URL,
            json={
                "tipo": "quiz",
                "quiz_id": quiz_id,
                "marca": marca,
                "modelo": modelo,
                "quiz_json": json.dumps(quiz)
            },
            timeout=10
        )
        link = f"{request.url_root}quiz/{quiz_id}"
        
        return f"""
        <h2>✅ Quiz creado</h2>
        <p>Link para enviar:</p>
        <a href="{link}" target="_blank">{link}</a>
        <br><br><a href="/admin">Crear otro</a>
        """

    return """
    <h1>🧑‍💼 PANEL ADMIN</h1>
    
    <form method="post">
    
    <label>Marca:</label><br>
    <input type="text" name="marca" required><br><br>
    
    <label>Modelo:</label><br>
    <input type="text" name="modelo" required><br><br>
    
    <textarea name="content" rows="10" cols="60" placeholder="Pegá texto o URL"></textarea><br><br>
    <button type="submit">Generar Evaluación</button>
    
    </form>
    """

# =========================
# 👤 USER
# =========================

@app.route("/quiz/<quiz_id>", methods=["GET"])
def quiz(quiz_id):
    r = requests.get(
        GOOGLE_SCRIPT_URL,
        params={"quiz_id": quiz_id},
        timeout=10
    )
    
    if r.text == "NOT_FOUND":
        return "Quiz no encontrado"
    
    data = r.json()
    
    marca = data["marca"]
    modelo = data["modelo"]
    quiz = data["quiz"]

    form_start = """
    <form method="post" action="/submit">
    """

    form_end = """
    <input type="hidden" name="quiz_id" value="{quiz_id}">
    <button type="submit">Enviar respuestas</button>
    </form>
    """

    body = """
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    * { box-sizing: border-box; }
    body {
        margin:0;
        min-height:100vh;
        font-family:Arial, Helvetica, sans-serif;
        color:#2f2b28;
        background:
            radial-gradient(circle at 20% 20%, rgba(255,255,255,.70), transparent 28%),
            radial-gradient(circle at 80% 15%, rgba(211,191,172,.70), transparent 30%),
            radial-gradient(circle at 50% 85%, rgba(244,226,209,.62), transparent 34%),
            linear-gradient(135deg, #d8c9bc, #b7a99e);
        padding:28px 14px;
    }
    .quiz-wrap {
        width:min(860px, 100%);
        margin:auto;
    }
    .glass {
        background:rgba(255,255,255,.22);
        border:1px solid rgba(255,255,255,.34);
        box-shadow:0 20px 55px rgba(67,53,44,.18);
        backdrop-filter:blur(22px);
        -webkit-backdrop-filter:blur(22px);
        border-radius:22px;
    }
    .hero {
        padding:24px;
        margin-bottom:16px;
    }
    .hero h1 {
        margin:0 0 8px;
        font-size:34px;
    }
    .hero p {
        margin:0;
        color:#6d655f;
    }
    .user-box {
        padding:20px;
        margin-bottom:16px;
    }
    .user-box label {
        display:block;
        margin:12px 0 6px;
        font-size:14px;
        font-weight:700;
    }
    .user-box input[type="email"],
    .user-box input[type="text"] {
        width:100%;
        border:1px solid rgba(255,255,255,.38);
        background:rgba(255,255,255,.35);
        color:#2f2b28;
        border-radius:14px;
        padding:12px 13px;
        font:inherit;
        outline:none;
    }
    .question-card {
        padding:20px;
        margin:14px 0;
    }
    .question-card p {
        margin:0 0 12px;
        line-height:1.45;
    }
    .option {
        display:block;
        padding:10px 12px;
        margin:7px 0;
        border-radius:13px;
        background:rgba(255,255,255,.22);
        border:1px solid rgba(255,255,255,.28);
    }
    .option input {
        margin-right:8px;
    }
    .submit-btn {
        width:100%;
        margin-top:18px;
        border:0;
        border-radius:15px;
        padding:14px 18px;
        background:#4a433e;
        color:white;
        font-size:15px;
        font-weight:700;
        cursor:pointer;
    }
    </style>
    </head>
    <body>
    <div class="quiz-wrap">
    <div class="glass hero">
        <h1>Evaluación</h1>
        <p>Completá tus datos y respondé todas las preguntas.</p>
    </div>
    """

    body += form_start
    body += """
    <div class="glass user-box">
        <label>Email:</label>
        <input type="email" name="email" required>

        <label>Nombre:</label>
        <input type="text" name="nombre" required>

        <label>Equipo:</label>
        <input type="text" name="equipo" required>
    </div>
    """

    for i, q in enumerate(quiz):
        body += f'<div class="glass question-card"><p><b>{q["pregunta"]}</b></p>'

        for op in q["opciones"]:
            body += f'<label class="option"><input type="radio" name="q{i}" value="{op}" required> {op}</label>'

        body += "</div>"

    body += f"""
    <input type="hidden" name="quiz_id" value="{quiz_id}">
    <button class="submit-btn" type="submit">Enviar</button>
    </form>
    </div>
    </body>
    </html>
    """

    return body
# =========================
# 📊 RESULTADOS
# =========================

@app.route("/submit", methods=["POST"])
def submit():
    nombre = request.form["nombre"]
    email = request.form["email"]
    equipo = request.form["equipo"]
    quiz_id = request.form["quiz_id"]

    r = requests.get(
        GOOGLE_SCRIPT_URL,
        params={"quiz_id": quiz_id},
        timeout=10
    )
    
    if r.text == "NOT_FOUND":
        return "Quiz no encontrado"
    
    data = r.json()
    
    marca = data["marca"]
    modelo = data["modelo"]
    quiz = data["quiz"]
    score = 0
    detalle = ""
    for i, q in enumerate(quiz):
        respuesta_usuario = request.form.get(f"q{i}")
        correcta = q["correcta"]
        texto_correcto = correcta
        
        # detectar en blanco
        if not respuesta_usuario:
            estado = "blanco"
            icono = "🟡"
            color = "#fff3cd"
        elif respuesta_usuario == texto_correcto:
            score += 1
            estado = "correcta"
            icono = "🟢"
            color = "#d4edda"
        else:
             estado = "incorrecta"
             icono = "🔴"
             color = "#f8d7da"
        detalle += f"""
        <div style="
            background:{color};
            padding:15px;
            margin:15px 0;
            border-radius:8px;
        ">
            <h3>{icono} Pregunta {i+1}</h3>
            
            <p><b>{q['pregunta']}</b></p>
            
            <p><b>Tu respuesta:</b> {respuesta_usuario if respuesta_usuario else "Sin responder"}</p>
            
            <p><b>Respuesta correcta:</b> {texto_correcto}</p>
        
        </div>
        """

    total = len(quiz)
    porcentaje = f"{round((score / total) * 100, 2)}%"

    data = {
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
                "https://script.google.com/macros/s/AKfycbybOrZVzoZYjIvagGcb7wfQwevVM93wIq4AMijPdLG82HXwXwxuC0p8pK4m-p4LACEYPg/exec",
                json={
                    "fecha": data["Fecha"],
                    "marca": data["Marca"],
                    "modelo": data["Modelo"],
                    "nombre": data["Nombre"],
                    "email": data["Email"],
                    "equipo": data["Equipo"],
                    "puntaje": data["Puntaje"],
                    "total": data["Total"],
                    "porcentaje": data["Porcentaje"]
                },
                timeout=10
            )

            print("GOOGLE STATUS:", r.status_code)
            print("GOOGLE RESPONSE:", r.text)

    except Exception as e:
            print("ERROR SHEETS:", e)
    
    return f"""
    <html>
    <body style="background:#f0ebf8;font-family:Arial;">
    <div style="width:70%;margin:auto;">
    
    <h1 style="background:#673ab7;color:white;padding:20px;border-radius:8px;">
    Resultado del examen
    </h1>
    
    <h2>{nombre}</h2>
    
    <h3>Puntaje: {score}/{total} ({porcentaje})</h3>
    
    <hr>
    
    {detalle}
    
    </div>
    </body>
    </html>
    """

# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
