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
api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    raise ValueError("Falta la API KEY de Groq en Render")

client = Groq(api_key=api_key)

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
"opciones": ["A","B","C","D"],
"correcta": "A"
}}
]

INSTRUCCIONES IMPORTANTES:

1. Basate ÚNICAMENTE en la información proporcionada.

2. Si el material contiene UN SOLO modelo de vehículo, generá un examen normal sobre ese modelo.

3. Si el material contiene DOS O MÁS modelos o versiones (por ejemplo Active, Allure, GT, etc.), distribuí las preguntas entre TODOS los modelos. Nunca concentres todas las preguntas en un solo modelo.

4. Repartí las preguntas de la forma más equilibrada posible entre todas las versiones encontradas.

5. Siempre que sea posible, generá preguntas COMPARATIVAS que obliguen a diferenciar un modelo de otro.

Ejemplos:
- ¿Qué versión incorpora techo panorámico?
- ¿Cuál versión posee ADAS?
- ¿Qué modelo equipa llantas de 18"?
- ¿Cuál versión ofrece cámara 360°?

6. Cuando una característica pertenezca únicamente a un modelo, utilizala como respuesta correcta y empleá características de los otros modelos como distractores.

7. Las opciones incorrectas deben ser creíbles y surgir de la información del documento. No inventes datos.

8. Evitá repetir preguntas sobre la misma característica.

9. Generá exactamente 15 preguntas.

Material:

{text[:8000]}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
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
    <body style="background:#f0ebf8;font-family:Arial;">
    <div style="width:60%;margin:auto;">
    <h1>Evaluación</h1>
    """

    body += form_start
    body += """
    <label>Email:</label><br>
    <input type="email" name="email" required><br><br>

    <label>Nombre:</label><br>
    <input type="text" name="nombre" required><br><br>

    <label>Equipo:</label><br>
    <input type="text" name="equipo" required><br><br>
    """

    for i, q in enumerate(quiz):
        body += f"<div><p><b>{q['pregunta']}</b></p>"

        for op in q["opciones"]:
            body += f'<input type="radio" name="q{i}" value="{op}" required> {op}<br>'

        body += "</div>"

    body += f"""
    <input type="hidden" name="quiz_id" value="{quiz_id}">
    <button type="submit">Enviar</button>
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
        indice = ord(correcta) - ord("A")
        if 0 <= indice < len(q["opciones"]):
            texto_correcto = q["opciones"][indice]
        else:
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
